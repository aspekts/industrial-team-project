# User Manual

## ATM Operations Hub

This manual explains how to use the ATM Operations Hub dashboard as an end user. It is separate from the project README and is intended for operators, managers, administrators, assessors, and report readers who need to understand how the system is used in practice.

## Purpose Of The System

The ATM Operations Hub is a dashboard for monitoring ATM-related operational data across multiple synthetic log and metrics sources. It helps users:

- view fleet-wide ATM status
- identify anomaly groups and incidents
- inspect ATM-level diagnostic evidence
- review rule-based recommendations
- record operator actions
- observe the data pipeline and live simulation state

The platform is backed by source data from:

- ATMA: ATM application logs
- ATMH: ATM hardware alerts
- KAFK: transaction stream metrics
- PROM: Prometheus runtime metrics
- GCP: cloud infrastructure metrics
- TERM: terminal handler application logs
- WINOS: Windows host metrics

## Accessing The Dashboard

When the application is running, open the dashboard in a web browser:

- `http://127.0.0.1:5000`

You will be taken to the sign-in page.

## Account Setup And Sign-In

### Create an account

1. Open the sign-in page.
2. Select `Create an account`.
3. Enter a username.
4. Enter and confirm a password.
5. Choose one role:
   - `Admin`
   - `Manager`
   - `Ops`
6. Select `Create account`.

After a successful sign-up, return to the login page and sign in.

### Sign in

1. Enter your username.
2. Enter your password.
3. Select `Continue`.

After sign-in, the system redirects you to the dashboard view for your stored role.

### Sign out

1. Open the `Settings` screen.
2. Select `Log out`.

## User Roles

### Admin

Admin users are focused on platform-wide visibility and oversight.

Typical admin tasks:

- monitor system readiness across all sources
- review anomaly distribution across the fleet
- inspect ML scoring summaries
- review recommendation feedback trends
- assess source coverage and configuration status

### Manager

Manager users are focused on operational review and follow-up.

Typical manager tasks:

- review flagged ATM issues
- monitor action queues
- record follow-up actions and notes
- review anomaly groups that need escalation or local handling

### Ops

Ops users are focused on frontline monitoring and investigation.

Typical ops tasks:

- inspect live operational anomalies
- investigate ATM-level issues
- review evidence across sources
- record actions taken during investigation

## Main Dashboard Layout

The dashboard is split into two main areas.

### Sidebar

The left sidebar includes:

- system branding and dashboard context
- search box
- source key glossary
- date filter
- accessibility display-size toggle
- data footprint summary
- navigation buttons

### Main content area

The main content area changes depending on the selected screen. Common content includes:

- screen title and description
- status pill showing the current state
- summary cards
- panels, tables, charts, and action areas

## Common Controls

### Search

Use the search box in the sidebar to search for:

- ATM IDs
- branch or location references
- anomaly names
- incident-related content
- source names

### Date filter

Use the `Dashboard date` filter to limit metrics, ATM lists, and anomaly groups to a single day.

To apply a date filter:

1. Choose a date.
2. Select `Apply filter`.

To remove the filter:

1. Select `Clear`.

### Display size toggle

Use `Turn on larger display` if you want larger text, cards, spacing, and controls across the interface.

## Screen Guide

## Dashboard

This is the main overview screen.

It includes:

- a priority banner for the most important issue
- metric cards such as observed ATMs, ATM app errors, hardware alerts, and throughput
- a priority item panel with a next-best-action summary
- trend visualisations
- source-backed checks
- source telemetry snapshot

Use this screen when you want a quick overview of system health and current priorities.

## ATM List

The `ATM list` screen shows a table of observed ATMs and their status.

It includes:

- ATM ID
- branch or location
- current severity or status
- current issue
- last update time
- action link

Use the filter chips to view:

- all ATMs
- critical ATMs
- warning ATMs
- healthy ATMs

Use this screen when you want to identify which machines need attention.

## ATM Detail

The `ATM detail` screen shows detailed evidence for a selected ATM.

It includes:

- anomaly summary
- confidence and likely root cause
- recommended next step
- issue timeline
- source-backed evidence cards
- impact summary
- action shortcuts

To use this screen:

1. Open the `ATM list` screen.
2. Select an ATM from the table.
3. Review the loaded diagnostic information.

Use this screen when investigating a single ATM in detail.

## Alerts

The `Alerts` screen groups active anomalies and correlated incidents.

It includes:

- critical anomalies
- warning anomalies
- correlated incident groups
- rule-based recommendations
- recommendation feedback history

Admin users may also see an anomaly type distribution table showing the number of active detection groups, affected ATMs, and confidence levels.

Use this screen when reviewing fleet-wide anomaly patterns and incident groupings.

