from stonks_overwatch.utils.domain.constants import ProductType, Sector

import pytest


def test_product_type_from_str():
    for t in ProductType:
        assert ProductType.from_str(t.value) == t

    assert ProductType.from_str("XXX") == ProductType.UNKNOWN


def test_sector_from_str():
    for t in Sector:
        if t == Sector.UNKNOWN:
            continue
        assert Sector.from_str(t.value) == t
        assert t.to_logo() is not None

    assert Sector.from_str(None) == Sector.UNKNOWN
    assert Sector.UNKNOWN.to_logo() is not None


def test_sector_invalid():
    with pytest.raises(ValueError):
        Sector.from_str("INVALID_TYPE")
