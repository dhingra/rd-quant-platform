# Event Bus

`EventBus` is an in-process asynchronous dispatcher. It accepts synchronous or asynchronous handlers, preserves subscription order, isolates handler failures, and returns failures to the publisher.

The initial bus is deliberately small. Business components depend on events rather than on each other. A durable queue can later implement the same publishing boundary without changing domain logic.

Initial events include `TickReceived`, `FactorUpdated`, `RankingUpdated`, `ScannerTriggered`, `SignalGenerated`, `OrderSubmitted`, `TradeFilled`, and `PortfolioUpdated`.
