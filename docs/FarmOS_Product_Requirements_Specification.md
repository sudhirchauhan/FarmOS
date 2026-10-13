# FarmOS — Natural Multi-Layer Integrated Farming Platform
## Product Requirements Document (PRD) and Technical Specification
**Version:** 1.2 | **Status:** Product requirements proposed; technology stack approved | **Primary market:** India | **Currency:** INR

## 1. Product vision
Build a web-first, mobile-friendly farm design, production planning, operations and financial optimization application. It must answer: *What is the minimum viable land, water, capital and labour configuration that can reliably fulfil a specified weekly customer basket, while maximizing risk-adjusted net profit and recovering staged investment?*

Do not equate theoretical multi-layer area with independent full-sun growing area. Biological and financial constraints must be explicit, measurable and adjustable. Support natural/ZBNF, organic, regenerative, conventional and hybrid systems as user-defined methods rather than claiming one method is inherently superior.

## 2. Users and permissions
- **Owner / entrepreneur:** designs farms, chooses optimization objectives, approves scenarios, controls budgets.
- **Agronomist:** maintains crop/variety data, climate suitability, layer compatibility, light/water/nutrient requirements, pest risks and confidence levels.
- **Farm manager:** schedules tasks, sowing, transplanting, harvest and input procurement.
- **Field worker:** mobile-first task checklist, harvest and inventory entry, optional offline sync.
- **Sales / CSA manager:** customer preferences, orders, weekly baskets, delivery routes, retention and price experiments.
- **Finance manager:** validates costs, cash flows, actual-versus-plan, inventory valuation and investment stage gates.
- **Admin:** user management, audit trail, data imports, backups, permission policies.

## 3. Initial reference case and benchmarks
Editable defaults: 50 households; 4 persons/household; 8 kg vegetables/household/week; 2 deliveries/week; ₹5,500/household/month; 20% total harvest/postharvest loss; 20,800 kg annual delivered demand; 26,000 kg annual gross harvest target; 1/2/3/4-acre scenarios; ₹5–10 lakh target initial farm CAPEX (excluding land purchase and extraordinary water works unless explicitly added). Non-bulk vegetables include onion and garlic; exclude potatoes and other bulk staples from the base basket. Fruits, mushrooms, milk, eggs, spices and value-added goods have separate product lines and revenue ledgers unless explicitly included in a customer basket.

**Abhinav transcript reference:** Interview describes 20 customers per acre receiving ~5 kg vegetables per household per week (100 kg/week delivered), ~24 crop types split among climbing, fruiting, leafy and root groups, 15-day staggered planting, boundary fruit trees, direct-to-customer sales, twice-weekly delivery and later investment in protected growing. Transcript separately mentions 40 kg/acre/day vegetables; these claims are not reconciled. Store them as separate testimonial benchmarks, not validated production observations. Source: user-provided Hindi transcript, particularly lines 185–226, 323–351, 398–455 and 753–769.

## 4. Product principles and non-goals
- Every scenario reproducible from versioned assumptions, engine version and random seed where stochastic.
- Every result shows units, time period, confidence class (measured, published, expert estimate, user assumption, testimonial), provenance and sensitivity.
- No double counting of land, trellis surface, fruit mass, harvests, revenues, labour, compost nutrients or water.
- No guaranteed yields, organic certification, pesticide efficacy or medical claims.
- A user can create a useful first scenario without supplying exhaustive data; missing inputs use visible, clearly labelled defaults.
- First release is a planning decision-support tool, not a crop-growth digital twin or legally authoritative certification system.

## 5. Functional requirements
### FR-01 Project setup
Create farms with coordinates or approximate region, agro-climatic zone, land tenure (owned/leased), land price/rent, area, boundary shape, slope, soil texture, soil tests, salinity/pH, water sources, rainfall, power availability, market distance, workforce and investment limits. Unknown values are explicitly unknown; app presents sensitivity ranges.

