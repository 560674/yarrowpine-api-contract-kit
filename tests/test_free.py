from pathlib import Path

import pytest

from ypapi.cli import main, template_names
from ypapi.loader import load_document
from ypapi.rules import active_rules, check

HERE = Path(__file__).parent
BAD = str(HERE / "fixtures" / "bad.yaml")
TEMPLATES = sorted((HERE.parent / "ypapi" / "templates").glob("*.yaml"))


def test_free_has_six_rules_and_three_templates():
    assert [r.code for r in active_rules()] == ["S001", "S002", "S003", "S004", "S005", "S006"]
    assert template_names() == ["crud-resource", "minimal", "problem-details-errors"]


def test_free_source_has_no_pro_rules():
    import ypapi.rules as rules

    names = [n for n in dir(rules) if n.startswith("r_")]
    assert sorted(names) == ["r_info", "r_operation_id", "r_path_params", "r_paths", "r_refs", "r_version"]


def test_bad_fixture_errors():
    found = {f.rule for f in check(load_document(BAD))}
    assert found == {"S002", "S003", "S004", "S005", "S006"}


@pytest.mark.parametrize("template", TEMPLATES, ids=lambda p: p.stem)
def test_templates_clean(template):
    assert check(load_document(template)) == []


def test_cli(tmp_path, capsys):
    assert main(["lint", BAD]) == 1
    target = tmp_path / "openapi.yaml"
    assert main(["init", "minimal", "-o", str(target)]) == 0
    assert main(["lint", "--strict", str(target)]) == 0
    assert main(["rules"]) == 0
    assert "S006" in capsys.readouterr().out
