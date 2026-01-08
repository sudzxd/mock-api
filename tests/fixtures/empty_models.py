"""Empty test fixture: No Pydantic models.

This module is used to test parser behavior when no models are found.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any

# Third-party

# =============================================================================
# MODULE CONTENTS
# =============================================================================

# No models defined - this is intentional for testing
SOME_CONSTANT: str = "test"


def some_helper_function() -> Any:
    """A helper function that doesn't define models."""
    return None
