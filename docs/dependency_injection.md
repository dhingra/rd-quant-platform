# Dependency Injection

`rdqp.app.build_container` is the composition root. It reads typed settings and registers the chosen provider behind `MarketDataProvider`. Application services resolve ports rather than infrastructure classes.

The custom container intentionally supports only instance and factory registration. This keeps the foundation transparent and avoids coupling the framework to a third-party DI API. It can be replaced later without changing domain code.
