# Daily portfolio environment

## Status and objective

Initial specification accepted with Santino on 2026-11-15 for Sprint 1. The environment
allocates wealth between one risky asset and one risk-free asset, with daily rebalancing and
zero transaction costs. Its objective is expected logarithmic terminal wealth over one year.

The modeling alternatives and their trade-offs are recorded in [the sprint plan](sprint-01.md).
This document specifies the initial model for implementation.

## Parameters and units

| Parameter              | Symbol  | Initial value | Meaning                             |
| ---------------------- | ------- | ------------- | ----------------------------------- |
| Time step              | `dt`    | `1 / 365`     | Years per calendar day              |
| Episode length         | `H`     | `365`         | Daily decisions and transitions     |
| Risky drift            | `mu`    | `0.04`        | Annual GBM drift                    |
| Risk-free rate         | `r`     | `0.02`        | Annual continuously compounded rate |
| Risky volatility       | `sigma` | `0.20`        | Annualized volatility               |
| Initial wealth         | `W_0`   | `1.0`         | Normalized wealth units             |
| Initial risky fraction | `x_0`   | `0.0`         | All initial wealth is risk-free     |
| Transaction cost       | `c`     | `0.0`         | Cost per unit of traded value       |

These are synthetic validation parameters. They stay fixed during and across episodes in the
initial experiment. A year has 365 calendar days, consistently with the proposed later crypto
evaluation. No trading-day calendar adjustment is applied.

## Market dynamics

Let `S_t` and `B_t` denote the risky and risk-free prices at the start of day `t`. For
independent standard normal shocks `z_t`, their gross daily growth factors are

```math
G^S_t = \frac{S_{t+1}}{S_t}
      = \exp\left[\left(\mu-\frac{\sigma^2}{2}\right)\Delta t
                   +\sigma\sqrt{\Delta t}\,z_t\right],
\qquad
G^B = \frac{B_{t+1}}{B_t} = \exp(r\Delta t).
```

This is the exact GBM transition at daily observation times. Both growth factors are positive.
Here `mu` is the drift of the price process: expected risky gross growth is `exp(mu * dt)`,
whereas expected risky log growth per step is `(mu - sigma**2 / 2) * dt`.
Annual volatility is converted with `sqrt(dt)`; the annual rates enter with `dt`.

Market shocks are independent of the agent's action. There is no market impact, borrowing,
short selling, external cash flow, consumption, or transaction cost in this initial model.

## State, observation, and action

Internally track wealth `W_t`, the current risky fraction `x_t`, and elapsed days `t`.
The observation is the two-element vector

```math
o_t = \left(x_t,\frac{H-t}{H}\right).
```

Both components lie in `[0, 1]`. At reset the observation is `(0, 1)`. At the terminal
observation the second component is zero.

The action `a_t` is a continuous target risky fraction in `[0, 1]`. For the Gymnasium interface,
represent it as a one-element `Box` array. The remaining fraction `1 - a_t` is allocated to the
risk-free asset. An action of `0.6` means a 60% risky target after rebalancing and before that
day's returns.

Wealth is recorded for evaluation and diagnostics. It is omitted from the observation because
the log reward and proportional allocations make the problem invariant to the scale of wealth.
Absolute asset prices are also unnecessary for these transitions. Market parameters are fixed,
so they are not additional observations in this version. The current risky fraction is
retained to describe the portfolio and support the later introduction of transaction costs,
although it does not affect the optimal cost-free rebalance.

## Order of events and accounting

For each day `t = 0, ..., H - 1`:

1. Observe the portfolio before trading and choose target `a_t`.
2. Rebalance at the current prices. Risky and safe holdings become `a_t * W_t` and
   `(1 - a_t) * W_t`. With zero costs, total wealth remains `W_t` at this instant.
3. Draw the day's market shock and apply the growth factors to the respective holdings.
4. Calculate the next wealth, risky fraction, reward, and remaining time.

The resulting transition is

```math
G^W_t = a_t G^S_t + (1-a_t)G^B,
\qquad
W_{t+1} = W_t G^W_t,
\qquad
x_{t+1} = \frac{a_t G^S_t}{G^W_t}.
```

The next observation contains `x_{t+1}`, not the previously chosen target. The agent chooses
its action before observing `z_t` or the day's returns.

### Worked one-day example

Start with wealth `1` and choose `a_t = 0.6`. After rebalancing, risky holdings are `0.6` and
safe holdings are `0.4`. Suppose the realized risky gross daily growth is `1.01`.
With the agreed risk-free rate, safe gross daily growth is `exp(0.02 / 365)`.

