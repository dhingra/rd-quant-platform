"""Built-in scanner definitions."""

from rdqp.scanners.domain.models import FilterOperator, ScanDefinition, ScannerFilter


def default_scans() -> tuple[ScanDefinition, ...]:
    return (
        ScanDefinition(
            name="Momentum Leaders",
            description="Positive ROC with confirmation above VWAP.",
            filters=(
                ScannerFilter("roc_pct", FilterOperator.GTE, 0.25),
                ScannerFilter("above_vwap", FilterOperator.IS_TRUE),
            ),
            sort_by="roc_pct",
        ),
        ScanDefinition(
            name="High RVOL",
            description="Relative volume at or above 1.5x.",
            filters=(ScannerFilter("rvol", FilterOperator.GTE, 1.5),),
            sort_by="rvol",
        ),
        ScanDefinition(
            name="Gap Up",
            description="Stocks opening at least 1% above the prior reference.",
            filters=(ScannerFilter("gap_pct", FilterOperator.GTE, 1.0),),
            sort_by="gap_pct",
        ),
        ScanDefinition(
            name="Gap Down",
            description="Stocks opening at least 1% below the prior reference.",
            filters=(ScannerFilter("gap_pct", FilterOperator.LTE, -1.0),),
            sort_by="gap_pct",
            descending=False,
        ),
        ScanDefinition(
            name="ORB Breakout",
            description="Price above the opening range high.",
            filters=(ScannerFilter("orb_breakout", FilterOperator.IS_TRUE),),
            sort_by="roc_pct",
        ),
        ScanDefinition(
            name="VWAP Reclaim",
            description="Positive momentum while trading above VWAP.",
            filters=(
                ScannerFilter("above_vwap", FilterOperator.IS_TRUE),
                ScannerFilter("roc_pct", FilterOperator.GT, 0.0),
            ),
            sort_by="vwap_distance_pct",
        ),
    )
