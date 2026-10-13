# FarmOS

Django + React planning core for the [product specification](docs/FarmOS_Product_Requirements_Specification.md).
See the [vertical-slice plan](docs/implementation-plan.md) and [JPG/GIF mockups](docs/mockups/README.md).

## Implemented

- Farm setup and explicit demand, loss, cost, cash and family-labour assumptions.
- Saved scenarios, cloning, full-replacement revisions and immutable run snapshots.
- Deterministic 104-week harvest from user-defined planting cohorts, category demand,
  delivered supply, shortfall/surplus, and cash calculations using decimal arithmetic.
- Physical bed footprint and occupation checks; no independent stacked-layer yield.
- Weekly results, scenario comparisons, assumption provenance and CSV exports.
- Responsive Next.js interface connected to Django REST Framework.
- A computed sunlight lab: NREL SPA solar position via pvlib, direct ray/box
  shadows, isotropic diffuse-sky visibility, oriented PAR and daily DLI. Supports
  supplied midpoint DNI/DHI or explicitly assumed clear-sky radiation, 15/30/60
  minute intervals, local calendar days and bounded annual runs.
- Optional crop-light coupling with complete growing-period study coverage,
  explicit linear DLI response curves and immutable provenance snapshots.
- Weekly water conservation, labour-capacity budgets, unknown-input flags and
  resource shortfall reports with CSV export.

All results are provisional. Solar/PAR/DLI can constrain unshaded crop potential
through user-assumed curves. Canopy growth, calibrated crop parameters, nutrient/biomass feasibility,
10-year financials, optimization and operations are subsequent slices.
Subscription revenue and collections are independent of fulfilled supply; refund
and service-dependent billing rules are not yet modeled. Zero costs generate a warning.

Authentication/user management are intentionally deferred. This is a local prototype;
shared deployment needs the authorization and isolation slice first.

## Install and run

Requires Python 3.12+, uv, and Node.js 20.9+ with npm. Run from the checkout root:

Use `bash scripts/setup.sh` for the repeatable installation, then `bash scripts/dev.sh`.
The equivalent individual steps are:

```bash
UV_CACHE_DIR=/workspace/.cache/uv uv venv --allow-existing .venv
UV_CACHE_DIR=/workspace/.cache/uv uv pip sync --python .venv/bin/python --require-hashes backend/requirements.txt
.venv/bin/python backend/manage.py migrate
cd frontend
npm --cache /workspace/.cache/npm ci
cd ..
bash scripts/dev.sh
```

The script starts Django on port 8000 and Next.js on port 3000, both on loopback.
Next.js proxies `/api/` to Django. Set `DJANGO_API_ORIGIN` before starting/building
Next.js to use another backend origin. Each saved calculation creates a new scenario;
the API also supports full scenario updates and cloning. Runs remain immutable.

SQLite is the default local database and is ignored by Git. Set `DATABASE_URL` to
a PostgreSQL connection URL to use PostgreSQL; that path has not yet been integration
tested. PostGIS spatial models arrive with the solar/resource slice. Celery and the
scientific packages will be installed when their executable slices are added, rather
than introducing unused infrastructure now. Read configuration in `backend/config/settings.py`.

## Validation

```bash
.venv/bin/python backend/manage.py test planning
.venv/bin/python backend/manage.py check
.venv/bin/python backend/manage.py makemigrations --check --dry-run
cd frontend
npm run typecheck
npm run build
```

`npm run test:e2e` exercises the browser-to-API workflow. Playwright starts the
servers if needed and reuses existing local servers. Build the frontend first;
the automatic frontend server uses the production build. In CI it starts fresh servers.
Tests use installed Chromium if present; otherwise install Playwright Chromium with
`npx playwright install chromium`. Set `CHROMIUM_PATH` for a custom browser.
Browser tests create farms with a `Browser test` prefix in the development database.
Do not run against a database containing real farm data.
The GitHub Actions workflow runs the same backend, migration, build and browser checks.

## Calculation policies

Demand is households × basket kg per week, with an annual benchmark of 52 weeks.
Combined loss is applied once to gross harvest. Cohorts use an explicitly provisional
uniform daily harvest profile over their harvest window. Bed occupation runs from
sowing through the end of harvest; back-to-back cycles are allowed, overbooking is
rejected. All physical bed areas count once against total farm area.

Weekly supply is fulfilled within each basket group without carryover, substitutions
or procurement. Weekly excess is reported as surplus and earns no assumed revenue.
Accrued subscription revenue uses 12 months/52 weeks; actual cash collection occurs
on calendar month starts and is multiplied by the paid fraction. No full payment is
invented for a partial opening month. Fixed OPEX is annualized over 52 weeks, variable
cost uses delivered kg, initial CAPEX is paid in the first week. Family labour reduces
economic surplus, not cash. Monthly summaries group entire weeks by start date.
Money is displayed to two decimal places; mass to three. Calculations retain higher
precision, so displayed weekly totals may differ slightly from rounded aggregate totals.

