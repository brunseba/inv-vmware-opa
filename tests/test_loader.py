"""Unit tests for loader module."""

import pytest
from datetime import datetime
from src.loader import (
    normalize_column_name,
    parse_date,
    parse_bool,
    parse_int,
    parse_float,
)
import pandas as pd


def test_normalize_column_name():
    """Test column name normalization."""
    assert normalize_column_name("VM Name") == "vm_name"
    assert normalize_column_name("Network #1") == "network_1"
    assert normalize_column_name("CPU(s)") == "cpus"
    assert normalize_column_name("Power State") == "power_state"


def test_parse_date():
    """Test date parsing."""
    # Valid datetime
    dt = datetime(2024, 1, 15)
    assert parse_date(dt) == dt
    
    # None/NaN
    assert parse_date(None) is None
    assert parse_date(pd.NaT) is None
    
    # String date
    result = parse_date("2024-01-15")
    assert result is not None
    assert result.year == 2024


def test_parse_bool():
    """Test boolean parsing."""
    # True values
    assert parse_bool(True) is True
    assert parse_bool("yes") is True
    assert parse_bool("Yes") is True
    assert parse_bool("true") is True
    assert parse_bool("1") is True
    
    # False values
    assert parse_bool(False) is False
    assert parse_bool("no") is False
    assert parse_bool("No") is False
    assert parse_bool("false") is False
    assert parse_bool("0") is False
    
    # None/invalid
    assert parse_bool(None) is None
    assert parse_bool(pd.NA) is None
    assert parse_bool("invalid") is None


def test_parse_int():
    """Test integer parsing."""
    assert parse_int(42) == 42
    assert parse_int("42") == 42
    assert parse_int(42.0) == 42
    assert parse_int(None) is None
    assert parse_int(pd.NA) is None
    assert parse_int("not a number") is None


def test_parse_float():
    """Test float parsing."""
    assert parse_float(42.5) == 42.5
    assert parse_float("42.5") == 42.5
    assert parse_float(42) == 42.0
    assert parse_float(None) is None
    assert parse_float(pd.NA) is None
    assert parse_float("not a number") is None