### FR-02 GIS/spatial farm designer
- Draw/import boundary as polygon (GeoJSON/KML), measure acreage and perimeter.
- Allocate zones for annual beds, orchard/food forest, understory, shade, trellises, paths, hedges, pond, nursery, packing, compost, livestock, buildings, solar and reserves.
- Define physical bed widths, lengths, orientation, paths and access for e-rickshaw/handcart.
- Define **vertical layers** per footprint: canopy, sub-canopy, shrubs, climbers/trellis, herbaceous, groundcover, root/rhizome; optional mushroom/controlled nursery modules.
- Track overlap geometrically: one footprint can support multiple crop layers; sum of exclusive land footprints must not exceed property area. Vertical surfaces are recorded separately, not counted as extra land.
- Validate setbacks, right-of-way, access, pond safety, service corridors and shade buffers; regulations are location-dependent.
- **Mandatory:** location-aware annual solar-position, 3-D seasonal shadow and crop-level PAR/DLI calculations, including canopy maturation and neighboring structures. Interactive 3-D preview may be delivered incrementally, but the physical light-budget engine is required for vertical yield claims.

### FR-03 Crop/variety library
Each record: botanical and common names; crop family; edible product; basket category; season and region suitability; temperature range; growth-degree-day requirements if available; direct seed/transplant; nursery days; days to first harvest; harvest duration; succession interval; typical yield per planting area per crop cycle (with low/base/high); canopy height, width and growth curve; PAR/light tolerance; root depth; irrigation/ET coefficient; approximate N/P/K export; support/trellis needs; labour hours; input costs; pest/disease risks; storage life; market prices; source/provenance. Store variety-specific data and missing-field flags. Include onions, garlic, leafy greens, solanaceous crops, cucurbits, legumes, roots, herbs, fruits, climbers, spices and climate-appropriate perennials. Do not assume betel/pepper/blueberry/avocado thrive in all Indian climates.

### FR-04 Layer compatibility and competition
Represent vertical overlap with seasonal light interception and available photosynthetically active radiation (PAR) by layer; shade tolerance, canopy age, pruning, trellis density, root competition, water and nutrient constraints, ventilation and access. Start with conservative empirical reduction factors; upgrade to a calibrated light model when data exist. Yield of a crop is bounded by crop-specific potential and limiting resources. Prevent applying an independent 100% monocrop yield to every stacked layer. Show LER only when valid monocrop controls are supplied, otherwise show incremental yield per land area and uncertainty.

### FR-05 Planting and weekly harvest engine
- Planting plans at bed × crop × variety × sowing/transplant date × area × cycle level.
- Support intercropping, relay cropping, rotations, staggered 7/10/15/21/30-day sowing, pruning and replanting, nursery lead time, crop loss and soil rest.
- Generate **weekly** harvest predictions for at least 104 weeks and monthly summaries for 10 years.
- Enforce plot occupation windows, crop rotation and resource constraints; warn of impossible double-booking.
- Separate marketable harvest, grading losses, postharvest losses, storage carryover, procurement and fulfilled delivery.
- Support tree establishment: juvenile yield years and mature canopy competition.
- Generate weekly crop-category deficits and surpluses, not only annual total tonnes.

### FR-06 Customer basket and demand planning
Editable households, family size, subscription tiers, weekly weights, crop-specific preferences, dislikes, seasonality, substitution rules, delivery days, retention/churn, onboarding cohorts and optional add-ons. Demand = active households × subscribed basket weight by delivery week, disaggregated by crop group and crop. Optimize baskets subject to minimum diversity, quality, storage and customer exclusions. Explicitly distinguish grown, purchased and delivered items. Two weekly delivery windows with configurable allocation.

### FR-07 Water and irrigation balance
Daily/weekly irrigation demand by crop and stage using weather and ET estimates, rainfall effectiveness, soil water holding, drip efficiency, pond evaporation, rainwater capture, storage, pumping limits and drought scenarios. Report peak-day demand, annual water use, storage drawdown and water shortfalls. Never assume ponds are free of evaporation or irrigation water is unlimited. Flag salinity and water-quality constraints.

### FR-08 Nutrient and biomass balance
Estimate crop removal of N/P/K and organic matter, compost/feedstock availability, manure/slurry nutrients (measured or ranges), crop residues, legumes, imports and losses. Account for nutrient availability rather than equating slurry volume to fertilizer equivalence. Avoid counting the same biomass as mulch, compost, animal feed and fuel simultaneously. Support no-cow startup and optional purchased inputs; manure/slurry hygiene and food-safety alerts.

