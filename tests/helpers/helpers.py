import pytest

def approx(value: float):
    return pytest.approx(value, abs=1e-9)