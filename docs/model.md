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
- `u_h` integer in `[0, r_h]`: shortfall at hour `h`, with `present_h + u_h >= r_h` and `present_h = sum x covering h`
- `v[e, t]` Boolean: the 24-hour rest window of employee `e` starts at hour `t` (cyclic)
- `N_e` = night shifts of `e`; `F = max_e N_e - min_e N_e` (`AddMaxEquality` / `AddMinEquality`)
- `g_e` integer in `[0, m_e]`: hours below the contract minimum `m_e`, only for employees with a minimum (section 8)
- `H_e` worked hours of `e`, `H_max`, `H_min`: only when `cost_tolerance_percent > 0` (section 7)

Hard constraints:

- at most one shift per day per employee;
- weekly hours per employee `<= min(max_weekly_hours, employee.max_weekly_hours)` (Article 105; the employee cap is optional and can only lower the law limit);
- for each pair of shifts whose rest is below `min_rest_between_shifts` (general formula, cyclic offsets 1 to 6), `x + x' <= 1`;
- every cyclic window of `max_consecutive_days + 1` days holds at most `max_consecutive_days` shifts;
- rest window: `v[e, t]` implies no work in hours `t .. t+23` (cyclic); at least one `v[e, t]` true (Article 111). Equivalent to the validator's longest-gap rule because a gap is an uncovered hour run;
- when the instance has a weekly budget, total labour cost `<= weekly_budget` (section 8).

Objective (lexicographic, one CP-SAT solve per tier, each tier capped at the optimum of the previous one):

```
Tier 1:  min sum_h u_h
Tier 1b: min sum_e g_e                                               (only if some employee has a minimum)
Tier 2:  min sum_{e,d,s} wage_e * cost_per_wage_unit(s) * x[e,d,s]   (Article 98 premium inside)
Tier 3:  min F                                                       (only if more than one employee)
Tier 3b: min H_max - H_min                                           (only if cost_tolerance_percent > 0)
Tier 4:  min number of shifts on the employee's preferred days off   (only if any preference)
```

Repair adds a `changes` tier after tier 1b (section 6). With a positive cost tolerance the cap after tier 2 is relaxed (section 7).

Status is `OPTIMAL` only when every tier is `OPTIMAL`; otherwise `FEASIBLE` with the bound and gap of the last tier that returned a solution.

Options:

- `symmetry_breaking` (default off): for employees with equal wage, equal maximum and minimum hours and no requests, `shifts_e >= shifts_{e+1}`. No measurement is kept in the repo for this option; it stays off.
- `decompose` (default off): solve the aggregate set covering model, then cap starts per day and shift type to `ceil(count)`. The result is an approximation and is reported as `FEASIBLE`, never `OPTIMAL`.

## 2a. ILP formulation of the per-employee roster

The same model is built twice: as a CP-SAT model (`roster_cpsat.py`, the production path) and as an integer program solved by HiGHS through PuLP (`roster_mip.py`, used for the solver comparison and the integrality gap). Both use the rows below. Row numbers match the docstring of `solve_roster_mip`.

Sets and parameters:

- `E` employees, `D = {0..6}` days (0 is Monday), `S` shift types with length at most `max_daily_hours`.
- `H = {0..167}` hours of the week. `A(d,s)` is the set of hours covered by shift `s` starting on day `d` (cyclic).
- `K = max_consecutive_days`; `W_k` is every cyclic window of `K+1` days.
- `P` is the set of forbidden pairs `(s, s', o)`, `o` in 1..6, whose rest `24 o + start(s') - end(s)` is below `min_rest_between_shifts` (Article 110).
- `T_e(t)` is the set of `(d,s)` whose hours intersect the 24 cyclic hours `t .. t+23`.
- `N` is the set of night shifts (more than half of the shift inside 22:00 to 06:00).
- `wage_e`, `cost(s) = cost_per_wage_unit(s)` (100 times length plus 30 times night hours), `cap_e = min(max_weekly_hours, max_weekly_hours_e)`, `r_h` the demand, `pref(e)` the preferred days off.

Variables:

- `x[e,d,s]` in {0,1}, only for days that `e` can work.
- `u[h]` integer, `0 <= u[h] <= r_h`: shortfall at hour `h`.
- `v[e,t]` in {0,1}: the 24-hour rest window of `e` starts at hour `t`.
- `n[e]`, `n_max`, `n_min`: integer, nonnegative auxiliaries for the night spread.
- `g[e]` integer in `[0, m_e]` for employees with a contract minimum `m_e`; `H_max`, `H_min` for the worked-hours spread when the cost tolerance is positive.

Rows:

