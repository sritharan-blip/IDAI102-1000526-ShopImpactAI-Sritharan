<div align="center">

![ShopImpactAI — Your everyday. Reimagined.](assets/shopimpact-banner.gif)

# ShopImpactAI

### Your everyday. Reimagined.

A personal impact studio for the space between **wanting something** and **choosing it well**.

[![App checks](https://github.com/sritharan-blip/IDAI102-1000526-ShopImpactAI-Sritharan/actions/workflows/tests.yml/badge.svg)](https://github.com/sritharan-blip/IDAI102-1000526-ShopImpactAI-Sritharan/actions/workflows/tests.yml)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3153D5?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.60%2B-7450DA?style=flat-square)
![Local recommendations](https://img.shields.io/badge/Recommendations-TF--IDF-117D78?style=flat-square)

[The experience](#the-experience) · [Run locally](#run-locally) · [How it thinks](#how-it-thinks) · [Under the glass](#under-the-glass) · [Classmate feedback](#classmate-feedback)

</div>

---

## The experience

Track what you spend. Explore your estimated footprint. Find products that fit your intent. Take a breath before the next purchase.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/screenshots/midnight-overview.jpg">
  <img src="assets/screenshots/daylight-overview.jpg" alt="ShopImpact's liquid-glass dashboard with its monthly snapshot, floating data cards, and animated orb" width="100%">
</picture>

<p align="center"><sub>Actual Chrome captures with the demo ledger. Daylight clarity. Midnight atmosphere.</sub></p>

<details>
<summary><strong>Explore Midnight and Decision lab</strong></summary>

![Midnight dashboard](assets/screenshots/midnight-overview.jpg)

![Decision lab with cost-per-use analysis, budget fit, and a saved purchase pause plan](assets/screenshots/decision-lab.jpg)

</details>

| A clearer view | What you can do |
| :--- | :--- |
| **Liquid glass, two ways** | Frosted layers, floating data cards, and a Daylight / Midnight palette. The 3D Earth backdrop turns to a distinct angle on each page. |
| **Orbit, your Earth mascot** | Drag the mini Earth to spin it and double-tap to make it celebrate. Its expression, colors, and haze react as this month's estimated footprint approaches or exceeds your goal. |
| **Your impact, in motion** | Follow monthly spending, category estimates, lower-impact choices, goals, and your recent activity. The hero cards use your actual session data. |
| **Smart matches** | Describe what you need. A local content model ranks the demo catalog by text similarity, category, budget, and estimated reduction, with reasons for every pick. |
| **Decision lab** | Explore cost per use and budget fit. Save a pause plan to your wishlist for tomorrow, three days, or next week. |
| **A more intentional wishlist** | Keep a shortlist, separate needs from wants, add notes, and choose a date to revisit an idea. |
| **The full shopping journey** | Explore demo products, a cart, simulated checkout, orders, returns, rewards, and analytics in one connected session. |

**Motion with an off switch.** Floating panels, orbital light, gentle card lifts, and page entrances respect your operating system's reduced-motion preference. You can also pause them under **Display & accessibility → Reduce motion**, or enable **High contrast**.

**Color changes happen together.** Text, fields, selected controls, and their backgrounds use a single active palette. The animation lives in the glass and light rather than in fading text colors.

<details>
<summary><strong>Explore all 12 spaces</strong></summary>

| Space | Inside |
| :--- | :--- |
| Overview | Monthly snapshot, goals, footprint trend, and personal activity brief |
| Discover | Search, filter, product details, and explainable smart matches |
| Decision lab | Cost per use, budget fit, and wishlist pause plans |
| Log a purchase | Purchase ledger, literal search, CSV import, and export |
| Wishlist | Need / want priorities, notes, estimated cost, and revisit dates |
| Cart & checkout | Quantities, totals, and a non-binding demo checkout |
| My orders | Illustrative session orders and tracking stages |
| Impact analytics | Category summaries, comparisons, and budget pacing |
| Swap studio | Assumed lower-factor scenarios and comparison baskets |
| Eco rewards | Milestones, progress, and weekly challenges |
| Help & returns | Local demo return and support forms |
| Profile | Session profile and purchase-history personalization preferences |

</details>

> **A prototype, with clear boundaries.** Commerce, ratings, product availability, payments, order tracking, returns, and support are demonstrations. Nothing is bought, charged, shipped, or sent to a support team. Carbon estimates are directional comparisons, not verified product lifecycle assessments.

## Run locally

Requires **Python 3.10 or later**. Choose **Explore the demo** on the sign-in screen to try an unconfigured local app without API keys or Streamlit secrets.

<details open>
<summary><strong>Windows PowerShell</strong></summary>

```powershell
git clone https://github.com/sritharan-blip/IDAI102-1000526-ShopImpactAI-Sritharan.git
cd IDAI102-1000526-ShopImpactAI-Sritharan
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run ShopImpactAI.py
```

If activation is restricted, run the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run ShopImpactAI.py
```

</details>

<details>
<summary><strong>macOS / Linux</strong></summary>

```bash
git clone https://github.com/sritharan-blip/IDAI102-1000526-ShopImpactAI-Sritharan.git
cd IDAI102-1000526-ShopImpactAI-Sritharan
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run ShopImpactAI.py
```

</details>

Open the local address printed in your terminal, usually `http://localhost:8501`. Choose **Load demo data** for a populated dashboard. Stop the server with **Ctrl+C**.

For Streamlit Community Cloud, select this repository, the `main` branch, and `ShopImpactAI.py` as the main file.

### Enable Google sign-in and cloud saves

1. In [Google Auth Platform](https://console.cloud.google.com/auth/overview), configure an external app audience and create a **Web application** OAuth client. If the app is in testing, add the Google accounts that should be able to sign in.
2. Add your exact callback URL under **Authorized redirect URIs**. For example, use `https://YOUR-APP.streamlit.app/oauth2callback` for Streamlit Community Cloud or `http://localhost:8501/oauth2callback` for local testing. Use the same value in the app's secrets.
3. Create a hosted PostgreSQL database with a TLS certificate trusted by the system. Run [`tools/cloud_schema.sql`](tools/cloud_schema.sql) in its SQL editor. Give the app's dedicated database role `SELECT`, `INSERT`, and `UPDATE` on `shopimpact_workspaces`.
4. Copy [`.streamlit/secrets.example.toml`](.streamlit/secrets.example.toml) into the deployed app's **Settings → Secrets**, or into the ignored `.streamlit/secrets.toml` for local testing. Fill in the Google client ID and secret, the Postgres connection string, and a random cookie secret generated with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
5. Restart the app. Sign in, add a purchase, then reopen the app in a fresh session to check that your data returns. Sign in with a second test account to verify it opens its own workspace.

The sign-in screen is shown to new visitors. After signing in, returning users go directly to their workspace in the same browser while Streamlit's 30-day sign-in cookie is active. Signing out clears the cookie. On hosts that support deployment environment variables, set `SHOPIMPACT_REQUIRE_ACCOUNT=1` to hide the demo option when credentials are missing. Keep the values in your host's secret settings.

## How it thinks

### Explainable matches, without an API

The recommender fits **TF-IDF** vectors to the small built-in catalog and compares them with your shopping intent using cosine similarity. Category affinity and the catalog's estimated reduction add explicit ranking signals. A selected category and maximum budget are hard filters.

When intent is blank, recent purchase descriptions can personalize the ranking. Disable that use of history in **Profile**. A score ranks catalog items; it is not a confidence probability, an environmental certification, or a generative AI answer.

### Estimates that keep their units

```text
Category estimate (kg CO2e) = category factor × price ÷ 10
Estimated reduction (kg CO2e) = max(0, recorded baseline − recorded footprint)
Cost per use ($) = price ÷ (uses per week × 52 × years kept)
```

Catalog checkout records its demo product factor and the category-average comparison baseline at purchase time. Manually choosing a greener scenario uses an assumed factor of at most 0.4 kg CO2e per $10. Decision lab uses your own usage and lifespan assumptions. These tools make assumptions visible; they do not measure product emissions or predict durability.

<details>
<summary><strong>View the category factors</strong></summary>

| Category | Estimated kg CO2e per $10 |
| :--- | ---: |
| Electronics | 3.5 |
| Fast fashion / leather | 2.8 |
| Groceries / organic food | 0.4 |
| Sustainable apparel / second-hand | 0.2 |
| Beauty & personal care | 1.1 |
| Home & living | 1.5 |

These are broad illustrative factors. Real footprints vary with materials, manufacturing, location, transport, energy sources, and methodology. Use this app for exploration rather than formal footprint reporting.

</details>

## Your data, your copy

In **local demo mode**, working data lives in Streamlit session state. A session ending or server restarting can clear it. Download a backup to keep your ledger and wishlist.

With **Google sign-in enabled**, ShopImpact automatically saves the ledger, wishlist, cart, demo order history, saved swaps, comparison basket, goals, and display and recommendation preferences to the signed-in account's PostgreSQL workspace. Temporary demo support and return requests, local profile fields, and demo delivery details stay in the current session. A cloud revision check prevents two tabs from silently overwriting each other.

| Tool | What it preserves |
| :--- | :--- |
| CSV import | Required `product`, `category`, `price`; optional ISO `date` and `brand`. Emissions are recalculated from category and price. |
| JSON backup v2 | Ledger, wishlist, recorded footprints, comparison baselines, identifiers, and wishlist dates. |
| Legacy v1 restore | Recorded CO2 snapshots are retained where present. The ambiguous old `green_savings` field is discarded, and reductions are recomputed from the footprint and baseline. |

CSV imports are limited to **5 MB / 5,000 rows**; invalid rows are skipped and reported. Backups support **5 MB, 5,000 purchases, and 500 wishlist ideas**. Invalid backups reject the entire restore, leaving your current data intact. Backups exclude profile, cart, orders, support requests, and display preferences.

<details>
<summary><strong>A purchase CSV example</strong></summary>

```csv
date,product,category,brand,price
2026-01-15,Refill hand wash,Beauty & personal care,Ethique,18.00
2026-01-16,Second-hand reading lamp,Home & living,Etsy (vintage),35.00
```

Category names must match the factor table. Dates must use `YYYY-MM-DD` and cannot be in the future. Prices must be finite and non-negative. A supplied `co2` column is ignored.

</details>

Purchases and profile details are not sent to retailers, support teams, or AI services. Account mode stores the workspace in the configured PostgreSQL database. Keep credentials, virtual environments, browser profiles, and private data out of commits.

## Under the glass

| Layer | Where it lives |
| :--- | :--- |
| Entry point & navigation | `ShopImpactAI.py`, `shopimpact/app.py` |
| Glass, motion & appearance tokens | `shopimpact/theme.py`, `shopimpact/assets/app.css` |
| Orbit's 3D renderer | `shopimpact/earth.py`, `shopimpact/assets/earth.js` |
| Google sign-in and cloud saves | `shopimpact/cloud.py`, `tools/cloud_schema.sql` |
| Reusable visual components | `shopimpact/ui.py` |
| Purchase math & catalog | `shopimpact/logic.py`, `shopimpact/catalog.py` |
| Local recommendation model | `shopimpact/recommendations.py` |
| Decision lab | `shopimpact/decisions.py` |
| Imports & snapshot backups | `shopimpact/data.py` |
| Feature views | `shopimpact/marketplace.py`, `ledger.py`, `insights.py`, `wishlist.py` |
| Reproducible animated cover | `tools/generate_banner.py` |
| Python Turtle animation | [`tools/turtle_demo.py`](tools/turtle_demo.py) |

The interface uses Streamlit and Plotly. pandas handles ledger summaries; Pillow and NumPy generate the self-hosted animated cover. There are no external image servers or API calls behind the app's artwork.

The Earth backdrop uses a locally served 2048 × 1024 satellite map from [NASA Earth Observatory's Blue Marble: Next Generation](https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/base-map/), produced by Reto Stöckli at NASA Goddard Space Flight Center. The [resized JPEG](https://github.com/MaxwellLee/physics-lab/blob/main/assets/textures/SOURCES.md#earth) was prepared by the Physics Lab project.

### Python Turtle animation

The desktop animation traces three steps from Decision lab: check the budget, estimate cost per use, and save a pause plan. Run it from the repository root on a computer with Python and Tk installed:

```bash
python tools/turtle_demo.py
```

Press **Space** to play or replay and **Esc** to close the window. Python Turtle renders the desktop demo. The Streamlit dashboard uses Plotly for charts, and Pillow generates the README banner.

### Checks that follow the experience

```bash
python -m compileall -q ShopImpactAI.py shopimpact tools tests
python -m unittest discover -s tests -v
```

GitHub Actions tests Python **3.10, 3.12, and 3.14**. A separate Chrome run checks real theme switches, foreground/background contrast, dropdowns, forms, mobile layout, and reduced motion, and saves screenshots as artifacts.

To run the browser checks locally, install Google Chrome and the optional test dependency:

```bash
python -m pip install playwright
python tests/browser_smoke.py
```

Rebuild the animated cover with `python tools/generate_banner.py`.

## Classmate feedback

I’m asking six classmates to try ShopImpactAI and tell me where it makes a shopping decision easier or where they get stuck. These sample recommendations give each person a starting point to confirm or refine. Adrian and Kavin are listed for review, and the other four names are placeholders. Review dates and responses are pending.

| Reviewer | Review date | Example recommendation to review | Feature I implemented |
| :--- | :--- | :--- | :--- |
| Adrian | Pending | I’d like to log something I bought and see its footprint without doing the math. | Log a purchase calculates an estimated footprint from the category and price. |
| Kavin | Pending | I want to see which category makes up the biggest part of my footprint. | Impact analytics shows estimated CO₂e by category. |
| Rohan (sample) | Pending | Before buying something new, I’d like to see a lower-impact option and compare the estimates. | Swap studio compares alternative scenarios and lets you save a swap. |
| Diya (sample) | Pending | I’d like to see what something would cost each time I use it and give myself a few days to think. | Decision lab calculates cost per use and saves a pause plan with a revisit date in Wishlist. |
| Nikhil (sample) | Pending | If I describe what I’m looking for, I’d like to know why the app picked a certain product. | Discover uses shopping intent and filters to suggest catalog items and explain the matches. |
| Meera (sample) | Pending | I’d like the Earth mascot to help me tell when I’m close to my monthly footprint goal. | Orbit changes its expression, colors, and haze based on the recorded monthly estimate and goal. |

The [six-person usability feedback record](docs/USABILITY_FEEDBACK.md) has one task per reviewer and space for ratings, comments, and changes made after testing.

---

<div align="center">

**A little less impulse. A little more intention.**

Built by [sritharan-blip](https://github.com/sritharan-blip).

</div>
