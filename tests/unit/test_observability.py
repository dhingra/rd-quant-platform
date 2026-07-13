from rdqp.observability import HealthMonitor, HealthStatus, MetricsRegistry


def test_health_monitor_isolates_failed_checks() -> None:
    monitor = HealthMonitor()
    monitor.register("ok", lambda: (HealthStatus.HEALTHY, "ready"))
    monitor.register("broken", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    results = {item.name: item for item in monitor.run()}
    assert results["ok"].status is HealthStatus.HEALTHY
    assert results["broken"].status is HealthStatus.UNHEALTHY


def test_metrics_registry_tracks_counters() -> None:
    registry = MetricsRegistry()
    registry.increment("ticks", 2)
    registry.increment("ticks", 3)
    metric = registry.snapshot()[0]
    assert metric.name == "ticks"
    assert metric.value == 5
