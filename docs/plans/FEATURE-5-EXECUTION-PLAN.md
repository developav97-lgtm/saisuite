# Feature #5 Execution Plan — Reporting & Analytics
**Project:** SaiSuite — ValMen Tech
**Date:** 2026-03-27
**Developer:** Juan David (solo developer)
**Stack:** Django 5 + Angular 18 + PostgreSQL 16 + Angular Material
**Planned duration:** 3 weeks (15 working days)

---

## Executive Summary

Feature #5 delivers dashboards, KPIs, charts, and data export capabilities on top of the
project data built in Features #1–#4. The backend analytics layer is entirely new Django
work. The frontend requires Chart.js (or ngx-charts — see decision below) wired into
Angular Material shells.

Feature #4 frontend is unfinished. That work is **partially blocking** Feature #5 because
several analytics components embed inside TareaDetail and ProyectoDetail, which are still
evolving. The strategy for handling both in parallel is defined in Section 6.

---

## 1. Epic Sequence — Order and Dependencies

### The Five Epics

| # | Epic | Description |
|---|---|---|
| E1 | Backend Analytics | Django aggregation endpoints, KPI services, export logic |
| E2 | Chart Setup + Base Charts | Install chart library, create reusable chart wrappers |
| E3 | Dashboard Components | Project dashboard, company dashboard, KPI cards |
| E4 | Report Builder | Filterable tabular reports, CSV/PDF export |
| E5 | Integrations | Embed analytics into existing Feature #4 components |

### Mandatory Sequence

```
E1 (Backend) → E2 (Chart lib) → E3 (Dashboards) → E4 (Reports) → E5 (Integrations)
              ↗ (parallel with E1 from Day 3 onward)
```

**E1 must start first.** Angular components cannot be developed meaningfully without
real API contracts. However, once the first two analytics endpoints exist (Days 1–2),
E2 chart library setup can begin in parallel on Day 3.

**E3 depends on E1 and E2** being complete. There is no productive shortcut: rendering
charts requires both data and the chart rendering layer.

**E4 is independent of E3** once E1 backend endpoints for tabular data exist. It can
begin at the same time as E3 if bandwidth allows (it does not — one developer).
E4 is scheduled after E3 because dashboards deliver more visible value first.

**E5 is last.** Embedding analytics into Feature #4 components requires those Feature #4
components to exist. E5 is the integration and polish step.

### Technical Handoffs Between Epics

| From | To | Handoff artifact |
|---|---|---|
| E1 complete | E2 starts for real | API contract doc: endpoint list, response shapes |
| E2 complete | E3 starts | `AnalyticsChartComponent` wrapper working with mock data |
| E3 complete | E4 starts | Dashboard shell and layout patterns established |
| E1+E4 complete | E4 export | Export endpoints available for PDF/CSV download |
| E3+E4 complete | E5 starts | All standalone analytics pages working end-to-end |

---

## 2. Three-Week Timeline

### Week 1 — Backend Foundation (Days 1–5)

**Goal:** All Django analytics endpoints are working and tested. Frontend is unblocked.

