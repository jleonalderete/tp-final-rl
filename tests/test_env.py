import math
from dataclasses import replace
from typing import Any

import numpy as np
import pytest
from gymnasium.error import ResetNeeded
from gymnasium.utils.env_checker import check_env

from tp_final_rl.env import PortfolioConfig, PortfolioEnv


def test_gymnasium_contract() -> None:
    check_env(PortfolioEnv(), skip_render_check=True)


def test_default_reset_and_custom_initial_state() -> None:
    env = PortfolioEnv()
    obs, info = env.reset(seed=42)
    np.testing.assert_array_equal(obs, [0, 1])
    assert info == {"wealth": 1.0, "risky_fraction": 0.0, "elapsed_days": 0}
    assert env.observation_space.contains(obs)
    assert env.action_space.contains(np.array([0.5]))

    config = PortfolioConfig(initial_wealth=100, initial_risky_fraction=0.7)
    obs, info = PortfolioEnv(config).reset(seed=42)
    np.testing.assert_array_equal(obs, [0.7, 1])
    assert info["wealth"] == 100


@pytest.mark.parametrize("initial_fraction", [0.0, 0.4, 1.0])
def test_rebalancing_preserves_wealth_with_zero_returns(initial_fraction: float) -> None:
    env = PortfolioEnv(
        PortfolioConfig(
            mu=0, r=0, sigma=0, initial_wealth=37, initial_risky_fraction=initial_fraction
        )
    )
    env.reset(seed=1)
    for target in (0.0, 0.2, 0.9, 1.0, 0.3):
        obs, reward, _, _, info = env.step(np.array([target]))
        assert info["wealth"] == pytest.approx(37)
        assert obs[0] == pytest.approx(target)
        assert reward == pytest.approx(0)


def test_all_cash_compounds_at_risk_free_rate_for_one_year() -> None:
    env = PortfolioEnv(PortfolioConfig(initial_wealth=100))
    _, info = env.reset(seed=5)
    rewards = []
    for _ in range(365):
        obs, reward, _, _, info = env.step(np.array([0.0]))
        rewards.append(reward)
        assert obs[0] == 0
    assert info["wealth"] == pytest.approx(100 * math.exp(0.02))
    assert math.fsum(rewards) == pytest.approx(0.02)


def test_all_risky_matches_seeded_gbm_path() -> None:
    config = PortfolioConfig(initial_wealth=7)
    env = PortfolioEnv(config)
    _, info = env.reset(seed=19)
    shocks = np.random.default_rng(19).standard_normal(config.horizon)
    expected_log_growth = (
        config.mu - config.sigma**2 / 2
    ) * config.dt * config.horizon + config.sigma * math.sqrt(config.dt) * float(shocks.sum())
    rewards = []
    for _ in range(config.horizon):
        obs, reward, _, _, info = env.step(np.array([1.0]))
        rewards.append(reward)
        assert obs[0] == 1
    assert math.fsum(rewards) == pytest.approx(expected_log_growth)
    assert info["wealth"] == pytest.approx(7 * math.exp(expected_log_growth))


def test_worked_example_and_fraction_drift() -> None:
    # Zero volatility and this drift produce exactly 1% risky daily growth.
    config = PortfolioConfig(mu=365 * math.log(1.01), sigma=0)
    env = PortfolioEnv(config)
    env.reset(seed=1)
    obs, reward, terminated, truncated, info = env.step(np.array([0.6]))
    assert info["wealth"] == pytest.approx(1.006021918408718)
    assert obs[0] == pytest.approx(0.6023725615824997)
    assert obs[1] == pytest.approx(364 / 365)
    assert reward == pytest.approx(0.006003859122821639)
    assert not terminated
    assert not truncated
    assert info["risky_growth"] == pytest.approx(1.01)
    assert info["safe_growth"] == pytest.approx(math.exp(0.02 / 365))
    assert info["portfolio_growth"] == pytest.approx(info["wealth"])
    assert info["target_fraction"] == 0.6
    assert info["elapsed_days"] == 1


def test_mixed_portfolio_matches_independently_computed_transition() -> None:
    config = PortfolioConfig(initial_wealth=17, initial_risky_fraction=0.9)
    env = PortfolioEnv(config)
    env.reset(seed=24)
    shock = float(np.random.default_rng(24).standard_normal())
    risky = math.exp((0.04 - 0.20**2 / 2) / 365 + 0.20 / math.sqrt(365) * shock)
    safe = math.exp(0.02 / 365)
    growth = 0.35 * risky + 0.65 * safe
    obs, reward, _, _, info = env.step(np.array([0.35]))
    assert info["wealth"] == pytest.approx(17 * growth)
    assert obs[0] == pytest.approx(0.35 * risky / growth)
    assert reward == pytest.approx(math.log(growth))


def test_reward_telescopes_and_observations_remain_valid() -> None:
    config = PortfolioConfig(initial_wealth=200)
    env = PortfolioEnv(config)
    _, info = env.reset(seed=32)
    rewards = []
    for day in range(config.horizon):
        target = (day % 11) / 10
        obs, reward, _, _, info = env.step(np.array([target]))
        rewards.append(reward)
        assert env.observation_space.contains(obs)
        assert math.isfinite(info["wealth"])
        assert info["wealth"] > 0
    assert math.fsum(rewards) == pytest.approx(math.log(info["wealth"] / 200))


