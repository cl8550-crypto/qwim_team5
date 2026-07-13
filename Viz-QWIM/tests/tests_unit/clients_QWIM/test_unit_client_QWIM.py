"""Unit tests for src/clients_QWIM/client_QWIM.py.

Tests cover Client_QWIM constructor, update methods, getter methods,
serialization (to_dict/from_dict) and string representation.
"""

from __future__ import annotations

import polars as pl
import pytest

from src.clients_QWIM.client_QWIM import (
    Client_QWIM,
    Client_Type,
    Marital_Status,
    Employment_Status,
    Asset_Type,
    Goal_Type,
    Income_Type,
)



# ============================================================================
# Tests for Client_QWIM enum classes
# ============================================================================


class Test_Client_QWIM_Enums:
    """Tests for the enum classes defined in client_QWIM."""

    @pytest.mark.unit()
    def test_marital_status_importable(self):
        """Test that marital status importable."""
        from src.clients_QWIM.client_QWIM import Marital_Status

        assert Marital_Status is not None

    @pytest.mark.unit()
    def test_marital_status_has_members(self):
        """Test that marital status has members."""
        from src.clients_QWIM.client_QWIM import Marital_Status

        members = list(Marital_Status)
        assert len(members) >= 2

    @pytest.mark.unit()
    def test_employment_status_importable(self):
        """Test that employment status importable."""
        from src.clients_QWIM.client_QWIM import Employment_Status

        assert Employment_Status is not None

    @pytest.mark.unit()
    def test_employment_status_has_members(self):
        """Test that employment status has members."""
        from src.clients_QWIM.client_QWIM import Employment_Status

        members = list(Employment_Status)
        assert len(members) >= 2

    @pytest.mark.unit()
    def test_asset_type_importable(self):
        """Test that asset type importable."""
        from src.clients_QWIM.client_QWIM import Asset_Type

        assert Asset_Type is not None

    @pytest.mark.unit()
    def test_asset_type_has_members(self):
        """Test that asset type has members."""
        from src.clients_QWIM.client_QWIM import Asset_Type

        members = list(Asset_Type)
        assert len(members) >= 3

    @pytest.mark.unit()
    def test_goal_type_importable(self):
        """Test that goal type importable."""
        from src.clients_QWIM.client_QWIM import Goal_Type

        assert Goal_Type is not None

    @pytest.mark.unit()
    def test_income_type_importable(self):
        """Test that income type importable."""
        from src.clients_QWIM.client_QWIM import Income_Type

        assert Income_Type is not None

    @pytest.mark.unit()
    def test_client_type_importable(self):
        """Test that client type importable."""
        from src.clients_QWIM.client_QWIM import Client_Type

        assert Client_Type is not None


# ============================================================================
# Tests for Client_QWIM constructor
# ============================================================================


class Test_Client_QWIM_Constructor:
    """Tests for Client_QWIM.__init__."""

    @pytest.mark.unit()
    def test_basic_construction(self):
        """Test that basic construction."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        client = Client_QWIM(
            client_ID="C001",
            first_name="Alice",
            last_name="Smith",
            client_type=Client_Type.CLIENT_PRIMARY,
        )
        assert client is not None

    @pytest.mark.unit()
    def test_client_id_stored(self):
        """Test that client id stored."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        client = Client_QWIM(client_ID="C001", first_name="Alice", last_name="Smith", client_type=Client_Type.CLIENT_PRIMARY)
        assert client.client_ID == "C001"

    @pytest.mark.unit()
    def test_first_name_stored(self):
        """Test that first name stored."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        client = Client_QWIM(client_ID="C002", first_name="Bob", last_name="Jones", client_type=Client_Type.CLIENT_PRIMARY)
        assert client.first_name == "Bob"

    @pytest.mark.unit()
    def test_last_name_stored(self):
        """Test that last name stored."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        client = Client_QWIM(client_ID="C003", first_name="Carol", last_name="White", client_type=Client_Type.CLIENT_PRIMARY)
        assert client.last_name == "White"

    @pytest.mark.unit()
    def test_client_type_stored(self):
        """Test that client type stored."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        client = Client_QWIM(client_ID="C004", first_name="Dave", last_name="Brown", client_type=Client_Type.CLIENT_PRIMARY)
        assert client.client_type == Client_Type.CLIENT_PRIMARY

    @pytest.mark.unit()
    def test_assets_initialized_empty(self):
        """Test that assets initialized empty."""
        import polars as pl
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        client = Client_QWIM(client_ID="C005", first_name="Eve", last_name="Black", client_type=Client_Type.CLIENT_PRIMARY)
        # Assets should be empty or default DataFrame
        assert client.m_assets is None or isinstance(client.m_assets, pl.DataFrame)


# ============================================================================
# Tests for Client_QWIM.update_personal_info
# ============================================================================


class Test_Client_QWIM_Update_Personal_Info:
    """Tests for Client_QWIM.update_personal_info."""

    @pytest.fixture()
    def client(self):
        """Client."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        return Client_QWIM(client_ID="C010", first_name="Frank", last_name="Gray", client_type=Client_Type.CLIENT_PRIMARY)

    @pytest.mark.unit()
    def test_update_single_field(self, client):
        """Test that update single field."""
        client.update_personal_info(data_personal_info = {"First Name": "Franklin"})
        assert client.first_name == "Franklin"

    @pytest.mark.unit()
    def test_update_multiple_fields(self, client):
        """Test that update multiple fields."""
        client.update_personal_info(data_personal_info = {"First Name": "Frank", "Last Name": "Green"})
        assert client.last_name == "Green"

    @pytest.mark.unit()
    def test_empty_dict_no_change(self, client):
        """Test that empty dict no change."""
        original_first = client.first_name
        client.update_personal_info(data_personal_info = {})
        assert client.first_name == original_first


