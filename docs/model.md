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

- `x[e, d, s]` Boolean — employee `e` works shift `s` on day `d`
- `w[e, d] = sum_s x[e,d,s]` — 1 if employee works on day `d`
- `u_h >= 0` — shortfall at hour `h` (`staff_h + u_h >= r_h`); overstaffing is computed in `kpi.py`

Objective (lexicographic):

```
Phase 1:  min sum_h u_h
Phase 2:  min sum_{e,d,s} c_s * x[e,d,s]  (sum_h u_h capped at the phase-1 value)
```

## 3. Labor Law Constraints (45/2019/QH14)

| Article | Constraint | Formula |
|---------|-----------|---------|
| 105 | Daily hours | `length_s <= max_daily_hours` for each shift worked |
| 105 | Weekly hours | `sum_{d,s} length_s * x[e,d,s] <= max_weekly_hours` |
| 106 | Night window | 22:00–06:00 |
| 110 | Rest between shifts | `24 + sigma' - (sigma + L) >= 12` (general, not L=8 shortcut) |
| 111 | Weekly continuous rest | Longest gap in hour axis >= 24 |

## 4. Staffing Conversion

Retail mode: `r[d,h] = max(r_min_h, ceil(alpha * D[d,h] / p))`

Call-centre mode: Erlang A (with abandonment) targeting 80/20 service level.
Implemented so far: Erlang C (no abandonment, tends to overstaff) and square-root staffing
`N = R + beta * sqrt(R)` as a fast approximation. Erlang A is deferred to task 6.2.

## 5. Sensitivity Analysis

- LP dual from set covering relaxation: approximate marginal cost per hour.
- Discrete marginal cost: `z(r + e_t) - z(r)` via 168 re-solves.
- Parametric sweep: `lambda in {0.8, 0.9, ..., 1.3}`, demand scaled by `ceil(lambda * r_t)`.
