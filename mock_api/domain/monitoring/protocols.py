"""Protocols for monitoring and health check strategies.

This module defines the interfaces for health checks, metrics collection,
and observability features.

TODO: Implement for Issues #52, #53
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any, Protocol

# =============================================================================
# PUBLIC API
# =============================================================================


class IHealthCheck(Protocol):
    """Protocol for health check implementations.

    Future implementations (Issue #52):
        - BasicHealthCheck: Basic uptime and status checks
        - DatabaseHealthCheck: Database connectivity checks
        - DependencyHealthCheck: External dependency health
        - CompositeHealthCheck: Aggregates multiple health checks

    Example usage (future):
        >>> health_check = BasicHealthCheck()
        >>> status = health_check.check()
        >>> status.is_healthy
        True
    """

    def check(self) -> HealthStatus:
        """Perform health check.

        Returns:
            Health status with status code and details

        Note:
            Should return quickly (< 1 second) for liveness probes.
            May include detailed diagnostics for readiness probes.
        """
        ...

    def get_name(self) -> str:
        """Get the name of this health check.

        Returns:
            Health check name (e.g., "database", "storage", "api")
        """
        ...


class IMetricsCollector(Protocol):
    """Protocol for metrics collection strategies.

    Future implementations (Issues #52, #53):
        - PrometheusMetricsCollector: Prometheus-format metrics
        - StatsDMetricsCollector: StatsD protocol metrics
        - CloudWatchMetricsCollector: AWS CloudWatch metrics
        - SimpleMetricsCollector: In-memory metrics aggregation

    Design pattern: Observer
        Metrics collectors observe system events and record measurements.

    Example usage (future):
        >>> collector = PrometheusMetricsCollector()
        >>> collector.record_request("GET", "/api/users", 0.125, 200)
        >>> metrics = collector.export_metrics()
        >>> print(metrics)
        # HELP http_requests_total Total HTTP requests
        # TYPE http_requests_total counter
        http_requests_total{method="GET",endpoint="/api/users",status="200"} 1
    """

    def record_request(
        self,
        method: str,
        endpoint: str,
        duration: float,
        status_code: int,
    ) -> None:
        """Record an HTTP request metric.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            duration: Request duration in seconds
            status_code: HTTP status code

        Note:
            Should be non-blocking and performant (< 1ms overhead).
        """
        ...

    def record_error(
        self,
        error_type: str,
        endpoint: str,
    ) -> None:
        """Record an error occurrence.

        Args:
            error_type: Type of error (e.g., "validation", "not_found")
            endpoint: API endpoint where error occurred
        """
        ...

    def record_custom(
        self,
        metric_name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record a custom metric.

        Args:
            metric_name: Name of the metric
            value: Metric value
            labels: Optional metric labels/tags

        Example:
            >>> collector.record_custom(
            ...     "data_generation_duration",
            ...     1.23,
            ...     {"model": "User", "count": "100"}
            ... )
        """
        ...

    def export_metrics(self) -> str:
        """Export metrics in the collector's format.

        Returns:
            Metrics as string in the appropriate format
            (Prometheus, JSON, etc.)

        Note:
            Format depends on implementation (Prometheus text format,
            JSON for CloudWatch, etc.)
        """
        ...

    def reset_metrics(self) -> None:
        """Reset all collected metrics.

        Note:
            Useful for testing and development. Production implementations
            may choose to not implement this or make it a no-op.
        """
        ...


class HealthStatus:
    """Result of a health check.

    Attributes:
        is_healthy: Whether the system is healthy
        status: Status string ("healthy", "degraded", "unhealthy")
        details: Additional diagnostic information
        timestamp: When the check was performed
    """

    def __init__(
        self,
        is_healthy: bool,
        status: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.is_healthy = is_healthy
        self.status = status
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_healthy": self.is_healthy,
            "status": self.status,
            "details": self.details,
        }
