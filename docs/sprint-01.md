# Sprint 1: daily portfolio environment and Merton benchmark

## Goal

Deliver a reproducible, tested environment for allocating between one simulated risky asset
and one risk-free asset without transaction costs. Produce a comparison of constant-target
policies against Merton's analytical fraction, with uncertainty estimates and an explicit
assessment of daily rebalancing.

## Agreed time settings

- One step represents one calendar day, with `dt = 1 / 365` years.
- One episode represents one year, with 365 decisions and daily market transitions.
- Each episode starts a new simulated trajectory. Later RL training will retain the agent's
  learned parameters across episodes.
- Market parameters are expressed in annual units and converted consistently using `dt`.

## Agreed initial model

The initial choices below were accepted with Santino on 2026-11-15. Their full specification,
daily accounting example, and validation requirements are in [environment.md](environment.md).
Both members should be able to explain the alternatives and the selected formulation.

| Decision       | Initial choice                                                         | Alternative and trade-off                                                                                                                                  |
| -------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Price dynamics | Exact daily GBM returns with fixed, known parameters                   | Historical returns add estimation and model mismatch; reserve that comparison for stage B                                                                  |
| Action         | Continuous target risky fraction in `[0, 1]`                           | A discrete grid simplifies action selection but limits allocation precision; leverage and shorting expand the domain and require additional solvency rules |
| Observation    | Current risky fraction and normalized remaining time                   | Adding market parameters supports varying markets but increases the scope of the initial validation                                                        |
| Reward         | `log(W_next / W_current)`                                              | Terminal-only log utility expresses the same undiscounted objective but provides less frequent feedback                                                    |
| Horizon        | A genuine finite one-year objective, ending with `terminated=True`     | Treating the year as a sampling cutoff requires a continuing objective and different bootstrapping semantics                                               |
| Initial state  | Wealth normalized to 1 and all holdings in the risk-free asset         | Random initial fractions broaden state coverage and may be useful when costs are introduced                                                                |
| Initial market | Annual `mu = 0.04`, `r = 0.02`, `sigma = 0.20`, giving `pi_star = 0.5` | Higher volatility at the same optimum can change the learning signal; retain the proposed case as a transparent validation scenario                        |

The initial market values are synthetic choices for validation. Here `mu` is the GBM price
drift, and `r` is a continuously compounded risk-free rate. These are the agreed initial
values; later experiments can assess other configurations.

## Agreed daily accounting

At the beginning of a day, observe the current portfolio and choose target risky fraction
`a`. Rebalance at the current prices, then generate the day's returns. For an independent
standard normal draw `z`, use:

```text
risky_growth = exp((mu - sigma**2 / 2) * dt + sigma * sqrt(dt) * z)
safe_growth = exp(r * dt)
portfolio_growth = a * risky_growth + (1 - a) * safe_growth
W_next = W_current * portfolio_growth
fraction_next = a * risky_growth / portfolio_growth
reward = log(portfolio_growth)
```

The observation for the next decision contains `fraction_next`, which generally differs from
the chosen target after prices move. The objective is the undiscounted sum of rewards,
equal to `log(W_final / W_initial)`. Future training settings must preserve that objective.

## Work sequence

Step 1 specification is recorded in [environment.md](environment.md). The Windows symlink
placeholder is excluded from newline and Markdown formatting so those hooks preserve its Git
target. Steps 2 and 3 are implemented in `src/tp_final_rl/env.py` and `tests/test_env.py`,
including Gymnasium validation. Baseline evaluation and the benchmark experiment remain
the next steps.

1. **Agree and document the environment specification.** Resolve the proposals above and
   record the accepted choices. Check the local development tools, including the existing
   Windows checkout issue where the end-of-file hook changes the `CLAUDE.md` symlink
   placeholder. Resolve that issue before declaring the full checks successful.
2. **Implement the environment.** Add a typed configuration and a Gymnasium environment with
   seeded `reset` and daily `step`. Validate parameters and actions, and expose wealth and
   portfolio accounting through diagnostic information. Run Gymnasium's environment checker.
3. **Test the financial accounting.** Verify wealth conservation on cost-free rebalancing,
   all-cash growth, all-risky growth, post-return fraction drift, positivity for supported
   inputs, reward telescoping, seed reproducibility, and termination after exactly 365 steps.
   Include deterministic cases with known answers and invalid-input handling.
4. **Implement baseline evaluation.** Compare constant-target policies over a grid containing
   Merton's fraction. Each policy rebalances to its target daily. Use the same simulated
   market trajectories across policies and report paired differences in total log return.
   Keep episode count, grid resolution, and seeds configurable and save them with results.
5. **Validate the benchmark.** Plot mean terminal log growth against target fraction, with
   confidence intervals and a marker for `pi_star`. Quantify uncertainty in differences
   near the maximum. If the experiment cannot distinguish neighboring fractions, report the
   uncertainty and assess the required sample size instead of claiming an exact recovery.
6. **Record the result.** Commit the implementation before the relevant run. Save outputs
   under `runs/YYYY-MM-DD_<description>/`, generate the figure into `report/figures/`, and add
   the configuration, source commit, metrics, figure path, and conclusion to the experiment log.

## Proposed deliverables

- `docs/environment.md`: the agreed model, units, transition order, and horizon semantics.
- `src/tp_final_rl/env.py`: environment and configuration.
- `src/tp_final_rl/evaluate.py`: reproducible baseline evaluation entry point and plot generation.
- `tests/test_env.py`: accounting, reproducibility, and episode tests.
- `report/figures/merton_baseline.pdf`: generated comparison figure.
- An entry in `docs/experiment-log.md` tracing the result to its source commit.

These file names are a proposed layout and can be adjusted during implementation.

## Acceptance criteria

- Both members can explain one complete transition, the reward, and the annual-to-daily units.
- The environment passes the financial tests and Gymnasium's environment checker.
- `uv run pre-commit run --all-files` and `uv run pytest` pass.
- A documented command reproduces the baseline evaluation from its recorded configuration.
- Results include uncertainty and distinguish the daily-rebalanced problem from the
  continuous-time Merton benchmark. Exact agreement is not assumed: assess the discrete-time
  optimum numerically or use a smaller-step diagnostic with the same one-year horizon if
  the observed gap needs investigation. Daily steps remain the primary experiment.
- The result and any unresolved discrepancy are recorded with evidence in the experiment log.

## Suggested pacing and next milestone

Plan for three focused working sessions: specification and environment, tests and evaluation,
then the benchmark run and diagnosis. This is a planning estimate, not a fixed deadline.

The next milestone is choosing and training an RL algorithm against this validated benchmark.
Transaction costs, the comparison of agents by cost level, and stages A, B, and C follow in
subsequent work. Record training-algorithm and hyperparameter trade-offs before implementing
that milestone.