### FR-09 Labour and machinery
Task-specific person-hours by sowing, nursery, trellising, pruning, irrigation, weeding, harvest, washing, packing, delivery and sales. Seasonal workload, peak days, hired vs family labour (family labour valued in economic-profit view), hourly wages, small-machine CAPEX, fuel/power, maintenance and payback. Warn when required labour exceeds availability.

### FR-10 Financial engine
- Itemized initial and recurring CAPEX: land prep, beds, irrigation, trellises, fencing, pond, nursery, protected structures, solar, machinery, packing, cold chain, vehicles, livestock.
- OPEX: seeds/seedlings, substrate, compost/feedstocks, water, energy, hired/family labour, packaging, transport, repairs, rent, insurance, spoilage, marketing, certifications and administration.
- Revenue: CSA subscription, retail surplus, fruits, mushrooms, nursery, livestock, processed goods; price, volume and channel-specific assumptions.
- Weekly operational cash flow for first 24 months, monthly cash flow thereafter, 10-year P&L, break-even, gross margin, contribution margin, EBITDA, net operating profit, economic profit, cash runway, peak funding need, ROI, IRR/NPV (with specified discount rate), CAPEX payback and stage-gate recovery.
- Differentiate revenue from cash collection, profit from cash flow, owner labour from free labour, and subscription commitments from actual customer payments.
- Taxes and debt schedules configurable and jurisdiction-specific, not silently assumed.

### FR-11 Scenario manager
Clone, branch, tag and compare scenarios with changes to farm area, crop mix, layering, irrigation, climate, yields, losses, CAPEX, wages, subscription, basket, price, tenure and capital constraints. Base, conservative, optimistic, drought, heatwave, disease, labour shortage and customer-churn presets. Side-by-side KPI comparison and difference attribution. Reproducible Monte Carlo ranges for risk-sensitive KPIs.

### FR-12 Optimization engine
Objectives (select one or weighted): maximize 10-year risk-adjusted NPV; maximize sustainable annual net profit; maximize profit/acre; minimize acreage needed to meet weekly basket service levels; minimize upfront CAPEX; minimize water use; minimize payback time. Constraints: minimum weekly fulfillment (e.g., >=95% weeks), crop diversity, minimum buffer, available land, budget, irrigation, peak labour, monthly cash balance, crop compatibility, access and legal limits. Recommend Pareto-optimal designs rather than one supposedly universal best answer. Use deterministic linear/mixed-integer optimization for land and planting schedules where tractable, followed by nonlinear agronomic feasibility checks and simulation.

### FR-13 Operations and actuals
Mobile task list, QR-coded plots/beds, sowing and transplant records, input use, irrigation meter readings, pest scouting, yield weigh-ins, quality grade, inventory, orders, delivery, returns, complaints and payments. Actual vs predicted crop yield, cost and labour; user approval required before calibrated coefficients affect future scenarios. Offline capture and sync conflict handling in later phase.

### FR-14 Sales and fulfillment
Weekly basket builder, order cutoffs, pack lists, harvest requests, route/cluster scheduling, subscription billing, payment status, customer feedback and retention dashboard. Separate optional procurement from farm-grown supply with traceability. Include per-kg packaging/transport fees and fixed-route economics.

### FR-15 Reporting and exports
Interactive farm map, weekly harvest calendar, basket fulfillment heatmap, layer productivity, light/water/nutrient balance, crop-level profit, cashflow, stage gates, scenario rankings and audit trail. Export CSV, XLSX, PDF, JSON and shareable read-only scenario reports. Include data source notes and assumption change logs.

## 6. Data model (minimum entities)
Organization, User, Role, Farm, LandParcel, Geometry, Zone, Bed, Layer, Structure, SoilTest, WaterSource, WeatherSeries, Crop, Variety, CropParameterVersion, CompatibilityRule, Planting, PlantingCycle, NurseryBatch, HarvestForecast, HarvestActual, InventoryLot, Customer, Subscription, BasketItem, Order, Delivery, InputMaterial, NutrientComposition, InputApplication, ResourceBudget, LabourTask, Asset, CapexEvent, OpexEvent, SalesEvent, CashTransaction, Scenario, ScenarioOverride, ScenarioRun, ResultMetric, EvidenceSource, Alert, AuditEvent. Use stable IDs, SI units internally, INR display, timestamps and timezone.

