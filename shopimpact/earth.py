"""Render Orbit using the same monthly estimate as the dashboard."""
from functools import lru_cache
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).parent / "assets"
PAGE_ANGLES = {
    "Sign in": (-1.12, .20),
    "Overview": (-.52, .20),
    "Discover": (.47, .15),
    "Decision lab": (1.46, -.18),
    "Log purchase": (-1.70, .40),
    "Wishlist": (2.10, .20),
    "Cart & checkout": (-2.42, -.20),
    "My orders": (2.68, .03),
    "Impact analytics": (-.13, .64),
    "Swap studio": (.95, -.47),
    "Eco rewards": (-.96, -.35),
    "Help & returns": (1.85, .65),
    "Profile": (-2.90, -.55),
}


def earth_mood(estimate: float, goal: float, has_purchases: bool) -> tuple[str, str]:
    # Leave a little room for a near-goal state before switching to the hazy planet.
    if not has_purchases:
        return "bright", "Awaiting your first purchase"
    if estimate > goal:
        return "hazy", "Above your CO₂e goal"
    if estimate >= goal * 0.75:
        return "watch", "Close to your CO₂e goal"
    return "bright", "Below your CO₂e goal"


@lru_cache(maxsize=1)
def _earth_script() -> str:
    return (ASSETS / "earth.js").read_text(encoding="utf-8")


def render_earth_background(page: str, reduce_motion: bool, high_contrast: bool = False) -> None:
    yaw, tilt = PAGE_ANGLES[page]
    st.html(
        f'<div class="si-earth-scene" aria-hidden="true" data-background="1" '
        f'data-contrast="{int(high_contrast)}" data-yaw="{yaw}" data-tilt="{tilt}" '
        f'data-reduce="{int(reduce_motion)}"><canvas width="360" height="360"></canvas></div>'
        f'<script>{_earth_script()}</script>',
        unsafe_allow_javascript=True,
    )


def render_earth(estimate: float = 0, goal: float = 1, has_purchases: bool = False,
                 reduce_motion: bool = False, *, on_login: bool = False) -> None:
    mood, label = earth_mood(estimate, goal, has_purchases)
    if on_login:
        label = "Your shopping footprint has a face"
        detail = "Log purchases to see how Orbit reacts to your monthly estimate."
    elif has_purchases:
        detail = f"{estimate:,.1f} kg CO₂e estimated this month · {goal:,.0f} kg goal"
    else:
        detail = "Orbit reacts to this month’s estimated shopping footprint."
    # The script is a bundled asset. Only internal labels, numbers and booleans enter this markup.
    st.html(
        f'<section class="si-earth-card" data-mood="{mood}">'
        '<div class="si-earth-copy"><div class="si-kicker">EARTH MASCOT</div>'
        '<h2>Meet Orbit</h2>'
        f'<p class="si-earth-status">{label}</p><p>{detail}</p>'
        '<p class="si-earth-help">Drag or use arrow keys to spin.</p></div>'
        f'<div class="si-earth-model" data-mood="{mood}" data-reduce="{int(reduce_motion)}">'
        '<canvas width="300" height="300" tabindex="0" aria-label="Rotate Orbit with the arrow keys"></canvas>'
        '<span class="si-earth-fallback" role="img" aria-label="Earth">🌍</span>'
        '</div></section>'
        f'<script>{_earth_script()}</script>',
        unsafe_allow_javascript=True,
    )
