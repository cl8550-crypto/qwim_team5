"""Hypothesis property-based tests for Client_QWIM.

Property tests verify structural invariants of the ``Client_QWIM`` class:

- Constructor stores client_ID, first_name, last_name, client_type correctly.
- Constructed client has empty DataFrames for personal_info, assets, goals, income.
- update_personal_info() returns True and updates m_first_name / m_last_name.
- Client enums (Client_Type, Goal_Type, Income_Type, etc.) are exhaustive.

Author: QWIM Team
Version: 1.0.0
"""

from __future__ import annotations

import pytest
from hypothesis import given, HealthCheck, settings
from hypothesis import strategies as st

from src.clients_QWIM.client_QWIM import (
    Client_QWIM,
    Client_Type,
    Goal_Type,
    Income_Type,
)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_strategy_nonempty_str = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    min_size=1,
    max_size=24,
)

_strategy_client_type = st.sampled_from(Client_Type)


# ---------------------------------------------------------------------------
# Construction invariants
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Client_QWIM_Construction:
    """Property tests for ``Client_QWIM.__init__``."""

    @pytest.mark.unit()
    @given(
        client_id=_strategy_nonempty_str,
        first_name=_strategy_nonempty_str,
        last_name=_strategy_nonempty_str,
        client_type=_strategy_client_type,
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_constructor_stores_id_and_names(
        self,
        client_id: str,
        first_name: str,
        last_name: str,
        client_type: Client_Type,
    ) -> None:
        """Constructor stores client_ID, first_name, last_name correctly."""
        client = Client_QWIM(
            client_ID=client_id,
            first_name=first_name,
            last_name=last_name,
            client_type=client_type,
        )
        assert client.client_ID == client_id
        assert client.first_name == first_name
        assert client.last_name == last_name

    @pytest.mark.unit()
    @given(
        client_id=_strategy_nonempty_str,
        first_name=_strategy_nonempty_str,
        last_name=_strategy_nonempty_str,
        client_type=_strategy_client_type,
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_constructor_stores_client_type(
        self,
        client_id: str,
        first_name: str,
        last_name: str,
        client_type: Client_Type,
    ) -> None:
        """Constructor stores client_type correctly."""
        client = Client_QWIM(
            client_ID=client_id,
            first_name=first_name,
            last_name=last_name,
            client_type=client_type,
        )
        assert client.client_type == client_type

    @pytest.mark.unit()
    @given(
        client_id=_strategy_nonempty_str,
        first_name=_strategy_nonempty_str,
        last_name=_strategy_nonempty_str,
        client_type=_strategy_client_type,
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_initial_dataframes_are_empty(
        self,
        client_id: str,
        first_name: str,
        last_name: str,
        client_type: Client_Type,
    ) -> None:
        """Personal info, assets, goals, and income DataFrames start empty."""
        client = Client_QWIM(
            client_ID=client_id,
            first_name=first_name,
            last_name=last_name,
            client_type=client_type,
        )
        assert len(client.m_personal_info) == 0
        assert len(client.m_assets) == 0
        assert len(client.m_goals) == 0
        assert len(client.m_income) == 0


# ---------------------------------------------------------------------------
# Enum exhaustiveness
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Client_QWIM_Enums:
    """Property tests confirming enum round-trips work for all members."""

    @pytest.mark.unit()
    @given(client_type=st.sampled_from(Client_Type))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_client_type_value_roundtrip(self, client_type: Client_Type) -> None:
        """Client_Type members have non-empty string values."""
        assert isinstance(client_type.value, str)
        assert len(client_type.value) > 0

    @pytest.mark.unit()
    @given(goal_type=st.sampled_from(Goal_Type))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_goal_type_value_roundtrip(self, goal_type: Goal_Type) -> None:
        """Goal_Type members have non-empty string values."""
        assert isinstance(goal_type.value, str)
        assert len(goal_type.value) > 0

    @pytest.mark.unit()
    @given(income_type=st.sampled_from(Income_Type))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_income_type_value_roundtrip(self, income_type: Income_Type) -> None:
        """Income_Type members have non-empty string values."""
        assert isinstance(income_type.value, str)
        assert len(income_type.value) > 0


# ---------------------------------------------------------------------------
# update_personal_info: name propagation
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Client_QWIM_Update_Personal_Info:
    """Property tests for ``Client_QWIM.update_personal_info``."""

    @pytest.mark.unit()
    @given(
        client_id=_strategy_nonempty_str,
        first_name_init=_strategy_nonempty_str,
        last_name_init=_strategy_nonempty_str,
        first_name_new=_strategy_nonempty_str,
        last_name_new=_strategy_nonempty_str,
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_update_personal_info_returns_true(
        self,
        client_id: str,
        first_name_init: str,
        last_name_init: str,
        first_name_new: str,
        last_name_new: str,
    ) -> None:
        """update_personal_info with valid data returns True."""
        client = Client_QWIM(
            client_ID=client_id,
            first_name=first_name_init,
            last_name=last_name_init,
            client_type=Client_Type.CLIENT_PRIMARY,
        )
        result = client.update_personal_info(
            data_personal_info = {
                "First Name": first_name_new,
                "Last Name": last_name_new,
            }
        )
        assert result is True

    @pytest.mark.unit()
    @given(
        client_id=_strategy_nonempty_str,
        first_name_init=_strategy_nonempty_str,
        last_name_init=_strategy_nonempty_str,
        first_name_new=_strategy_nonempty_str,
        last_name_new=_strategy_nonempty_str,
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_update_personal_info_updates_names(
        self,
        client_id: str,
        first_name_init: str,
        last_name_init: str,
        first_name_new: str,
        last_name_new: str,
    ) -> None:
        """update_personal_info updates m_first_name and m_last_name."""
        client = Client_QWIM(
            client_ID=client_id,
            first_name=first_name_init,
            last_name=last_name_init,
            client_type=Client_Type.CLIENT_PRIMARY,
        )
        client.update_personal_info(
            data_personal_info = {
                "First Name": first_name_new,
                "Last Name": last_name_new,
            }
        )
        assert client.first_name == first_name_new
        assert client.last_name == last_name_new
