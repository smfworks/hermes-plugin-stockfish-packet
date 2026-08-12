"""Stockfish research packet schema + validators."""
from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

REQUIRED_TOP = ["title", "topic", "claims", "sources", "method"]
CLAIM_REQUIRED = ["id", "text", "support"]
SOURCE_REQUIRED = ["id", "url", "title"]
URL_RE = re.compile(r"^https?://", re.I)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def init_packet(title: str, topic: str, place: Optional[str] = None) -> Dict[str, Any]:
    return {
        "schema": "smf.stockfish_packet.v1",
        "title": title,
        "topic": topic,
        "place": place,
        "created_at": utc_now(),
        "method": {
            "bridge_mode": "unknown",
            "tools": [],
            "notes": "Fill method.tools with web_search/web_extract/etc.",
        },
        "sources": [],
        "claims": [],
        "open_questions": [],
        "opposition": {"status": "not_run", "findings": []},
        "metaphor": {
            "name": "stockfish",
            "note": (
                "Lofoten stockfish (torrfisk) is unsalted cod dried in cold wind on hjell. "
                "A claim without a source is wet fish left in the hold."
            ),
        },
    }


def _err(path: str, msg: str, severity: str = "error") -> Dict[str, str]:
    return {"path": path, "message": msg, "severity": severity}


def validate_packet(packet: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    if not isinstance(packet, dict):
        return {
            "ok": False,
            "errors": [_err("$", "packet must be an object")],
            "warnings": [],
            "stats": {},
        }

    for k in REQUIRED_TOP:
        if k not in packet:
            errors.append(_err(k, f"missing required field '{k}'"))

    sources = packet.get("sources") if isinstance(packet.get("sources"), list) else []
    claims = packet.get("claims") if isinstance(packet.get("claims"), list) else []
    source_ids = set()

    for i, s in enumerate(sources):
        if not isinstance(s, dict):
            errors.append(_err(f"sources[{i}]", "must be object"))
            continue
        for rk in SOURCE_REQUIRED:
            if not s.get(rk):
                errors.append(_err(f"sources[{i}].{rk}", "required"))
        sid = s.get("id")
        if sid in source_ids:
            errors.append(_err(f"sources[{i}].id", f"duplicate id {sid}"))
        source_ids.add(sid)
        url = s.get("url") or ""
        if url and not URL_RE.match(url):
            errors.append(_err(f"sources[{i}].url", "must be http(s) URL"))
        else:
            try:
                host = urlparse(url).netloc
                if url and not host:
                    errors.append(_err(f"sources[{i}].url", "missing host"))
            except Exception:
                errors.append(_err(f"sources[{i}].url", "unparseable"))
        if not s.get("accessed_at"):
            warnings.append(
                _err(f"sources[{i}].accessed_at", "missing access timestamp", "warning")
            )

    claim_ids = set()
    unsupported = 0
    for i, c in enumerate(claims):
        if not isinstance(c, dict):
            errors.append(_err(f"claims[{i}]", "must be object"))
            continue
        for rk in CLAIM_REQUIRED:
            if rk not in c:
                errors.append(_err(f"claims[{i}].{rk}", "required"))
        cid = c.get("id")
        if cid in claim_ids:
            errors.append(_err(f"claims[{i}].id", f"duplicate id {cid}"))
        claim_ids.add(cid)
        support = c.get("support") or []
        if not isinstance(support, list) or len(support) == 0:
            errors.append(_err(f"claims[{i}].support", "need >=1 source id"))
            unsupported += 1
            continue
        missing = [sid for sid in support if sid not in source_ids]
        if missing:
            errors.append(
                _err(f"claims[{i}].support", f"unknown source ids: {missing}")
            )
        conf = c.get("confidence")
        if conf is not None:
            try:
                cf = float(conf)
                if not 0.0 <= cf <= 1.0:
                    errors.append(_err(f"claims[{i}].confidence", "must be 0..1"))
            except (TypeError, ValueError):
                errors.append(_err(f"claims[{i}].confidence", "must be number"))
        if c.get("status") == "contested" and not c.get("contest_note"):
            warnings.append(
                _err(
                    f"claims[{i}].contest_note",
                    "contested claim lacks note",
                    "warning",
                )
            )

    if len(claims) == 0:
        warnings.append(_err("claims", "no claims yet", "warning"))
    if len(sources) == 0:
        warnings.append(_err("sources", "no sources yet", "warning"))

    used = set()
    for c in claims:
        if isinstance(c, dict):
            for sid in c.get("support") or []:
                used.add(sid)
    orphans = [sid for sid in source_ids if sid not in used]
    if orphans:
        warnings.append(
            _err("sources", f"orphan sources unused by claims: {orphans}", "warning")
        )

    stats = {
        "claims": len(claims),
        "sources": len(sources),
        "unsupported_claims": unsupported,
        "orphan_sources": len(orphans),
        "error_count": len(errors),
        "warning_count": len(warnings),
    }
    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
        "grade": _grade(stats, errors, warnings),
    }