| Row | Rule | Constraint |
|---|---|---|
| C1 | At most one shift a day (code: `_add_one_shift_per_day`) | `sum_s x[e,d,s] <= 1` |
| C2 | Weekly hours, Article 105 (code: `_add_weekly_hours`) | `sum_{d,s} L_s x[e,d,s] <= cap_e` |
| C3 | Rest of at least 12 hours between shifts, Article 110 (code: `_add_rest_between_shifts`) | `x[e,d,s] + x[e,(d+o) mod 7,s'] <= 1` for every `(s,s',o)` in `P` |
| C4 | At most `K` working days in any `K+1` cyclic days (code: `_add_consecutive_days`) | `sum_{d in W, s} x[e,d,s] <= K` for every window `W` |
| C5 | At least 24 consecutive hours of rest a week, Article 111 (code: `_add_weekly_rest`) | `v[e,t] + x[e,d,s] <= 1` for every `(d,s)` in `T_e(t)`, and `sum_t v[e,t] >= 1` |
| C7 | Coverage, soft (code: `_add_coverage`) | `sum_{(e,d,s): h in A(d,s)} x[e,d,s] + u[h] >= r_h` |
| C8 | Night spread (code: `_add_night_spread`) | `n[e] = sum_{d, s in N} x[e,d,s]`; `n_max >= n[e]`; `n_min <= n[e]` |
| C9 | Weekly budget, optional (code: `_add_budget`) | `sum_{e,d,s} wage_e cost(s) x[e,d,s] <= B` |
| C10 | Contract minimum, soft (code: `_add_min_hours`) | `sum_{d,s} L_s x[e,d,s] + g[e] >= m_e` |
| C11 | Worked-hours spread, only with a cost tolerance (code: `_add_hours_spread`) | `H_max >= sum_{d,s} L_s x[e,d,s]`; `H_min <= sum_{d,s} L_s x[e,d,s]` |

Why C5 is written pairwise: a 24-hour rest window starting at `t` exists exactly when no worked hour falls in `t .. t+23`. The pairwise rows are tighter than one big-M row per window, at the cost of more rows (see the model-size table in `benchmarks.md`).

Why C8 is exact at the optimum: the tier minimises `n_max - n_min`. Increasing `n_max` and decreasing `n_min` only make the objective worse, so at the optimum `n_max` equals the largest `n[e]` and `n_min` the smallest.

Repair (`RepairSpec`, code: `_add_repair`): for `d < from_day` and for pinned shifts, `x` is fixed to 1 if the shift is in the locked set and to 0 otherwise. The change count is

```
changes = sum_{(e,d,s) in baseline} (1 - x[e,d,s]) + sum_{(e,d,s) not in baseline} x[e,d,s] + #{baseline shifts with no variable}
```

which equals the size of the symmetric difference between the baseline and the new roster.

Lexicographic objective. Each tier is one solve; after tier `j` with optimum `f_j*` the row `f_j <= f_j*` is added:

1. `min sum_h u[h]` (shortfall, hours);
2. `min sum_e g[e]` (hours below contract minimums; only when some employee has a minimum);
3. `min changes` (repair only);
4. `min sum_{e,d,s} wage_e cost(s) x[e,d,s]` (labour cost including the Article 98 premium; capped at its optimum, or relaxed by the cost tolerance);
5. `min n_max - n_min` (night spread; only with at least two employees);
6. `min H_max - H_min` (worked-hours spread; only when the cost tolerance is positive);
7. `min sum_{e,d in pref(e)} sum_s x[e,d,s]` (preference misses; only when some employee has preferences).

The MIP and the CP-SAT model share these tiers and therefore agree on the optimum of each tier whenever both prove it (`tests/test_roster_mip.py`).

Code map (row to function): C1 `_add_one_shift_per_day`, C2 `_add_weekly_hours`, C3 `_add_rest_between_shifts`, C4 `_add_consecutive_days`, C5 `_add_weekly_rest`, C7 `_add_coverage`, C8 `_add_night_spread`, C9 `_add_budget`, C10 `_add_min_hours`, C11 `_add_hours_spread`, repair `_add_repair`, tiers `_stages`. The MIP has the same names in `roster_mip.py` (`_add_*`, `_stages`).

## 3. Labor Law Constraints (45/2019/QH14)

| Article | Constraint | Formula |
|---------|-----------|---------|
| 105 | Daily hours | `length_s <= max_daily_hours` for each shift worked |
| 105 | Weekly hours | `sum_{d,s} length_s * x[e,d,s] <= min(max_weekly_hours, employee cap)` |
| 106 | Night window | 22:00–06:00 |
| 110 | Rest between shifts | `24 + sigma' - (sigma + L) >= 12` (general, not L=8 shortcut) |
| 111 | Weekly continuous rest | Longest gap in hour axis >= 24 |

