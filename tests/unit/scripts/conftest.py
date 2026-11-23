"""Activate the M1 guard only for the explicitly scoped integration contracts."""

import pytest

from tests.unit.scripts.m1_isolation import m1_isolation as m1_isolation

_M1_CONTRACT_MODULES = {
    "test_data_quality_contract",
    "test_effective_configuration_contract",
    "test_run_bt_run_agent_manifest",
    "test_strategy_profile_cash_contract",
    "test_strategy_profile_turnover_contract",
    "test_strategy_profile_regime_exposure_contract",
    "test_run_regime_cash_testmatrix",
    "test_run_profile_compare_v1",
    "test_run_max_turnover_cap_testmatrix",
}


@pytest.fixture(autouse=True)
def _guard_m1_contracts(request):
    if request.path.stem in _M1_CONTRACT_MODULES:
        request.getfixturevalue("m1_isolation")