def _grade(stats, errors, warnings) -> str:
    if errors:
        return "rotten"
    if stats.get("claims", 0) == 0:
        return "wet"
    if warnings:
        return "curing"
    return "stockfish"


def oppose_claims(packet: Dict[str, Any]) -> Dict[str, Any]:
    findings: List[Dict[str, str]] = []
    claims = packet.get("claims") or []
    sources = {
        s.get("id"): s for s in (packet.get("sources") or []) if isinstance(s, dict)
    }

    weasel = re.compile(
        r"\b(some say|many believe|it is known|obviously|clearly|everyone knows|revolutionize)\b",
        re.I,
    )
    absolute = re.compile(r"\b(always|never|the only|unprecedented|perfect)\b", re.I)

    for c in claims:
        if not isinstance(c, dict):
            continue
        cid = c.get("id", "?")
        text = c.get("text") or ""
        support = c.get("support") or []
        if weasel.search(text):
            findings.append(
                {
                    "claim_id": cid,
                    "code": "weasel",
                    "detail": "Weasel / empty authority language",
                }
            )
        if absolute.search(text) and float(c.get("confidence") or 0) >= 0.9:
            findings.append(
                {
                    "claim_id": cid,
                    "code": "absolute_high_conf",
                    "detail": "Absolute wording with high confidence",
                }
            )
        if len(support) == 1:
            findings.append(
                {
                    "claim_id": cid,
                    "code": "single_source",
                    "detail": "Only one supporting source — seek corroboration",
                }
            )
        hosts = []
        for sid in support:
            u = (sources.get(sid) or {}).get("url") or ""
            hosts.append(urlparse(u).netloc)
        if hosts and len(set(hosts)) == 1 and len(support) > 1:
            findings.append(
                {
                    "claim_id": cid,
                    "code": "single_domain",
                    "detail": f"All support from {hosts[0]}",
                }
            )
        if len(text) > 400:
            findings.append(
                {
                    "claim_id": cid,
                    "code": "claim_too_long",
                    "detail": "Claim should be atomic; split compound assertions",
                }
            )
        if c.get("confidence") is None:
            findings.append(
                {
                    "claim_id": cid,
                    "code": "no_confidence",
                    "detail": "Missing confidence 0..1",
                }
            )

    if not claims:
        findings.append(
            {"claim_id": "-", "code": "empty", "detail": "No claims to oppose"}
        )

    status = (
        "pass"
        if not findings
        else ("pass_with_fixes" if len(findings) < 5 else "fail")
    )
    if any(f["code"] == "empty" for f in findings):
        status = "fail"

    out = deepcopy(packet)
    out["opposition"] = {
        "status": status,
        "ran_at": utc_now(),
        "findings": findings,
        "method": "heuristic-v1",
    }
    return {
        "status": status,
        "findings": findings,
        "packet": out,
        "summary": f"Opposition {status}: {len(findings)} finding(s).",
    }


def load_packet(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_packet(path: str, packet: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(packet, f, indent=2, ensure_ascii=False)
        f.write("\n")
