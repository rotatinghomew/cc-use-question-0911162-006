from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from governance_vocabulary.concepts.model import ContractError
from governance_vocabulary.curation_workbench import Application, run, verify


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog='governance_vocabulary', description='多国人工智能治理术语本体版本迁移库')
    commands = root.add_subparsers(dest="command", required=True)
    execute = commands.add_parser("run")
    execute.add_argument("--fixture", required=True)
    execute.add_argument("--database", required=True)
    execute.add_argument("--output", required=True)
    check = commands.add_parser("verify")
    check.add_argument("--database", required=True)
    check.add_argument("--output", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--database", required=True)
    report = commands.add_parser("verify-report")
    report.add_argument("--database", required=True)
    report.add_argument("--analysis-id", required=True)
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "run":
            result = run(args.fixture, args.database, args.output)
        elif args.command == "verify":
            result = verify(args.database, args.output)
        elif args.command == "verify-report":
            result = Application(args.database).verify_historical_report(args.analysis_id)
        else:
            result = Application(args.database).inspect()
    except ContractError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