| Day | Tasks | Epic |
|---|---|---|
| 1 | Project KPI service: budget variance, schedule variance, completion % per project. Serializers. | E1 |
| 2 | Company-level aggregation service: projects by status, total budget/spent, team utilization. Serializers. | E1 |
| 3 | Timesheet analytics service: hours by user/project/phase/week. Workload trend endpoint. Chart library selection + `package.json` update. | E1 + E2 |
| 4 | Resource utilization endpoint (builds on Feature #4 `resource_services.py`). Export service skeleton (CSV writer). | E1 |
| 5 | Backend tests: `test_analytics_services.py` (target >= 85% coverage). Wire all URLs. `manage.py check` clean. | E1 |

**Week 1 checkpoint (see Section 3).**

### Week 2 — Frontend Core (Days 6–10)

**Goal:** Standalone analytics pages are working with real data. Export works for CSV.

| Day | Tasks | Epic |
|---|---|---|
| 6 | Chart wrapper component (`analytics-chart`). Angular model interfaces for all analytics DTOs. Analytics service (TypeScript). | E2 |
| 7 | Project dashboard component: KPI cards (budget, schedule, completion), phase progress bar, team utilization mini-chart. | E3 |
| 8 | Company dashboard component: projects status distribution chart, budget overview, top delayed projects table. | E3 |
| 9 | Timesheet report page: filterable by user/project/date range, hours table with totals, CSV export button. | E4 |
| 10 | Resource utilization report page: workload by user over date range, overallocation flags, CSV export. | E4 |

**Week 2 checkpoint (see Section 3).**

### Week 3 — Polish, PDF Export, Integrations (Days 11–15)

**Goal:** PDF export working, analytics embedded in existing Feature #4 views, Feature #4 frontend backlog cleared.

| Day | Tasks | Epic |
|---|---|---|
| 11 | PDF export backend (WeasyPrint or reportlab — see risk R3). PDF download endpoint. | E4 |
| 12 | PDF export frontend: export button with loading state, `MatSnackBar` feedback. | E4 |
| 13 | Feature #4 frontend catch-up: `ResourceAssignmentPanel` tab in TareaDetail (IT-1), team avatars in Gantt (IT-2). | E5 / F4 FE |
| 14 | Feature #4 frontend catch-up: `TeamTimeline` tab in ProyectoDetail (IT-3). Embed analytics KPI section in ProyectoDetail header. | E5 / F4 FE |
| 15 | Buffer: bug fixes, test gaps, CONTEXT.md + DECISIONS.md updates, PR review prep. | All |

**Week 3 checkpoint / done criteria (see Section 3).**

### Buffer Strategy

Day 15 is a dedicated buffer day. If any previous day ran over, Day 15 absorbs it.
If the timeline is on track by Day 13, use Day 15 for Feature #4 backend tests
(BK-26, BK-27, BK-28) which are still pending.

---

## 3. Review Checkpoints

### End of Week 1 — Backend Green Light

Before starting Week 2, all of the following must be true:

- [ ] All analytics endpoints return correct data against the development database
- [ ] `python manage.py check` reports 0 issues
- [ ] Analytics services test file exists with >= 85% line coverage
- [ ] API contract document written (endpoint list, request params, response shapes)
- [ ] Chart library decision finalized and package installed (see risk R1)

If any item is red, do not start E2. Extend Week 1 into Day 6 and compress Week 2.

### End of Week 2 — Frontend Pages Working

Before starting Week 3, all of the following must be true:

- [ ] Project dashboard renders with real data from the API
- [ ] Company dashboard renders with real data from the API
- [ ] Timesheet report page filters work (user, project, date range)
- [ ] Resource utilization report page renders correctly
- [ ] CSV export downloads a valid file for at least one report
- [ ] `ng build --configuration=production` compiles with 0 TypeScript errors
- [ ] All new Angular components use `ChangeDetectionStrategy.OnPush`
- [ ] No `any` types in new TypeScript files

If CSV export is not done by end of Day 10, move it to Day 11 and defer PDF by one day.

### End of Week 3 — Feature #5 Done

Feature #5 is complete when:

- [ ] All must-have items (Section 5) are delivered and working
- [ ] PDF export works for at least the project KPI report
- [ ] Analytics KPI section is visible in ProyectoDetail
- [ ] Feature #4 integration items IT-1, IT-2, IT-3 are complete
- [ ] Backend analytics service coverage >= 85%
- [ ] Zero PrimeNG, zero Bootstrap, zero Tailwind in any new file
- [ ] CONTEXT.md updated with Feature #5 final state
- [ ] DECISIONS.md updated with any new architecture decisions

---

## 4. Risk Management

### R1 — Chart Library Decision (Probability: High, Impact: High)

**Description:** Feature #4 plan approved `ngx-charts` (`@swimlane/ngx-charts`).
However, `ngx-charts` has had Angular 18 compatibility issues in recent versions.
If it does not compile cleanly, the entire chart layer is blocked.

**Mitigation:**
- Day 3 spike: install `ngx-charts`, render one bar chart with static data. Pass/fail in 2 hours.
- Fallback: Chart.js via `ng2-charts` (`chart.js` + `ng2-charts`). Both are Angular Material
  compatible. Chart.js has broader Angular 18 support. Decide and commit on Day 3.
- Do not attempt to use `p-chart` (PrimeNG). This is prohibited by CLAUDE.md DEC-011.

### R2 — Feature #4 Frontend Debt Blocks Integrations (Probability: High, Impact: Medium)

**Description:** E5 integrations (IT-1, IT-2, IT-3) require Feature #4 components that do
not exist yet. If Feature #4 frontend takes longer than Days 13–14, E5 slips.

**Mitigation:**
- Feature #4 frontend work is allocated specifically in Week 3 (Days 13–14).
- The must-have analytics pages (dashboards, reports) are standalone routes — they do not
  depend on Feature #4 frontend components. Value is delivered even if E5 slips.
- If Day 13–14 are not enough for Feature #4 frontend, carry IT-2 (Gantt avatars) to the
  buffer day. IT-2 is the lowest-value integration item.

### R3 — PDF Export Complexity (Probability: Medium, Impact: Medium)

**Description:** PDF generation on the backend can be unexpectedly complex. WeasyPrint
requires system-level dependencies (Cairo, Pango). reportlab is pure Python but has a
steeper API. Either can consume a full extra day.

**Mitigation:**
- Day 11 is allocated exclusively to PDF backend. If it is not working by end of Day 11,
  classify PDF as "Should have" and defer it.
- Minimum viable alternative: render the report as HTML in the browser and let the user
  print to PDF via `window.print()`. This is zero backend work and acceptable for MVP.

### R4 — Database Query Performance on Analytics (Probability: Medium, Impact: Medium)

**Description:** Analytics aggregations run across the full project dataset for a company.
On a company with 50+ projects and 500+ tasks, naive ORM queries will be slow.

**Mitigation:**
- All analytics services must use a single aggregated query with `annotate()` + `values()`.
  No Python loops over queryset results.
- Add `db_index=True` on `fecha_inicio`, `fecha_fin` in `ResourceAssignment` if not already
  present (verify in migration 0015).
- If a query exceeds 500ms in development, convert it to a raw SQL query with `EXPLAIN ANALYZE`
  before deploying.

### R5 — Scope Creep from Dashboard "Nice to Haves" (Probability: High, Impact: Low)

**Description:** Analytics dashboards invite endless additions. Real-time updates, drill-down
charts, export to Excel, email scheduling — all are plausible but out of scope for Feature #5 MVP.

**Mitigation:**
- Anything not in the must-have list (Section 5) requires an explicit scope change request.
- Log all requested additions in a "Feature #5 backlog" section at the bottom of this document
  rather than adding them to the current sprint.
- The rule: if it takes more than 4 hours, it is not in this feature. Park it.

---

## 5. Prioritization Decisions

### Must Have — MVP of Feature #5

These items will be delivered by end of Week 3 or Feature #5 is not done.

1. **Project KPI dashboard** — budget vs. actual, schedule status, phase completion percentages
2. **Company overview dashboard** — projects by status, total active resources, budget summary
3. **Timesheet report** — hours by user and project, filterable by date range, CSV export
4. **Resource utilization report** — workload per user over a date range, overallocation flags
5. **Analytics embedded in ProyectoDetail** — KPI section visible inside the project detail view
6. **CSV export** — for both timesheet and resource utilization reports
7. **Backend analytics services** — with >= 85% test coverage

### Should Have — High Value, Not Blocking

These items will be attempted in Week 3 buffer time. If time is insufficient, they move to Feature #6.

1. **PDF export** — project KPI report as downloadable PDF
2. **Feature #4 integrations IT-1 and IT-3** — ResourceAssignmentPanel in TareaDetail, TeamTimeline tab in ProyectoDetail
3. **Chart drill-down** — clicking a phase in the progress chart filters the task list below

### Could Have — Nice to Have

These are explicitly deferred to a future feature or sprint.

1. **Real-time dashboard updates** (WebSocket or polling)
2. **Excel export** (XLSX format)
3. **Scheduled email reports** (n8n workflow)
4. **Custom date comparison** (this month vs. last month)
5. **Feature #4 integration IT-2** (Gantt avatars) — low visual impact, high frontend complexity
6. **Gantt chart in analytics** (separate from the existing Gantt view)

---

## 6. Integration with Pending Feature #4 Work

### What Is Pending in Feature #4

From CONTEXT.md (27 March 2026):

**Backend (Feature #4):**
- [ ] BK-26: `test_resource_models.py`
- [ ] BK-27: `test_resource_services.py` (>= 85% coverage required)
- [ ] BK-28: `test_resource_views.py`

**Frontend (Feature #4):**
- [ ] FE-1 to FE-10: 8 Angular components (ResourceAssignmentCard, ResourceCalendar, WorkloadChart, TeamTimeline, ResourcePanel, AvailabilityForm, CapacityForm, OverallocationBadge)
- [ ] IT-1: Tab "Recursos" in TareaDetail
- [ ] IT-2: Team avatars in Gantt view
- [ ] IT-3: Tab "Equipo" in ProyectoDetail

### Does Feature #4 Pending Work Block Feature #5?

**Backend tests (BK-26–28): NO.** Feature #5 analytics endpoints are independent of whether
the resource management tests exist. They share models but not test files.

**Feature #4 frontend components: PARTIALLY YES for E5 only.**
- The standalone analytics pages (dashboards, reports) are loaded as their own routes.
  They do not depend on Feature #4 frontend at all.
- E5 integrations (IT-1, IT-3) require TareaDetail and ProyectoDetail to be in a stable state.
  Both components are currently unstable (modified in working tree per git status). These must
  be stabilized before embedding analytics sections into them.

### Strategy: Sequential with Deliberate Overlap

Do NOT attempt to finish all Feature #4 frontend work before starting Feature #5.
That approach guarantees delays because Feature #4 frontend is estimated at 8+ components.

Instead, use this approach:

1. **Weeks 1–2:** Feature #5 backend and standalone frontend pages. Feature #4 frontend is
   untouched. This keeps Feature #5 progress unblocked.

2. **Week 3, Days 13–14:** Dedicate two days specifically to Feature #4 frontend debt.
   Focus only on IT-1 and IT-3 (the integration items that also appear in Feature #5 E5).
   This clears the integration blockers and delivers Feature #4 value simultaneously.

3. **Feature #4 backend tests (BK-26–28):** Schedule these on Day 15 buffer day if everything
   else is on track. If not, create a separate 2-day task after Feature #5 closes.

**The guiding principle:** Feature #5 standalone value (dashboards, reports, CSV export) is
independent. Deliver that first. Then use Week 3 to bridge the Feature #4 gap.

---

## 7. Technical Handoffs

### Backend Endpoints Required Before Each Frontend Component

| Frontend component | Required endpoint | Available by |
|---|---|---|
| ProjectDashboard | `GET /api/v1/projects/{id}/kpis/` | Day 2 |
| CompanyDashboard | `GET /api/v1/projects/analytics/overview/` | Day 2 |
| AnalyticsChart wrapper | Any endpoint (uses mock initially) | Day 3 |
| TimesheetReport | `GET /api/v1/projects/analytics/timesheets/` | Day 3 |
| ResourceUtilizationReport | `GET /api/v1/projects/resources/workload/` | Exists (Feature #4) |
| CSV export button | `GET /api/v1/projects/analytics/timesheets/export/` | Day 4 |
| PDF export button | `GET /api/v1/projects/{id}/kpis/export/` | Day 11 |
| Analytics section in ProyectoDetail | `GET /api/v1/projects/{id}/kpis/` | Day 2 |

### Data Requirements for Chart Development

Charts require realistic data in the development database to validate rendering.
Before starting E3 on Day 7, the development database should have:

- At minimum 2 projects with at least 3 phases each
- At least 1 project with a budget set and some actual spend (WorkSession hours)
- At least 2 users with resource assignments in Feature #4 models
- At least 30 days of timesheet data (WorkSession records)

If the development database does not have this, run the Django management commands
or seed fixtures before Day 7. Do not develop charts against an empty database —
the empty states will render but chart validation is impossible.

### Angular Interface Contracts

All TypeScript interfaces for analytics DTOs must be created on Day 6 before
any component development begins. Naming convention follows existing project patterns:

```
frontend/src/app/features/proyectos/models/analytics.model.ts
frontend/src/app/features/proyectos/services/analytics.service.ts
```

The analytics service follows the same pattern as `resource.service.ts` — typed methods,
`HttpClient`, no manual JWT headers (interceptor handles it), returns `Observable<T>`.

---

## 8. Feature #5 Backlog (Deferred Items)

Items captured here during development that are out of scope for this sprint:

_(Empty at plan creation — populate during execution)_

---

## Plan Metadata

**Created by:** Project Shepherd agent
**Reviewed by:** n/a (solo developer — Juan David is the approver)
**Next review:** End of Week 1 checkpoint
**Document path:** `docs/plans/FEATURE-5-EXECUTION-PLAN.md`
