"""Checks for API description documents (versions 3.0 and 3.1)."""

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")
PARAM = re.compile(r"{([^}/]+)}")


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str  # "error" or "warning"
    path: str
    message: str


@dataclass(frozen=True)
class Rule:
    code: str
    name: str
    severity: str
    summary: str
    check: Callable[[dict], Iterator[tuple[str, str]]]


def operations(doc: dict) -> Iterator[tuple[str, str, dict, dict]]:
    paths = doc.get("paths") or {}
    if not isinstance(paths, dict):
        return
    for route, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method in METHODS:
            op = item.get(method)
            if isinstance(op, dict):
                yield route, method, op, item


def where(route: str, method: str) -> str:
    return f"paths.{route}.{method}"


def r_version(doc):
    version = str(doc.get("openapi", ""))
    if not re.match(r"^3\.(0|1)\.\d+$", version):
        yield "openapi", f"'openapi' must be 3.0.x or 3.1.x, found {version or 'nothing'}"


def r_info(doc):
    info = doc.get("info")
    if not isinstance(info, dict):
        yield "info", "'info' object is missing"
        return
    for key in ("title", "version"):
        if not info.get(key):
            yield f"info.{key}", f"'info.{key}' is required"


def r_paths(doc):
    paths = doc.get("paths")
    if not doc.get("webhooks") and (not isinstance(paths, dict) or not paths):
        yield "paths", "document has no paths (or webhooks)"
        return
    for route in paths or {}:
        if not str(route).startswith("/"):
            yield f"paths.{route}", "path must start with '/'"
        elif len(route) > 1 and route.endswith("/"):
            yield f"paths.{route}", "remove the trailing '/'"


def r_operation_id(doc):
    seen: dict[str, str] = {}
    for route, method, op, _ in operations(doc):
        op_id = op.get("operationId")
        if not op_id:
            yield where(route, method), "operation has no operationId"
        elif op_id in seen:
            yield where(route, method), f"operationId '{op_id}' is also used by {seen[op_id]}"
        else:
            seen[op_id] = where(route, method)


def _params(op: dict, item: dict, doc: dict) -> list[dict]:
    out = []
    for p in list(item.get("parameters") or []) + list(op.get("parameters") or []):
        if isinstance(p, dict) and "$ref" in p:
            p = resolve(doc, p["$ref"]) or {}
        if isinstance(p, dict):
            out.append(p)
    return out


def r_path_params(doc):
    for route, method, op, item in operations(doc):
        in_template = set(PARAM.findall(route))
        declared = {p.get("name") for p in _params(op, item, doc) if p.get("in") == "path"}
        for name in sorted(in_template - declared):
            yield where(route, method), f"path parameter '{name}' is not declared"
        for name in sorted(declared - in_template):
            yield where(route, method), f"declared path parameter '{name}' is not in the path"
        for p in _params(op, item, doc):
            if p.get("in") == "path" and p.get("required") is not True:
                yield where(route, method), f"path parameter '{p.get('name')}' must have required: true"


def resolve(doc: dict, ref: str) -> Any:
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return None
    node: Any = doc
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def walk_refs(node: Any, trail: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                yield trail or "$", value
            else:
                yield from walk_refs(value, f"{trail}.{key}" if trail else str(key))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from walk_refs(value, f"{trail}[{i}]")


def r_refs(doc):
    for trail, ref in walk_refs(doc):
        if ref.startswith("#/") and resolve(doc, ref) is None:
            yield trail, f"$ref '{ref}' does not resolve"


RULES: list[Rule] = [
    Rule("S001", "version", "error", "openapi field is 3.0.x or 3.1.x", r_version),
    Rule("S002", "info", "error", "info.title and info.version are present", r_info),
    Rule("S003", "paths", "error", "paths exist, start with '/', no trailing slash", r_paths),
    Rule("S004", "operation-id", "error", "every operation has a unique operationId", r_operation_id),
    Rule("S005", "refs", "error", "every local $ref resolves", r_refs),
    Rule("S006", "path-params", "error", "path template and path parameters match", r_path_params),
]


def active_rules() -> list[Rule]:
    """The free edition ships only rules S001-S006."""
    return list(RULES)


def check(doc: Any, disabled: set[str] | None = None) -> list[Finding]:
    if not isinstance(doc, dict):
        return [Finding("S000", "error", "$", "document root must be a mapping")]
    disabled = disabled or set()
    findings = []
    for rule in active_rules():
        if rule.code in disabled or rule.name in disabled:
            continue
        for path, message in rule.check(doc):
            findings.append(Finding(rule.code, rule.severity, path, message))
    return findings
