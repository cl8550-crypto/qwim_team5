import pytest
import polars as pl

from src.dashboard.shiny_tab_covariance.subtab_covariance_overview import (
    automatic_backtest_config,
    rank_covariance_estimators,
)


@pytest.mark.parametrize(
    ("horizon", "expected_training_window"),
    [
        ("Short term (1-3 years)", 126),
        ("Medium term (4-10 years)", 252),
        ("Long term (10+ years)", 504),
    ],
)
def test_horizon_selects_training_window(
    horizon: str,
    expected_training_window: int,
) -> None:
    config = automatic_backtest_config(
        investment_horizon=horizon,
        review_frequency="Monthly",
    )

    assert config.train_window == expected_training_window


@pytest.mark.parametrize(
    ("frequency", "expected_window"),
    [
        ("Monthly", 21),
        ("Quarterly", 63),
        ("Annually", 126),
    ],
)
def test_review_frequency_selects_test_and_step_windows(
    frequency: str,
    expected_window: int,
) -> None:
    config = automatic_backtest_config(
        investment_horizon="Medium term (4-10 years)",
        review_frequency=frequency,
    )

    assert config.test_window == expected_window
    assert config.step_size == expected_window


def test_unknown_horizon_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported investment horizon"):
        automatic_backtest_config(
            investment_horizon="Unknown",
            review_frequency="Monthly",
        )


def test_unknown_review_frequency_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported review frequency"):
        automatic_backtest_config(
            investment_horizon="Medium term (4-10 years)",
            review_frequency="Weekly",
        )


def _sample_summary() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "estimator": [
                "Accuracy Winner",
                "Balanced Winner",
                "Other Estimator",
                "Stability Winner",
            ],
            "number_of_windows": [20, 20, 20, 20],
            "average_relative_frobenius_loss": [
                0.70,
                0.80,
                0.90,
                1.10,
            ],
            "average_condition_number": [
                500.0,
                100.0,
                200.0,
                50.0,
            ],
        }
    )


def test_accuracy_priority_selects_lowest_forecast_loss() -> None:
    ranked = rank_covariance_estimators(
        summary=_sample_summary(),
        portfolio_priority="Accuracy",
    )

    assert ranked["estimator"][0] == "Accuracy Winner"


def test_stability_priority_selects_lowest_condition_number() -> None:
    ranked = rank_covariance_estimators(
        summary=_sample_summary(),
        portfolio_priority="Stability",
    )

    assert ranked["estimator"][0] == "Stability Winner"


def test_balanced_priority_combines_both_ranks() -> None:
    ranked = rank_covariance_estimators(
        summary=_sample_summary(),
        portfolio_priority="Balanced",
    )

    assert ranked["estimator"][0] == "Balanced Winner"


def test_unknown_portfolio_priority_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported portfolio priority",
    ):
        rank_covariance_estimators(
            summary=_sample_summary(),
            portfolio_priority="Unknown",
        )