## 7. Core calculation contracts
- **Annual delivered demand:** customers × kg/customer/week × 52 (or actual weekly calendar count).
- **Gross production needed:** delivered demand ÷ (1 − combined loss fraction), where loss stages must not be applied twice.
- **Weekly marketable harvest:** sum over planting cohorts of (planting area × stage-specific harvest profile × crop potential × weather modifier × light modifier × root/water/nutrient modifiers × survival/grade fraction). Calibrate modifiers to avoid multiplying correlated penalties twice.
- **Fulfillment by crop group/week:** min(available stock + eligible procurement, accepted demand), respecting perishability and substitution; procurement must be reported separately.
- **Effective land use:** sum exclusive physical footprints ≤ total land; multi-layer harvest may overlap but cannot increase the denominator of physical land.
- **Water budget:** opening storage + rain capture + other permitted inflows − crop irrigation − evaporation − conveyance losses − other uses = closing storage.
- **Cash balance:** opening cash + collections + finance inflows − paid CAPEX − paid OPEX − debt service − taxes = closing cash.
- **Stage-gate:** next CAPEX stage unlocked only if prior-stage cumulative *net cash recovery* / prior-stage eligible CAPEX ≥ chosen threshold (default 75% when enabled), plus sufficient reserve and service reliability.
- **Sensitivity:** every critical yield, loss, customer price, labour rate and water parameter supports low/base/high and optional probability distribution.

## 8. Interface / information architecture
1. **Dashboard:** area, customers served, weekly supply reliability, cash runway, forecast net profit, alerts.
2. **Farm Designer:** GIS plan, beds, vertical layer editor, access/pond/solar overlays.
3. **Crop Library:** crop/variety catalog, assumptions and sources.
4. **Crop Planner:** drag-and-drop weekly Gantt calendar, 24-crop Abhinav template, rotations and nursery.
5. **Resources:** water, nutrient, biomass, labour and infrastructure.
6. **Customers:** subscription tiers, basket templates, weekly demand, orders.
7. **Economics:** editable unit costs, CAPEX phases, cash flow, break-even.
8. **Scenarios:** side-by-side comparisons, stress tests and optimization.
9. **Operations:** task checklists, actual harvests and expenses.
10. **Reports / Settings:** exports, provenance, team access, backup.

### First-run wizard
Ask only farm location/region (optional), area, water reliability, initial budget, number of households, weekly basket weight and growing approach. Populate the rest with transparent presets and immediately display a provisional result. Show a prominent 'illustrative, not validated' label until agronomic inputs are verified.

## 9. Approved architecture and technology stack
**Decision recorded:** 12 October 2026. The owner approved a Python backend and scientific computation stack, specifying Django as the backend framework. This supersedes the earlier request to match BrightStudio's Erlang/OTP architecture. Erlang is not a required runtime. The browser frontend remains TypeScript/JavaScript.

### 9.1 Selected components
- **Frontend:** React + TypeScript + Next.js; mobile-first PWA; accessible forms and maps.
- **Map and visualization:** MapLibre GL with GeoJSON editing; Three.js for 3-D scenes and light/shadow visualization. Presentation must use simulation outputs rather than independently inventing yield or light estimates.
- **Backend:** Django with Django REST Framework for REST APIs, validated serializers and asynchronous job submission/status; Django ORM, migrations, admin and authentication provide the application foundation. Use GeoDjango with PostGIS for spatial models. CPU-intensive simulation runs in separate Celery worker processes rather than request handlers.
- **Database:** PostgreSQL + PostGIS for transactional and spatial data; object storage for photos, imports and reports.
- **Simulation:** Python with NumPy for numerical calculations and pvlib for tested solar-position/radiation routines. Implement farm-specific shading, PAR/DLI integration, crop response, calendar/resource balances and financial calculations as versioned calculation modules. Libraries do not establish agronomic validity; validate the composed models against §11 and §18.9.
- **Optimization:** OR-Tools for tractable linear/mixed-integer scheduling and allocation; SciPy where nonlinear/numerical methods are needed. Follow optimization with agronomic feasibility checks and simulation; report infeasibility and Pareto tradeoffs.
- **Background jobs:** Celery + Redis for scenario runs, sweeps, optimization and exports. PostgreSQL is the authoritative store of job state, input snapshots and accepted results; queue delivery alone does not establish completion.
- **Auth:** secure session/OIDC, organization-based RBAC, audit logs, encrypted secrets and backups.
- **Deployment:** containers with independently managed API and worker processes; managed database, object storage, metrics, logging and automated CI/CD. Pin dependency versions and retain reproducible build inputs.
- **API endpoints:** POST /farms, /zones, /plantings, /customers, /scenarios, /scenario-runs; GET /scenario-runs/{id}, /weekly-forecast, /resource-balance, /financials, /comparison; POST /actuals/harvest and /imports.
- **Interoperability:** CSV/XLSX import from the existing workbook, GeoJSON/KML, optional weather providers. Every external data source is versioned and cached with retrieval date.

