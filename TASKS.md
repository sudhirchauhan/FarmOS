# FarmOS implementation tasks

Work in vertical slices: schema → pure calculation → persisted API run → usable UI
→ meaningful acceptance tests. Django/DRF + Next.js; scientific tools as approved.
Authentication and user management remain deferred until the access/deployment slice.
All agronomic results stay provisional until evidence and calibration justify more.

## Completed foundations
- [x] P01 Farm setup, saved scenarios, cloning, immutable run snapshots and assumptions.
- [x] P02 104-week harvest, basket-group deficits, footprint/occupation validation,
  cash calculations, comparisons and CSV exports.
- [x] S01 pvlib solar position, opaque-box direct shading, isotropic diffuse visibility,
  PAR/DLI, local calendar/DST handling and a computed sunlight interface.
- [x] S02 Full-growing-period study links and explicit capped crop-light response;
  reject missing/conflicting dates and preserve study provenance.
- [x] R01 Weekly water conservation, pumping/efficiency limits, task-based labour,
  unknown requirements, constraint reports and resource CSV.
- [x] Q01 Frozen dependencies, setup/start scripts, local tests and GitHub CI definition.

## Next: resource and evidence core
- [x] R02 **Nutrient and biomass accounting.** Explicit dry-mass
  batches and exclusive allocations; available elemental N/P/K versus harvest removal.
  Acceptance: never allocate the same biomass twice, availability differs from total
  nutrient content, unknown composition stays unknown, balances conserve mass and
  deficits do not silently create fertilizer or crop-stress penalties.
- [ ] R03 Crop/variety and parameter-version library with sources, region suitability,
  low/base/high ranges, missing-field flags and import validation.
  Acceptance: scenario runs retain the exact parameter versions they used.
- [ ] R04 Soil water, weather/ET and effective rainfall; daily peak pumping/storage.
  Acceptance: drought and peak-day failures remain visible even with sufficient annual water.
- [ ] R05 Nursery lead time, stage-specific harvest profiles, rotations and seasonal
  suitability. Acceptance: impossible calendars and occupation conflicts fail clearly.
- [ ] R06 Calibrated light/stress responses, canopy transmission/growth/pruning,
  terrain/horizon and supplemental-light energy. Acceptance: PRD §18 reference cases,
  no correlated penalty counted twice and no tier-count yield multiplier.

## Spatial planning
- [ ] G01 PostgreSQL/PostGIS integration, farm polygon import, exclusive zones/beds,
  georeferencing, orientation, access and buffers. Test both geometry and SQL paths.
- [ ] G02 MapLibre editor and selectable growing positions connected to solar runs.
- [ ] G03 Three.js scene, seasonal shadows and PAR/DLI heatmaps driven by computed
  results; concept GIFs must not be mistaken for simulation output.

## Investment and risk
- [ ] F01 Dated CAPEX/OPEX/collections, inventory valuation and actual-versus-plan;
  calendar-accurate cash, 10-year P&L, depreciation/tax/debt assumptions and owner labour.
- [ ] F02 Staged CAPEX with net-cash recovery ≥75%, reserve and service gates.
  Acceptance: revenue/profit cannot unlock a gate that requires cash recovery.
- [ ] F03 NPV/IRR/payback, sensitivity and seeded uncertainty runs with provenance.
- [ ] J01 Durable Celery/Redis jobs: progress, cancellation, recovery, idempotency,
  time/resource limits and bounded retries. Test duplicate delivery and worker failure.
- [ ] O01 OR-Tools scheduling/allocation, nonlinear feasibility checks and Pareto
  comparisons. Acceptance: explain infeasibility; never recommend a universal optimum.

## Demand and operations
- [ ] D01 Subscription tiers, customer exclusions, diversity, substitutions, churn,
  two delivery windows and separate add-on ledgers.
- [ ] D02 Perishable inventory, eligible procurement, packing and route economics.
  Acceptance: no harvest lot sold twice; purchased supply remains separately traceable.
- [ ] A01 Field tasks, nursery batches, inputs, irrigation readings, harvest/grades,
  orders, deliveries, payments and actual-versus-plan.
- [ ] A02 User-approved calibration; coefficients never silently alter future scenarios.
- [ ] A03 Offline capture, synchronization and conflict handling.

## Reporting, access and release
- [ ] E01 XLSX/PDF/JSON exports, reproducible report bundles and provenance history.
- [ ] U01 Mobile-first wizard refinements, meaningful charts and Hindi/English UI.
- [ ] SEC01 OIDC/session auth, organizations, roles, authorization, audit and PII-safe
  sharing. Deferred by owner instruction; required before shared deployment.
- [ ] DEP01 Managed database/object storage, encrypted secrets, observability,
  backup/restore tests, deployment and target-infrastructure performance checks.

## Current verification
Engine 0.3: 49 backend tests, 6 browser tests, migration consistency and production
build passed locally on 13 October 2026. R02 includes persisted nutrient ledgers,
exclusive biomass allocation, UI editing, unknown-input flags and CSV export.
The next implementation task is R03. Remote CI and fresh-task restoration have not
been verified. Conceptual screens are not counted as implemented features.
