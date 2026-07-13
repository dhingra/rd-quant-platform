"""Durable SQLite execution journal with no external dependency."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from rdqp.execution.domain.models import (
    ExecutionFill,
    ExecutionMode,
    ExecutionOrderType,
    ExecutionSide,
    ExecutionStatus,
    ManagedOrder,
    OrderRequest,
)
from rdqp.execution.domain.ports import TradeJournal


class SQLiteTradeJournal(TradeJournal):
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    def _initialize(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.executescript(
                """
                    CREATE TABLE IF NOT EXISTS orders (
                        order_id TEXT PRIMARY KEY, broker_order_id TEXT, mode TEXT, status TEXT,
                        symbol TEXT, side TEXT, quantity INTEGER, order_type TEXT,
                        limit_price REAL, stop_price REAL, reference_price REAL,
                        strategy TEXT, note TEXT, submitted_at TEXT, updated_at TEXT,
                        filled_quantity INTEGER,
                        average_fill_price REAL,
                        commission REAL,
                        message TEXT
                    );
                    CREATE TABLE IF NOT EXISTS fills (
                        fill_id TEXT PRIMARY KEY, order_id TEXT, broker_order_id TEXT, symbol TEXT,
                        side TEXT, quantity INTEGER, price REAL, commission REAL, timestamp TEXT
                    );
                    """
            )

    def record_order(self, order: ManagedOrder) -> None:
        r = order.request
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """INSERT OR REPLACE INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    order.order_id,
                    order.broker_order_id,
                    order.mode.value,
                    order.status.value,
                    r.symbol,
                    r.side.value,
                    r.quantity,
                    r.order_type.value,
                    r.limit_price,
                    r.stop_price,
                    r.reference_price,
                    r.strategy,
                    r.note,
                    order.submitted_at.isoformat(),
                    order.updated_at.isoformat(),
                    order.filled_quantity,
                    order.average_fill_price,
                    order.commission,
                    order.message,
                ),
            )

    def record_fill(self, fill: ExecutionFill) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """INSERT OR REPLACE INTO fills VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    fill.fill_id,
                    fill.order_id,
                    fill.broker_order_id,
                    fill.symbol,
                    fill.side.value,
                    fill.quantity,
                    fill.price,
                    fill.commission,
                    fill.timestamp.isoformat(),
                ),
            )

    def recent_orders(self, limit: int = 100) -> tuple[ManagedOrder, ...]:
        with closing(self._connect()) as conn, conn:
            rows = conn.execute(
                "SELECT * FROM orders ORDER BY submitted_at DESC LIMIT ?", (limit,)
            ).fetchall()
        result: list[ManagedOrder] = []
        for row in rows:
            request = OrderRequest(
                symbol=row[4],
                side=ExecutionSide(row[5]),
                quantity=row[6],
                order_type=ExecutionOrderType(row[7]),
                limit_price=row[8],
                stop_price=row[9],
                reference_price=row[10],
                strategy=row[11],
                note=row[12],
            )
            result.append(
                ManagedOrder(
                    order_id=row[0],
                    broker_order_id=row[1],
                    mode=ExecutionMode(row[2]),
                    status=ExecutionStatus(row[3]),
                    request=request,
                    submitted_at=datetime.fromisoformat(row[13]),
                    updated_at=datetime.fromisoformat(row[14]),
                    filled_quantity=row[15],
                    average_fill_price=row[16],
                    commission=row[17],
                    message=row[18],
                )
            )
        return tuple(result)

    def recent_fills(self, limit: int = 100) -> tuple[ExecutionFill, ...]:
        with closing(self._connect()) as conn, conn:
            rows = conn.execute(
                "SELECT * FROM fills ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
        return tuple(
            ExecutionFill(
                fill_id=row[0],
                order_id=row[1],
                broker_order_id=row[2],
                symbol=row[3],
                side=ExecutionSide(row[4]),
                quantity=row[5],
                price=row[6],
                commission=row[7],
                timestamp=datetime.fromisoformat(row[8]),
            )
            for row in rows
        )
