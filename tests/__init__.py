# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Shared test package: pin runtime type-checking strictness before imports.

Importing this package sets ``RUNTIME_TYPE_CHECKING_MODE`` (unless the
environment already defines it), so every test module that follows inherits
the same beartype strictness.
"""

import sys
from os import environ, getenv


def _default_runtime_type_checking_mode() -> str:
    """Return the default beartype strictness for the current interpreter."""
    return 'ERROR' if sys.version_info >= (3, 10) else 'WARNING'


environ['RUNTIME_TYPE_CHECKING_MODE'] = getenv(
    'RUNTIME_TYPE_CHECKING_MODE', _default_runtime_type_checking_mode()
)
