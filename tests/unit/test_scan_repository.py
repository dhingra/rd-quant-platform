from rdqp.scanners import FilterOperator, ScanDefinition, ScannerFilter
from rdqp.scanners.infrastructure.yaml_repository import YamlScanRepository


def test_yaml_repository_round_trip(tmp_path):
    repo = YamlScanRepository(tmp_path / "scans.yaml")
    definition = ScanDefinition(
        name="High RVOL",
        filters=(ScannerFilter("rvol", FilterOperator.GTE, 2.0),),
        sort_by="rvol",
    )
    repo.save(definition)
    assert repo.list() == (definition,)
    repo.delete("High RVOL")
    assert repo.list() == ()
