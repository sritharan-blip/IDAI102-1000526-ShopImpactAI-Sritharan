"""Exercise account gating and persistence through the Streamlit entry point."""
import json
import os
from pathlib import Path
from time import time
import unittest
from unittest.mock import patch

import streamlit as st
from streamlit.testing.v1 import AppTest

from shopimpact.cloud import SaveConflict, account_id
from shopimpact.catalog import MONTHLY_CO2_TARGET
from shopimpact.earth import earth_mood

ENTRY = str(Path(__file__).resolve().parents[1] / "ShopImpactAI.py")


class GoogleUser(dict):
    def __init__(self, subject):
        self.is_logged_in = subject is not None
        super().__init__(sub=subject, iss="https://accounts.google.com", exp=time() + 3600, name="Demo")


class AccountTests(unittest.TestCase):
    def test_sign_in_gate_does_not_open_workspace(self):
        with patch("shopimpact.app.cloud_settings", return_value="test-dsn"), patch.object(st, "user", GoogleUser(None)):
            app = AppTest.from_file(ENTRY).run()
        self.assertFalse(app.exception)
        self.assertIn("Continue with Google", [button.label for button in app.button])
        self.assertFalse(app.radio)

    def test_account_mode_blocks_incomplete_configuration(self):
        with patch.dict(os.environ, {"SHOPIMPACT_REQUIRE_ACCOUNT": "1"}), patch.object(st, "secrets", {}):
            app = AppTest.from_file(ENTRY).run()
        self.assertIn("need to be configured", app.error[0].value)
        self.assertFalse(app.radio)

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
              patch("shopimpact.cloud.write_workspace", side_effect=write)):
            with patch.object(st, "user", GoogleUser("1")):
                account = AppTest.from_file(ENTRY).run()
                account.button(key="load_demo").click().run()
                account.number_input(key="monthly_target").set_value(55).run()
                account.radio(key="view").set_value("Profile").run()
                account.checkbox(key="_account_personalization_widget").uncheck().run()
                account.radio(key="view").set_value("Overview").run()
                reopened = AppTest.from_file(ENTRY).run()
            with patch.object(st, "user", GoogleUser("2")):
                other = AppTest.from_file(ENTRY).run()

        self.assertFalse(reopened.exception)
        self.assertTrue(reopened.session_state["purchases"])
        self.assertEqual(reopened.number_input(key="monthly_target").value, 55)
        self.assertFalse(reopened.session_state["account_personalization"])
        self.assertEqual(other.session_state["purchases"], [])
        self.assertEqual(other.number_input(key="monthly_target").value, MONTHLY_CO2_TARGET)

    def test_identity_uses_subject_and_rejects_expired_token(self):
        user = GoogleUser("1")
        original = account_id(user)
        self.assertIsNotNone(original)
        user["email"] = "changed@example.com"
        self.assertEqual(account_id(user), original)
        user["exp"] = time() - 1
        self.assertIsNone(account_id(user))

    def test_orbit_reacts_to_monthly_goal(self):
        self.assertEqual(earth_mood(0, 10, False)[0], "bright")
        self.assertEqual(earth_mood(5, 10, True)[0], "bright")
        self.assertEqual(earth_mood(8, 10, True)[0], "watch")
        self.assertEqual(earth_mood(10.1, 10, True)[0], "hazy")
