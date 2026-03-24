# Operations Hub Prototype

This prototype now frames the product as a large-estate operations console rather than a single-device monitor.

## Scale-oriented UI direction

- Open on aggregated service health, queue health, and regional posture before showing individual asset detail.
- Emphasize incident grouping, ownership routing, and telemetry freshness so operators can act on large volumes without scanning raw alert lists.
- Treat individual device pages as drill-down evidence views, not the main command surface.

## Implementation implications

- The dashboard should be fed by pre-aggregated views such as `incident_groups`, `regional_health`, `queue_backlog`, and `telemetry_freshness`, not only raw event streams.
- Alerts should support correlation and suppression so one shared failure does not explode into hundreds of duplicate rows.
- Ownership metadata should exist at the incident-group level so work can route directly to network, field, platform, or security teams.
- Data freshness and coverage should be first-class fields in the API because operator trust drops quickly if the UI looks current but is stale underneath.