## Action Center

The `Action center` is used to record operational responses.

It includes:

- recommended action options
- a free-text operator note field
- a confirmation area
- a recent actions history list

### Recording an action

1. Open `Action center`.
2. Select one of the recommended responses.
3. Enter an optional note in `Operator note`.
4. Select `Confirm action`.

The action will appear in the confirmation card and recent history list.

Note:

- action recording is available to `Manager` and `Ops` users
- `Admin` users are not allowed to record actions

## Data Flow

The `Data flow` screen shows the pipeline stages from ingestion to recommendations.

It includes:

- source data ingestion stage
- rule detection stage
- ML anomaly scoring stage
- incident grouping stage
- recommendation stage
- source-level breakdown table
- anomaly taxonomy table
- live streaming log agent controls

Use this screen when you want to explain how data moves through the system or verify pipeline state.

## Settings

The `Settings` screen shows account and platform information.

It includes:

- username
- role
- console type
- session state
- detection threshold summary
- source coverage summary
- notification and escalation information
- log out button

Use this screen when checking your account role, confirming threshold values, or signing out.

## Recommendations And Feedback

The system generates rule-based recommendations for active anomaly types.

Each recommendation may include:

- anomaly type and name
- suggested root cause
- recommended actions or steps
- confidence score

Recommendation confidence changes over time using user feedback.

### Giving feedback

Feedback is recorded from the dashboard recommendation flow. Depending on the interface state, this may be shown as like or dislike controls tied to a recommendation.

The system stores feedback history and updates confidence scores automatically.

Use feedback when you want to indicate whether a recommendation was useful.

## Live Agent

The platform includes a live simulation feature called the streaming log agent.

It can:

- generate synthetic events at a chosen interval
- write those events into the database
- re-run detection and incident correlation automatically
- inject selected anomaly types for demonstration

### Starting the live agent

1. Open `Data flow`.
2. Locate the `Streaming log agent` panel.
3. Enter an interval in seconds.
4. Select `Start agent`.

### Stopping the live agent

1. Open `Data flow`.
2. Select `Stop agent`.

### Injecting a test anomaly

1. Start the agent.
2. In the anomaly injection area, select one of the available anomaly types such as:
   - `A1` Network timeout
   - `A2` Cash depletion
   - `A4` Container restart
   - `A5` Performance degradation
   - `A6` OS pressure
   - `A7` Malformed Kafka
3. Watch the dashboard update over the next few ticks.

Use the live agent during demonstrations or report walkthroughs when you want to show how the system reacts to simulated changes in near real time.

## Typical User Tasks

## Review the most urgent issue

1. Sign in.
2. Open the `Dashboard` screen.
3. Read the priority banner.
4. Select `View anomaly groups` if more detail is needed.

## Investigate a single ATM

1. Open `ATM list`.
2. Filter to `Critical` or `Warning` if needed.
3. Select an ATM.
4. Review the `ATM detail` page.
5. Move to `Action center` if a response should be recorded.

## Record an operational response

1. Open `Action center`.
2. Select an action option.
3. Add an operator note.
4. Confirm the action.
5. Check `Recent actions` to confirm it was saved.

## Review platform and source readiness

1. Sign in as an `Admin` user.
2. Open `Dashboard` and `Data flow`.
3. Review source-backed checks, telemetry summaries, taxonomy entries, and ML summaries.

## Troubleshooting

## I cannot sign in

Check that:

- the username exists
- the password is correct
- the account was created successfully

If sign-in fails, return to the sign-up page and confirm that the account was created.

## The dashboard loads but shows unavailable or empty data

Possible reasons:

- the cleaned database is missing
- the pipeline has not been run yet
- the selected date filter has no matching records

Try:

1. clearing the date filter
2. checking the `Data flow` screen
3. checking `/health` or `/api/status`

## I cannot record an action

Only `Manager` and `Ops` roles can record actions. If you are signed in as `Admin`, action recording is blocked.

## The live agent injection buttons do not work

The live agent must be running before anomaly injection can succeed.

Steps:

1. open `Data flow`
2. start the agent
3. try the injection again

## The dashboard is difficult to read on screen

Use the `Display size` accessibility toggle in the sidebar.

## Useful Endpoints

These URLs may be useful during demos, testing, or report preparation:

- `/health`: system health summary
- `/api/status`: API and database status
- `/api/docs/`: Swagger UI
- `/api/openapi.json`: OpenAPI spec

## Notes For Report Use

This manual can be used as:

- a standalone appendix
- a handover guide for assessors or teammates
- a companion document to the dashboard wireframe and README

If needed, this document can also be converted into PDF or expanded with screenshots of each screen.
