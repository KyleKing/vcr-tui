# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Pytest configuration."""

import sys
from os import environ, getenv
from pathlib import Path

import pytest

from .configuration import TEST_TMP_CACHE, clear_test_cache

# Pin beartype strictness before any test module is imported.
environ['RUNTIME_TYPE_CHECKING_MODE'] = getenv(
    'RUNTIME_TYPE_CHECKING_MODE',
    'ERROR' if sys.version_info >= (3, 10) else 'WARNING',
)


@pytest.fixture
def fix_test_cache() -> Path:
    """Fixture to clear and return the test cache directory for use.

    Returns:
        Path: Path to the test cache directory

    """
    clear_test_cache()
    return TEST_TMP_CACHE
