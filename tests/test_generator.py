"""Tests for data generator."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from mock_api.core.constants import DEFAULT_GENERATION_COUNT, PRIMARY_KEY_FIELD
from mock_api.core.generator import DataGenerator
from mock_api.core.parser import SchemaParser
from mock_api.core.types import ModelSchema

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def parser() -> SchemaParser:
    """Create a SchemaParser instance."""
    return SchemaParser()


@pytest.fixture
def generator_models_file() -> str:
    """Path to generator test models fixture file."""
    return str(Path(__file__).parent / "fixtures" / "generator_models.py")


@pytest.fixture
def contact_schema(
    parser: SchemaParser, generator_models_file: str
) -> dict[str, ModelSchema]:
    """Parse Contact model schema."""
    schemas = parser.parse_file(generator_models_file)
    return {"Contact": schemas["Contact"]}


@pytest.fixture
def relationship_schemas(
    parser: SchemaParser, generator_models_file: str
) -> dict[str, ModelSchema]:
    """Parse Author/Book/Review schemas for FK testing."""
    schemas = parser.parse_file(generator_models_file)
    return {
        "Author": schemas["Author"],
        "Book": schemas["Book"],
        "Review": schemas["Review"],
    }


@pytest.fixture
def enum_schema(
    parser: SchemaParser, generator_models_file: str
) -> dict[str, ModelSchema]:
    """Parse Product schema with enums."""
    schemas = parser.parse_file(generator_models_file)
    return {"Product": schemas["Product"]}


@pytest.fixture
def self_ref_schema(
    parser: SchemaParser, generator_models_file: str
) -> dict[str, ModelSchema]:
    """Parse Node schema with self-reference."""
    schemas = parser.parse_file(generator_models_file)
    return {"Node": schemas["Node"]}


# =============================================================================
# TESTS: Initialization
# =============================================================================


def test_generator_initialization_with_empty_schemas() -> None:
    """Test generator can be initialized with empty schemas."""
    generator = DataGenerator({})
    assert generator.schemas == {}
    assert generator.data == {}


def test_generator_initialization_with_seed(
    contact_schema: dict[str, ModelSchema],
) -> None:
    """Test generator seed produces reproducible results."""
    seed = 42

    generator1 = DataGenerator(contact_schema, seed=seed)
    result1 = generator1.generate("Contact", count=1)

    generator2 = DataGenerator(contact_schema, seed=seed)
    result2 = generator2.generate("Contact", count=1)

    # Same seed should produce identical data (excluding ID which is sequential)
    assert result1[0]["email"] == result2[0]["email"]
    assert result1[0]["name"] == result2[0]["name"]


def test_generator_initialization_with_locale() -> None:
    """Test generator accepts different locales."""
    generator = DataGenerator({}, locale="fr_FR")
    # Verify faker instance was created (locale check depends on Faker internals)
    assert generator.faker is not None


# =============================================================================
# TESTS: Basic Generation
# =============================================================================


def test_generate_returns_correct_count(contact_schema: dict[str, ModelSchema]) -> None:
    """Test generate returns requested number of instances."""
    generator = DataGenerator(contact_schema)
    count = 5

    result = generator.generate("Contact", count=count)

    assert len(result) == count


def test_generate_default_count(contact_schema: dict[str, ModelSchema]) -> None:
    """Test generate uses default count when not specified."""
    generator = DataGenerator(contact_schema)

    result = generator.generate("Contact")

    assert len(result) == DEFAULT_GENERATION_COUNT


def test_generate_raises_on_invalid_model(
    contact_schema: dict[str, ModelSchema],
) -> None:
    """Test generate raises ValueError for non-existent model."""
    generator = DataGenerator(contact_schema)

    with pytest.raises(ValueError, match="Model 'Invalid' not found"):
        generator.generate("Invalid")


def test_generate_creates_unique_ids(contact_schema: dict[str, ModelSchema]) -> None:
    """Test generated instances have unique sequential IDs."""
    generator = DataGenerator(contact_schema)

    result = generator.generate("Contact", count=5)

    ids = [instance[PRIMARY_KEY_FIELD] for instance in result]
    assert ids == [1, 2, 3, 4, 5]


def test_generate_stores_data_for_fk_resolution(
    contact_schema: dict[str, ModelSchema],
) -> None:
    """Test generated data is stored for later FK resolution."""
    generator = DataGenerator(contact_schema)

    generator.generate("Contact", count=3)

    assert "Contact" in generator.data
    assert len(generator.data["Contact"]) == 3


# =============================================================================
# TESTS: Field Pattern Generation
# =============================================================================


def test_generate_email_field(contact_schema: dict[str, ModelSchema]) -> None:
    """Test email field generates valid email addresses."""
    generator = DataGenerator(contact_schema)

    result = generator.generate("Contact", count=1)

    assert "@" in result[0]["email"]


def test_generate_phone_field(contact_schema: dict[str, ModelSchema]) -> None:
    """Test phone field generates phone numbers."""
    generator = DataGenerator(contact_schema)

    result = generator.generate("Contact", count=1)

    assert isinstance(result[0]["phone"], str)
    assert len(result[0]["phone"]) > 0


def test_generate_name_fields(contact_schema: dict[str, ModelSchema]) -> None:
    """Test name field patterns generate names."""
    generator = DataGenerator(contact_schema)

    result = generator.generate("Contact", count=1)

    assert isinstance(result[0]["name"], str)
    assert isinstance(result[0]["username"], str)
    assert isinstance(result[0]["first_name"], str)
    assert isinstance(result[0]["last_name"], str)


def test_generate_address_fields(
    parser: SchemaParser, generator_models_file: str
) -> None:
    """Test address field patterns generate location data."""
    schemas = parser.parse_file(generator_models_file)
    generator = DataGenerator({"Location": schemas["Location"]})

    result = generator.generate("Location", count=1)
    location = result[0]

    assert isinstance(location["address"], str)
    assert isinstance(location["street"], str)
    assert isinstance(location["city"], str)
    assert isinstance(location["state"], str)
    assert isinstance(location["country"], str)
    assert isinstance(location["zip"], str)


def test_generate_content_fields(
    parser: SchemaParser, generator_models_file: str
) -> None:
    """Test content field patterns generate text."""
    schemas = parser.parse_file(generator_models_file)
    generator = DataGenerator({"Article": schemas["Article"]})

    result = generator.generate("Article", count=1)
    article = result[0]

    assert isinstance(article["title"], str)
    assert isinstance(article["content"], str)
    assert isinstance(article["description"], str)
    assert isinstance(article["url"], str)
    assert "http" in article["url"]


def test_generate_timestamp_fields(
    parser: SchemaParser, generator_models_file: str
) -> None:
    """Test timestamp fields generate datetime objects."""
    schemas = parser.parse_file(generator_models_file)
    generator = DataGenerator({"Article": schemas["Article"]})

    result = generator.generate("Article", count=1)
    article = result[0]

    assert isinstance(article["created_at"], datetime)
    assert isinstance(article["updated_at"], datetime)


# =============================================================================
# TESTS: Type-Based Generation
# =============================================================================


def test_generate_falls_back_to_type_for_unknown_pattern(
    parser: SchemaParser, generator_models_file: str
) -> None:
    """Test generator falls back to type-based generation for unknown patterns."""
    schemas = parser.parse_file(generator_models_file)
    generator = DataGenerator({"Author": schemas["Author"]})

    result = generator.generate("Author", count=1)

    # "name" should match pattern, but verify type fallback works
    assert isinstance(result[0]["name"], str)


# =============================================================================
# TESTS: Enum Field Generation
# =============================================================================


def test_generate_enum_field(enum_schema: dict[str, ModelSchema]) -> None:
    """Test enum fields generate valid enum values."""
    generator = DataGenerator(enum_schema)

    result = generator.generate("Product", count=10)

    # Check all priority values are valid enum values
    priority_values = {instance["priority"] for instance in result}
    assert priority_values.issubset({1, 2, 3})


def test_generate_optional_enum_field(enum_schema: dict[str, ModelSchema]) -> None:
    """Test optional enum fields can be None or valid enum values."""
    generator = DataGenerator(enum_schema)

    result = generator.generate("Product", count=50)

    status_values = {instance["status"] for instance in result}
    # Should contain None and/or valid enum values
    assert None in status_values or status_values.issubset({"active", "inactive"})


# =============================================================================
# TESTS: Optional Field Generation
# =============================================================================


def test_generate_optional_field_sometimes_none(
    enum_schema: dict[str, ModelSchema],
) -> None:
    """Test optional fields are sometimes None based on probability."""
    generator = DataGenerator(enum_schema)

    result = generator.generate("Product", count=100)

    none_count = sum(1 for instance in result if instance["description"] is None)
    non_none_count = sum(
        1 for instance in result if instance["description"] is not None
    )

    # With 100 instances and 20% probability, expect ~20 None values
    # Allow range to account for randomness
    assert 10 <= none_count <= 30
    assert 70 <= non_none_count <= 90


def test_generate_required_field_never_none(
    enum_schema: dict[str, ModelSchema],
) -> None:
    """Test required fields are never None."""
    generator = DataGenerator(enum_schema)

    result = generator.generate("Product", count=50)

    for instance in result:
        assert instance["name"] is not None
        assert instance["priority"] is not None


# =============================================================================
# TESTS: Foreign Key Generation
# =============================================================================


def test_generate_foreign_key_references_existing_data(
    relationship_schemas: dict[str, ModelSchema],
) -> None:
    """Test FK fields reference IDs from related models."""
    generator = DataGenerator(relationship_schemas)

    # Generate authors first
    authors = generator.generate("Author", count=5)
    author_ids = {author[PRIMARY_KEY_FIELD] for author in authors}

    # Generate books
    books = generator.generate("Book", count=10)

    # All author_id values should be valid author IDs
    for book in books:
        assert book["author_id"] in author_ids


def test_generate_foreign_key_auto_generates_dependency(
    relationship_schemas: dict[str, ModelSchema],
) -> None:
    """Test FK generation auto-generates dependency if not exists."""
    generator = DataGenerator(relationship_schemas)

    # Generate books without generating authors first
    books = generator.generate("Book", count=5)

    # Authors should have been auto-generated
    assert "Author" in generator.data
    assert len(generator.data["Author"]) == DEFAULT_GENERATION_COUNT

    # Book FKs should reference those authors
    author_ids = {author[PRIMARY_KEY_FIELD] for author in generator.data["Author"]}
    for book in books:
        assert book["author_id"] in author_ids


def test_generate_self_referential_foreign_key(
    self_ref_schema: dict[str, ModelSchema],
) -> None:
    """Test self-referential FKs work correctly."""
    generator = DataGenerator(self_ref_schema)

    result = generator.generate("Node", count=10)

    # parent_id can be None or reference another node
    for node in result:
        parent_id = node.get("parent_id")
        assert parent_id is None or isinstance(parent_id, int)


# =============================================================================
# TESTS: Dependency Resolution
# =============================================================================


def test_generate_all_respects_dependency_order(
    relationship_schemas: dict[str, ModelSchema],
) -> None:
    """Test generate_all generates models in correct dependency order."""
    generator = DataGenerator(relationship_schemas)

    result = generator.generate_all(count_per_model=5)

    # Should have all three models
    assert "Author" in result
    assert "Book" in result
    assert "Review" in result

    # Each should have 5 instances
    assert len(result["Author"]) == 5
    assert len(result["Book"]) == 5
    assert len(result["Review"]) == 5


def test_generate_all_maintains_referential_integrity(
    relationship_schemas: dict[str, ModelSchema],
) -> None:
    """Test generate_all maintains FK integrity across models."""
    generator = DataGenerator(relationship_schemas)

    result = generator.generate_all(count_per_model=10)

    # Get all author IDs
    author_ids = {author[PRIMARY_KEY_FIELD] for author in result["Author"]}

    # All books should reference valid authors
    for book in result["Book"]:
        assert book["author_id"] in author_ids

    # Get all book IDs
    book_ids = {book[PRIMARY_KEY_FIELD] for book in result["Book"]}

    # All reviews should reference valid books
    for review in result["Review"]:
        assert review["book_id"] in book_ids


def test_generate_all_with_custom_count(
    relationship_schemas: dict[str, ModelSchema],
) -> None:
    """Test generate_all respects custom count per model."""
    generator = DataGenerator(relationship_schemas)
    count = 3

    result = generator.generate_all(count_per_model=count)

    for _model_name, instances in result.items():
        assert len(instances) == count


# =============================================================================
# TESTS: Reproducibility
# =============================================================================


def test_generator_with_seed_produces_reproducible_results(
    contact_schema: dict[str, ModelSchema],
) -> None:
    """Test same seed produces same data."""
    seed = 42

    generator1 = DataGenerator(contact_schema, seed=seed)
    result1 = generator1.generate("Contact", count=5)

    generator2 = DataGenerator(contact_schema, seed=seed)
    result2 = generator2.generate("Contact", count=5)

    # Results should be identical
    assert result1 == result2


def test_generator_without_seed_produces_different_results(
    contact_schema: dict[str, ModelSchema],
) -> None:
    """Test generators without seed produce different data."""
    generator1 = DataGenerator(contact_schema)
    result1 = generator1.generate("Contact", count=5)

    generator2 = DataGenerator(contact_schema)
    result2 = generator2.generate("Contact", count=5)

    # Results should differ (at least in some fields besides ID)
    # Check emails are different
    emails1 = [instance["email"] for instance in result1]
    emails2 = [instance["email"] for instance in result2]
    assert emails1 != emails2


# =============================================================================
# TESTS: Edge Cases
# =============================================================================


def test_generate_with_zero_count(contact_schema: dict[str, ModelSchema]) -> None:
    """Test generate with count=0 returns empty list."""
    generator = DataGenerator(contact_schema)

    result = generator.generate("Contact", count=0)

    assert result == []


def test_generate_all_with_empty_schemas() -> None:
    """Test generate_all with no schemas returns empty dict."""
    generator = DataGenerator({})

    result = generator.generate_all()

    assert result == {}


def test_generator_handles_missing_fk_gracefully(
    parser: SchemaParser, generator_models_file: str
) -> None:
    """Test generator handles missing FK target gracefully."""
    schemas = parser.parse_file(generator_models_file)
    # Only include Book, not Author
    generator = DataGenerator({"Book": schemas["Book"]})

    # Should fall back to random ID
    result = generator.generate("Book", count=1)

    assert isinstance(result[0]["author_id"], int)
    assert result[0]["author_id"] > 0
