"""Integration tests for generate_data utility workflows."""

from __future__ import annotations

from pathlib import Path

import pytest


class Class_Test_Integration_Generate_Data:
    """Integration tests for file-producing generate_data entry points."""

    @pytest.mark.integration()
    def Test_Main_Writes_Csv_To_Resolved_Project_Root(self, tmp_path: Path, monkeypatch) -> None:
        """main() writes its CSV output beneath the resolved temporary project root."""
        import src.utils.data_utils.generate_data as module

        fake_file = tmp_path / "a" / "b" / "generate_data.py"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.touch()
        monkeypatch.setattr(module, "__file__", str(fake_file))

        module.main()

        output_file = tmp_path / "inputs" / "raw" / "data_timeseries.csv"
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    @pytest.mark.integration()
    def Test_Generate_Scenarios_Writes_Xlsx_And_Returns_All_Sheets(
        self,
        tmp_path: Path,
        monkeypatch,
    ) -> None:
        """Scenario generation writes its workbook and returns the public sheet mapping."""
        import src.utils.data_utils.generate_data as module

        fake_file = tmp_path / "a" / "b" / "c" / "generate_data.py"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.touch()
        monkeypatch.setattr(module, "__file__", str(fake_file))

        result = module.generate_scenarios_daily_returns_CMA_Tier_0(
            start_date="2024-01-01",
            end_date="2024-03-31",
            num_scenarios=5,
            random_seed=42,
        )

        output_file = tmp_path / "inputs" / "raw" / "returns_CMA_Tier_0.xlsx"
        assert output_file.exists()
        assert output_file.stat().st_size > 0
        assert set(result) == {
            "Expected Returns",
            "Volatilities",
            "Correlations",
            "Scenarios",
        }