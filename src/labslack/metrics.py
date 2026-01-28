"""Metrics and observability module for LabSlack.

Provides lightweight metrics collection without external dependencies.
"""

import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class Counter:
    """A monotonically increasing counter metric."""

    name: str
    description: str
    _value: float = field(default=0.0, init=False)
    _labels: dict[str, str] = field(default_factory=dict, init=False)
    _labeled_values: dict[tuple[tuple[str, str], ...], float] = field(
        default_factory=dict, init=False
    )
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    @property
    def value(self) -> float:
        """Get the current counter value."""
        if self._labels:
            key = tuple(sorted(self._labels.items()))
            return self._labeled_values.get(key, 0.0)
        return self._value

    def inc(self, amount: float = 1.0) -> None:
        """Increment the counter.

        Args:
            amount: Amount to increment by (default 1).
        """
        with self._lock:
            if self._labels:
                key = tuple(sorted(self._labels.items()))
                self._labeled_values[key] = self._labeled_values.get(key, 0.0) + amount
            else:
                self._value += amount

    def labels(self, **kwargs: str) -> "Counter":
        """Return a labeled instance of this counter.

        Args:
            **kwargs: Label key-value pairs.

        Returns:
            A Counter instance with the specified labels.
        """
        labeled = Counter(self.name, self.description)
        labeled._labels = kwargs
        labeled._labeled_values = self._labeled_values
        labeled._lock = self._lock
        return labeled

    def to_dict(self) -> dict[str, Any]:
        """Convert counter to dictionary representation."""
        result: dict[str, Any] = {
            "name": self.name,
            "type": "counter",
            "value": self._value,
        }
        if self._labeled_values:
            result["labeled_values"] = {
                str(dict(k)): v for k, v in self._labeled_values.items()
            }
        return result


@dataclass
class Gauge:
    """A metric that can increase or decrease."""

    name: str
    description: str
    _value: float = field(default=0.0, init=False)
    _labels: dict[str, str] = field(default_factory=dict, init=False)
    _labeled_values: dict[tuple[tuple[str, str], ...], float] = field(
        default_factory=dict, init=False
    )
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    @property
    def value(self) -> float:
        """Get the current gauge value."""
        if self._labels:
            key = tuple(sorted(self._labels.items()))
            return self._labeled_values.get(key, 0.0)
        return self._value

    def set(self, value: float) -> None:
        """Set the gauge to a specific value.

        Args:
            value: The value to set.
        """
        with self._lock:
            if self._labels:
                key = tuple(sorted(self._labels.items()))
                self._labeled_values[key] = value
            else:
                self._value = value

    def inc(self, amount: float = 1.0) -> None:
        """Increment the gauge.

        Args:
            amount: Amount to increment by (default 1).
        """
        with self._lock:
            if self._labels:
                key = tuple(sorted(self._labels.items()))
                self._labeled_values[key] = self._labeled_values.get(key, 0.0) + amount
            else:
                self._value += amount

    def dec(self, amount: float = 1.0) -> None:
        """Decrement the gauge.

        Args:
            amount: Amount to decrement by (default 1).
        """
        with self._lock:
            if self._labels:
                key = tuple(sorted(self._labels.items()))
                self._labeled_values[key] = self._labeled_values.get(key, 0.0) - amount
            else:
                self._value -= amount

    def labels(self, **kwargs: str) -> "Gauge":
        """Return a labeled instance of this gauge.

        Args:
            **kwargs: Label key-value pairs.

        Returns:
            A Gauge instance with the specified labels.
        """
        labeled = Gauge(self.name, self.description)
        labeled._labels = kwargs
        labeled._labeled_values = self._labeled_values
        labeled._lock = self._lock
        return labeled

    def to_dict(self) -> dict[str, Any]:
        """Convert gauge to dictionary representation."""
        result: dict[str, Any] = {
            "name": self.name,
            "type": "gauge",
            "value": self._value,
        }
        if self._labeled_values:
            result["labeled_values"] = {
                str(dict(k)): v for k, v in self._labeled_values.items()
            }
        return result


