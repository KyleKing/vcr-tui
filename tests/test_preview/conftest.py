# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Shared fixtures for preview tests."""

from pathlib import Path

import pytest

CASSETTE = Path(__file__).parents[2] / 'fixtures' / 'cassettes' / 'example_api.yaml'


@pytest.fixture(scope='module')
def cassette_path() -> Path:
    return CASSETTE


@pytest.fixture(scope='module')
def cassette_data(cassette_path: Path):
    from vcr_tui.preview.yaml_parser import load_yaml

    return load_yaml(cassette_path)
