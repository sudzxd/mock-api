"""Shared test fixtures and configuration."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from datetime import datetime
from typing import Any

# Third-party
import pytest

# Project/local
from mock_api.domain.value_objects.schema import FieldSchema, ModelSchema
from mock_api.infrastructure.repositories.memory.memory_repository import (
    MemoryRepository,
)
from mock_api.infrastructure.services.filter_executor import FilterExecutor
from mock_api.infrastructure.services.sort_executor import SortExecutor
from mock_api.infrastructure.services.validation_service import ValidationService
from pydantic import BaseModel


# =============================================================================
# FIXTURES - SCHEMAS
# =============================================================================
@pytest.fixture
def user_schema() -> ModelSchema:
    """Create User model schema for testing."""
    return ModelSchema(
        name="User",
        fields=(
            FieldSchema(name="id", type=int, is_optional=False),
            FieldSchema(name="name", type=str, is_optional=False),
            FieldSchema(name="email", type=str, is_optional=False),
            FieldSchema(name="age", type=int, is_optional=True, default=None),
            FieldSchema(name="created_at", type=datetime, is_optional=False),
        ),
        primary_key="id",
    )


@pytest.fixture
def product_schema() -> ModelSchema:
    """Create Product model schema for testing."""
    return ModelSchema(
        name="Product",
        fields=(
            FieldSchema(name="id", type=int, is_optional=False),
            FieldSchema(name="name", type=str, is_optional=False),
            FieldSchema(name="price", type=float, is_optional=False),
            FieldSchema(name="in_stock", type=bool, is_optional=False, default=True),
        ),
        primary_key="id",
    )


@pytest.fixture
def schemas_dict(
    user_schema: ModelSchema, product_schema: ModelSchema
) -> dict[str, ModelSchema]:
    """Create dictionary of schemas for testing."""
    return {
        "User": user_schema,
        "Product": product_schema,
    }


# =============================================================================
# FIXTURES - SERVICES
# =============================================================================
@pytest.fixture
def validation_service() -> ValidationService:
    """Create ValidationService for testing."""
    return ValidationService()


@pytest.fixture
def filter_executor() -> FilterExecutor:
    """Create FilterExecutor for testing."""
    return FilterExecutor()


@pytest.fixture
def sort_executor() -> SortExecutor:
    """Create SortExecutor for testing."""
    return SortExecutor()


# =============================================================================
# FIXTURES - REPOSITORY
# =============================================================================
@pytest.fixture
def memory_repository(
    schemas_dict: dict[str, ModelSchema],
    validation_service: ValidationService,
    filter_executor: FilterExecutor,
    sort_executor: SortExecutor,
) -> MemoryRepository:
    """Create MemoryRepository with test schemas."""
    return MemoryRepository(
        schemas=schemas_dict,
        validation_service=validation_service,
        filter_executor=filter_executor,
        sort_executor=sort_executor,
    )


# =============================================================================
# FIXTURES - TEST DATA
# =============================================================================
@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Create sample user data for testing."""
    return {
        "name": "Alice",
        "email": "alice@example.com",
        "age": 30,
        "created_at": "2026-01-17T00:00:00",
    }


@pytest.fixture
def sample_product_data() -> dict[str, Any]:
    """Create sample product data for testing."""
    return {
        "name": "Laptop",
        "price": 1500.0,
        "in_stock": True,
    }


# =============================================================================
# FIXTURES - PYDANTIC MODELS
# =============================================================================
@pytest.fixture
def user_pydantic_model() -> type[BaseModel]:
    """Create Pydantic User model for testing."""

    class User(BaseModel):
        id: int
        name: str
        email: str
        age: int | None = None
        created_at: datetime

    return User


@pytest.fixture
def product_pydantic_model() -> type[BaseModel]:
    """Create Pydantic Product model for testing."""

    class Product(BaseModel):
        id: int
        name: str
        price: float
        in_stock: bool = True

    return Product
