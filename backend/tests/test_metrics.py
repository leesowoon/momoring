from app.services.metrics import Counter, Gauge, Histogram, MetricsRegistry


def test_counter_inc_and_render() -> None:
    c = Counter("foo", "test counter")
    c.inc()
    c.inc(2.0)
    text = "\n".join(c.render())
    assert "# TYPE foo counter" in text
    assert "foo 3" in text


def test_counter_with_labels_renders_each_label_set() -> None:
    c = Counter("foo")
    c.inc(category="a")
    c.inc(category="b")
    c.inc(category="a")
    text = "\n".join(c.render())
    assert 'foo{category="a"} 2' in text
    assert 'foo{category="b"} 1' in text


def test_counter_renders_zero_when_unused() -> None:
    text = "\n".join(Counter("foo").render())
    assert "foo 0" in text


def test_histogram_observe_and_render() -> None:
    h = Histogram("lat", "ms", buckets=(10, 100, 1000, float("inf")))
    h.observe(5)
    h.observe(50)
    h.observe(500)
    text = "\n".join(h.render())
    assert 'lat_bucket{le="10"} 1' in text
    assert 'lat_bucket{le="100"} 2' in text
    assert 'lat_bucket{le="1000"} 3' in text
    assert 'lat_bucket{le="+Inf"} 3' in text
    assert "lat_count 3" in text
    assert "lat_sum 555" in text


def test_gauge_inc_dec_set() -> None:
    g = Gauge("active")
    g.inc()
    g.inc()
    g.dec()
    text = "\n".join(g.render())
    assert "active 1" in text
    g.set(10)
    assert "active 10" in "\n".join(g.render())


def test_registry_renders_all_metrics() -> None:
    reg = MetricsRegistry()
    reg.counter("a")
    reg.histogram("b")
    reg.gauge("c")
    output = reg.render()
    assert "# TYPE a counter" in output
    assert "# TYPE b histogram" in output
    assert "# TYPE c gauge" in output