## 4. Staffing Conversion

Conversion (the only demand mode): `r[d,h] = max(r_min_h, ceil(alpha * D[d,h] / p))`, applied to the weekly load index
built by `staffing/latent_demand.py`. Per product, each stockout cell (`hours_stock_status = 1`)
is replaced by the mean of that product's non-stockout sales at the same weekday and hour; a cell
with no non-stockout day keeps its observed value and is counted. Hourly sales are summed over
products and averaged over the days of each weekday. The demand profile stores this load as it is (`demand_profiles.sales_load`), so assumption sweeps do not need the source file.
At quantify time, `zero_night_load` sets night hours (`LaborRules.night_start` to `night_end`) to
zero, so their head count is the night floor `night_min_staff`. The night window is therefore a
caller assumption, recorded in the result metadata. The load is the normalized sales of an
e-commerce front warehouse, not staffing demand.

Call-centre mode (Erlang A/C) was removed on 2026-11-07 (spec D18).

## 5. Sensitivity Analysis

- Discrete marginal cost: `delta_t = z(r + e_t) - z(r)` by 168 re-solves of the head-count (set covering) model. This is the exact marginal cost of the integer model, not a shadow price. A point is `proven` only when both solves are `OPTIMAL`.
- LP relaxation dual per hour: from the same model with continuous `x`, taken from constraint `cover_h`. Always labelled approximate; the integrality gap can be large. Duals are only read at an LP optimum.
- Dual vs marginal cost: the table `(hour, lp_dual, delta_t, proven)` shows the integrality effect hour by hour. This replaces "fix the integer variables and re-solve the LP": with every variable integer, fixing them all leaves no free variable, so the duals of that LP are degenerate.
- Parametric sweep: `lambda in {0.8, ..., 1.3}`, demand scaled by `tolerant_ceil(lambda * r_t)`. Each point carries `proven`; a `FEASIBLE` point is never read as an optimum.
- Re-solve resolvers: `aggregate_resolver` (head-count model) or `roster_resolver` (CP-SAT roster). Labor cost comes from `kpi.labor_cost`, not from the lexicographic objective, whose last tier is not a cost.
- Covariate scenarios: `DemandScenario` scales demand per weekday and keeps the source text beside the result. The promotion uplift `1.43` is a suggested default from the FreshRetailNet paper (arXiv:2505.16319 v5). Holiday and rain have no default: the caller supplies the factor and its source.
- Staffing assumptions: `sweep_staffing_assumption` re-derives demand with `required_staff` for each value of `alpha`, `productivity`, `min_staff` or `night_min_staff`, then re-solves. Sensitivity to these team assumptions is part of the analysis.
- Greedy baseline comparison: the same instance solved by CP-SAT and by `baseline.greedy_roster`, a heuristic that is never reported as optimal.
- Cost-tolerance sweep (`fairness_sweep`): one full re-solve per tolerance, reporting the cost increase against tolerance 0, the night spread and the worked-hours spread (section 7).

## 6. Repair (C6)

Input: lịch gốc `B` (một `Solution`), `from_day` (0..7) và ca ghim `P`. Tập khóa `L = {b in B : b.day < from_day} ∪ P`.

- Ngày `d < from_day`: `work[e,d,s]` cố định bằng 1 khi `(e,d,s)` thuộc `L`, bằng 0 nếu không.
- Ca ghim: `work = 1`.
- `changes = sum_{(e,d,s) in B} (1 - work[e,d,s]) + sum_{(e,d,s) not in B} work[e,d,s] + |{b in B : b không có biến work}|`. Đây là khoảng cách Hamming trên bộ (nhân viên, ngày, ca).
- Thứ tự tầng: `shortfall`, `min_hours` (nếu có), `changes`, `cost`, `night_spread`, `hours_spread` (nếu có dung sai), `preference`. Mỗi tầng ràng buộc bằng tối ưu của tầng trước (cùng cơ chế với mô hình thường).
- Khả thi: mọi ràng buộc cứng (một ca/ngày, giờ, nghỉ 12 giờ, nghỉ 24 giờ tuần, ngày liên tiếp, ngày không làm được, ngân sách tuần) đều đơn điệu: bỏ ca không bao giờ tạo vi phạm mới. Vậy tập `L` đã qua `validate` là nghiệm khả thi của mô hình (không thêm ca nào). Backend kiểm `L` trước khi tạo lượt; vi phạm trả 422 với danh sách. Solver không bao giờ nhận đầu vào không khả thi do khóa.
- Không kết hợp với phá đối xứng và phân rã (lịch gốc phá vỡ tính đồng nhất).