@dataclass
class Histogram:
    """A metric for measuring distributions of values."""

    name: str
    description: str
    _count: int = field(default=0, init=False)
    _sum: float = field(default=0.0, init=False)
    _labels: dict[str, str] = field(default_factory=dict, init=False)
    _labeled_stats: dict[tuple[tuple[str, str], ...], dict[str, float]] = field(
        default_factory=dict, init=False
    )
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def observe(self, value: float) -> None:
        """Observe a value.

        Args:
            value: The value to observe.
        """
        with self._lock:
            if self._labels:
                key = tuple(sorted(self._labels.items()))
                stats = self._labeled_stats.setdefault(key, {"count": 0, "sum": 0.0})
                stats["count"] += 1
                stats["sum"] += value
            else:
                self._count += 1
                self._sum += value

    @contextmanager
    def time(self) -> Generator[None, None, None]:
        """Context manager to time a block of code.

        Yields:
            None
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.observe(duration)

    def get_stats(self) -> dict[str, float]:
        """Get histogram statistics.

        Returns:
            Dictionary with count and sum.
        """
        if self._labels:
            key = tuple(sorted(self._labels.items()))
            return self._labeled_stats.get(key, {"count": 0, "sum": 0.0})
        return {"count": self._count, "sum": self._sum}

    def labels(self, **kwargs: str) -> "Histogram":
        """Return a labeled instance of this histogram.

        Args:
            **kwargs: Label key-value pairs.

        Returns:
            A Histogram instance with the specified labels.
        """
        labeled = Histogram(self.name, self.description)
        labeled._labels = kwargs
        labeled._labeled_stats = self._labeled_stats
        labeled._lock = self._lock
        return labeled

    def to_dict(self) -> dict[str, Any]:
        """Convert histogram to dictionary representation."""
        result: dict[str, Any] = {
            "name": self.name,
            "type": "histogram",
            "count": self._count,
            "sum": self._sum,
        }
        if self._labeled_stats:
            result["labeled_values"] = {
                str(dict(k)): v for k, v in self._labeled_stats.items()
            }
        return result


class MetricsRegistry:
    """Registry for all application metrics."""

    def __init__(self) -> None:
        self._metrics: dict[str, Counter | Gauge | Histogram] = {}
        self._lock = Lock()

    def counter(self, name: str, description: str) -> Counter:
        """Get or create a counter metric.

        Args:
            name: Metric name.
            description: Metric description.

        Returns:
            Counter instance.
        """
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Counter(name, description)
            metric = self._metrics[name]
            if not isinstance(metric, Counter):
                raise TypeError(f"Metric {name} is not a Counter")
            return metric

    def gauge(self, name: str, description: str) -> Gauge:
        """Get or create a gauge metric.

        Args:
            name: Metric name.
            description: Metric description.

        Returns:
            Gauge instance.
        """
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Gauge(name, description)
            metric = self._metrics[name]
            if not isinstance(metric, Gauge):
                raise TypeError(f"Metric {name} is not a Gauge")
            return metric

    def histogram(self, name: str, description: str) -> Histogram:
        """Get or create a histogram metric.

        Args:
            name: Metric name.
            description: Metric description.

        Returns:
            Histogram instance.
        """
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Histogram(name, description)
            metric = self._metrics[name]
            if not isinstance(metric, Histogram):
                raise TypeError(f"Metric {name} is not a Histogram")
            return metric

    def get_all(self) -> dict[str, Any]:
        """Get all metrics as a dictionary.

        Returns:
            Dictionary of all metrics and their values.
        """
        with self._lock:
            result: dict[str, Any] = {}
            for name, metric in self._metrics.items():
                result[name] = metric.to_dict()
            return result


# Global metrics registry singleton
_metrics_registry: MetricsRegistry | None = None


def get_metrics() -> MetricsRegistry:
    """Get the global metrics registry.

    Returns:
        The global MetricsRegistry instance.
    """
    global _metrics_registry
    if _metrics_registry is None:
        _metrics_registry = MetricsRegistry()
    return _metrics_registry


def reset_metrics() -> None:
    """Reset the global metrics registry. Used for testing."""
    global _metrics_registry
    _metrics_registry = None
