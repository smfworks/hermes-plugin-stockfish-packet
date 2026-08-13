"""stockfish-packet plugin."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

try:
    from . import packet as pk
except ImportError:
    import packet as pk

logger = logging.getLogger(__name__)

VALIDATE_SCHEMA = {
    "name": "stockfish_validate",
    "description": (
        "Validate a grounded research packet (JSON object or path). Checks "
        "claim-source integrity, URL shape, orphans, and returns grade "
        "rotten|wet|curing|stockfish."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "packet": {"type": "object", "description": "Inline packet object"},
            "path": {"type": "string", "description": "Path to packet JSON file"},
        },
    },
}

INIT_SCHEMA = {
    "name": "stockfish_init_packet",
    "description": "Create an empty stockfish research packet scaffold (smf.stockfish_packet.v1).",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "topic": {"type": "string"},
            "place": {"type": "string"},
            "path": {"type": "string", "description": "Optional path to write JSON"},
        },
        "required": ["title", "topic"],
    },
}

OPPOSE_SCHEMA = {
    "name": "stockfish_oppose_claims",
    "description": (
        "Run heuristic oppositional assessment on packet claims (weasel words, "
        "single-source, single-domain, absolute+high-conf)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "packet": {"type": "object"},
            "path": {"type": "string"},
            "write": {
                "type": "boolean",
                "description": "If true and path is set, write opposition back to the file. Default false.",
            },
        },
    },
}


def _err(exc: Exception) -> str:
    return json.dumps({"ok": False, "error": str(exc), "version": pk.__version__})


def _load(args: dict) -> dict:
    if "packet" in args and args["packet"] is not None:
        if not isinstance(args["packet"], dict):
            raise ValueError("packet must be an object")
        return args["packet"]
    path = args.get("path")
    if not path:
        raise ValueError("Provide packet object or path")
    return pk.load_packet(path)


def handle_validate(args: dict, **kwargs) -> str:
    del kwargs
    try:
        p = _load(args)
        return json.dumps(pk.validate_packet(p), indent=2)
    except Exception as e:
        return _err(e)


def handle_init(args: dict, **kwargs) -> str:
    del kwargs
    try:
        p = pk.init_packet(args.get("title", ""), args.get("topic", ""), args.get("place"))
        path = args.get("path")
        if path:
            wrote = pk.save_packet(path, p)
            return json.dumps(
                {"ok": True, "version": pk.__version__, "path": wrote, "packet": p},
                indent=2,
            )
        p_out = dict(p)
        p_out["ok"] = True
        p_out["version"] = pk.__version__
        return json.dumps(p_out, indent=2)
    except Exception as e:
        return _err(e)


def handle_oppose(args: dict, **kwargs) -> str:
    del kwargs
    try:
        p = _load(args)
        result = pk.oppose_claims(p)
        path = args.get("path")
        write = args.get("write") in (True, "true", "1", "yes")
        if write and path and result.get("packet"):
            result["wrote"] = pk.save_packet(path, result["packet"])
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return _err(e)


def _cli(argv: Any) -> None:
    import argparse
    import sys

    parser = argparse.ArgumentParser(prog="hermes stockfish")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_init = sub.add_parser("init")
    p_init.add_argument("--title", required=True)
    p_init.add_argument("--topic", required=True)
    p_init.add_argument("--place")
    p_init.add_argument("--out", required=True)
    p_val = sub.add_parser("validate")
    p_val.add_argument("path")
    p_op = sub.add_parser("oppose")
    p_op.add_argument("path")
    p_op.add_argument("--write", action="store_true")
    sub.add_parser("selftest")
    sub.add_parser("version")
    ns = parser.parse_args(list(argv) if isinstance(argv, list) else [])
    try:
        if ns.cmd == "version":
            print(pk.__version__)
            return
        if ns.cmd == "init":
            p = pk.init_packet(ns.title, ns.topic, ns.place)
            print(pk.save_packet(ns.out, p))
        elif ns.cmd == "validate":
            print(json.dumps(pk.validate_packet(pk.load_packet(ns.path)), indent=2))
        elif ns.cmd == "oppose":
            r = pk.oppose_claims(pk.load_packet(ns.path))
            if ns.write:
                pk.save_packet(ns.path, r["packet"])
            print(
                json.dumps(
                    {
                        "ok": r.get("ok"),
                        "version": r.get("version"),
                        "status": r["status"],
                        "findings": r["findings"],
                        "summary": r["summary"],
                    },
                    indent=2,
                )
            )
        elif ns.cmd == "selftest":
            r = __import__("subprocess").run(
                [sys.executable, "-m", "pytest", str(Path(__file__).parent / "tests"), "-q"]
            )
            raise SystemExit(r.returncode)
    except SystemExit:
        raise
    except Exception as e:
        print(_err(e), file=sys.stderr)
        raise SystemExit(1)


def _cli_setup(subparser: Any) -> None:
    subparser.add_argument("rest", nargs="*")


def _cli_handler(ns: Any) -> int:
    rest = list(getattr(ns, "rest", []) or [])
    try:
        _cli(rest)
        return 0
    except SystemExit as e:
        code = e.code
        if code is None:
            return 0
        return int(code) if not isinstance(code, int) else code


def register(ctx):
    ctx.register_tool(
        name="stockfish_validate",
        toolset="stockfish",
        schema=VALIDATE_SCHEMA,
        handler=handle_validate,
    )
    ctx.register_tool(
        name="stockfish_init_packet",
        toolset="stockfish",
        schema=INIT_SCHEMA,
        handler=handle_init,
    )
    ctx.register_tool(
        name="stockfish_oppose_claims",
        toolset="stockfish",
        schema=OPPOSE_SCHEMA,
        handler=handle_oppose,
    )
    ctx.register_command(
        "stockfish", lambda raw: _slash(raw), description="Stockfish packet: validate path"
    )
    try:
        ctx.register_cli_command(
            name="stockfish",
            help="Grounded research packet tools",
            setup_fn=_cli_setup,
            handler_fn=_cli_handler,
            description="Stockfish research packets",
        )
    except TypeError:
        try:
            ctx.register_cli_command("stockfish", _cli)
        except Exception as e:
            logger.warning("cli: %s", e)
    skill = Path(__file__).parent / "skills" / "stockfish-research"
    if (skill / "SKILL.md").is_file():
        try:
            ctx.register_skill(name="stockfish-research", path=skill / "SKILL.md")
        except TypeError:
            try:
                ctx.register_skill(str(skill))
            except Exception as e:
                logger.debug("%s", e)


def _slash(raw: str) -> str:
    parts = (raw or "").split()
    if parts and parts[0] == "version":
        return json.dumps({"ok": True, "version": pk.__version__})
    if len(parts) >= 2 and parts[0] == "validate":
        return handle_validate({"path": parts[1]})
    if len(parts) >= 2 and parts[0] == "oppose":
        return handle_oppose({"path": parts[1]})
    return json.dumps(
        {
            "ok": False,
            "error": "usage: /stockfish validate <path> | oppose <path> | version",
            "version": pk.__version__,
        }
    )
