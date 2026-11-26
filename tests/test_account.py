"""Exercise account gating and persistence through the Streamlit entry point."""
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import streamlit as st
from streamlit.testing.v1 import AppTest

from shopimpact.accounts import AccountInputError, _derive, _email, authenticate
from shopimpact.cloud import SaveConflict
from shopimpact.catalog import MONTHLY_CO2_TARGET
from shopimpact.earth import earth_mood

ENTRY = str(Path(__file__).resolve().parents[1] / "ShopImpactAI.py")


class AccountTests(unittest.TestCase):
    def sign_in(self, app, email, password):
        app.text_input[0].set_value(email)
        app.text_input[1].set_value(password)
        return next(button for button in app.button if button.label == "Sign in").click().run()

    def test_sign_in_gate_does_not_open_workspace(self):
        with patch("shopimpact.app.cloud_settings", return_value="test-dsn"):
            app = AppTest.from_file(ENTRY).run()
        self.assertFalse(app.exception)
        login = next(button for button in app.button if button.label == "Sign in")
        self.assertFalse(login.disabled)
        self.assertEqual(len(app.radio), 1)

    def test_account_mode_blocks_incomplete_configuration(self):
        with patch.dict(os.environ, {"SHOPIMPACT_REQUIRE_ACCOUNT": "1"}), patch.object(st, "secrets", {}):
            app = AppTest.from_file(ENTRY).run()
        self.assertIn("persistent account storage", app.info[0].value)
        self.assertTrue(next(button for button in app.button if button.label == "Sign in").disabled)
        self.assertEqual(len(app.radio), 1)

    def test_unconfigured_first_visit_shows_sign_in_with_demo_option(self):
        with patch.dict(os.environ, {"SHOPIMPACT_REQUIRE_ACCOUNT": "0"}), patch.object(st, "secrets", {}):
            app = AppTest.from_file(ENTRY).run()
            self.assertEqual(len(app.radio), 1)
            self.assertTrue(next(button for button in app.button if button.label == "Sign in").disabled)
            app.button(key="start_demo").click().run()
            self.assertEqual(app.radio(key="view").value, "Overview")

    def test_reopen_account_and_isolate_another_account(self):
        # Substitute only the storage transport so the app follows its actual session/rerun path.
        rows = {}

        def load(_dsn, owner):
            revision, serialized = rows.get(owner, (0, "{}"))
            return revision, json.loads(serialized)

        def write(_dsn, owner, revision, serialized):
            if load(_dsn, owner)[0] != revision:
                raise SaveConflict
            rows[owner] = (revision + 1, serialized)
            return revision + 1

        with (patch("shopimpact.app.cloud_settings", return_value="test-dsn"),
              patch("shopimpact.cloud.load_workspace", side_effect=load),
              patch("shopimpact.cloud.write_workspace", side_effect=write),
              patch("shopimpact.app.authenticate", side_effect=lambda dsn, email, password, ip, name: (email, "Tester"))):
            account = self.sign_in(AppTest.from_file(ENTRY).run(), "one@example.org", "test-credential")
            account.button(key="load_demo").click().run()
            account.number_input(key="monthly_target").set_value(55).run()
            account.radio(key="view").set_value("Profile").run()
            account.checkbox(key="_account_personalization_widget").uncheck().run()
            account.radio(key="view").set_value("Overview").run()
            account.button(key="account_sign_out").click().run()
            self.assertIn("Sign in to ShopImpact", [title.value for title in account.title])
            reopened = self.sign_in(AppTest.from_file(ENTRY).run(), "one@example.org", "test-credential")
            other = self.sign_in(AppTest.from_file(ENTRY).run(), "two@example.org", "test-credential")

        self.assertFalse(reopened.exception)
        self.assertTrue(reopened.session_state["purchases"])
        self.assertEqual(reopened.number_input(key="monthly_target").value, 55)
        self.assertFalse(reopened.session_state["account_personalization"])
        self.assertEqual(other.session_state["purchases"], [])
        self.assertEqual(other.number_input(key="monthly_target").value, MONTHLY_CO2_TARGET)

    def test_password_is_salted_and_checked(self):
        password = "a sample password for the test"
        self.assertNotEqual(_derive(password, bytes(16)), _derive(password, bytes([1]) * 16))
        stored_hash = f"{bytes(16).hex()}${_derive(password, bytes(16)).hex()}"
        with patch("shopimpact.accounts._connect") as connect, patch("shopimpact.accounts._limit", return_value=True):
            conn = connect.return_value.__enter__.return_value
            conn.execute.return_value.fetchone.return_value = ("owner", "Tester", stored_hash)
            self.assertEqual(authenticate("dsn", "Tester@Example.org", password, "127.0.0.1"), ("owner", "Tester"))
            with self.assertRaisesRegex(AccountInputError, "incorrect"):
                authenticate("dsn", "tester@example.org", "wrong", "127.0.0.1")
        self.assertEqual(_email(" Tester@Example.org "), "tester@example.org")

    def test_orbit_reacts_to_monthly_goal(self):
        self.assertEqual(earth_mood(0, 10, False)[0], "bright")
        self.assertEqual(earth_mood(5, 10, True)[0], "bright")
        self.assertEqual(earth_mood(8, 10, True)[0], "watch")
        self.assertEqual(earth_mood(10.1, 10, True)[0], "hazy")