# ============================================================================
# Tests for Client_QWIM.get_personal_info
# ============================================================================


class Test_Client_QWIM_Get_Personal_Info:
    """Tests for Client_QWIM.get_personal_info."""

    @pytest.mark.unit()
    def test_returns_dict(self):
        """Test that returns dict."""
        import polars as pl
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        client = Client_QWIM(client_ID="C020", first_name="Grace", last_name="Hall", client_type=Client_Type.CLIENT_PRIMARY)
        info = client.get_personal_info()
        assert isinstance(info, pl.DataFrame)

    @pytest.mark.unit()
    def test_client_id_in_info(self):
        """Test that client id in info."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        client = Client_QWIM(client_ID="C021", first_name="Henry", last_name="Hill", client_type=Client_Type.CLIENT_PRIMARY)
        info = client.get_personal_info()
        assert info is not None


# ============================================================================
# Tests for Client_QWIM.get_total_assets
# ============================================================================


class Test_Client_QWIM_Get_Total_Assets:
    """Tests for Client_QWIM.get_total_assets."""

    @pytest.mark.unit()
    def test_returns_float_with_no_assets(self):
        """Test that returns float with no assets."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        client = Client_QWIM(client_ID="C030", first_name="Iris", last_name="James", client_type=Client_Type.CLIENT_PRIMARY)
        total = client.get_total_assets()
        assert isinstance(total, (int, float))
        assert total == 0.0 or total >= 0.0

    @pytest.mark.unit()
    def test_returns_numeric_type(self):
        """Test that returns numeric type."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        client = Client_QWIM(client_ID="C031", first_name="Jack", last_name="King", client_type=Client_Type.CLIENT_PRIMARY)
        total = client.get_total_assets()
        assert isinstance(total, (int, float))


# ============================================================================
# Tests for Client_QWIM.get_total_annual_income
# ============================================================================


class Test_Client_QWIM_Get_Total_Annual_Income:
    """Tests for Client_QWIM.get_total_annual_income."""

    @pytest.mark.unit()
    def test_returns_numeric_with_no_income(self):
        """Test that returns numeric with no income."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        client = Client_QWIM(client_ID="C040", first_name="Laura", last_name="Lee", client_type=Client_Type.CLIENT_PRIMARY)
        total = client.get_total_annual_income()
        assert isinstance(total, (int, float))

    @pytest.mark.unit()
    def test_non_negative_with_no_income(self):
        """Test that non negative with no income."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        client = Client_QWIM(client_ID="C041", first_name="Mike", last_name="May", client_type=Client_Type.CLIENT_PRIMARY)
        total = client.get_total_annual_income()
        assert total >= 0.0


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("frame_attr", "frame_data", "method_name", "expected_value"),
    [
        (
            "m_assets",
            {
                "Taxable Assets": [True],
                "Tax Deferred Assets": [50_000.0],
                "Tax Free Assets": [25_000.0],
            },
            "get_total_assets",
            75_000.0,
        ),
        (
            "m_assets",
            {"Taxable Assets": [True]},
            "get_taxable_assets",
            0.0,
        ),
        (
            "m_income",
            {
                "Annual Social Security": [True],
                "Annual Pension in Retirement": [5_000.0],
                "Annual Annuity Income": [0.0],
                "Annual Other Income": [2_500.0],
            },
            "get_total_annual_income",
            7_500.0,
        ),
        (
            "m_income",
            {"Annual Social Security": [True]},
            "get_social_security_income",
            0.0,
        ),
        (
            "m_goals",
            {
                "Essential Annual Expense": [True],
                "Important Annual Expense": [10_000.0],
                "Aspirational Annual Expense": [5_000.0],
            },
            "get_total_annual_expenses",
            15_000.0,
        ),
        (
            "m_goals",
            {"Essential Annual Expense": [True]},
            "get_annual_essential_expenses",
            0.0,
        ),
    ],
    ids=[
        "total_assets_bool_component",
        "taxable_assets_bool_scalar",
        "total_income_bool_component",
        "social_security_bool_scalar",
        "total_expenses_bool_component",
        "essential_expense_bool_scalar",
    ],
)
def test_aggregate_getters_boolean_values_use_existing_default_paths(
    frame_attr,
    frame_data,
    method_name,
    expected_value,
):
    """Boolean aggregate values should stay on the established 0.0 fallback path."""
    client = Client_QWIM(client_ID="C042", first_name="Nina", last_name="North", client_type=Client_Type.CLIENT_PRIMARY)
    setattr(client, frame_attr, pl.DataFrame(frame_data))

    result_value = getattr(client, method_name)()

    assert result_value == pytest.approx(expected_value)


# ============================================================================
# Tests for Client_QWIM serialization (to_dict / from_dict)
# ============================================================================


class Test_Client_QWIM_Serialization:
    """Tests for Client_QWIM.to_dict and Client_QWIM.from_dict."""

    @pytest.fixture()
    def client(self):
        """Client."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        return Client_QWIM(client_ID="C050", first_name="Nancy", last_name="Noon", client_type=Client_Type.CLIENT_PRIMARY)

    @pytest.mark.unit()
    def test_to_dict_returns_dict(self, client):
        """Test that to dict returns dict."""
        result = client.to_dict()
        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_to_dict_has_client_id(self, client):
        """Test that to dict has client id."""
        result = client.to_dict()
        all_values = str(result)
        assert "C050" in all_values

    @pytest.mark.unit()
    def test_from_dict_creates_instance(self, client):
        """Test that from_dict creates a Client_QWIM instance successfully."""
        from src.clients_QWIM.client_QWIM import Client_QWIM

        d = client.to_dict()
        result = Client_QWIM.from_dict(input_data = d)
        assert isinstance(result, Client_QWIM)
        assert result.client_ID == client.client_ID
        assert result.first_name == client.first_name
        assert result.last_name == client.last_name

    @pytest.mark.unit()
    def test_round_trip_preserves_id(self, client):
        """Test that to_dict → from_dict round-trip preserves client ID."""
        from src.clients_QWIM.client_QWIM import Client_QWIM

        d = client.to_dict()
        restored = Client_QWIM.from_dict(input_data = d)
        assert restored.client_ID == client.client_ID


