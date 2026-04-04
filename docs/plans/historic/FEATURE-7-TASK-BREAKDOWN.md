# FEATURE-7: Budget & Cost Tracking — Task Breakdown

**Feature:** Budget & Cost Tracking
**Milestone:** 100% Odoo Parity (Feature #7 of 7)
**Stack:** Django 5 + DRF + Angular 18 + Angular Material + PostgreSQL 16
**Created:** 2026-03-27
**Status:** Planning

---

## Specification Summary

**Goal:** Provide full budget planning, real-time cost tracking, expense management, earned value metrics, and invoicing preparation for projects managed in SaiSuite.

**Dependencies on existing features:**
- Feature #1 (Projects/Tasks): `Project.presupuesto_total`, `Task.estimated_hours`
- Feature #3 (Timesheets): `TimesheetEntry.hours_worked`, used as actual cost basis
- Feature #4 (Resource Management): `ResourceAssignment`, `ResourceCapacity` for allocation context
- Feature #5 (Analytics): Existing chart infrastructure reusable in cost reports
- Feature #6 (Scheduling): Task completion % used in EVM progress calculations

**New entities:** `ResourceCostRate`, `ProjectBudget`, `ProjectExpense`, `BudgetSnapshot`

---

## Epic Overview

| Epic | Name | Tasks | Est. Hours |
|------|------|-------|------------|
| Epic 1 | Backend Models & Migrations | BG-01 – BG-06 | 14h |
| Epic 2 | Cost Calculation Engine | BG-07 – BG-14 | 20h |
| Epic 3 | Budget Variance & Alerts | BG-15 – BG-19 | 12h |
| Epic 4 | Expenses & Cost Rates Management | BG-20 – BG-28 | 18h |
| Epic 5 | EVM Metrics | BG-29 – BG-33 | 16h |
| Epic 6 | Frontend Angular Material UI | BG-34 – BG-46 | 38h |
| Epic 7 | Cost Reports & Analytics | BG-47 – BG-52 | 16h |
| Epic 8 | Invoicing Preparation | BG-53 – BG-57 | 12h |
| Epic 9 | Tests (≥85% coverage) | BG-58 – BG-66 | 22h |
| Epic 10 | Documentation | BG-67 – BG-70 | 8h |
| **Total** | | **70 tasks** | **176h** |

---

## Epic 1: Backend Models & Migrations

**Acceptance Criteria:**
- All four new models pass Django system checks
- Migrations apply cleanly on empty and existing databases
- All models inherit from `BaseModel` (UUID pk, company FK, timestamps)
- Multi-tenant isolation enforced: every model filters by `company_id`
- Admin registration complete for debugging

---

### [ ] BG-01: ResourceCostRate model

**Description:** Create `ResourceCostRate` model to store per-user hourly billing rates with validity periods. A user may have multiple non-overlapping rates over time.

**Acceptance Criteria:**
- Fields: `user (FK User)`, `hourly_rate (NUMERIC 15,2)`, `currency (CharField, max 3, default 'COP')`, `start_date (DATE)`, `end_date (DATE, null=True, blank=True)`, `notes (TextField, blank=True)`
- Inherits `BaseModel` (includes `company` FK)
- `unique_together` does not apply — overlapping is prevented at service level
- `__str__` returns `"{user} @ {hourly_rate} {currency} from {start_date}"`
- Registered in Django admin with list_display and date filters
- Migration generates without warnings

**Estimated effort:** 2h
**Dependencies:** None
**Assignee role:** Backend developer

---

### [ ] BG-02: ProjectBudget model

**Description:** Create `ProjectBudget` model as a one-to-one extension of `Project` to hold planned budget figures, approval status, and alert thresholds.

**Acceptance Criteria:**
- Fields: `project (OneToOneField Project, related_name='budget')`, `planned_labor_cost (NUMERIC 15,2, default 0)`, `planned_expense_cost (NUMERIC 15,2, default 0)`, `planned_total_budget (NUMERIC 15,2, default 0)`, `approved_budget (NUMERIC 15,2, null=True)`, `is_approved (BooleanField, default False)`, `approved_by (FK User, null=True)`, `approved_at (TIMESTAMPTZ, null=True)`, `alert_threshold_percentage (IntegerField, default 80)`, `currency (CharField, max 3, default 'COP')`
- `planned_total_budget` is NOT auto-computed by model — services handle this
- Inherits `BaseModel`
- Migration generates without warnings

**Estimated effort:** 2h
**Dependencies:** BG-01
**Assignee role:** Backend developer

---

### [ ] BG-03: ProjectExpense model

**Description:** Create `ProjectExpense` model to record individual expense line items charged to a project.

**Acceptance Criteria:**
- Fields: `project (FK Project)`, `category (CharField, choices: TRAVEL, SOFTWARE, HARDWARE, CONSULTING, OTHER)`, `description (TextField)`, `amount (NUMERIC 15,2)`, `expense_date (DATE)`, `paid_by (FK User)`, `billable (BooleanField, default True)`, `receipt_url (URLField, blank=True)`, `approved (BooleanField, default False)`, `approved_by (FK User, null=True)`, `approved_at (TIMESTAMPTZ, null=True)`
- Inherits `BaseModel` (includes `company` FK)
- Index on `(project, expense_date)` for date-range queries
- Migration generates without warnings

**Estimated effort:** 2h
**Dependencies:** BG-01
**Assignee role:** Backend developer

---

### [ ] BG-04: BudgetSnapshot model

**Description:** Create `BudgetSnapshot` model to store point-in-time cost snapshots for trend analysis.

**Acceptance Criteria:**
- Fields: `project (FK Project)`, `snapshot_date (DATE)`, `labor_cost (NUMERIC 15,2)`, `expense_cost (NUMERIC 15,2)`, `total_cost (NUMERIC 15,2)`, `planned_budget (NUMERIC 15,2)`, `variance (NUMERIC 15,2)`, `variance_percentage (NUMERIC 8,2)`
- `unique_together: (project, snapshot_date)` — one snapshot per project per day
- Inherits `BaseModel`
- Migration generates without warnings

**Estimated effort:** 2h
**Dependencies:** BG-02, BG-03
**Assignee role:** Backend developer

---

### [ ] BG-05: Run and verify all migrations

**Description:** Generate and apply all four migrations for Epic 1 models. Validate on a clean DB and an existing DB with seeded data.

**Acceptance Criteria:**
- `python manage.py makemigrations proyectos` produces migration files without conflicts
- `python manage.py migrate` applies cleanly on empty PostgreSQL instance
- `python manage.py migrate` applies cleanly on DB seeded with Features #1–#6 data
- `python manage.py check` reports zero issues
- No raw SQL in any migration file

**Estimated effort:** 2h
**Dependencies:** BG-01, BG-02, BG-03, BG-04
**Assignee role:** Backend developer

---

### [ ] BG-06: Serializers for new models

**Description:** Create list and detail serializers for all new models following DRF patterns already established in the app.

**Acceptance Criteria:**
- `ResourceCostRateListSerializer`: id, user (nested minimal), hourly_rate, currency, start_date, end_date
- `ResourceCostRateDetailSerializer`: all fields including notes
- `ProjectBudgetSerializer`: all fields + read-only computed fields: actual_labor_cost, actual_expense_cost, actual_total_cost, variance, variance_percentage (populated by view from service calls, not computed in serializer)
- `ProjectExpenseListSerializer`: id, category, description, amount, expense_date, paid_by (name), billable, approved
- `ProjectExpenseDetailSerializer`: all fields including receipt_url, approval info
- `BudgetSnapshotSerializer`: all fields, read-only
- No business logic in any serializer — transformation only
- All serializers use `read_only_fields` for computed/audit fields

**Estimated effort:** 2h
**Dependencies:** BG-01, BG-02, BG-03, BG-04
**Assignee role:** Backend developer

---

## Epic 2: Cost Calculation Engine

**Acceptance Criteria:**
- All calculation functions live exclusively in `budget_services.py`
- Functions are pure: same inputs produce same outputs
- Rate lookup uses the rate valid on the timesheet entry date (not latest rate)
- Zero-rate entries are handled without division errors
- All monetary results are Python `Decimal` with two decimal places

---

### [ ] BG-07: Create budget_services.py skeleton

**Description:** Create `backend/apps/proyectos/budget_services.py` with module docstring, imports, and logger.

**Acceptance Criteria:**
- File exists at correct path
- Logger initialized as `logger = logging.getLogger(__name__)`
- Imports: `Decimal`, `datetime`, Django ORM models, `select_related` pattern documented in comments
- No `print()` statements anywhere in file

**Estimated effort:** 0.5h
**Dependencies:** BG-06
**Assignee role:** Backend developer

---

### [ ] BG-08: Implement get_effective_rate(user_id, target_date, company_id)

**Description:** Helper function that returns the `ResourceCostRate.hourly_rate` for a given user on a given date, or `Decimal('0')` if no rate is defined for that period.

**Acceptance Criteria:**
- Queries `ResourceCostRate` where `start_date <= target_date` and `(end_date IS NULL OR end_date >= target_date)` and `company_id = company_id`
- Returns `Decimal('0')` when no matching rate exists (not an exception)
- Uses `.first()` — if multiple rates match (data error), uses the most recently created
- Logs warning if multiple rates found for same user/date

**Estimated effort:** 2h
**Dependencies:** BG-07
**Assignee role:** Backend developer

---

### [ ] BG-09: Implement calculate_labor_cost(project_id, company_id)

**Description:** Calculate total actual labor cost for a project by multiplying each `TimesheetEntry.hours_worked` by the effective hourly rate of the assigned user on that entry's date.

**Acceptance Criteria:**
- Fetches all `TimesheetEntry` records for the project via `task__project_id`
- For each entry, calls `get_effective_rate(entry.user_id, entry.date, company_id)`
- Result: `sum(entry.hours_worked * rate for all entries)`
- Uses `select_related('user', 'task')` to avoid N+1 queries
- Returns `Decimal('0.00')` for projects with no timesheet entries
- All arithmetic uses `Decimal`, never `float`

**Estimated effort:** 3h
**Dependencies:** BG-08
**Assignee role:** Backend developer

---

### [ ] BG-10: Implement calculate_expense_cost(project_id, company_id)

**Description:** Calculate total approved expense cost for a project.

**Acceptance Criteria:**
- Signature: `calculate_expense_cost(project_id, company_id, billable_only=False) -> Decimal`
- Queries `ProjectExpense` filtered by `project_id`, `company_id`, and `approved=True`
- If `billable_only=True`, also filters `billable=True`
- Returns sum using `aggregate(Sum('amount'))`
- Returns `Decimal('0.00')` when no expenses exist

**Estimated effort:** 1.5h
**Dependencies:** BG-07
**Assignee role:** Backend developer

---

### [ ] BG-11: Implement calculate_total_cost(project_id, company_id)

**Description:** Aggregate labor and expense costs into a single total.

**Acceptance Criteria:**
- Returns: `{"labor_cost": Decimal, "expense_cost": Decimal, "total_cost": Decimal}`
- Calls `calculate_labor_cost` and `calculate_expense_cost` internally
- All values are `Decimal` with 2 decimal places

**Estimated effort:** 1h
**Dependencies:** BG-09, BG-10
**Assignee role:** Backend developer

---

### [ ] BG-12: Implement calculate_cost_breakdown_by_resource(project_id, company_id)

**Description:** Return a per-user cost breakdown showing hours worked and cost contribution per resource.

**Acceptance Criteria:**
- Each dict: `{"user_id", "user_full_name", "hours_worked": Decimal, "cost": Decimal, "percentage_of_total": Decimal}`
- Sorted by cost descending
- Percentage calculated against total labor cost (0 if total is 0)
- Uses `values('user_id').annotate(total_hours=Sum('hours_worked'))` then applies rates per user

**Estimated effort:** 3h
**Dependencies:** BG-09
**Assignee role:** Backend developer

---

### [ ] BG-13: Implement calculate_cost_breakdown_by_task(project_id, company_id)

**Description:** Return a per-task cost breakdown aggregating timesheet entries by task.

**Acceptance Criteria:**
- Each dict: `{"task_id", "task_name", "estimated_hours": Decimal, "actual_hours": Decimal, "actual_cost": Decimal, "hours_variance": Decimal}`
- Includes tasks with zero actual hours (from `Task` model directly)
- Sorted by actual_cost descending

**Estimated effort:** 3h
**Dependencies:** BG-09
**Assignee role:** Backend developer

---

### [ ] BG-14: Implement set_project_budget(project_id, company_id, budget_data)

**Description:** Create or update the `ProjectBudget` record for a project.

**Acceptance Criteria:**
- Uses `update_or_create(project_id=project_id, company_id=company_id)`
- Validates `planned_total_budget >= 0`, raises `ValidationError` otherwise
- Validates `alert_threshold_percentage` is between 1 and 100
- Does NOT set `is_approved=True` — approval is a separate service call
- Logs `logger.info("budget_set", extra={"project_id": str(project_id), "total": ...})`

**Estimated effort:** 2h
**Dependencies:** BG-06
**Assignee role:** Backend developer

---

## Epic 3: Budget Variance & Alerts

**Acceptance Criteria:**
- Variance calculations are consistent: `variance = planned - actual` (positive = under budget)
- Alert thresholds evaluated on every cost-read endpoint
- No background jobs — alerts are synchronous checks
- Budget snapshots idempotent (update_or_create by date)

---

### [ ] BG-15: Implement calculate_budget_variance(project_id, company_id)

**Description:** Compare actual total cost against approved (or planned) budget.

**Acceptance Criteria:**
- Returns: `{"planned_budget", "actual_cost", "variance", "variance_percentage", "is_over_budget": bool, "alert_triggered": bool}`
- Uses `approved_budget` if set, falls back to `planned_total_budget`
- `variance = planned_budget - actual_cost` (negative = over budget)
- `variance_percentage = (variance / planned_budget) * 100` — returns 0 if `planned_budget` is 0
- `alert_triggered = True` when `(actual_cost / planned_budget * 100) >= alert_threshold_percentage`

**Estimated effort:** 2.5h
**Dependencies:** BG-11, BG-14
**Assignee role:** Backend developer

---

### [ ] BG-16: Implement approve_budget(project_id, company_id, approver_user_id)

**Description:** Mark a `ProjectBudget` as approved.

**Acceptance Criteria:**
- Raises `ValidationError` if no `ProjectBudget` exists for project
- Raises `ValidationError` if budget is already approved
- Sets `is_approved=True`, `approved_by_id`, `approved_at=now()`, `approved_budget=planned_total_budget`
- Logs approval event with project_id and approver_id

**Estimated effort:** 1.5h
**Dependencies:** BG-14
**Assignee role:** Backend developer

---

### [ ] BG-17: Implement check_budget_alerts(project_id, company_id)

**Description:** Evaluate current cost against threshold and return structured alert payload.

**Acceptance Criteria:**
- Returns: `{"alert_level": "none"|"warning"|"critical", "message": str, "current_percentage": Decimal, "threshold_percentage": int}`
- `warning` when `current_percentage >= threshold_percentage`
- `critical` when `current_percentage >= 100`
- `none` otherwise
- Does not send emails — returns data only

**Estimated effort:** 2h
**Dependencies:** BG-15
**Assignee role:** Backend developer

---

### [ ] BG-18: Implement create_budget_snapshot(project_id, company_id)

**Description:** Persist a `BudgetSnapshot` record for the current date.

**Acceptance Criteria:**
- Uses `update_or_create(project_id=project_id, snapshot_date=today())` — idempotent
- Populates all cost fields from `calculate_total_cost` and `calculate_budget_variance`
- Returns the saved snapshot instance
- Logs snapshot creation with project_id and snapshot_date

**Estimated effort:** 2h
**Dependencies:** BG-15
**Assignee role:** Backend developer

---

### [ ] BG-19: Budget variance & alerts endpoints

**Description:** Expose variance, alert, and snapshot data via DRF views.

**Acceptance Criteria:**
- `GET /api/v1/projects/{id}/budget/variance/` → `calculate_budget_variance`
- `GET /api/v1/projects/{id}/budget/alerts/` → `check_budget_alerts`
- `POST /api/v1/projects/{id}/budget/snapshot/` → `create_budget_snapshot`, returns 201
- `GET /api/v1/projects/{id}/budget/snapshots/` → list snapshots ordered by date desc
- All endpoints require authenticated user with `company_admin` or `valmen_admin` role

**Estimated effort:** 2.5h
**Dependencies:** BG-15, BG-17, BG-18
**Assignee role:** Backend developer

---

## Epic 4: Expenses & Cost Rates Management

**Acceptance Criteria:**
- Full CRUD for both `ProjectExpense` and `ResourceCostRate`
- Approval workflow for expenses enforced at service level
- Cost rate overlaps detected and rejected with clear error messages
- All endpoints paginated (server-side, page size 20)

---

### [ ] BG-20: Implement register_expense(project_id, company_id, expense_data, paid_by_user_id)

**Acceptance Criteria:**
- Validates `amount > 0`, raises `ValidationError` otherwise
- Validates `expense_date` is not in the future by more than 1 day
- Sets `approved=False` by default
- Logs expense registration with project_id and amount

**Estimated effort:** 2h
**Dependencies:** BG-07
**Assignee role:** Backend developer

---

### [ ] BG-21: Implement approve_expense(expense_id, approver_user_id, company_id)

**Acceptance Criteria:**
- Raises `ValidationError` if expense already approved
- Sets `approved=True`, `approved_by_id`, `approved_at=now()`
- Raises `PermissionDenied` if approver is same user who submitted (`paid_by`)
- Logs approval event

**Estimated effort:** 1.5h
**Dependencies:** BG-20
**Assignee role:** Backend developer

---

### [ ] BG-22: Expense CRUD endpoints

**Acceptance Criteria:**
- `GET /api/v1/projects/{id}/expenses/` — list, paginated, filterable by category and approved status
- `POST /api/v1/projects/{id}/expenses/` — calls `register_expense`
- `GET/PUT/PATCH /api/v1/projects/{id}/expenses/{expense_id}/` — detail/update (not allowed if approved)
- `DELETE /api/v1/projects/{id}/expenses/{expense_id}/` — hard delete
- `POST /api/v1/projects/{id}/expenses/{expense_id}/approve/` — calls `approve_expense`

**Estimated effort:** 2.5h
**Dependencies:** BG-21
**Assignee role:** Backend developer

---

### [ ] BG-23: Implement validate_rate_overlap(user_id, start_date, end_date, company_id, exclude_id=None)

**Acceptance Criteria:**
- Raises `ValidationError` with message if overlap detected
- Handles open-ended rates (end_date=None) correctly
- Excludes a specific rate ID (for update operations)

**Estimated effort:** 2h
**Dependencies:** BG-07
**Assignee role:** Backend developer

---

### [ ] BG-24: Implement create_cost_rate and update_cost_rate

**Acceptance Criteria:**
- Both call `validate_rate_overlap` before saving
- Validates `hourly_rate > 0`
- Validates `end_date > start_date` when end_date provided
- Logs rate creation/update with user_id and effective dates

**Estimated effort:** 2h
**Dependencies:** BG-23
**Assignee role:** Backend developer

---

### [ ] BG-25: Cost rates CRUD endpoints

**Acceptance Criteria:**
- `GET/POST /api/v1/cost-rates/` — list/create, filterable by user_id
- `GET/PUT/PATCH/DELETE /api/v1/cost-rates/{id}/`
- `GET /api/v1/users/{user_id}/cost-rates/` — rates for a specific user
- All require `company_admin` or `valmen_admin` role

**Estimated effort:** 2.5h
**Dependencies:** BG-24
**Assignee role:** Backend developer

---

### [ ] BG-26: ProjectBudget CRUD endpoints

**Acceptance Criteria:**
- `GET /api/v1/projects/{id}/budget/` — returns budget with computed actuals
- `POST/PUT/PATCH /api/v1/projects/{id}/budget/` — create or update (not allowed if approved)
- `POST /api/v1/projects/{id}/budget/approve/` — calls `approve_budget`
- GET response includes: all fields + actual_labor_cost, actual_expense_cost, actual_total_cost, variance, variance_percentage, alert

**Estimated effort:** 2.5h
**Dependencies:** BG-14, BG-16, BG-17
**Assignee role:** Backend developer

---

### [ ] BG-27: Cost summary endpoints

**Acceptance Criteria:**
- `GET /api/v1/projects/{id}/costs/labor/` — labor cost + breakdown by resource
- `GET /api/v1/projects/{id}/costs/expenses/` — expense cost total
- `GET /api/v1/projects/{id}/costs/total/` — all three figures
- `GET /api/v1/projects/{id}/costs/by-resource/` — `calculate_cost_breakdown_by_resource`
- `GET /api/v1/projects/{id}/costs/by-task/` — `calculate_cost_breakdown_by_task`
- Cached for 60 seconds

**Estimated effort:** 2h
**Dependencies:** BG-11, BG-12, BG-13
**Assignee role:** Backend developer

---

### [ ] BG-28: URL configuration consolidation

**Acceptance Criteria:**
- All 20+ new endpoints registered in `proyectos/urls.py`
- `python manage.py show_urls` lists all new routes without duplicates
- Existing Feature #1–#6 endpoints unchanged

**Estimated effort:** 1h
**Dependencies:** BG-19, BG-22, BG-25, BG-26, BG-27
**Assignee role:** Backend developer

---

## Epic 5: EVM Metrics

**Acceptance Criteria:**
- EVM calculations follow PMI PMBOK standard definitions
- All metrics returned in a single endpoint call
- Division-by-zero handled gracefully (returns None, not exception)
- `task.completion_percentage` from Feature #6 used as progress source

---

### [ ] BG-29: Implement calculate_planned_value(project_id, company_id, as_of_date)

**Acceptance Criteria:**
- PV = `planned_total_budget * (elapsed_project_duration / total_project_duration)`
- Uses `Project.fecha_inicio` and `Project.fecha_fin`
- Returns 0 if project dates not set; returns `planned_total_budget` if `as_of_date >= fecha_fin`
- Uses `Decimal` throughout, no `float`

**Estimated effort:** 2.5h
**Dependencies:** BG-14
**Assignee role:** Backend developer

---

### [ ] BG-30: Implement calculate_earned_value(project_id, company_id)

**Acceptance Criteria:**
- EV = `planned_total_budget * overall_project_completion_percentage`
- `overall_project_completion_percentage` = average of all task `completion_percentage` values
- Returns 0 if no tasks or budget is zero
- Logs the completion percentage used for auditability

**Estimated effort:** 2h
**Dependencies:** BG-14
**Assignee role:** Backend developer

---

### [ ] BG-31: Implement calculate_earned_value_metrics(project_id, company_id)

**Acceptance Criteria:**
- Returns: `{"PV", "EV", "AC", "CV", "SV", "CPI", "SPI", "EAC"}`
- CV = EV - AC; SV = EV - PV; CPI = EV/AC; SPI = EV/PV; EAC = planned_total_budget/CPI
- Returns `None` for ratio metrics when denominator is 0 (not exception)

**Estimated effort:** 3h
**Dependencies:** BG-29, BG-30
**Assignee role:** Backend developer

---

### [ ] BG-32: EVM endpoint

**Acceptance Criteria:**
- `GET /api/v1/projects/{id}/costs/evm/` — optional `?as_of_date=YYYY-MM-DD`
- Returns 200 with full EVM dict
- Cached for 5 minutes

**Estimated effort:** 1.5h
**Dependencies:** BG-31
**Assignee role:** Backend developer

---

### [ ] BG-33: EVM edge case hardening

**Acceptance Criteria:**
- Project with no tasks → all zeros, no exceptions
- Project with no budget → all zeros / None for index metrics
- Project with future start date → PV = 0
- Project with past end date → PV = planned_total_budget
- All edge cases documented with inline comments

**Estimated effort:** 2h
**Dependencies:** BG-31
**Assignee role:** Backend developer

---

## Epic 6: Frontend Angular Material UI

**Acceptance Criteria:**
- All components use `ChangeDetectionStrategy.OnPush`
- No `any` types — all interfaces mirror backend serializers
- Empty states use `sc-empty-state` per UI-UX-STANDARDS.md
- Loading states: `mat-progress-bar` above tables, never centered spinner
- Confirmations: `MatDialog` with `ConfirmDialogComponent`
- Feedback: `MatSnackBar` with `panelClass: ['snack-success'|'snack-error'|'snack-warning']`
- Angular 18: `@if`, `@for`, `@switch` — never `*ngIf`, `*ngFor`
- SCSS: `var(--sc-*)` variables only

---

### [ ] BG-34: TypeScript interfaces — budget.model.ts

**Acceptance Criteria:**
- File: `frontend/src/app/features/proyectos/models/budget.model.ts`
- Interfaces: `ResourceCostRate`, `ProjectBudget`, `ProjectBudgetDetail`, `ProjectExpense`, `BudgetSnapshot`, `CostSummary`, `CostBreakdownByResource`, `CostBreakdownByTask`, `EvmMetrics`, `BudgetAlert`, `BudgetVariance`, `InvoiceData`
- All monetary fields typed as `number`; all date fields as `string`
- No `any`

**Estimated effort:** 2h
**Dependencies:** BG-06
**Assignee role:** Frontend developer

---

### [ ] BG-35: budget.service.ts

**Acceptance Criteria:**
- Methods: `getBudget`, `setBudget`, `approveBudget`, `getVariance`, `getAlerts`, `getLaborCost`, `getExpenseCost`, `getTotalCost`, `getCostByResource`, `getCostByTask`, `getEvmMetrics(projectId, asOfDate?)`, `createSnapshot`, `getSnapshots`
- All return typed `Observable<T>` — no `any`

**Estimated effort:** 2.5h
**Dependencies:** BG-34
**Assignee role:** Frontend developer

---

### [ ] BG-36: cost-rates.service.ts

**Acceptance Criteria:**
- Methods: `getCostRates(filters?)`, `getUserCostRates(userId)`, `createCostRate`, `updateCostRate`, `deleteCostRate`
- All typed with `ResourceCostRate`

**Estimated effort:** 1h
**Dependencies:** BG-34
**Assignee role:** Frontend developer

---

### [ ] BG-37: expense.service.ts

**Acceptance Criteria:**
- Methods: `getExpenses(projectId, filters?)`, `getExpense`, `createExpense`, `updateExpense`, `deleteExpense`, `approveExpense`
- All typed with `ProjectExpense`

**Estimated effort:** 1h
**Dependencies:** BG-34
**Assignee role:** Frontend developer

---

### [ ] BG-38: BudgetManagementComponent

**Acceptance Criteria:**
- Shows: planned budget, approved budget, actual costs, variance, alert status
- `mat-card` per KPI, `mat-progress-bar` (determinate) for budget consumed
- Progress bar color: primary (<threshold), warn (>=threshold), overrides to red (>100%)
- Approve button visible only to `company_admin` — disabled if already approved
- `sc-empty-state` with "Set Budget" CTA when no budget configured

**Estimated effort:** 4h
**Dependencies:** BG-35
**Assignee role:** Frontend developer

---

### [ ] BG-39: ExpenseRegistrationDialogComponent

**Acceptance Criteria:**
- `mat-dialog` with: category (mat-select), description (mat-textarea), amount (mat-input numeric), expense_date (mat-datepicker), billable (mat-slide-toggle), receipt_url (mat-input, optional)
- All fields `appearance="outline"`
- Reactive form with validators
- Inline errors with `@if` inside `mat-form-field`
- Submit calls `expense.service.createExpense()`, shows `MatSnackBar` on success/error
- Closes dialog on success

**Estimated effort:** 3h
**Dependencies:** BG-37
**Assignee role:** Frontend developer

---

### [ ] BG-40: CostBreakdownTableComponent

**Acceptance Criteria:**
- `@Input() data: CostBreakdownByResource[] | CostBreakdownByTask[]`
- `@Input() mode: 'resource' | 'task'`
- Appropriate columns per mode; `MatSortModule` on numeric columns
- Formatted currency via `CurrencyPipe`
- `sc-empty-state` outside `mat-table`
- Purely presentational — no HTTP calls

**Estimated effort:** 3h
**Dependencies:** BG-34
**Assignee role:** Frontend developer

---

### [ ] BG-41: BudgetAlertsComponent

**Acceptance Criteria:**
- On init, calls `budget.service.getAlerts(projectId)`
- `warning` → persistent `MatSnackBar` with `snack-warning` panelClass
- `critical` → persistent `MatSnackBar` with `snack-error` panelClass
- `none` → no snackbar
- `mat-badge` indicator on "Presupuesto" tab label

**Estimated effort:** 2.5h
**Dependencies:** BG-35
**Assignee role:** Frontend developer

---

### [ ] BG-42: InvoicePreviewComponent

**Acceptance Criteria:**
- `mat-card` header with project + client info
- `mat-table` for labor and expense line items
- Subtotals per section + grand total
- Print button: `window.print()` with print-only CSS class hiding nav
- Export PDF button: disabled, `matTooltip="Disponible en próxima versión"`

**Estimated effort:** 3h
**Dependencies:** BG-35, BG-40
**Assignee role:** Frontend developer

---

### [ ] BG-43: "Presupuesto" tab in proyecto-detail

**Acceptance Criteria:**
- New tab with `mat-icon` "account_balance" between Analytics and Baselines tabs
- Content: `BudgetManagementComponent` + `BudgetAlertsComponent` initialized with project ID
- Lazy via `@defer (on viewport)`
- Does not break existing tabs

**Estimated effort:** 2h
**Dependencies:** BG-38, BG-41
**Assignee role:** Frontend developer

---

### [ ] BG-44: Expenses list within Budget tab

**Acceptance Criteria:**
- `mat-table` columns: Date, Category, Description, Amount, Paid By, Billable, Status
- `MatPaginatorModule` server-side, page size 10
- Filter row: category + approved status (mat-select)
- Actions: Approve (company_admin, if unapproved) | Delete (opens `ConfirmDialogComponent`)
- "Add Expense" `mat-raised-button` opens `ExpenseRegistrationDialogComponent`
- `mat-progress-bar` while loading; `sc-empty-state` outside `mat-table` when empty

**Estimated effort:** 4h
**Dependencies:** BG-37, BG-39
**Assignee role:** Frontend developer

---

### [ ] BG-45: Budget set/edit form

**Acceptance Criteria:**
- `mat-expansion-panel` inside Budget tab, collapsed by default when budget exists
- Fields: planned_labor_cost, planned_expense_cost, planned_total_budget (mat-input numeric), alert_threshold_percentage (mat-slider 50–100), currency (mat-select)
- Read-only when `is_approved === true` with `mat-hint`
- Save calls `budget.service.setBudget()` with snackbar feedback

**Estimated effort:** 3h
**Dependencies:** BG-35
**Assignee role:** Frontend developer

---

### [ ] BG-46: Module and routing updates

**Acceptance Criteria:**
- All new components registered in `proyectos` module
- All required Material modules imported
- `ng build` completes with `strict: true`, zero errors

**Estimated effort:** 2h
**Dependencies:** BG-38 through BG-45
**Assignee role:** Frontend developer

---

## Epic 7: Cost Reports & Analytics

**Acceptance Criteria:**
- Charts rendered with Chart.js (same library as Feature #5)
- Reports are read-only
- Responsive on mobile viewport

---

### [ ] BG-47: CostReportsComponent shell

**Acceptance Criteria:**
- `mat-tab-group` with three tabs: "Costo en el tiempo", "Por Recurso", "EVM"
- Date range filter shared across tabs (mat-datepicker)
- `@Input() projectId: string`

**Estimated effort:** 2h
**Dependencies:** BG-35
**Assignee role:** Frontend developer

---

### [ ] BG-48: Cost Over Time chart (snapshots)

**Acceptance Criteria:**
- Chart.js line chart with three datasets: Labor, Expenses, Total
- Planned budget as horizontal dashed reference line; alert threshold as second dashed line
- Empty state when < 2 snapshots

**Estimated effort:** 3h
**Dependencies:** BG-47
**Assignee role:** Frontend developer

---

### [ ] BG-49: Resource cost breakdown chart

**Acceptance Criteria:**
- Chart.js horizontal bar chart, sorted by cost desc
- `CostBreakdownTableComponent` below chart for tabular view

**Estimated effort:** 2h
**Dependencies:** BG-47, BG-40
**Assignee role:** Frontend developer

---

### [ ] BG-50: EVM Dashboard tab

**Acceptance Criteria:**
- `mat-card` tiles for PV, EV, AC, CV, SV, CPI, SPI, EAC
- CPI/SPI color: green (≥1.0), orange (0.8–0.99), red (<0.8)
- Doughnut Chart.js gauge for CPI and SPI
- Date picker for "as of date" — recalculates PV, SV, SPI

**Estimated effort:** 4h
**Dependencies:** BG-47
**Assignee role:** Frontend developer

---

### [ ] BG-51: generate_invoice_data service function

**Acceptance Criteria:**
- Returns: `{"project", "client", "line_items": [{type, description, quantity, unit_rate, subtotal}], "subtotal_labor", "subtotal_expenses", "grand_total", "currency"}`
- Labor: one row per resource; Expenses: only `billable=True, approved=True`
- Pure read — no DB writes

**Estimated effort:** 2.5h
**Dependencies:** BG-09, BG-10
**Assignee role:** Backend developer

---

### [ ] BG-52: Invoice data endpoint

**Acceptance Criteria:**
- `GET /api/v1/projects/{id}/invoice-data/`
- Returns 400 "No billable costs found" if all costs are zero
- `company_admin` and `valmen_admin` roles only
- Cached for 2 minutes

**Estimated effort:** 1h
**Dependencies:** BG-51
**Assignee role:** Backend developer

---

## Epic 8: Invoicing Preparation

---

### [ ] BG-53: Invoice data endpoint integration test

**Acceptance Criteria:**
- Test project: 3 resources, 2 expenses (1 billable, 1 non-billable)
- Verify grand_total = labor costs + billable expense only
- Verify non-billable and unapproved expenses excluded from line_items

**Estimated effort:** 2h
**Dependencies:** BG-52
**Assignee role:** Backend developer

---

### [ ] BG-54: Print CSS for InvoicePreviewComponent

**Acceptance Criteria:**
- `@media print` block hides nav, toolbar, action buttons, progress bars
- Invoice content at full page width
- No page breaks within line item rows

**Estimated effort:** 1.5h
**Dependencies:** BG-42
**Assignee role:** Frontend developer

---

### [ ] BG-55: Invoice route and navigation

**Acceptance Criteria:**
- Route: `/proyectos/:id/invoice` renders `InvoicePreviewComponent` full-page
- "Preview Invoice" button in `BudgetManagementComponent` navigates to route
- Guarded by `company_admin` role; Back button returns to project detail

**Estimated effort:** 1h
**Dependencies:** BG-42
**Assignee role:** Frontend developer

---

### [ ] BG-56: Currency formatting consistency

**Acceptance Criteria:**
- All monetary values use `ProjectBudget.currency` setting for formatting
- Defaults to COP with Colombian Peso formatting
- No hardcoded currency symbols in templates

**Estimated effort:** 2h
**Dependencies:** BG-38, BG-42
**Assignee role:** Frontend developer

---

### [ ] BG-57: Export PDF button (disabled/future state)

**Acceptance Criteria:**
- `mat-button` with `mat-icon` "picture_as_pdf" present, `[disabled]="true"`
- `matTooltip="Exportación PDF disponible en próxima versión"` visible even when disabled
- No `window.alert()` or `console.log()` in handler

**Estimated effort:** 0.5h
**Dependencies:** BG-42
**Assignee role:** Frontend developer

---

## Epic 9: Tests (≥85% coverage)

---

### [ ] BG-58: Tests for get_effective_rate + calculate_labor_cost

**Acceptance Criteria:**
- User with rate on entry date returns correct Decimal rate
- User with no rate returns Decimal('0') — no exception
- User with open-ended rate returns correct rate
- Labor cost for project with 3 users, mixed rates = expected total
- Labor cost for project with no timesheets returns Decimal('0.00')
- All arithmetic stays in Decimal (assert isinstance)

**Estimated effort:** 3h
**Dependencies:** BG-09
**Assignee role:** Backend developer

---

### [ ] BG-59: Tests for expense and budget services

**Acceptance Criteria:**
- `register_expense` with valid data creates correctly
- `register_expense` with `amount <= 0` raises ValidationError
- `approve_expense` sets approved=True and records approver
- `approve_expense` when approver is submitter raises PermissionDenied
- `approve_expense` on already-approved expense raises ValidationError
- `set_project_budget` creates new / updates existing (idempotent)
- `approve_budget` sets is_approved=True

**Estimated effort:** 3h
**Dependencies:** BG-21, BG-16
**Assignee role:** Backend developer

---

### [ ] BG-60: Tests for cost breakdown services

**Acceptance Criteria:**
- `calculate_cost_breakdown_by_resource` with 3 users returns correct list sorted desc
- Percentages sum to 100 (within Decimal rounding tolerance)
- `calculate_cost_breakdown_by_task` includes tasks with zero actual hours
- `calculate_total_cost` matches sum of labor + expense independently calculated

**Estimated effort:** 2.5h
**Dependencies:** BG-12, BG-13
**Assignee role:** Backend developer

---

### [ ] BG-61: Tests for variance and alerts

**Acceptance Criteria:**
- Under budget → positive variance, `is_over_budget=False`
- Over budget → negative variance, `is_over_budget=True`
- `check_budget_alerts` returns 'none' / 'warning' / 'critical' correctly
- Zero-budget project → variance 0, percentage 0, no exceptions

**Estimated effort:** 2h
**Dependencies:** BG-15, BG-17
**Assignee role:** Backend developer

---

### [ ] BG-62: Tests for EVM metrics

**Acceptance Criteria:**
- Project 50% complete, on-schedule → CPI=1.0, SPI=1.0
- Over-budget project → CPI < 1.0
- Ahead-of-schedule project → SPI > 1.0
- AC=0 → CPI=None, no exception
- PV=0 → SPI=None, no exception
- `calculate_planned_value` on day 0 returns 0; on last day returns planned_total_budget

**Estimated effort:** 3h
**Dependencies:** BG-31
**Assignee role:** Backend developer

---

### [ ] BG-63: Tests for overlap validation

**Acceptance Criteria:**
- Non-overlapping rates for same user — both save without error
- Overlapping rates for same user raises ValidationError with descriptive message
- Rates for different users can overlap without error
- Update excludes itself from overlap check

**Estimated effort:** 2h
**Dependencies:** BG-23
**Assignee role:** Backend developer

---

### [ ] BG-64: API endpoint integration tests

**Acceptance Criteria:**
- Unauthenticated request → 401
- Different-company user → 403 or 404
- POST budget → 201
- Approve budget → is_approved=True
- GET EVM → all keys present
- GET invoice-data → correct line items count
- Expense approval by submitter → 400

**Estimated effort:** 3h
**Dependencies:** BG-19, BG-26, BG-27, BG-32, BG-52
**Assignee role:** Backend developer

---

### [ ] BG-65: Angular service unit tests

**Acceptance Criteria:**
- Each service spec uses `HttpClientTestingModule`
- Tests: correct URL, correct HTTP verb, typed response mapped correctly
- At least 3 method tests per service
- No actual HTTP calls in tests

**Estimated effort:** 2h
**Dependencies:** BG-35, BG-36, BG-37
**Assignee role:** Frontend developer

---

### [ ] BG-66: Coverage report and gap remediation

**Acceptance Criteria:**
- `pytest --cov=apps/proyectos/budget_services` outputs ≥85% line coverage
- Coverage report saved to `docs/test-coverage/feature-7-coverage.txt`
- `ng test --code-coverage` runs without failures

**Estimated effort:** 2h
**Dependencies:** BG-58 through BG-65
**Assignee role:** Backend + Frontend developer

---

## Epic 10: Documentation

---

### [ ] BG-67: OpenAPI / Swagger annotations

**Acceptance Criteria:**
- All new views decorated with `@extend_schema` where auto-generation is insufficient
- `GET /api/schema/swagger-ui/` shows all 20+ new endpoints grouped under "Budget & Costs" tag
- Request/response examples for set_project_budget, register_expense, EVM metrics, invoice-data

**Estimated effort:** 2.5h
**Dependencies:** BG-28
**Assignee role:** Backend developer

---

### [ ] BG-68: FEATURE-7-BACKEND-ARCHITECTURE.md

**Acceptance Criteria:**
- File: `docs/plans/FEATURE-7-BACKEND-ARCHITECTURE.md`
- Sections: data model ERD (text), service call graph, EVM formulas, rate lookup algorithm, multi-tenant isolation strategy

**Estimated effort:** 2h
**Dependencies:** All Epic 1–5 tasks
**Assignee role:** Backend developer

---

### [ ] BG-69: DECISIONS.md updates

**Acceptance Criteria:**
- Entry: why `approved_budget` stored separately from `planned_total_budget`
- Entry: why alert checking is synchronous (not Celery)
- Entry: why EVM uses `completion_percentage` (Feature #6) vs hours-based progress
- Entry: currency handling strategy (stored as string, formatting at UI layer)

**Estimated effort:** 1h
**Dependencies:** All implementation tasks
**Assignee role:** Tech lead

---

### [ ] BG-70: CONTEXT.md update

**Acceptance Criteria:**
- Feature #7 status: Complete; Odoo parity milestone marked as achieved
- Known limitations and follow-up items listed
- Next session context accurate (Wompi + Billing as next feature)

**Estimated effort:** 0.5h
**Dependencies:** All tasks complete
**Assignee role:** Tech lead

---

## Integration Points with Existing Features

### Feature #1 (Projects/Tasks)
- `Project.presupuesto_total` remains as legacy field — `ProjectBudget.planned_total_budget` is authoritative going forward
- `Task.estimated_hours` used in `calculate_cost_breakdown_by_task` for variance comparison
- `Task.completion_percentage` (Feature #6) drives EV calculation

### Feature #3 (Timesheets)
- `TimesheetEntry` is the primary data source for labor cost, queried via `task__project_id`
- No changes to `TimesheetEntry` model required
- `select_related('user', 'task__project')` used consistently

### Feature #4 (Resource Management)
- `ResourceCapacity.hours_per_week` is NOT used for cost rates — `ResourceCostRate` is the dedicated model
- `ResourceAssignment` not directly queried — actual timesheet hours used instead of planned allocation

### Feature #5 (Analytics)
- Chart.js already imported — reused in `CostReportsComponent`
- Existing chart color palette applied to cost charts

### Feature #6 (Scheduling)
- `Task.completion_percentage` is the EVM progress source
- Fallback to `(actual_hours / estimated_hours) * 100` if Feature #6 data absent (logged warning)

---

## Total Estimate

| Epic | Hours |
|------|-------|
| Epic 1: Backend Models & Migrations | 14h |
| Epic 2: Cost Calculation Engine | 16.5h |
| Epic 3: Budget Variance & Alerts | 10h |
| Epic 4: Expenses & Cost Rates | 15.5h |
| Epic 5: EVM Metrics | 11h |
| Epic 6: Frontend Angular Material | 33h |
| Epic 7: Cost Reports & Analytics | 14.5h |
| Epic 8: Invoicing Preparation | 7h |
| Epic 9: Tests | 21.5h |
| Epic 10: Documentation | 6h |
| **Total** | **149h** |

**Buffer (20%):** +30h = **~179h total**
**Calendar estimate (parallel, 2 devs):** ~13 working days (2.5 weeks)
**Calendar estimate (sequential, 1 dev):** ~25 working days (5 weeks)

---

## Risk Register

### Risk 1: TimesheetEntry data quality for cost calculations
**Probability:** High | **Impact:** High
**Mitigation:** `get_effective_rate` logs WARNING for every zero-rate lookup; admin dashboard shows unconfigured users; data validation endpoint `GET /projects/{id}/costs/validation-warnings/`

### Risk 2: EVM accuracy depends on task completion_percentage discipline
**Probability:** Medium | **Impact:** Medium
**Mitigation:** EVM dashboard shows "Data quality" indicator (% tasks with progress > 0); prominent warning if < 50% of tasks have progress reported

### Risk 3: Multi-currency support added mid-development
**Probability:** Low | **Impact:** High
**Mitigation:** Validate at `register_expense` that currency matches `ProjectBudget.currency`; document in API: "All values in project base currency"; DECISIONS.md entry: multi-currency out of scope for Feature #7

### Risk 4: Performance of labor cost calculation on large projects
**Probability:** Medium | **Impact:** Medium
**Mitigation:** Index on `TimesheetEntry(task__project_id, date, user_id)`; 60-second response cache; nightly snapshots via `create_budget_snapshot` as precomputed fallback

### Risk 5: ProjectBudget OneToOne causing RelatedObjectDoesNotExist
**Probability:** Low | **Impact:** Low
**Mitigation:** All access via `getattr(project, 'budget', None)` or `hasattr`; services return zeros for missing budget; frontend shows `sc-empty-state` with "Set Budget" CTA; no auto-creation in migration

---

## Definition of Done

**Task done when:**
1. Code reviewed by at least one other developer
2. All acceptance criteria checked off
3. No `any` types in TypeScript, no `print()` in Python
4. `ng build --strict` passes (frontend) / `python manage.py check` passes (backend)
5. Unit tests written and passing
6. Coverage threshold maintained (85% for services)

**Feature #7 done when:**
- All 70 tasks marked done
- `CONTEXT.md` updated with Odoo parity milestone
- Product owner reviewed Budget tab in `proyecto-detail`
- `docs/plans/FEATURE-7-BACKEND-ARCHITECTURE.md` merged to main
