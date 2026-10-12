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