### 9.2 Reliability and execution contracts
Retain the fault isolation, supervision and message-passing goals discussed for Erlang through explicit Python service architecture; this does not claim equivalence to BEAM scheduling or supervision.

- Run CPU-intensive jobs outside API processes. Service/container managers restart failed processes; isolate worker failures from request handling.
- Persist organization-scoped job IDs, immutable input snapshots, engine/dependency versions, seeds, status, progress, cancellation requests and result references. Support observable queued/running/succeeded/failed/cancelled states and recover abandoned work after worker failure.
- Assume duplicate delivery is possible. Make job execution and result publication idempotent; use database transactions and concurrency controls to prevent duplicate accepted results or business side effects. Do not promise exactly-once queue execution.
- Use bounded retries for transient faults with backoff; expose permanent failures. Set execution time/resource limits and checkpoint long runs where useful. Check cancellation cooperatively at bounded intervals and prevent cancelled runs from publishing successful results.
- Keep database transactions short. Audit meaningful state changes and enforce organization isolation in API, worker and result access paths.
- Make calculations pure functions of versioned inputs where practical. Pin numerical dependencies and define reproducibility tolerances for supported execution environments; preserve the deterministic contract in §11.F.
- Include job-correlated logs and metrics, queue age and worker-health monitoring, durable storage configuration, and tested backup/restore procedures.

### 9.3 Decision rationale and scope
Python reduces custom scientific implementation by providing pvlib, NumPy, SciPy and OR-Tools. BrightStudio remains a conceptual reference for modular boundaries and operational reliability, not a required codebase or deployment dependency. Package/API versions and infrastructure sizing are implementation decisions to validate before installation; this specification does not assert the stack is already installed or benchmarked.

## 10. Scenario output specification
Each run produces: assumptions snapshot; scenario ID and engine version; acreage and productive footprint; crop/variety planting cohorts; weekly delivered/shortfall by crop group; fruit/mushroom add-on volumes; monthly and annual yields; minimum/median/maximum production; water deficit weeks; nutrient deficits; peak labour; CAPEX schedule; 24-month cashflow; 10-year P&L; peak financing requirement; stage-gate status; NPV/payback; 10 most sensitive assumptions; infeasibility reasons; provenance and warnings.

## 11. Validation, tests and acceptance criteria
**A. Arithmetic baseline:** 50 × 8 × 52 = 20,800 kg delivered; with 20% single-stage losses = 26,000 kg gross; 50 × ₹5,500 × 12 = ₹33,00,000 subscription revenue at 100% paid enrollment.
**B. Testimonial benchmark:** 20 × 5 = 100 kg/week/acre delivered; 5,200 kg/year delivered; display separate 40 kg/day/acre claim without treating them as equivalent.
**C. Conservation:** farm land footprints never exceed polygon area; nutrient input mass and water balance reconcile within tolerance; same harvest cannot be sold twice.
**D. Feasibility:** impossible crop overlap, out-of-season planting, excessive shade, inadequate irrigation, unaffordable CAPEX and unfillable baskets generate clear warnings.
**E. Economics:** zero customers does not create subscription revenue; changing price affects revenue not harvest; changing CAPEX affects cash and payback; family labour can be valued; negative cash is shown even when accounting profit is positive.
**F. Scenario reproducibility:** same inputs + engine version + random seed yield identical results.
**G. Weekly realism:** annual supply above target does not mark a scenario feasible if weekly group-level shortfalls exceed the configured service threshold.
**H. Usability:** first scenario created in <10 minutes with defaults; primary dashboard usable on phone; exports match displayed results.
**I. Performance targets:** deterministic 2-year farm scenario <10 seconds for a typical 1–10 acre farm and ~1000 planting cohorts on target infrastructure; scenario optimization runs asynchronously with progress and cancellation.
**J. Security:** organization isolation, authorization checks, backups, auditable modifications, and no exposure of customer PII in shared scenario reports.