## API

- `POST/GET /api/farms/`, `GET /api/farms/{id}/`
- `POST/GET /api/scenarios/`, `GET/PUT /api/scenarios/{id}/`
- `POST /api/scenarios/{id}/clone/`
- `POST /api/scenario-runs/` with `{"scenario": "uuid"}`; `GET` list/detail
- `GET /api/scenario-runs/{id}/weekly-export/`
- `GET /api/scenario-runs/{id}/resource-export/`
- `GET /api/scenario-runs/comparison/?run={uuid}&run={uuid}` (2–4 distinct runs)
- `GET /api/health/`
- `POST /api/solar-runs/`, `GET /api/solar-runs/{id}/` — immutable standalone light studies.

## Sunlight model

Open the Sunlight lab from the planning header.
Saved light studies can be reopened using `/sunlight?run={id}`; reloading preserves
the computed result and restores its assumptions. Coordinates are local east/north/up
metres at the supplied latitude/longitude, referenced to true north. Obstacles are
ground-rooted, opaque, axis-aligned boxes; points inside/on their surfaces are rejected.
Tilt is 0° horizontal to 90° vertical; surface azimuth is clockwise from north.
Point-level direct radiation uses surface incidence and ray/box intersections.
Direct-shade hours count only intervals with positive direct radiation incident on
that surface before obstruction; a back-facing surface is not counted as shaded.
Diffuse radiation uses an isotropic sky, tilt factor and projected visibility from
10° azimuth × 5° elevation quadrature. Reflected light and transmissive vegetation
are not modeled. DLI integrates midpoint PAR over actual interval seconds, including
23/25-hour daylight-saving days. PAR = irradiance × explicit PAR fraction × explicit
photon conversion. Nighttime radiation is zero.

Clear-sky radiation uses pvlib's Ineichen model with user-assumed Linke turbidity,
not historical cloud/weather observations. Supplied DNI/DHI arrays must have one
sample per midpoint and a source/version note. The synchronous endpoint is bounded
to 24 positions, 32 obstacles and 250,000 position-interval combinations; larger
scene sweeps require the future asynchronous-job slice. Up to 366 local days can
be computed within that budget. Results retain input and library versions and do
not modify planting yields or claim agronomic feasibility.

Validation includes the published Colorado example from the
[NREL SPA report](https://www.nrel.gov/docs/fy08osti/34302.pdf), analytic wall
shadows, orientation effects, diffuse-only DLI, both hemispheres, date-line equivalence,
DST day lengths and deterministic results. This is initial verification, not complete
field calibration or all PRD §18 acceptance gates. A 365-day hourly one-position run
produced 8,760 samples in about 0.36 seconds on the current machine; larger workloads
have not been benchmarked.

## Light coupling and resource budgets (engine 0.2)

Each planting can include `light_response` with `solar_runs` (1–4 IDs), `point_id`,
`minimum_dli`, `optimum_dli` and `source_note`. Response is zero at/below minimum,
linear to optimum and capped at one. Mean daily response over sowing through harvest
end constrains gross cycle yield, which must represent unshaded potential. It is
an empirical assumption, not a calibrated growth model. Combined loss is applied
once afterward. Every growing day needs a study value. Missing dates/positions,
conflicting dates and mixed-site studies are rejected; one day is not reused for
other seasons. Runs snapshot DLI, study inputs, sources, versions and fingerprints.
At most 64 distinct studies are supported per synchronous run.

Enable `resources.water` with `storage_capacity_m3`, `opening_storage_m3`,
`weekly_inflow_m3`, `weekly_evaporation_m3`, `weekly_pumping_limit_m3`,
`irrigation_efficiency` and optional `weekly_overrides` of `{week, inflow_m3?, evaporation_m3?}`.
Each crop's `daily_water_l_per_m2` drives demand during occupation. Weekly chronology:
opening storage + inflow → overflow at capacity → evaporation → pumping-limited
withdrawal → closing storage. Withdrawal × efficiency is delivered crop water;
conveyance loss is separate. Evaporation cannot exceed available water. This is a
weekly assumed-demand model, not weather-driven ET or daily peak assessment.

Enable `resources.labour` with `available_hours_per_week`, optional
`fixed_hours_per_week`, `packing_hours_per_delivered_kg` and `delivery_hours_per_week`.
Crop parameters are `sowing_hours_per_m2`, `maintenance_hours_per_m2_week` and
`harvest_hours_per_kg`. Sowing is dated, maintenance is prorated to occupation days,
harvesting uses gross mass and packing uses delivered mass. Delivery hours apply
to supplied weeks. Owner-labour valuation remains a separate financial assumption;
extra hiring or wages are not silently introduced.

Blank crop resource requirements stay unknown rather than zero. Capacity results
are `true`, `false` or `null` (incomplete/not assessed). Water/labour deficits are
constraints and do not invent another yield penalty without a response rule.
Nutrients, root competition, calibrated curves and combined-stress validation remain
outstanding before agronomic feasibility claims.
