# ShiftOpt — Model Reference

## 1. Set Covering (Dantzig 1954)

Minimise total staffing cost over a cyclic 24-hour (or 168-hour) horizon:

```
min  sum_{d,s} c_s * x[d,s]
s.t. sum_{d,s} a[h,d,s] * x[d,s] >= r_h   for all h in H
     x[d,s] in Z_+
```

where `a[h,d,s] = 1` when shift `s` starting on day `d` covers hour `h` (cyclic wrap).
LP relaxation duals approximate marginal cost; always labelled "approximate".

## 2. Per-Employee Roster (CP-SAT)

Variables:

- `x[e, d, s]` Boolean: employee `e` works shift `s` on day `d` (absent when `d` is an unavailable day of `e`)
- `b[e, d, s, k]` Boolean: the break of that shift starts at offset `k` (`k` in the break window, Article 109)
- `u_h` integer in `[0, r_h]`: shortfall at hour `h`, with `present_h + u_h >= r_h` and `present_h = sum x covering h - sum b breaking at h`
- `v[e, t]` Boolean: the 24-hour rest window of employee `e` starts at hour `t` (cyclic)
- `N_e` = night shifts of `e`; `F = max_e N_e - min_e N_e` (`AddMaxEquality` / `AddMinEquality`)

Hard constraints:

- at most one shift per day per employee;
- weekly hours per employee `<= max_weekly_hours` (Article 105);
- for each pair of shifts whose rest is below `min_rest_between_shifts` (general formula, cyclic offsets 1 to 6), `x + x' <= 1`;
- every cyclic window of `max_consecutive_days + 1` days holds at most `max_consecutive_days` shifts;
- rest window: `v[e, t]` implies no work in hours `t .. t+23` (cyclic); at least one `v[e, t]` true (Article 111). Equivalent to the validator's longest-gap rule because a gap is an uncovered hour run;
- each shift that needs a break has exactly one break slot in its window (Article 109).

Objective (lexicographic, one CP-SAT solve per tier, each tier capped at the optimum of the previous one):

```
Tier 1:  min sum_h u_h
Tier 2:  min sum_{e,d,s} wage_e * cost_per_wage_unit(s) * x[e,d,s]   (Article 98 premium inside)
Tier 3:  min F                                                       (only if more than one employee)
Tier 4:  min number of shifts on the employee's preferred days off   (only if any preference)
```

Status is `OPTIMAL` only when every tier is `OPTIMAL`; otherwise `FEASIBLE` with the bound and gap of the last tier that returned a solution.

Options:

- `symmetry_breaking` (default off): for employees with equal wage and no requests, `shifts_e >= shifts_{e+1}`. Measured on the 20/30/40 employee benchmark, it was slower on seed 0 (see WORKLOG 4.3).
- `decompose` (default off): solve the aggregate model with implicit breaks (section 1b), then cap starts per day and shift type to `ceil(count)`. The result is an approximation and is reported as `FEASIBLE`, never `OPTIMAL`.

## 1b. Implicit Breaks (Bechtold-Jacobs style)

Each worker of a shift that needs a break is counted once in `x[d, s]` and once in one slot `y[d, s, k]` inside the break window. The break removes that worker from coverage at hour `k`. This has the same optimum as enumerating every (shift, break position) column; the test suite checks this against an explicit enumeration on small instances.

Breaks are whole hours. A 30 or 45 minute break takes a full hour of coverage, which is a conservative approximation.

## 3. Labor Law Constraints (45/2019/QH14)

| Article | Constraint | Formula |
|---------|-----------|---------|
| 105 | Daily hours | `length_s <= max_daily_hours` for each shift worked |
| 105 | Weekly hours | `sum_{d,s} length_s * x[e,d,s] <= max_weekly_hours` |
| 106 | Night window | 22:00–06:00 |
| 110 | Rest between shifts | `24 + sigma' - (sigma + L) >= 12` (general, not L=8 shortcut) |
| 111 | Weekly continuous rest | Longest gap in hour axis >= 24 |

## 4. Staffing Conversion

Retail mode: `r[d,h] = max(r_min_h, ceil(alpha * D[d,h] / p))`, applied to the weekly load index
built by `staffing/latent_demand.py`. Per product, each stockout cell (`hours_stock_status = 1`)
is replaced by the mean of that product's non-stockout sales at the same weekday and hour; a cell
with no non-stockout day keeps its observed value and is counted. Hourly sales are summed over
products and averaged over the days of each weekday. The processed file stores this load as it is.
At quantify time, `zero_night_load` sets night hours (`LaborRules.night_start` to `night_end`) to
zero, so their head count is the night floor `night_min_staff`. The night window is therefore a
caller assumption, recorded in the result metadata. The load is the normalized sales of an
e-commerce front warehouse, not staffing demand.

Call-centre mode: Erlang A (with abandonment) targeting 80/20 service level.
- Erlang C (no abandonment, tends to overstaff) and square-root staffing `N = R + beta * sqrt(R)`.
- Erlang A (`erlang_a_service_level`): M/M/n+M queue with exponential patience. The queue
  distribution is a birth-death recursion in log space. The service level is measured on the
  virtual waiting time (Garnett, Mandelbaum and Reiman 2002): a call that would be served without
  its own abandonment counts; the abandonment of calls ahead still counts. Patience is capped at
  one hour (`MAX_PATIENCE_SECONDS`), because the queue grows with patience. The agent search runs
  in `[1, n_C]`, where `n_C` is the Erlang C staffing. The virtual wait CDF is
  computed by uniformization, so every term is non-negative. As patience grows the result matches
  Erlang C. `patience_seconds` has no default: it is a team assumption.
- Synthetic arrivals (`staffing/call_arrivals.py`): a seeded weekly shape with weekday factors and
  daily peaks. This is an assumption for testing the pipeline, not observed call data.

## 5. Sensitivity Analysis

- Discrete marginal cost: `delta_t = z(r + e_t) - z(r)` by 168 re-solves of the head-count model with implicit breaks. This is the exact marginal cost of the integer model, not a shadow price. A point is `proven` only when both solves are `OPTIMAL`.
- LP relaxation dual per hour: from the same model with continuous `x` and `y`, taken from constraint `cover_h`. Always labelled approximate; the integrality gap can be large. Duals are only read at an LP optimum.
- Dual vs marginal cost: the table `(hour, lp_dual, delta_t, proven)` shows the integrality effect hour by hour. This replaces "fix the integer variables and re-solve the LP": with every variable integer, fixing them all leaves no free variable, so the duals of that LP are degenerate.
- Parametric sweep: `lambda in {0.8, ..., 1.3}`, demand scaled by `tolerant_ceil(lambda * r_t)`. Each point carries `proven`; a `FEASIBLE` point is never read as an optimum.
- Re-solve resolvers: `aggregate_resolver` (head-count model) or `roster_resolver` (CP-SAT roster). Labor cost comes from `kpi.labor_cost`, not from the lexicographic objective, whose last tier is not a cost.
- Covariate scenarios: `DemandScenario` scales demand per weekday and keeps the source text beside the result. The promotion uplift `1.43` is a suggested default from the FreshRetailNet paper (arXiv:2505.16319 v5). Holiday and rain have no default: the caller supplies the factor and its source.
- Staffing assumptions: `sweep_staffing_assumption` re-derives demand with `required_staff` for each value of `alpha`, `productivity`, `min_staff` or `night_min_staff`, then re-solves. Sensitivity to these team assumptions is part of the analysis.