## 12. Development roadmap
### Phase 0 — Data and mathematical foundation
Audit existing workbook; import assumptions with provenance; define crop library schema, units, scenario snapshots, baseline tests and conservative yield ranges. Deliver calculation reference specification and unit tests.

### Phase 1 — Planning MVP (priority)
Farm setup, zone/bed allocation, crop library, planting calendar, basic multi-layer competition coefficients, weekly harvest, demand/basket fulfillment, cost/price assumptions, 24-month cashflow, 10-year summary, scenario cloning and 1/2/3/4-acre comparisons. Export XLSX/CSV/PDF. No detailed 3-D, livestock or external customer app.

### Phase 2 — Resource and financial optimization
Water and nutrient balances, labour scheduling, phased CAPEX and 75% recovery gates, seasonal stress tests, Pareto optimizer, uncertainty bands, lease-vs-own comparison, crop profitability and stage-gated expansion.

### Phase 3 — Operational system
Actuals capture, field tasks, nursery scheduling, orders, packing, twice-weekly deliveries, subscriptions, actual-vs-plan calibration, offline-first field interface.

### Phase 4 — Advanced farm intelligence
Calibrated seasonal shade model, GIS sun-path and tree-growth simulation, weather integrations, satellite/soil sensors where economical, 3-D visualization, controlled-environment growing, integrated mushrooms/animals/pond/solar, multi-farm cooperative planning.

## 13. Open decisions (not blockers for MVP)
- First target agro-climatic region and local crop calendar; default to region-neutral with selectable India region presets until chosen.
- Farm footprint and land tenure; irrigation water quality, volume and reliability.
- Whether ₹5,500 basket covers vegetables alone or includes fruit/add-ons; define basket category contracts.
- Owner-operated versus hired labour, and target subscription retention.
- Organic/ZBNF claims and certification workflow; app must not auto-certify.
- Hosting/offline requirements, target user count, multilingual UI (Hindi/English), and data sharing policies.

## 14. Prioritization / exclusions
**Must-have MVP:** realistic weekly production, basket demand, land accounting, cost and cashflow, scenario comparison, assumption provenance and infeasibility warnings.
**Should-have:** climate presets, water budget, nursery, 75% CAPEX stage gates, sensitivity charts, crop rotations, map layout.
**Later:** full 3-D digital twin, IoT, disease image diagnosis, route optimization, marketplace, livestock/pond/solar co-simulation, automated compliance filings.

## 15. Product success metrics
- ≥95% simulated weekly basket fulfillment for chosen target scenario under base assumptions, plus reported conservative-case performance.
- Forecast error measured by crop group and week after actuals available (track MAPE/WAPE with zero-volume handling).
- All scenarios provide auditable gross-to-delivered mass balance and cash balance.
- Farm operators can identify which crops, weeks, water constraints or costs cause failures.
- Users can compare 2-acre intensive, 3-acre hybrid and 4-acre testimonial-scaled scenarios without editing formulas.
- No investment recommendation presented as guaranteed profit.

## 16. Suggested first demonstration scenarios
1. **Abhinav testimonial baseline:** 1 acre, 20 customers, 5 kg/week, boundary fruit, four rotating crop blocks, 24 varieties, 15-day sowing cohorts. Treat as testimonial, not verified yield.
2. **Intensive target:** 2 acres, 50 customers, 8 kg/week; maximize vertical productivity subject to sunlight and resource limits.
3. **Hybrid reference:** 3 acres, 50 customers, 8 kg/week; intensive beds + managed perennial canopy + productive trellis paths.
4. **Conservative comparison:** 4 acres, 50 customers, 8 kg/week; less density, more resilience and crop rotation.
5. **Water-limited lease:** 2–3 acres, rented land, portable structures, restricted irrigation, stage-gated CAPEX.

