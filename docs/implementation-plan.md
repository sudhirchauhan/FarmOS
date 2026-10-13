# FarmOS vertical slices

Approved stack: Django / Django REST Framework, PostgreSQL / PostGIS, Celery / Redis,
NumPy / pvlib / OR-Tools / SciPy, React / TypeScript / Next.js, MapLibre / Three.js.
Authentication and user management are deferred by the owner. The unauthenticated
prototype is for local planning only; organization isolation must precede shared deployment.

## 1. First saved scenario
Farm wizard → visible demand/loss/financial assumptions → saved scenario → immutable
104-week run → demand, gross target, subscription benchmark and cash report.
Record full input snapshots and engine version. Acceptance: PRD arithmetic baseline,
zero customers, price changes independent of harvest, CAPEX/cash and negative cash.

## 2. Weekly supply and comparison
Exclusive physical beds and user-defined crop cohorts → occupation validation →
weekly harvest/category fulfillment → shortfall report → scenario clone/compare → CSV.
Acceptance: reject overbooked beds and excess footprint; apply loss once; allow
successive cycles; annual supply never overrides weekly deficits; repeat runs agree.
Yield profiles are uniform assumptions initially, not validated crop parameters.
No vertical uplift, storage, substitutions or purchased supply in this slice.

## 3. Core solar and resource feasibility (required before vertical yield claims)
Coordinates/time zone + obstacles + crop positions → pvlib solar geometry → direct
and diffuse PAR/DLI and basic shading → configurable light response → resource
balance → conservative weekly forecasts. Add provenance-backed crop library,
water/nutrient/biomass budgets, peak labour and stage-specific harvest profiles.
Acceptance: PRD §18.9 reference ephemerides, analytic shadows, DLI units, both
hemispheres and provisional behavior for missing data. Detailed 3-D UI follows
core physics; the physics requirement is not deferred to an optional enhancement.

## 4. Investment and risk decisions
24-month operational cash plus 10-year monthly financial model → staged CAPEX and
75% recovery gates → versioned uncertainty runs → asynchronous Pareto optimization.
Add durable Celery jobs, cancellation, retries, idempotent results and progress.
Acceptance: resource/cash conservation, repeatable seeds and infeasibility reasons.

## 5. Operations and fulfillment
Field tasks/actuals → harvest inventory → baskets/pack lists/deliveries/payments →
actual-versus-plan → user-approved calibration. Offline capture is subsequent.

## 6. Team access and deployment
OIDC/session security, organization isolation, roles, audit, read-only sharing,
backup/restore and production deployment. Build before exposing data to multiple
users; deferral is a sequencing choice, not removal of PRD security requirements.

## Current boundary
Slices 1–2 begin the planning core. SQLite supports a local development loop;
PostgreSQL is configurable but PostGIS models/integration are reserved for slice 3.
The initial solar slice now provides standalone position-level light studies with
pvlib SPA, explicit clear-sky/supplied radiation, opaque-box ray shading, diffuse sky
visibility and PAR/DLI integration. Its interface is available at `/sunlight`.
Canopy transmission/growth, crop response, spatial persistence and resource coupling
remain outstanding; it does not change planting yield assumptions.
There is no validated agronomic feasibility result, vertical forecast, optimizer,
10-year ledger or investment recommendation yet. Cost defaults are explicitly zero
where input is missing and produce warnings. Revenue assumes subscribed households;
actual collections are modeled separately. Monthly summaries bucket whole weeks
by start date rather than pretending to be daily calendar accounting.
