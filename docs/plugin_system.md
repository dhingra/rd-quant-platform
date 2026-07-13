# Plugin System

The registry groups plugins by category and stable lowercase name. Decorators register adapters during module import.

```python
@plugin("market_data", "example")
class ExampleProvider(MarketDataProvider):
    ...
```

Future categories include `indicator`, `scanner`, `strategy`, and `broker`. Plugin discovery from Python entry points is planned after the core extension interfaces stabilize.
