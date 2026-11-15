"""Daily, cost-free portfolio allocation with exact geometric Brownian returns."""

import math
from dataclasses import dataclass
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from gymnasium.error import ResetNeeded
from numpy.typing import NDArray

type FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class PortfolioConfig:
    """Fixed market and episode parameters, with rates expressed in annual units.

    Attributes:
        mu: Risky asset's annual GBM price drift.
        r: Annual continuously compounded risk-free rate.
        sigma: Annualized risky volatility; zero supports deterministic diagnostics.
        dt: Years represented by one step.
        horizon: Number of decisions per episode.
        initial_wealth: Positive initial wealth in arbitrary currency units.
        initial_risky_fraction: Fraction held in the risky asset at reset.
    """

    mu: float = 0.04
    r: float = 0.02
    sigma: float = 0.20
    dt: float = 1 / 365
    horizon: int = 365
    initial_wealth: float = 1.0
    initial_risky_fraction: float = 0.0

    def __post_init__(self) -> None:
        """Reject non-finite values and unsupported parameter domains."""
        for name in ("mu", "r", "sigma", "dt", "initial_wealth", "initial_risky_fraction"):
            if not math.isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be finite")
        if self.sigma < 0:
            raise ValueError("sigma must be nonnegative")
        if self.dt <= 0:
            raise ValueError("dt must be positive")
        if self.initial_wealth <= 0:
            raise ValueError("initial_wealth must be positive")
        if not 0 <= self.initial_risky_fraction <= 1:
            raise ValueError("initial_risky_fraction must be in [0, 1]")
        if isinstance(self.horizon, bool) or not isinstance(self.horizon, int) or self.horizon <= 0:
            raise ValueError("horizon must be a positive integer")


class PortfolioEnv(gym.Env[FloatArray, FloatArray]):
    """Allocate wealth between a GBM asset and a risk-free asset without costs.

    Actions are one-element arrays specifying a target risky fraction in [0, 1].
    Observations contain the post-return risky fraction and normalized remaining time.
    Each step rebalances before generating returns and rewards log wealth growth.
    The finite horizon ends with termination, without an extra terminal reward.

    Args:
        config: Fixed market and episode settings; defaults to daily, one-year episodes.
    """

    def __init__(self, config: PortfolioConfig | None = None) -> None:
        self.metadata = {"render_modes": []}
        self.config = config if config is not None else PortfolioConfig()
        self.action_space = spaces.Box(0.0, 1.0, shape=(1,), dtype=np.float64)
        self.observation_space = spaces.Box(0.0, 1.0, shape=(2,), dtype=np.float64)
        self._wealth = self.config.initial_wealth
        self._risky_fraction = self.config.initial_risky_fraction
        self._elapsed_days = 0
        self._needs_reset = True

    def reset(
        self, *, seed: int | None = None, options: dict[str, Any] | None = None
    ) -> tuple[FloatArray, dict[str, Any]]:
        """Restore the initial portfolio, optionally reseeding the market generator.

        Args:
            seed: Market seed; None continues the existing generator's sequence.
            options: Reserved Gymnasium reset options; no portfolio overrides are supported.

        Returns:
            Initial observation and portfolio diagnostics.
        """
        super().reset(seed=seed)
        self._wealth = self.config.initial_wealth
        self._risky_fraction = self.config.initial_risky_fraction
        self._elapsed_days = 0
        self._needs_reset = False
        return self._get_obs(), self._get_info()

    def step(self, action: FloatArray) -> tuple[FloatArray, float, bool, bool, dict[str, Any]]:
        """Rebalance to the target, simulate returns, and mark the portfolio to market.

        Args:
            action: Finite real numeric array with shape (1,) and value in [0, 1].

        Returns:
            Observation, log growth reward, termination, truncation, and diagnostics.

        Raises:
            ResetNeeded: The environment has not been reset or the episode has ended.
            ValueError: The action is malformed or outside the supported interval.
            FloatingPointError: The transition cannot be represented with finite positive
                growth and wealth. Portfolio and generator state are preserved on failure.
        """
        if self._needs_reset:
            raise ResetNeeded("Call reset before stepping or after episode termination")
        if (
            not isinstance(action, np.ndarray)
            or action.shape != (1,)
            or action.dtype.kind not in "fiu"
        ):
            raise ValueError("action must be a real numeric array with shape (1,)")
        target = float(action[0])
        if not math.isfinite(target) or not 0 <= target <= 1:
            raise ValueError("action must be finite and in [0, 1]")

        config = self.config
        generator_state = self.np_random.bit_generator.state
        try:
            shock = float(self.np_random.standard_normal())
            risky_growth = math.exp(
                (config.mu - config.sigma**2 / 2) * config.dt
                + config.sigma * math.sqrt(config.dt) * shock
            )
            safe_growth = math.exp(config.r * config.dt)
            portfolio_growth = target * risky_growth + (1 - target) * safe_growth
            wealth = self._wealth * portfolio_growth
            if not all(
                math.isfinite(value) and value > 0
                for value in (risky_growth, safe_growth, portfolio_growth, wealth)
            ):
                raise FloatingPointError("growth factors and wealth must be finite and positive")
            risky_fraction = target * risky_growth / portfolio_growth
            reward = math.log(portfolio_growth)
        except (OverflowError, FloatingPointError) as error:
            self.np_random.bit_generator.state = generator_state
            raise FloatingPointError("Portfolio transition exceeds numerical limits") from error

        self._wealth = wealth
        self._risky_fraction = risky_fraction
        self._elapsed_days += 1
        terminated = self._elapsed_days == config.horizon
        self._needs_reset = terminated
        info = self._get_info()
        info.update(
            target_fraction=target,
            risky_growth=risky_growth,
            safe_growth=safe_growth,
            portfolio_growth=portfolio_growth,
        )
        return self._get_obs(), reward, terminated, False, info

    def _get_obs(self) -> FloatArray:
        return np.array(
            [
                self._risky_fraction,
                (self.config.horizon - self._elapsed_days) / self.config.horizon,
            ],
            dtype=np.float64,
        )

    def _get_info(self) -> dict[str, Any]:
        return {
            "wealth": self._wealth,
            "risky_fraction": self._risky_fraction,
            "elapsed_days": self._elapsed_days,
        }