| Quantity after returns | Value, rounded |
| ---------------------- | -------------- |
| Risky holdings         | `0.6060000000` |
| Safe holdings          | `0.4000219184` |
| Total wealth           | `1.0060219184` |
| Risky fraction         | `0.6023725616` |
| Log reward             | `0.0060038591` |

After the first day, remaining time is `364 / 365`. The 1% risky daily return is an illustrative
realization, not a fixed simulated return or an annual parameter.

## Reward and episode boundary

The reward is the log wealth ratio

```math
R_t = \log\frac{W_{t+1}}{W_t} = \log G^W_t,
\qquad
\sum_{t=0}^{H-1}R_t = \log\frac{W_H}{W_0}.
```

The objective is `E[sum(R_t)]`. With fixed initial wealth this has the same optimizer as
`E[log(W_H)]`. There is no additional terminal reward. Any later RL configuration must preserve
this undiscounted objective; algorithm-specific choices will be discussed separately.

The one-year horizon is part of the task. The 365th transition sets `terminated=True` and
`truncated=False`. Earlier transitions set both flags to false. A call to `step` after
termination requires a reset. Terminal wealth is the market value of the two holdings after
the final day's returns. At zero costs a final liquidation would have the same value.

## Reset, randomness, and diagnostics

`reset` restores wealth to `1`, risky fraction to `0`, and elapsed days to `0`. Use the
environment's seeded `numpy.random.Generator`, initialized through Gymnasium's reset interface.
Repeating the seed and action sequence must reproduce the same trajectory. Resetting without
a new seed continues the generator's sequence, allowing new episodes rather than repeating
the same year's shocks. Resetting the environment does not reset a future agent's learning.

The planned diagnostic information includes wealth, elapsed days, current risky fraction,
and, after each transition, the action and realized risky, safe, and portfolio growth factors.
These values support accounting tests and evaluation without revealing future returns.

The implementation should reject malformed, non-finite, or out-of-range actions rather than
silently clipping them. Configuration validation requires finite parameters, positive finite
`dt` and initial wealth, a positive integer horizon, nonnegative volatility, and an initial
fraction in `[0, 1]`. Zero volatility may be used for deterministic accounting tests; Merton's
formula requires strictly positive volatility. Unsupported non-finite numerical outcomes
should produce an explicit error instead of an invalid observation or reward.

## Validation against Merton

For strictly positive volatility, the continuous-time unconstrained log-utility fraction is

```math
\pi^* = \frac{\mu-r}{\sigma^2} = 0.5.
```

With the agreed initial parameters this lies inside the allowed action interval. In other
parameter scenarios, the continuous-time reference must be constrained to `[0, 1]`.

Baseline policies will rebalance daily to a constant target and be compared on shared market
trajectories. Report mean terminal log growth and uncertainty in paired policy differences.
GBM transitions are exact, but daily rebalancing differs from continuously maintaining a
fixed fraction. Therefore evaluate the daily optimum numerically and assess any discrepancy
from Merton, rather than requiring exact equality.

Implementation acceptance checks will cover conservation on rebalancing, deterministic
all-cash and all-risky accounting, fraction drift, reward telescoping, reproducibility,
action validation, and exactly 365 transitions. The sprint also requires Gymnasium's
environment checker, pre-commit, and pytest to pass once implementation and tests exist.

## Using the implementation

`PortfolioConfig` and `PortfolioEnv` are available from `tp_final_rl.env`. The default
configuration implements the parameters above. Both Gymnasium spaces use `float64` arrays;
wealth and rewards are calculated with double precision. Nonempty reset options do not
override the configuration. Transaction costs are fixed at zero in this implementation.

For example, run a seeded episode that rebalances to a 50% risky target each day:

```python
import math

import numpy as np

from tp_final_rl.env import PortfolioEnv

env = PortfolioEnv()
observation, info = env.reset(seed=42)
rewards = []
for _ in range(env.config.horizon):
    observation, reward, terminated, truncated, info = env.step(np.array([0.5]))
    rewards.append(reward)
print(info["wealth"], math.fsum(rewards))
env.close()
```

The final observation has zero time remaining and `terminated` is true. Each step's `info`
contains `wealth`, `risky_fraction`, `elapsed_days`, `target_fraction`, `risky_growth`,
`safe_growth`, and `portfolio_growth`. Reset diagnostics contain only the first three fields.
Invalid actions and numerical failures preserve the portfolio and market generator state.

Run `uv run pytest` to verify the accounting, numerical error handling, seed behavior, and
Gymnasium interface contract. These are implementation checks; the policy comparison and
Merton benchmark remain the sprint's next experiment.