## 17. Reference materials
- User-provided Hindi interview transcript of Dnyaneshwar Bodke / Abhinav Farmers Club (video `https://www.youtube.com/watch?v=goEyH_jQThM&t=616s`), especially lines 185–226, 323–351, 398–455, 753–769. Interview statements are claims, not independent field verification.
- Existing project spreadsheet `50_Family_Multilayer_Crop_Calendar_Model.xlsx` (legacy illustrative assumptions; requires audit before migration).
- Existing Zero Budget Natural Farming research PDFs (background context, not a universal validation of claimed yields).


## 18. Mandatory Solar Intelligence and 3-D Cultivation Engine (v1.1)

### 18.1 Objective and acceptance principle
Optimize **annual saleable crop yield and risk-adjusted profit per total farm footprint** subject to light, water, nutrients, root space, labour, access, capital and structural constraints. Vertical planting positions must never be equated automatically with independently productive full-sun area. The solar engine is **required for all vertical-system yield forecasts**, not a future enhancement. If radiation or crop-response inputs are missing, flag the scenario as provisional and show ranges rather than a precise claim.

### 18.2 Site and geospatial inputs
Required: latitude, longitude, time zone, plot boundary polygon, true-north orientation, terrain elevation/slope/aspect, planting coordinates, obstacle positions/heights, dates and simulation time step. Optional but supported: horizon obstruction profile, nearby buildings, boundary trees, historical cloud cover, measured global/diffuse/direct irradiance, soil surface albedo, altitude, local weather station. The engine must handle locations across both hemispheres and crossing the date line; no hard-coded Delhi or India solar geometry. Georeferencing and orientation must be validated, and users must be able to specify uncertainty in surveyed obstacles.

### 18.3 Solar geometry and radiation
Use a tested solar-position algorithm (e.g. NREL SPA via pvlib) to calculate sun elevation/azimuth, sunrise/sunset and equation-of-time adjustments from latitude, longitude and timestamp. Convert weather/clear-sky estimates into direct and diffuse PAR and integrate irradiance into daily light integral (DLI, mol photons/m²/day). Model annual seasonality, day length, solar-noon displacement, monsoon cloud cover and diffuse sky radiation. Do not infer PAR from geometric shadows alone. Report modeled versus observed radiation where sensor data exist.

### 18.4 Farm scene representation
Georeferenced objects: towers, stepped planters, trellises, pandals, arches, vertical walls, shelves, greenhouses, solar panels, boundary hedges, trees, buildings, ponds, paths and terrain. Store geometry, orientation, height, spacing, plant locations, canopy leaf area/porosity, spectral transmissivity where known, phenological growth curves, pruning schedules, and changes over 1–10 years. Model self-shading, mutual shading and occlusion of planting pockets, including the north/south/east/west faces of towers. Include direct and diffuse light and optional reflected light. Provide hourly results and a configurable finer step for detailed studies.

### 18.5 Plant-level light and yield
For each crop cohort and growing position, calculate hourly PAR and daily/weekly DLI, sunfleck/shade duration, thermal exposure and season-specific growth stage. Link available light to a crop/variety-specific response curve with confidence bounds. Respect minimum viable light, photoperiod sensitivity where applicable, head/root size, root volume, water and nutrient demand, planting density, pest pressure, harvest access and survival/marketable-grade fraction. Never use simple level-count yield multiplication. Avoid double counting correlated stress modifiers. Where local response curves are unavailable, use conservative low/base/high parameters clearly labeled as unvalidated.