def test_wealth_scale_and_initial_fraction_do_not_change_cost_free_decisions() -> None:
    first = PortfolioEnv()
    second = PortfolioEnv(PortfolioConfig(initial_wealth=123, initial_risky_fraction=0.8))
    first.reset(seed=7)
    second.reset(seed=7)
    for target in (0.4, 0.1, 1.0, 0.0):
        obs_a, reward_a, _, _, info_a = first.step(np.array([target]))
        obs_b, reward_b, _, _, info_b = second.step(np.array([target]))
        np.testing.assert_array_equal(obs_a, obs_b)
        assert reward_a == reward_b
        assert info_b["wealth"] == pytest.approx(123 * info_a["wealth"])


def test_horizon_requires_reset_and_reset_restores_portfolio() -> None:
    env = PortfolioEnv()
    with pytest.raises(ResetNeeded):
        env.step(np.array([0.5]))
    env.reset(seed=2)
    for day in range(1, 366):
        obs, _, terminated, truncated, info = env.step(np.array([0.5]))
        assert terminated == (day == 365)
        assert not truncated
        assert obs[1] == pytest.approx((365 - day) / 365)
        assert info["elapsed_days"] == day
    with pytest.raises(ResetNeeded):
        env.step(np.array([0.5]))
    obs, info = env.reset()
    np.testing.assert_array_equal(obs, [0, 1])
    assert info["wealth"] == 1
    assert info["elapsed_days"] == 0


def test_reset_without_seed_continues_market_sequence_and_seed_replays() -> None:
    env = PortfolioEnv(PortfolioConfig(horizon=1))
    generator = np.random.default_rng(12)
    expected_shocks = generator.standard_normal(2)
    env.reset(seed=12)
    first = env.step(np.array([0.5]))
    env.reset()
    second = env.step(np.array([0.5]))
    for transition, shock in zip((first, second), expected_shocks, strict=True):
        expected = math.exp((0.04 - 0.20**2 / 2) / 365 + 0.20 / math.sqrt(365) * shock)
        assert transition[4]["risky_growth"] == pytest.approx(expected)
    env.reset(seed=12)
    replay = env.step(np.array([0.5]))
    np.testing.assert_array_equal(replay[0], first[0])
    assert replay[1:] == first[1:]


@pytest.mark.parametrize(
    "action",
    [
        np.array([-0.01]),
        np.array([1.01]),
        np.array([np.nan]),
        np.array([np.inf]),
        np.array([-np.inf]),
        np.array([]),
        np.array([0.2, 0.3]),
        np.array([[0.5]]),
        np.array(0.5),
        np.array([True]),
        np.array([0.5j]),
        np.array(["0.5"]),
        np.array([0.5], dtype=object),
        0.5,
        [0.5],
    ],
)
def test_invalid_actions_preserve_portfolio_and_market_sequence(action: Any) -> None:
    env = PortfolioEnv()
    reference = PortfolioEnv()
    env.reset(seed=8)
    reference.reset(seed=8)
    with pytest.raises(ValueError, match="action"):
        env.step(action)
    actual = env.step(np.array([0.4]))
    expected = reference.step(np.array([0.4]))
    np.testing.assert_array_equal(actual[0], expected[0])
    assert actual[1:] == expected[1:]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("mu", math.nan),
        ("mu", math.inf),
        ("r", -math.inf),
        ("sigma", math.nan),
        ("sigma", -0.1),
        ("dt", 0),
        ("dt", -1),
        ("dt", math.inf),
        ("initial_wealth", 0),
        ("initial_wealth", -1),
        ("initial_wealth", math.nan),
        ("initial_risky_fraction", -0.01),
        ("initial_risky_fraction", 1.01),
        ("initial_risky_fraction", math.inf),
        ("horizon", 0),
        ("horizon", -1),
        ("horizon", 1.5),
        ("horizon", True),
    ],
)
def test_invalid_configuration(field: str, value: Any) -> None:
    with pytest.raises(ValueError, match=field):
        replace(PortfolioConfig(), **{field: value})


@pytest.mark.parametrize(
    "config",
    [
        PortfolioConfig(mu=1e308, dt=1),
        PortfolioConfig(mu=-1e308, dt=1),
        PortfolioConfig(r=1e308, dt=1),
        PortfolioConfig(sigma=1e308),
        PortfolioConfig(mu=1, sigma=0, dt=1, initial_wealth=1e308),
        PortfolioConfig(mu=-2, sigma=0, dt=1, initial_wealth=5e-324),
    ],
)
def test_numerical_failures_preserve_state(config: PortfolioConfig) -> None:
    env = PortfolioEnv(config)
    obs, info = env.reset(seed=11)
    state = env.np_random.bit_generator.state
    with pytest.raises(FloatingPointError, match="numerical limits"):
        env.step(np.array([1.0]))
    assert env.np_random.bit_generator.state == state
    assert env._wealth == config.initial_wealth
    assert env._risky_fraction == config.initial_risky_fraction
    assert env._elapsed_days == 0
    assert not env._needs_reset
    # Reset can still recover the portfolio after a failed transition.
    new_obs, new_info = env.reset(seed=11)
    np.testing.assert_array_equal(new_obs, obs)
    assert new_info == info
