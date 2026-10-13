# FarmOS planning mockups

JPG renders of the implemented interface and an animated GIF walkthrough:

- [Farm setup](01-farm-setup.jpg)
- [Weekly planning results](02-weekly-plan.jpg)
- [Scenario comparison](03-scenario-comparison.jpg)
- [Mobile results](04-mobile-results.jpg)
- [Animated planning walkthrough](planning-walkthrough.gif)

The fixtures are illustrative, with unvalidated yield assumptions and deliberately
incomplete two-year planting coverage. They demonstrate shortfalls, not production
or profit promises. The 3-acre alternative changes both yield assumptions and CAPEX;
additional land alone does not automatically increase harvest. Calculations are
produced by the same Django planning engine. The renderer intercepts API requests
to supply fixtures without changing the development database.

To regenerate with the frontend running on port 3000, from `frontend/`:

```bash
npm run mockups
```

Requires the backend virtual environment, Playwright Chromium (`CHROMIUM_PATH`
can specify its path) and ffmpeg. Source fixtures: `backend/scripts/mockup_data.py`.
Renderer: `frontend/scripts/render-mockups.mjs`. These images represent the current
planning core; GIS/solar visualization and resource optimization are subsequent slices.

## Full product design previews

These additional screens show the intended full product, including capabilities
that are not implemented. Every screen carries a design-preview banner. Values,
charts, optimizer progress, canopy shadows and light budgets are illustrative
fixtures; they are not outputs of a validated solar or agronomic model.

| Area | JPG |
| --- | --- |
| Dashboard | [Supply, cash and decision alerts](05-dashboard.jpg) |
| Farm designer | [Physical footprints, layers and access](06-farm-designer.jpg) |
| Sunlight simulation | [Sun path, shadows and position-level PAR/DLI](07-sunlight-simulation.jpg) |
| Crop library | [Varieties, technique compatibility and evidence](08-crop-library.jpg) |
| Planting calendar | [Occupation, harvest and category deficits](09-planting-calendar.jpg) |
| Resources | [Water, nutrients, biomass and labour](10-resource-balances.jpg) |
| Customers & baskets | [Demand, farm-grown supply and procurement](11-customers-baskets.jpg) |
| Economics | [Cash, 10-year summaries and CAPEX stage gates](12-economics-stage-gates.jpg) |
| Scenarios & optimizer | [Pareto tradeoffs, constraints and asynchronous jobs](13-scenarios-optimizer.jpg) |
| Operations | [Tasks, actual harvest and traceable inventory](14-operations-actuals.jpg) |
| Reports & provenance | [Exports, evidence and assumption changes](15-reports-provenance.jpg) |

- [Full product walkthrough GIF](full-product-walkthrough.gif)
- [Sunlight and shadow animation GIF](sunlight-shadow-simulation.gif)
- [Standalone interactive concept HTML](concept-preview.html): download and open
  in a browser; navigation switches screens and the sunlight slider animates a
  schematic day. This is a visual prototype, not a production application.

The sunlight GIF covers 06:00–18:00 with a schematic sun path and changing shadow
shapes. It does not calculate solar geometry, direct/diffuse irradiance or DLI.
The real engine remains required by PRD §18 before vertical yield claims.

To regenerate these expanded previews, with frontend dependencies installed and
Chromium plus ffmpeg available, run from the repository root:

```bash
node docs/mockups/render-full-mockups.mjs
```

The renderer loads the self-contained HTML and does not require a running API
or modify farm/scenario data. Authentication and user management remain deferred.

## Implemented sunlight interface

[Computed sunlight lab JPG](16-sunlight-lab-implemented.jpg) shows the actual
`/sunlight` interface with calculated values from the new light engine. This is
separate from the schematic animations above. The engine models opaque boxes and
isotropic diffuse radiation; it does not infer crop yield or calibrated canopy behavior.
To regenerate with both servers running, from `frontend/`:

```bash
node scripts/render-sunlight.mjs
```

This calculation creates a retained solar study in the local development database.