### 18.6 Technique catalog (editable and extensible)
Include at minimum: (1) cabbage/cauliflower pocket towers (experimental); (2) stepped brassica pyramids (experimental); (3) strawberry towers; (4) leafy/herb towers; (5) vertical pipe/pocket gardens; (6) overhead gourd pandals; (7) A-frame/V-frame trellises; (8) high-wire tomato/cucumber; (9) productive walkway arches; (10) multi-tier growing racks; (11) multi-strata agroforestry; (12) living-tree climbers such as pepper/betel where climate suitable; (13) espalier fruit walls; (14) rotating towers (research); (15) hanging baskets; (16) green walls; (17) double-row fruiting walls; (18) lean-and-lower vines; (19) potato grow bags (experimental, no presumed multiplier); (20) tiered mushroom racks (separate non-solar yield engine); (21) nursery racks; (22) solar-powered supplemental-lit nurseries (explicit electrical energy accounting); (23) productive fences; (24) pond-edge trellises; (25) floating beds (research); (26) bamboo support networks; (27) fodder sprouting racks (separate feed-yield accounting); (28) spiral herb gardens; (29) raised platforms above shade crops; (30) retractable seasonal trellises. Each record includes compatible crops, planting geometry, support loads, root volume, water distribution, installation/maintenance cost, labour, seasonality, access requirements, and evidence quality.

### 18.7 Optimizer and visual interfaces
Interactive GIS farm map, 3-D sun-path viewer, date/time shadow animation, per-position PAR/DLI heatmaps, seasonal/monthly/annual light-budget dashboards, and side-by-side baseline comparisons. Optimize structure orientation, spacing, tier count, crop placement, sowing dates, seasonal relocation, pruning, access corridors and capex stages. Allow user to select objectives (profit, delivered kg, water productivity, labour productivity, land productivity, resilience) and hard constraints. Output Pareto tradeoffs rather than implying one universally optimal layout. Always compare against an equal **total land footprint**, including service aisles and access.

### 18.8 Technical architecture
Python simulation workers using the approved stack in §9, with pvlib and NumPy for solar calculations; geospatial geometry in PostGIS; 3-D scene rendering with Three.js; shadow/visibility ray casting or voxelized canopy models for direct radiation, sky-view factors or calibrated approximation for diffuse radiation. Version models, weather sources, crop-response coefficients, resolution and random seeds. Support caching and incremental recomputation when one structure changes. Long-running annual multi-year simulations execute asynchronously with progress and cancellation. User-visible outputs must distinguish measured, literature-derived, assumed and calibrated parameters.

### 18.9 Verification and acceptance tests
1. Compare solar position at multiple latitudes, longitudes, seasons and time zones against independent reference ephemerides, including solstices and equinoxes.
2. Compare geometric shadows for simple poles and walls against analytic trigonometry at known sun elevations; verify both hemisphere orientations.
3. Confirm a north-facing and south-facing tower pocket can receive different modeled direct radiation depending on date/time.
4. Confirm lower tiers can have less PAR than upper tiers, and additional tiers do not automatically increase predicted harvest.
5. Compare clear and cloudy days to ensure diffuse radiation is represented; validate DLI integration and units.
6. Compare an overhead trellis and ground-level crop against a monocrop control on equal total footprints.
7. Confirm maturing tree canopies and pruning alter downstream light forecasts across years.
8. Confirm a solar panel or neighboring building can shade a crop and that a seasonal relocation changes exposure.
9. For missing crop response data, show uncertainty/provisional status rather than fabricate an exact yield gain.
10. Report calculation provenance and reproducible results for identical inputs.

### 18.10 Implementation order
**MVP required:** coordinates/time-zone-aware solar geometry, basic geometry/obstacle shading, hourly direct/diffuse light budgets, DLI at plant positions, simple configurable crop-light response, baseline comparisons, warnings and confidence levels. **Next:** detailed canopy porosity, terrain/horizon profiles, automated spatial optimization, multi-year tree growth, field-sensor calibration, GPU acceleration and polished animated 3-D digital twin. This sequencing does not defer the core solar model.

## 19. Specification change log
- **v1.2 — 12 October 2026:** Recorded owner approval of the Python stack, superseding the Erlang/BrightStudio runtime requirement; selected Django/Django REST Framework/GeoDjango, PostgreSQL/PostGIS, Celery/Redis, pvlib/NumPy, OR-Tools/SciPy, and React/TypeScript/Next.js with MapLibre/Three.js. The owner subsequently specified Django in place of FastAPI. Added job isolation, recovery, idempotency, cancellation and reproducibility contracts. Product scope and mandatory MVP solar requirements remain unchanged.
- **v1.1:** Added mandatory solar intelligence and 3-D cultivation requirements in §18.
