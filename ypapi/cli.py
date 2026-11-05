"""Command line: ypapi lint | init | list | rules."""

import argparse
import json
import sys
from importlib import resources
from pathlib import Path

from ypapi import EDITION, __version__
from ypapi.loader import LoadError, load_document
from ypapi.rules import active_rules, check


def template_names() -> list[str]:
    folder = resources.files("ypapi") / "templates"
    return sorted(p.name.removesuffix(".yaml") for p in folder.iterdir() if p.name.endswith(".yaml"))


def cmd_lint(args: argparse.Namespace) -> int:
    disabled = set(filter(None, (args.disable or "").split(",")))
    status, report = 0, []
    for file in args.files:
        try:
            findings = check(load_document(file), disabled)
        except LoadError as exc:
            print(f"error: {exc}", file=sys.stderr)
            status = 2
            continue
        errors = [f for f in findings if f.severity == "error"]
        warnings = [f for f in findings if f.severity == "warning"]
        if errors or (args.strict and warnings):
            status = max(status, 1)
        if args.format == "json":
            report.append({"file": file, "findings": [f.__dict__ for f in findings]})
            continue
        for f in findings:
            print(f"{file}: {f.severity} {f.rule} {f.path}: {f.message}")
        print(f"{file}: {len(errors)} error(s), {len(warnings)} warning(s)")
    if args.format == "json":
        print(json.dumps(report, indent=2))
    return status


def cmd_init(args: argparse.Namespace) -> int:
    if args.template not in template_names():
        print(f"error: unknown template '{args.template}'. Try: ypapi list", file=sys.stderr)
        return 2
    target = Path(args.output)
    if target.exists() and not args.force:
        print(f"error: {target} exists (use --force to overwrite)", file=sys.stderr)
        return 2
    text = (resources.files("ypapi") / "templates" / f"{args.template}.yaml").read_text(encoding="utf-8")
    if args.title:
        text = text.replace("YourBrand", args.title)
    target.write_text(text, encoding="utf-8")
    print(f"wrote {target} from template '{args.template}'")
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    for name in template_names():
        print(name)
    return 0


def cmd_rules(_: argparse.Namespace) -> int:
    for rule in active_rules():
        print(f"{rule.code}  {rule.severity:<7}  {rule.name:<18}  {rule.summary}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ypapi", description="Templates and checker for API description files.")
    parser.add_argument("--version", action="version", version=f"ypapi {__version__} ({EDITION})")
    sub = parser.add_subparsers(dest="command", required=True)
    lint = sub.add_parser("lint", help="check one or more YAML/JSON files")
    lint.add_argument("files", nargs="+")
    lint.add_argument("--format", choices=["text", "json"], default="text")
    lint.add_argument("--strict", action="store_true", help="fail on warnings too")
    lint.add_argument("--disable", help="comma-separated rule codes or names to skip")
    lint.set_defaults(func=cmd_lint)
    init = sub.add_parser("init", help="write a template to a file")
    init.add_argument("template")
    init.add_argument("-o", "--output", default="openapi.yaml")
    init.add_argument("--title", help="replace the demo brand name")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)
    sub.add_parser("list", help="list templates").set_defaults(func=cmd_list)
    sub.add_parser("rules", help="list rules").set_defaults(func=cmd_rules)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