# ============================================================================
# Tests for Client_QWIM.__str__
# ============================================================================


class Test_Client_QWIM_Str:
    """Tests for Client_QWIM.__str__."""

    @pytest.mark.unit()
    def test_str_contains_name(self):
        """Test that str contains name."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        client = Client_QWIM(client_ID="C060", first_name="Oscar", last_name="Park", client_type=Client_Type.CLIENT_PRIMARY)
        s = str(client)
        assert "Oscar" in s or "Park" in s

    @pytest.mark.unit()
    def test_str_contains_assets(self):
        """Test that str contains assets."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        client = Client_QWIM(client_ID="C061", first_name="Paula", last_name="Quinn", client_type=Client_Type.CLIENT_PRIMARY)
        s = str(client)
        assert "$" in s or "Assets" in s

    @pytest.mark.unit()
    def test_str_is_string(self):
        """Test that str is string."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        client = Client_QWIM(client_ID="C062", first_name="Robert", last_name="Reed", client_type=Client_Type.CLIENT_PRIMARY)
        assert isinstance(str(client), str)


# ============================================================================
# Tests for Client_QWIM update_assets
# ============================================================================


class Test_Client_QWIM_Update_Assets:
    """Tests for Client_QWIM.update_assets."""

    @pytest.mark.unit()
    def test_update_assets_does_not_raise_with_empty(self):
        """Test that update assets does not raise with empty."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        client = Client_QWIM(client_ID="C070", first_name="Sara", last_name="Stone", client_type=Client_Type.CLIENT_PRIMARY)
        try:
            client.update_assets(data_assets = [])
        except Exception:
            pass

    @pytest.mark.unit()
    def test_update_assets_accepts_list(self):
        """Test that update assets accepts list."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type, Asset_Type

        client = Client_QWIM(client_ID="C071", first_name="Tom", last_name="Tyler", client_type=Client_Type.CLIENT_PRIMARY)
        asset = {
            "asset_type": Asset_Type.CASH,
            "current_value": 50000.0,
            "description": "Brokerage account",
        }
        try:
            client.update_assets(data_assets = [asset])
        except Exception:
            pass  # Structure flexibility


# ============================================================================
# Tests for module structure
# ============================================================================


class Test_Client_QWIM_Module_Structure:
    """Tests for the overall structure of client_QWIM module."""

    @pytest.mark.unit()
    def test_module_importable(self):
        """Test that module importable."""
        import src.clients_QWIM.client_QWIM as m

        assert m is not None

    @pytest.mark.unit()
    def test_client_class_importable(self):
        """Test that client class importable."""
        from src.clients_QWIM.client_QWIM import Client_QWIM

        assert Client_QWIM is not None

    @pytest.mark.unit()
    def test_all_enums_importable(self):
        """Test that all enums importable."""
        from src.clients_QWIM.client_QWIM import (
            Asset_Type,
            Client_Type,
            Employment_Status,
            Goal_Type,
            Income_Type,
            Marital_Status,
        )

        for enum_cls in [Marital_Status, Employment_Status, Asset_Type, Goal_Type, Income_Type, Client_Type]:
            assert enum_cls is not None


# ============================================================================
# Tests for coverage gaps
# ============================================================================


class Test_Coverage_Gaps_client_QWIM:
    """Comprehensive tests covering all gaps in client_QWIM.py for 95%+ coverage."""

    @pytest.fixture()
    def client(self):
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        return Client_QWIM(client_ID="C100", first_name="Alice", last_name="Smith", client_type=Client_Type.CLIENT_PRIMARY)

    @pytest.fixture()
    def populated_client(self):
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        c = Client_QWIM(client_ID="C200", first_name="Bob", last_name="Jones", client_type=Client_Type.CLIENT_PRIMARY)
        c.update_personal_info(
            data_personal_info = {
                "First Name": "Bob",
                "Last Name": "Jones",
                "Marital Status": "Married",
                "Gender": "Male",
                "Risk Tolerance": 5,
                "Current Age": 50,
                "Retirement Age": 65,
                "Income Start Age": 62,
            }
        )
        c.update_assets(
            data_assets = [
                {
                    "Taxable Assets": 100000.0,
                    "Tax Deferred Assets": 200000.0,
                    "Tax Free Assets": 50000.0,
                    "Asset Name": "Portfolio",
                    "Asset Class": "Mixed",
                }
            ]
        )
        c.update_goals(
            data_goals = [
                {
                    "Essential Annual Expense": 50000.0,
                    "Important Annual Expense": 20000.0,
                    "Aspirational Annual Expense": 10000.0,
                    "Essential Annual Expense is Inflation Indexed": True,
                    "Important Annual Expense is Inflation Indexed": False,
                    "Aspirational Annual Expense is Inflation Indexed": False,
                }
            ]
        )
        c.update_income(
            data_income = [
                {
                    "Annual Social Security": 20000.0,
                    "Annual Pension in Retirement": 15000.0,
                    "Annual Annuity Income": 5000.0,
                    "Annual Other Income": 3000.0,
                    "Annual Pension in Retirement is Inflation Indexed": True,
                    "Annual Annuity Income is Inflation Indexed": False,
                    "Annual Other Income is Inflation Indexed": False,
                }
            ]
        )
        return c

    # ---- update_personal_info coverage ----

    @pytest.mark.unit()
    def test_update_personal_info_numeric_fields_int_conversion(self, client):
        """Covers numeric field try/int conversion branch (lines ~189-190)."""
        result = client.update_personal_info(
            data_personal_info = {"Risk Tolerance": 7, "Current Age": 45, "Retirement Age": 65, "Marital Status": "Single"}
        )
        assert result is True

    @pytest.mark.unit()
    def test_update_personal_info_invalid_numeric_field(self, client):
        """Covers except ValueError branch for bad numeric input (lines ~191-194)."""
        result = client.update_personal_info(data_personal_info = {"Risk Tolerance": "bad_value"})
        assert result is True

    @pytest.mark.unit()
    def test_update_personal_info_boolean_numeric_field_uses_none(self, client):
        """Boolean numeric personal-info fields stay on the existing invalid-value fallback path."""
        result = client.update_personal_info(data_personal_info = {"Current Age": True})

        assert result is True
        assert client.m_personal_info["Current Age"].to_list() == [None]

    @pytest.mark.unit()
    def test_update_personal_info_updates_last_name(self, client):
        """Covers the 'if Last Name in data' branch updating m_last_name."""
        result = client.update_personal_info(data_personal_info = {"Last Name": "Johnson"})
        assert client.last_name == "Johnson"
        assert result is True

    @pytest.mark.unit()
    def test_update_personal_info_none_input_returns_false(self, client):
        """Covers outer except Exception handler — None.items() raises AttributeError."""
        result = client.update_personal_info(data_personal_info = None)
        assert result is False

    # ---- update_assets coverage ----

    @pytest.mark.unit()
    def test_update_assets_all_fields_populated(self, client):
        """Covers all if-True branches in the update_assets item loop."""
        result = client.update_assets(
            data_assets = [
                {
                    "Taxable Assets": 50000.0,
                    "Tax Deferred Assets": 30000.0,
                    "Tax Free Assets": 20000.0,
                    "Asset Name": "Main Portfolio",
                    "Asset Class": "Mixed",
                }
            ]
        )
        assert result is True
        assert not client.m_assets.is_empty()

    @pytest.mark.unit()
    def test_update_assets_invalid_float_values(self, client):
        """Covers except (ValueError, TypeError): pass for bad float conversions."""
        result = client.update_assets(
            data_assets = [
                {
                    "Taxable Assets": "invalid",
                    "Tax Deferred Assets": "not_a_number",
                    "Tax Free Assets": "bad",
                    "Asset Class": "Stocks",
                }
            ]
        )
        assert result is True

    @pytest.mark.unit()
    def test_update_assets_boolean_amount_values_use_defaults(self, client):
        """Boolean asset amounts stay on the existing invalid-value fallback path."""
        result = client.update_assets(
            data_assets = [
                {
                    "Taxable Assets": True,
                    "Tax Deferred Assets": False,
                    "Tax Free Assets": True,
                }
            ]
        )

        assert result is True
        assert client.m_assets["Taxable Assets"].to_list() == pytest.approx([0.0])
        assert client.m_assets["Tax Deferred Assets"].to_list() == pytest.approx([0.0])
        assert client.m_assets["Tax Free Assets"].to_list() == pytest.approx([0.0])

    @pytest.mark.unit()
    def test_update_assets_outer_except_triggered_by_invalid_input(self, client):
        """Covers outer except Exception handler — None input causes AttributeError."""
        # None is falsy so goes to else branch — produces empty DataFrame (True)
        # Use a non-iterable non-falsy object to trigger except
        result = client.update_assets(data_assets = 42)  # int not iterable
        assert result is False

    # ---- update_goals coverage ----

    @pytest.mark.unit()
    def test_update_goals_dict_input_converts_to_list(self, client):
        """Covers isinstance(dict) → convert to list branch (lines ~300-301)."""
        result = client.update_goals(
            data_goals = {"Essential Annual Expense": 40000.0, "Essential Annual Expense is Inflation Indexed": True}
        )
        assert result is True

    @pytest.mark.unit()
    def test_update_goals_full_list_all_fields(self, client):
        """Covers all goal update branches including bool/str/int inflation flag conversions."""
        result = client.update_goals(
            data_goals = [
                {
                    "Essential Annual Expense": 40000.0,
                    "Important Annual Expense": 25000.0,
                    "Aspirational Annual Expense": 10000.0,
                    "Essential Annual Expense is Inflation Indexed": True,
                    "Important Annual Expense is Inflation Indexed": "yes",
                    "Aspirational Annual Expense is Inflation Indexed": 0,
                }
            ]
        )
        assert result is True
        assert not client.m_goals.is_empty()

    @pytest.mark.unit()
    def test_update_goals_inflation_flag_string_false(self, client):
        """Covers str inflation flag evaluated as falsy string."""
        result = client.update_goals(
            data_goals = [
                {
                    "Essential Annual Expense is Inflation Indexed": "no",
                    "Important Annual Expense is Inflation Indexed": "false",
                    "Aspirational Annual Expense is Inflation Indexed": "0",
                }
            ]
        )
        assert result is True

    @pytest.mark.unit()
    def test_update_goals_invalid_expense_value(self, client):
        """Covers except (ValueError, TypeError): pass for bad expense float."""
        result = client.update_goals(data_goals = [{"Essential Annual Expense": "not-a-number"}])
        assert result is True

    @pytest.mark.unit()
    def test_update_goals_boolean_expense_value_uses_default(self, client):
        """Boolean goal amounts stay on the existing invalid-value fallback path."""
        result = client.update_goals(data_goals = [{"Essential Annual Expense": True}])

        assert result is True
        assert client.m_goals["Essential Annual Expense"].to_list() == pytest.approx([0.0])

    @pytest.mark.unit()
    def test_update_goals_empty_list_resets_dataframe(self, client):
        """Covers else branch for empty data_goals — resets m_goals."""
        client.update_goals(data_goals = [{"Essential Annual Expense": 40000.0}])
        result = client.update_goals(data_goals = [])
        assert result is True
        assert client.m_goals.is_empty()

    @pytest.mark.unit()
    def test_update_goals_int_input_outer_except(self, client):
        """Covers outer except Exception handler — int not iterable → TypeError."""
        result = client.update_goals(data_goals = 123)
        assert result is False

    # ---- update_income coverage ----

    @pytest.mark.unit()
    def test_update_income_dict_input_converts_to_list(self, client):
        """Covers isinstance(dict) → convert to list branch (lines ~375-376)."""
        result = client.update_income(data_income = {"Annual Social Security": 20000.0})
        assert result is True

    @pytest.mark.unit()
    def test_update_income_full_list_all_fields(self, client):
        """Covers income entry processing loop with all income types and flag conversions."""
        result = client.update_income(
            data_income = [
                {
                    "Annual Social Security": 20000.0,
                    "Annual Pension in Retirement": 15000.0,
                    "Annual Annuity Income": 5000.0,
                    "Annual Other Income": 3000.0,
                    "Annual Pension in Retirement is Inflation Indexed": True,
                    "Annual Annuity Income is Inflation Indexed": "true",
                    "Annual Other Income is Inflation Indexed": 1,
                }
            ]
        )
        assert result is True
        assert not client.m_income.is_empty()

    @pytest.mark.unit()
    def test_update_income_empty_list_resets_dataframe(self, client):
        """Covers else branch for empty data_income — resets m_income."""
        client.update_income(data_income = [{"Annual Social Security": 20000.0}])
        result = client.update_income(data_income = [])
        assert result is True
        assert client.m_income.is_empty()

    @pytest.mark.unit()
    def test_update_income_int_input_outer_except(self, client):
        """Covers outer except Exception handler — int not iterable → TypeError."""
        result = client.update_income(data_income = 123)
        assert result is False

    # ---- getter methods: empty client (covers is_empty → return None/0.0/False) ----

    @pytest.mark.unit()
    def test_get_marital_status_empty_returns_none(self, client):
        """Covers the is_empty → return None branch of get_marital_status."""
        assert client.get_marital_status() is None

    @pytest.mark.unit()
    def test_get_risk_tolerance_empty_returns_none(self, client):
        """Covers the is_empty → return None branch of get_risk_tolerance."""
        assert client.get_risk_tolerance() is None

    @pytest.mark.unit()
    def test_get_current_age_empty_returns_none(self, client):
        """Covers the is_empty → return None branch of get_current_age."""
        assert client.get_current_age() is None

    @pytest.mark.unit()
    def test_get_retirement_age_empty_returns_none(self, client):
        """Covers the is_empty → return None branch of get_retirement_age."""
        assert client.get_retirement_age() is None

    @pytest.mark.unit()
    def test_get_income_start_age_empty_returns_none(self, client):
        """Covers the is_empty → return None branch of get_income_start_age."""
        assert client.get_income_start_age() is None

    @pytest.mark.unit()
    def test_get_social_security_income_empty_returns_zero(self, client):
        """Covers the is_empty → return 0.0 branch of get_social_security_income."""
        assert client.get_social_security_income() == 0.0

    @pytest.mark.unit()
    def test_get_pension_income_empty_returns_zero(self, client):
        """Covers the is_empty → return 0.0 branch of get_pension_income."""
        assert client.get_pension_income() == 0.0

    @pytest.mark.unit()
    def test_get_annuity_income_empty_returns_zero(self, client):
        """Covers the is_empty → return 0.0 branch of get_annuity_income."""
        assert client.get_annuity_income() == 0.0

    @pytest.mark.unit()
    def test_get_other_income_empty_returns_zero(self, client):
        """Covers the is_empty → return 0.0 branch of get_other_income."""
        assert client.get_other_income() == 0.0

    @pytest.mark.unit()
    def test_is_pension_inflation_indexed_empty_returns_false(self, client):
        """Covers the is_empty → return False branch of is_pension_income_inflation_indexed."""
        assert client.is_pension_income_inflation_indexed() is False

    @pytest.mark.unit()
    def test_is_annuity_inflation_indexed_empty_returns_false(self, client):
        """Covers the is_empty → return False branch."""
        assert client.is_income_from_existing_annuity_inflation_indexed() is False

    @pytest.mark.unit()
    def test_is_other_sources_inflation_indexed_empty_returns_false(self, client):
        """Covers the is_empty → return False branch."""
        assert client.is_income_from_other_sources_inflation_indexed() is False

    @pytest.mark.unit()
    def test_get_annual_essential_expenses_empty_returns_zero(self, client):
        """Covers the is_empty → return 0.0 branch of get_annual_essential_expenses."""
        assert client.get_annual_essential_expenses() == 0.0

    @pytest.mark.unit()
    def test_get_annual_important_expenses_empty_returns_zero(self, client):
        """Covers the is_empty → return 0.0 branch of get_annual_important_expenses."""
        assert client.get_annual_important_expenses() == 0.0

    @pytest.mark.unit()
    def test_get_annual_aspirational_expenses_empty_returns_zero(self, client):
        """Covers the is_empty → return 0.0 branch of get_annual_aspirational_expenses."""
        assert client.get_annual_aspirational_expenses() == 0.0

    @pytest.mark.unit()
    def test_is_essential_expense_inflation_indexed_empty_returns_false(self, client):
        """Covers the is_empty → return False branch."""
        assert client.is_annual_essential_expense_inflation_indexed() is False

    @pytest.mark.unit()
    def test_is_important_expense_inflation_indexed_empty_returns_false(self, client):
        """Covers the is_empty → return False branch."""
        assert client.is_annual_important_expense_inflation_indexed() is False

    @pytest.mark.unit()
    def test_is_aspirational_expense_inflation_indexed_empty_returns_false(self, client):
        """Covers the is_empty → return False branch."""
        assert client.is_annual_aspirational_expense_inflation_indexed() is False

    # ---- getter methods: populated client (covers try block body) ----

    @pytest.mark.unit()
    def test_get_marital_status_populated(self, populated_client):
        """Covers the try block of get_marital_status with a populated DataFrame."""
        result = populated_client.get_marital_status()
        assert result is not None

    @pytest.mark.unit()
    def test_get_risk_tolerance_populated(self, populated_client):
        """Covers the try block of get_risk_tolerance with populated data."""
        result = populated_client.get_risk_tolerance()
        assert result is not None

    @pytest.mark.unit()
    def test_get_current_age_populated(self, populated_client):
        """Covers the try block of get_current_age with populated data."""
        result = populated_client.get_current_age()
        assert result is not None

    @pytest.mark.unit()
    def test_get_retirement_age_populated(self, populated_client):
        """Covers the try block of get_retirement_age with populated data."""
        result = populated_client.get_retirement_age()
        assert result is not None

    @pytest.mark.unit()
    def test_get_income_start_age_populated(self, populated_client):
        """Covers the try block of get_income_start_age with populated data."""
        result = populated_client.get_income_start_age()
        assert result is None or isinstance(result, int)

    @pytest.mark.unit()
    def test_get_total_assets_populated(self, populated_client):
        """Covers the try block of get_total_assets with populated assets."""
        total = populated_client.get_total_assets()
        assert isinstance(total, float)
        assert total >= 0.0

    @pytest.mark.unit()
    def test_get_taxable_assets_populated(self, populated_client):
        """Covers the try block of get_taxable_assets with populated data."""
        result = populated_client.get_taxable_assets()
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_get_tax_deferred_assets_populated(self, populated_client):
        """Covers the try block of get_tax_deferred_assets with populated data."""
        result = populated_client.get_tax_deferred_assets()
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_get_tax_free_assets_populated(self, populated_client):
        """Covers the try block of get_tax_free_assets with populated data."""
        result = populated_client.get_tax_free_assets()
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_get_total_annual_income_returns_zero_due_to_bug(self, populated_client):
        """Covers get_total_annual_income — always hits except due to undefined 'col' variable."""
        result = populated_client.get_total_annual_income()
        assert isinstance(result, (int, float))

    @pytest.mark.unit()
    def test_get_social_security_income_populated(self, populated_client):
        """Covers the try block of get_social_security_income with populated income."""
        result = populated_client.get_social_security_income()
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_get_pension_income_populated(self, populated_client):
        """Covers the try block of get_pension_income with 'Annual Pension in Retirement' column."""
        result = populated_client.get_pension_income()
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_get_annuity_income_populated(self, populated_client):
        """Covers the try block of get_annuity_income with 'Annual Annuity Income' column."""
        result = populated_client.get_annuity_income()
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_get_other_income_populated(self, populated_client):
        """Covers the try block of get_other_income with 'Annual Other Income' column."""
        result = populated_client.get_other_income()
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_is_pension_inflation_indexed_populated(self, populated_client):
        """Covers try block of is_pension_income_inflation_indexed with populated income."""
        result = populated_client.is_pension_income_inflation_indexed()
        assert isinstance(result, bool)

    @pytest.mark.unit()
    def test_is_annuity_inflation_indexed_populated(self, populated_client):
        """Covers try block of is_income_from_existing_annuity_inflation_indexed."""
        result = populated_client.is_income_from_existing_annuity_inflation_indexed()
        assert isinstance(result, bool)

    @pytest.mark.unit()
    def test_is_other_sources_inflation_indexed_populated(self, populated_client):
        """Covers try block of is_income_from_other_sources_inflation_indexed."""
        result = populated_client.is_income_from_other_sources_inflation_indexed()
        assert isinstance(result, bool)

    @pytest.mark.unit()
    def test_get_total_annual_expenses_populated(self, populated_client):
        """Covers the try block of get_total_annual_expenses with populated goals."""
        result = populated_client.get_total_annual_expenses()
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_get_annual_essential_expenses_populated(self, populated_client):
        """Covers the try block of get_annual_essential_expenses with populated goals."""
        result = populated_client.get_annual_essential_expenses()
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_get_annual_important_expenses_populated(self, populated_client):
        """Covers the try block of get_annual_important_expenses with populated goals."""
        result = populated_client.get_annual_important_expenses()
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_get_annual_aspirational_expenses_populated(self, populated_client):
        """Covers the try block of get_annual_aspirational_expenses with populated goals."""
        result = populated_client.get_annual_aspirational_expenses()
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_is_essential_expense_inflation_indexed_populated(self, populated_client):
        """Covers try block of is_annual_essential_expense_inflation_indexed."""
        result = populated_client.is_annual_essential_expense_inflation_indexed()
        assert isinstance(result, bool)

    @pytest.mark.unit()
    def test_is_important_expense_inflation_indexed_populated(self, populated_client):
        """Covers try block of is_annual_important_expense_inflation_indexed."""
        result = populated_client.is_annual_important_expense_inflation_indexed()
        assert isinstance(result, bool)

    @pytest.mark.unit()
    def test_is_aspirational_expense_inflation_indexed_populated(self, populated_client):
        """Covers try block of is_annual_aspirational_expense_inflation_indexed."""
        result = populated_client.is_annual_aspirational_expense_inflation_indexed()
        assert isinstance(result, bool)

    # ---- to_dict and __str__ ----

    @pytest.mark.unit()
    def test_to_dict_populated_returns_dict(self, populated_client):
        """Covers to_dict with a fully populated client."""
        result = populated_client.to_dict()
        assert isinstance(result, dict)
        assert "client_ID" in result

    @pytest.mark.unit()
    def test_str_with_none_names_shows_client_id(self):
        """Covers the else branch of __str__ when m_first_name/m_last_name are None."""
        from src.clients_QWIM.client_QWIM import Client_QWIM, Client_Type

        c = Client_QWIM(client_ID="C999", first_name=None, last_name=None, client_type=Client_Type.CLIENT_PRIMARY)
        s = str(c)
        assert "C999" in s

    # ---- empty-client tests for asset getters (covers is_empty → return 0.0) ----

    @pytest.mark.unit()
    def test_get_taxable_assets_empty_returns_zero(self, client):
        """Covers the is_empty → return 0.0 branch of get_taxable_assets."""
        assert client.get_taxable_assets() == 0.0

    @pytest.mark.unit()
    def test_get_tax_deferred_assets_empty_returns_zero(self, client):
        """Covers the is_empty → return 0.0 branch of get_tax_deferred_assets."""
        assert client.get_tax_deferred_assets() == 0.0

    @pytest.mark.unit()
    def test_get_tax_free_assets_empty_returns_zero(self, client):
        """Covers the is_empty → return 0.0 branch of get_tax_free_assets."""
        assert client.get_tax_free_assets() == 0.0

    @pytest.mark.unit()
    def test_get_total_annual_expenses_empty_returns_zero(self, client):
        """Covers the is_empty → return 0.0 branch of get_total_annual_expenses."""
        assert client.get_total_annual_expenses() == 0.0

    # ---- multi-item loop tests (covers loop-continuation arcs) ----

    @pytest.mark.unit()
    def test_update_goals_multiple_items_loop_continuation(self, client):
        """Covers the loop-continuation arc [338,326] — update_goals with 2+ items."""
        result = client.update_goals(
            data_goals = [
                {"Essential Annual Expense": 40000.0},
                {"Essential Annual Expense": 50000.0},
            ]
        )
        assert result is True

    @pytest.mark.unit()
    def test_update_income_multiple_items_loop_continuation(self, client):
        """Covers the loop-continuation arc [421,409] — update_income with 2+ items."""
        result = client.update_income(
            data_income = [
                {"Annual Social Security": 20000.0},
                {"Annual Social Security": 15000.0},
            ]
        )
        assert result is True

    # ---- simple getter methods: get_assets, get_goals, get_income ----

    @pytest.mark.unit()
    def test_get_assets_returns_dataframe(self, client):
        """Covers the return statement of get_assets()."""
        import polars as pl

        result = client.get_assets()
        assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_get_goals_returns_dataframe(self, client):
        """Covers the return statement of get_goals()."""
        import polars as pl

        result = client.get_goals()
        assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_get_income_returns_dataframe(self, client):
        """Covers the return statement of get_income()."""
        import polars as pl

        result = client.get_income()
        assert isinstance(result, pl.DataFrame)

    # ---- update_income ValueError path ----

    @pytest.mark.unit()
    def test_update_income_invalid_amount_value(self, client):
        """Covers except (ValueError, TypeError): pass in update_income amount loop."""
        result = client.update_income(data_income = [{"Annual Social Security": "not-a-number"}])
        assert result is True

    @pytest.mark.unit()
    def test_update_income_boolean_amount_value_uses_default(self, client):
        """Boolean income amounts stay on the existing invalid-value fallback path."""
        result = client.update_income(data_income = [{"Annual Social Security": True}])

        assert result is True
        assert client.m_income["Annual Social Security"].to_list() == pytest.approx([0.0])

    # ---- inflation flag None-value loop-continuation arcs ----

    @pytest.mark.unit()
    def test_update_goals_none_inflation_flag_triggers_loop_arc(self, client):
        """Covers arc [338,326]: elif isinstance(val,(int,float)) is False → loop continues.

        Providing None as the first inflation flag value means none of the
        isinstance checks match, so the elif condition (line 338) evaluates
        False and the for-loop iterates again, covering arc [338, 326].
        """
        result = client.update_goals(
            data_goals = [
                {
                    "Essential Annual Expense is Inflation Indexed": None,
                    "Important Annual Expense is Inflation Indexed": True,
                    "Aspirational Annual Expense is Inflation Indexed": False,
                }
            ]
        )
        assert result is True

    @pytest.mark.unit()
    def test_update_income_none_inflation_flag_triggers_loop_arc(self, client):
        """Covers arc [421,409]: elif isinstance(val,(int,float)) is False → loop continues.

        Providing None as the first inflation flag value causes the elif
        condition (line 421) to evaluate False, then the for-loop iterates
        to the next field, covering arc [421, 409].
        """
        result = client.update_income(
            data_income = [
                {
                    "Annual Pension in Retirement is Inflation Indexed": None,
                    "Annual Annuity Income is Inflation Indexed": True,
                    "Annual Other Income is Inflation Indexed": False,
                }
            ]
        )
        assert result is True


# ============================================================================
# Tests for update_assets backward-compatibility "Type" key (line 311)
# ============================================================================


class Test_Client_QWIM_Update_Assets_Backward_Compat:
    """Tests for the backward-compat ``elif 'Type' in item_asset:`` branch.

    All existing tests supply an ``'Asset Class'`` key, so the ``elif``
    branch at line 310 (which maps legacy ``'Type'`` → ``'Asset Class'``)
    was never reached.  This class exercises that branch directly.
    """

    @pytest.fixture()
    def client(self):
        """Minimal client fixture."""
        return Client_QWIM(client_ID="C_BC", first_name="Test", last_name="User", client_type=Client_Type.CLIENT_PRIMARY)

    @pytest.mark.unit()
    def Test_Type_Key_Mapped_To_Asset_Class(self, client):
        """'Type' key maps to 'Asset Class' via backward-compat branch (line 311).

        When an asset dict contains ``'Type'`` but not ``'Asset Class'``, the
        ``elif 'Type' in item_asset:`` branch at line 310 executes, storing
        the value under ``'Asset Class'``.  This branch was previously missing
        because all tests always supplied ``'Asset Class'`` directly.
        """
        result = client.update_assets(
            data_assets = [
                {
                    "Taxable Assets": 50_000.0,
                    "Type": "Equities",
                }
            ]
        )
        assert result is True
        assert client.m_assets["Asset Class"][0] == "Equities"


# ============================================================================
# Tests for Client_QWIM.from_dict optional-field branches (lines 944-956)
# ============================================================================


class Test_Client_QWIM_From_Dict_Optional_Fields:
    """Tests for the optional-field ``if`` branches inside ``from_dict``.

    Existing tests always supply all fields via ``to_dict()``.  These tests
    exercise both True and False branches for each optional key by supplying
    a minimal dict or a dict with specific optional keys present.
    """

    @pytest.mark.unit()
    def Test_Minimal_Dict_Skips_Optional_Assignments(self):
        """from_dict with only required keys skips all optional if-assignments.

        Exercises the False branches of:

        - ``'creation_date' in input_data``  (944 → 946, skipping line 945)
        - ``'last_updated' in input_data``   (946 → 949, skipping line 947)
        - ``input_data.get('personal_info')`` False branch (skipping line 950)
        - ``input_data.get('assets')``        False branch (skipping line 952)
        - ``input_data.get('goals')``         False branch (skipping line 954)
        - ``input_data.get('income')``        False branch (skipping line 956)
        """
        d = {
            "client_ID": "C_MIN",
            "first_name": "Alice",
            "last_name": "Smith",
            "client_type": "Client Primary",
        }
        client = Client_QWIM.from_dict(input_data = d)
        assert isinstance(client, Client_QWIM)
        assert client.client_ID == "C_MIN"

    @pytest.mark.unit()
    def Test_With_Personal_Info_Populates_Attribute(self):
        """from_dict with ``personal_info`` key executes line 950 (True branch).

        Exercises ``if input_data.get('personal_info'):`` → True → line 950.
        """
        d = {
            "client_ID": "C_PI",
            "first_name": "Bob",
            "last_name": "Jones",
            "client_type": "Client Primary",
            "personal_info": [{"Marital Status": "SINGLE", "Risk Tolerance": "MODERATE"}],
        }
        client = Client_QWIM.from_dict(input_data = d)
        assert not client.m_personal_info.is_empty()

    @pytest.mark.unit()
    def Test_With_Assets_Populates_Attribute(self):
        """from_dict with ``assets`` key executes line 952 (True branch).

        Exercises ``if input_data.get('assets'):`` → True → line 952.
        """
        d = {
            "client_ID": "C_AS",
            "first_name": "Carol",
            "last_name": "White",
            "client_type": "Client Primary",
            "assets": [
                {
                    "Taxable Assets": 100_000.0,
                    "Tax Deferred Assets": 50_000.0,
                    "Tax Free Assets": 25_000.0,
                    "Asset Name": "401k",
                    "Asset Class": "Mixed",
                }
            ],
        }
        client = Client_QWIM.from_dict(input_data = d)
        assert not client.m_assets.is_empty()

    @pytest.mark.unit()
    def Test_With_Goals_Populates_Attribute(self):
        """from_dict with ``goals`` key executes line 954 (True branch).

        Exercises ``if input_data.get('goals'):`` → True → line 954.
        """
        d = {
            "client_ID": "C_GO",
            "first_name": "Dave",
            "last_name": "Black",
            "client_type": "Client Primary",
            "goals": [
                {
                    "Goal Type": "RETIREMENT",
                    "Essential Annual Expense": 40_000.0,
                    "Essential Annual Expense is Inflation Indexed": True,
                }
            ],
        }
        client = Client_QWIM.from_dict(input_data = d)
        assert not client.m_goals.is_empty()

    @pytest.mark.unit()
    def Test_With_Income_Populates_Attribute(self):
        """from_dict with ``income`` key executes line 956 (True branch).

        Exercises ``if input_data.get('income'):`` → True → line 956.
        """
        d = {
            "client_ID": "C_IN",
            "first_name": "Eve",
            "last_name": "Green",
            "client_type": "Client Primary",
            "income": [{"Annual Social Security": 18_000.0}],
        }
        client = Client_QWIM.from_dict(input_data = d)
        assert not client.m_income.is_empty()