Gợi ý người thay (`shiftopt.replacement.suggest_replacements`): với ô (nhân viên vắng `a`, ngày `d`), thử từng nhân viên khác không có ca ngày `d` và không vắng `d`, cùng loại ca; giữ ứng viên mà `validate` không báo vi phạm. Xếp theo `(muốn nghỉ ngày d, chi phí thêm, giờ tuần sau khi thay, mã)`. Không gọi solver.

## 7. Cost tolerance and worked-hours spread (F)

Parameter `cost_tolerance_percent` t in [0, 10] (`SolveParams`, default 0; decision D21 in `đặc tả.md`).

- t = 0: tiers are shortfall, min_hours (if any), changes (repair only), cost capped at its optimum, night spread, preference. This is the order of section 2 and it is unchanged.
- t > 0: the cost tier is capped at floor(C * (100 + t) / 100), where C is the cost optimum the solver found. The cap is relative to that value: if the cost tier is FEASIBLE and not optimal, the tolerance is measured from the found value, not from the true optimum. Use kpi.labor_cost on the returned roster for the real cost, which can exceed the cost tier value.
- t > 0 adds a tier hours_spread = H_max - H_min after the night-shift spread, before preference. H_e = sum over shifts of length_s * x[e,d,s]; H_max >= H_e and H_min <= H_e, the same linearisation as the night-shift spread in section 2a.
- Scope: solve_roster (CP-SAT, also the decomposition path) and solve_roster_mip. solve_roster_weighted ignores the tolerance.
- KPI: hours_spread = max - min of worked hours per employee, counting each shift at full length. Idle employees count as zero.
- Rationale: the default order puts cost before fairness, so the cheapest employees take the night shifts. A tolerance of a few percent lets fairness improve at a bounded extra cost. Measured effect: docs/benchmarks.md section 6.

## 8. Weekly budget and contract minimum hours (G3)

Decisions D25 and D26 in `đặc tả.md`.

- Weekly budget B (`Instance.weekly_budget`, optional, hundredths of the wage unit like `kpi.labor_cost`): one hard row, sum over (e,d,s) of wage_e * cost_s * x[e,d,s] <= B. Coverage stays soft, so a binding budget raises the shortfall tier and never makes the model infeasible. The empty roster always satisfies the row. `validate` adds the kind OVER_BUDGET (no employee), so manual edits above the budget are rejected, and a repair whose locked days already exceed B is rejected before solving.
- Contract minimum m_e (`Employee.min_weekly_hours`, optional, at most the weekly cap): a gap variable g_e in [0, m_e] with H_e + g_e >= m_e, where H_e = sum of length_s * x[e,d,s]. The tier min_hours = sum of g_e comes right after the shortfall tier and before changes and cost. It is soft: an employee who cannot reach the minimum (for example too many unavailable days) shows up as a positive tier value, not as INFEASIBLE. It is not a validator violation, so "removing a shift never creates a violation" still holds for repair and replacement.
- The tier is added only when at least one employee has a minimum, so rosters without minimums are unchanged. `solve_roster_weighted` ignores the minimum tier.
- Tier order with both: shortfall, min_hours, changes (repair only), cost, night spread, hours spread (when the cost tolerance is positive), preference.
- Symmetry breaking groups employees by wage, maximum hours and minimum hours.
- Greedy baseline: skips an employee whose shift would push the running cost above the budget.
- Pre-solve warnings: MIN_HOURS_UNREACHABLE when m_e exceeds the most hours the employee can work; BUDGET_BELOW_DEMAND when B is below total demand times the lowest wage times 100.

## 9. Explaining understaffed hours (G2)

`shiftopt.shortfall.explain_shortfall(instance, solution)` is a post-hoc diagnosis, not part of the model, and it does not call a solver.

- For each hour h with demand above the staff on the floor, each employee who is not working at h is tried with one extra assignment: every allowed shift (length at most max_daily_hours) that covers h and starts on the day of h or the day before.
- Each candidate is checked with `validate` on that employee alone, keeping only the violation kinds that the candidate adds, plus OVER_BUDGET when the roster cost plus the shift cost exceeds the weekly budget. An employee is free if some candidate adds nothing. Otherwise the candidate with the fewest new kinds gives the reasons, and `blocked` counts employees per kind.
- If no allowed shift covers h, the hour is marked uncoverable.
- When the shortfall tier of the solve is OPTIMAL, no employee can be free, since a legal extra shift would lower the shortfall. With a FEASIBLE solve, free employees mean the solver had not found that improvement in the time limit. The UI says so.
