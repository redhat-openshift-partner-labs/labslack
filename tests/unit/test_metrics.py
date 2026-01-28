"""Tests for metrics/observability module."""

import time

from labslack.metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsRegistry,
    get_metrics,
)


class TestCounter:
    """Tests for Counter metric."""

    def test_initial_value_is_zero(self) -> None:
        """Test that counter starts at zero."""
        counter = Counter("test_counter", "Test counter")
        assert counter.value == 0

    def test_increment_by_one(self) -> None:
        """Test incrementing counter by one."""
        counter = Counter("test_counter", "Test counter")
        counter.inc()
        assert counter.value == 1

    def test_increment_by_amount(self) -> None:
        """Test incrementing counter by specific amount."""
        counter = Counter("test_counter", "Test counter")
        counter.inc(5)
        assert counter.value == 5

    def test_multiple_increments(self) -> None:
        """Test multiple increments accumulate."""
        counter = Counter("test_counter", "Test counter")
        counter.inc()
        counter.inc(3)
        counter.inc()
        assert counter.value == 5

    def test_labels(self) -> None:
        """Test counter with labels."""
        counter = Counter("test_counter", "Test counter")
        counter.labels(source="dm").inc()
        counter.labels(source="webhook").inc(2)

        assert counter.labels(source="dm").value == 1
        assert counter.labels(source="webhook").value == 2


class TestGauge:
    """Tests for Gauge metric."""

    def test_initial_value_is_zero(self) -> None:
        """Test that gauge starts at zero."""
        gauge = Gauge("test_gauge", "Test gauge")
        assert gauge.value == 0

    def test_set_value(self) -> None:
        """Test setting gauge value."""
        gauge = Gauge("test_gauge", "Test gauge")
        gauge.set(42)
        assert gauge.value == 42

    def test_inc_gauge(self) -> None:
        """Test incrementing gauge."""
        gauge = Gauge("test_gauge", "Test gauge")
        gauge.set(10)
        gauge.inc(5)
        assert gauge.value == 15

    def test_dec_gauge(self) -> None:
        """Test decrementing gauge."""
        gauge = Gauge("test_gauge", "Test gauge")
        gauge.set(10)
        gauge.dec(3)
        assert gauge.value == 7

    def test_labels(self) -> None:
        """Test gauge with labels."""
        gauge = Gauge("test_gauge", "Test gauge")
        gauge.labels(handler="webhook").set(5)
        gauge.labels(handler="dm").set(10)

        assert gauge.labels(handler="webhook").value == 5
        assert gauge.labels(handler="dm").value == 10


class TestHistogram:
    """Tests for Histogram metric."""

    def test_observe_value(self) -> None:
        """Test observing a value."""
        histogram = Histogram("test_histogram", "Test histogram")
        histogram.observe(0.5)
        histogram.observe(1.5)

        stats = histogram.get_stats()
        assert stats["count"] == 2
        assert stats["sum"] == 2.0

    def test_time_context_manager(self) -> None:
        """Test timing with context manager."""
        histogram = Histogram("test_histogram", "Test histogram")

        with histogram.time():
            time.sleep(0.01)  # Small delay

        stats = histogram.get_stats()
        assert stats["count"] == 1
        assert stats["sum"] >= 0.01

    def test_labels(self) -> None:
        """Test histogram with labels."""
        histogram = Histogram("test_histogram", "Test histogram")
        histogram.labels(operation="relay").observe(0.1)
        histogram.labels(operation="format").observe(0.05)

        assert histogram.labels(operation="relay").get_stats()["count"] == 1
        assert histogram.labels(operation="format").get_stats()["count"] == 1


class TestMetricsRegistry:
    """Tests for MetricsRegistry."""

    def test_register_counter(self) -> None:
        """Test registering a counter."""
        registry = MetricsRegistry()
        counter = registry.counter("my_counter", "My counter")

        assert counter.name == "my_counter"
        assert counter.value == 0

    def test_register_gauge(self) -> None:
        """Test registering a gauge."""
        registry = MetricsRegistry()
        gauge = registry.gauge("my_gauge", "My gauge")

        assert gauge.name == "my_gauge"
        assert gauge.value == 0

    def test_register_histogram(self) -> None:
        """Test registering a histogram."""
        registry = MetricsRegistry()
        histogram = registry.histogram("my_histogram", "My histogram")

        assert histogram.name == "my_histogram"

    def test_get_all_metrics(self) -> None:
        """Test getting all metrics as dict."""
        registry = MetricsRegistry()
        registry.counter("counter1", "Counter 1").inc(5)
        registry.gauge("gauge1", "Gauge 1").set(10)

        metrics = registry.get_all()

        assert "counter1" in metrics
        assert "gauge1" in metrics
        assert metrics["counter1"]["value"] == 5
        assert metrics["gauge1"]["value"] == 10

    def test_same_name_returns_same_metric(self) -> None:
        """Test that registering same name returns existing metric."""
        registry = MetricsRegistry()
        counter1 = registry.counter("my_counter", "My counter")
        counter1.inc(5)

        counter2 = registry.counter("my_counter", "My counter")
        assert counter2.value == 5
        assert counter1 is counter2


class TestGetMetrics:
    """Tests for global metrics access."""

    def test_get_metrics_returns_registry(self) -> None:
        """Test that get_metrics returns a registry."""
        metrics = get_metrics()
        assert isinstance(metrics, MetricsRegistry)

    def test_get_metrics_is_singleton(self) -> None:
        """Test that get_metrics returns the same instance."""
        metrics1 = get_metrics()
        metrics2 = get_metrics()
        assert metrics1 is metrics2
