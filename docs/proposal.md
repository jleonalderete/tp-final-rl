# Proposal: scope beyond the minimum objectives

**Status:** draft for the two of us to discuss, written on 2026-11-14. Nothing here is decided.

## The idea

Take the Merton project past the assignment's two objectives and turn it into a small allocation
system:

1. Several risky assets, cryptocurrencies included, first in simulation with known parameters.
2. Run the learned policy against a live market, on a testnet or with a small amount of real
   money, so that sim-to-real transfer and the production work become part of the project.
3. Possibly add optimal order execution, the course's other finance topic.

## Constraints

- Submission is on Nov 29, 15 days after this draft, and the report is capped at 10 pages.
- Grading is on problem formulation and diagnosis, not on scope.
- The minimum objectives must be met without exception: recover the Merton fraction π\*, learn
  the no-trade band, and show how its width changes with the cost level.

## Proposed scope

| Stage            | What                                                                             | Validated against                                          |
| ---------------- | -------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Core (mandatory) | One GBM asset, log utility; proportional costs; band width against cost          | Merton's fraction; the cube-root law below                 |
| A                | N risky assets without costs, with crypto-like parameters                        | The closed form Σ⁻¹(μ − r·1)                               |
| B                | Policy conditioned on (μ, σ, cost); evaluation on historical BTC and ETH returns | Merton with estimated parameters; loss from the error in μ̂ |
| C (optional)     | Paper trading with the frozen policy                                             | Realized cost against modeled cost                         |

Left out: a bot trading real money, and optimal execution.

## Why this cut

- **The core is harder than it looks.** The objective is nearly flat around the optimum. With
  σ = 20% a year and daily steps, being 5 points off π\* = 0.5 costs about 2·10⁻⁷ of reward per
  step, against per-step noise of about 6·10⁻³. This drives the environment design (parameters,
  time step, variance reduction) and is the likely source of the diagnostic case.
- **The band has a quantitative prediction.** For log utility and a small round-trip spread ε,
  the half-width of the band, measured in risky fraction, is

  ```math
  \left( \tfrac{3}{4} (\pi^*)^2 (1 - \pi^*)^2 \varepsilon \right)^{1/3}
  ```

  (Gerhold et al.). With π\* = 0.5 that is ±4.5 points for ε = 0.2% and ±9.8 points for ε = 2%:
  ten times the cost gives 2.15 times the width. Objective 3 becomes "slope 1/3 on a log-log
  plot". The formula assumes continuous time and an infinite horizon, and our environment is
  discrete and finite, so the deviations are diagnostic material too.

- **Several assets are cheap without costs and expensive with them.** Without costs there is a
  closed form, Σ⁻¹(μ − r·1). With costs the no-trade region is N-dimensional and has no closed
  form (with two risky assets it is close to a quadrilateral, per Muthuraman and Kumar), and
  validating it takes a numerical benchmark. Stage A stops at the frictionless case.
- **With real parameters the problem is estimation, not RL.** The standard error of μ̂ is σ/√T,
  with T in years, whatever the sampling frequency. Assuming σ ≈ 55% for BTC (a ballpark we
  still have to measure) and four years of data, that is ±27% a year, so π\* is uncertain by
  about ±0.9.
- **"Transfer" needs reframing.** An agent trained with fixed (μ, σ, cost) learns one constant
  and one band, so there is nothing to transfer. To deploy it, the policy has to take the
  parameters as observations and train with domain randomization. The sim-to-real gap is then
  measured offline on historical returns (fat tails, volatility clustering), where there is
  enough data to say something.
- **A week of live trading says nothing about performance.** Under the same σ assumption,
  holding a fraction 20 points off the optimum costs about 1 basis point per week, against a
  weekly volatility of roughly 7.6%. A live run only works as an engineering demo: realized cost
  against modeled cost, and drift from the target fraction.
- **Paper trading covers the frictions that matter here.** Alpaca's paper trading fills orders
  against the real-time best quote, so prices and spread are real. It does not model market
  impact, latency slippage, or queue position, which matter at high frequency or with size, not
  for small hourly or daily rebalances: one second of latency on BTC is about 1 basis point of
  zero-mean noise, against a 25 basis point taker fee. Whether paper accounts charge the crypto
  fee is not documented. If they don't, we apply the published schedule ourselves.
- **Venue.** Alpaca paper gives crypto (24/7) and US stocks through one API, and a paper-only
  account needs just an email. Binance Spot Demo Mode is the alternative if we stay crypto-only:
  its prices and order books are similar to the live exchange. The classic Binance Spot Testnet
  doesn't work for this, because its prices are independent of the live market and it resets
  monthly.
- **Optimal execution is a separate project.** And at test-portfolio sizes our orders don't move
  the price, so there would be nothing to optimize. It goes into future work.
- **No reference implementation.** A quick search found no paper where an RL agent recovers the
  Merton no-trade band.

## Open decisions

1. **The cut itself.** Do we drop the real-money bot and optimal execution?
2. **Real-money calibration.** Instead of a real-money bot, about ten small real orders to
   measure the realized fee and slippage against the model. Only worth it if one of us already
   has a funded exchange account with API access. Minimum order sizes can distort a
   small-capital run, and we haven't checked them.
3. **Venue for stage C.** Alpaca paper or Binance Spot Demo Mode.
4. **Objective 3.** One policy conditioned on the cost, or one run per cost level. The first
   gives stage B the generalization it needs but is harder to train. The second is simpler and
   more robust.
5. **Timing of stage C.** To have a week of data in the report the bot has to start around
   Nov 21. It can keep running until the oral defense, around Dec 10.

## References

- Gerhold, Guasoni, Muhle-Karbe, Schachermayer,
  [Transaction Costs, Trading Volume, and the Liquidity Premium](https://arxiv.org/abs/1108.1167).
- Muhle-Karbe, Reppen, Soner,
  [A Primer on Portfolio Choice with Small Transaction Costs](https://arxiv.org/abs/1612.01302).
- Muthuraman, Kumar,
  [Multidimensional Portfolio Optimization with Proportional Transaction Costs](https://econpapers.repec.org/RePEc:bla:mathfi:v:16:y:2006:i:2:p:301-335).
- Cai, Judd, Xu,
  [Numerical Solution of Dynamic Portfolio Optimization with Transaction Costs](https://arxiv.org/abs/2003.01809).
- Alpaca: [Paper Trading](https://docs.alpaca.markets/docs/paper-trading),
  [Crypto Spot Trading Fees](https://docs.alpaca.markets/docs/crypto-fees).
- Binance:
  [Demo Mode for Spot Trading](https://developers.binance.com/docs/binance-spot-api-docs/demo-mode/general-info),
  [Spot Testnet](https://developers.binance.com/docs/binance-spot-api-docs/testnet/general-info).
