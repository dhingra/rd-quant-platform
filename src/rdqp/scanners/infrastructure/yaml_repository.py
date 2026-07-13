"""YAML-backed saved scanner repository."""

from __future__ import annotations

from pathlib import Path

import yaml

from rdqp.scanners.domain.models import FilterOperator, ScanDefinition, ScannerFilter


class YamlScanRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def list(self) -> tuple[ScanDefinition, ...]:
        if not self.path.exists():
            return ()
        raw = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        return tuple(self._from_dict(item) for item in raw.get("scans", []))

    def save(self, definition: ScanDefinition) -> None:
        definitions = {item.name: item for item in self.list()}
        definitions[definition.name] = definition
        self._write(tuple(definitions.values()))

    def delete(self, name: str) -> None:
        self._write(tuple(item for item in self.list() if item.name != name))

    def _write(self, definitions: tuple[ScanDefinition, ...]) -> None:
        payload = {"scans": [self._to_dict(item) for item in definitions]}
        self.path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    @staticmethod
    def _to_dict(definition: ScanDefinition) -> dict[str, object]:
        return {
            "name": definition.name,
            "description": definition.description,
            "enabled": definition.enabled,
            "sort_by": definition.sort_by,
            "descending": definition.descending,
            "limit": definition.limit,
            "filters": [
                {
                    "field": f.field,
                    "operator": f.operator.value,
                    "value": f.value,
                    "second_value": f.second_value,
                }
                for f in definition.filters
            ],
        }

    @staticmethod
    def _from_dict(data: dict[str, object]) -> ScanDefinition:
        filters = tuple(
            ScannerFilter(
                field=str(item["field"]),
                operator=FilterOperator(str(item["operator"])),
                value=item.get("value"),
                second_value=item.get("second_value"),
            )
            for item in data.get("filters", [])  # type: ignore[union-attr]
        )
        return ScanDefinition(
            name=str(data["name"]),
            description=str(data.get("description", "")),
            enabled=bool(data.get("enabled", True)),
            sort_by=str(data.get("sort_by", "roc")),
            descending=bool(data.get("descending", True)),
            limit=int(data.get("limit", 50)),
            filters=filters,
        )
