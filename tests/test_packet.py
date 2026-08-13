from packet import (
    __version__,
    init_packet,
    load_packet,
    oppose_claims,
    save_packet,
    safe_user_path,
    validate_packet,
)
import json
import importlib.util
from pathlib import Path


def _load_plugin():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("stockfish_plugin", root / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_init_and_empty_validate():
    p = init_packet("T", "topic", place="Lofoten")
    v = validate_packet(p)
    assert v["ok"] is True
    assert v["version"] == __version__
    assert v["grade"] in ("wet", "curing", "stockfish")


def test_init_requires_title():
    try:
        init_packet("", "topic")
        assert False
    except ValueError:
        pass


def test_broken_support():
    p = init_packet("T", "t")
    p["claims"] = [{"id": "c1", "text": "X", "support": ["missing"]}]
    v = validate_packet(p)
    assert v["ok"] is False
    assert v["grade"] == "rotten"


def test_duplicate_ids_and_bad_url():
    p = init_packet("T", "t")
    p["sources"] = [
        {"id": "s1", "url": "ftp://nope", "title": "A"},
        {"id": "s1", "url": "https://example.com", "title": "B"},
    ]
    v = validate_packet(p)
    paths = {e["path"] for e in v["errors"]}
    assert "sources[0].url" in paths
    assert any("duplicate" in e["message"] for e in v["errors"])


def test_orphan_and_contested_warnings():
    p = init_packet("T", "t")
    p["sources"] = [
        {"id": "s1", "url": "https://example.com/a", "title": "A", "accessed_at": "2026-08-13"},
        {"id": "s2", "url": "https://example.com/b", "title": "B", "accessed_at": "2026-08-13"},
    ]
    p["claims"] = [
        {
            "id": "c1",
            "text": "A short claim.",
            "support": ["s1"],
            "confidence": 0.4,
            "status": "contested",
        }
    ]
    v = validate_packet(p)
    assert v["ok"] is True
    assert v["grade"] == "curing"
    msgs = " ".join(w["message"] for w in v["warnings"])
    assert "orphan" in msgs
    assert "contested" in msgs


def test_good_packet_stockfish_grade():
    p = init_packet("Lofoten", "geography")
    p["sources"] = [
        {
            "id": "s1",
            "url": "https://en.wikipedia.org/wiki/Lofoten",
            "title": "Lofoten",
            "accessed_at": "2026-08-12",
        },
        {
            "id": "s2",
            "url": "https://www.britannica.com/place/Lofoten",
            "title": "Britannica",
            "accessed_at": "2026-08-12",
        },
    ]
    p["claims"] = [
        {
            "id": "c1",
            "text": "Lofoten lies north of the Arctic Circle in Nordland, Norway.",
            "support": ["s1", "s2"],
            "confidence": 0.95,
        }
    ]
    v = validate_packet(p)
    assert v["ok"] is True
    assert v["grade"] == "stockfish"
    opp = oppose_claims(p)
    assert opp["status"] in ("pass", "pass_with_fixes", "fail")
    assert opp["ok"] is True


def test_weasel_opposition():
    p = init_packet("T", "t")
    p["sources"] = [{"id": "s1", "url": "https://example.com/a", "title": "A"}]
    p["claims"] = [
        {
            "id": "c1",
            "text": "Everyone knows Lofoten will revolutionize tourism forever.",
            "support": ["s1"],
            "confidence": 0.99,
        }
    ]
    opp = oppose_claims(p)
    codes = {f["code"] for f in opp["findings"]}
    assert "weasel" in codes or "absolute_high_conf" in codes


def test_single_domain_opposition():
    p = init_packet("T", "t")
    p["sources"] = [
        {"id": "s1", "url": "https://example.com/a", "title": "A"},
        {"id": "s2", "url": "https://example.com/b", "title": "B"},
    ]
    p["claims"] = [
        {
            "id": "c1",
            "text": "A reasonably long but atomic claim about weather.",
            "support": ["s1", "s2"],
            "confidence": 0.5,
        }
    ]
    opp = oppose_claims(p)
    codes = {f["code"] for f in opp["findings"]}
    assert "single_domain" in codes


def test_safe_path_blocks_etc():
    try:
        safe_user_path("/etc/passwd")
        assert False
    except ValueError:
        pass


def test_save_load_roundtrip(tmp_path):
    p = init_packet("T", "t")
    dest = tmp_path / "pkt.json"
    wrote = save_packet(str(dest), p)
    loaded = load_packet(wrote)
    assert loaded["title"] == "T"
    assert loaded["schema"] == "smf.stockfish_packet.v1"


def test_load_rejects_non_object(tmp_path):
    dest = tmp_path / "arr.json"
    dest.write_text("[1,2]\n")
    try:
        load_packet(str(dest))
        assert False
    except ValueError:
        pass


def test_oppose_does_not_write_without_flag(tmp_path):
    plug = _load_plugin()
    dest = tmp_path / "p.json"
    save_packet(str(dest), init_packet("T", "t"))
    before = dest.read_text()
    raw = json.loads(plug.handle_oppose({"path": str(dest)}))
    assert "wrote" not in raw
    assert dest.read_text() == before
    raw2 = json.loads(plug.handle_oppose({"path": str(dest), "write": True}))
    assert raw2.get("wrote")
    assert dest.read_text() != before


def test_bool_confidence_rejected():
    p = init_packet("T", "t")
    p["sources"] = [{"id": "s1", "url": "https://example.com/a", "title": "A"}]
    p["claims"] = [{"id": "c1", "text": "X", "support": ["s1"], "confidence": True}]
    v = validate_packet(p)
    assert v["ok"] is False


def test_sources_must_be_list():
    p = init_packet("T", "t")
    p["sources"] = "https://example.com"
    v = validate_packet(p)
    assert v["ok"] is False
    assert any(e["path"] == "sources" for e in v["errors"])


def test_handler_refuses_protected_write():
    plug = _load_plugin()
    raw = json.loads(
        plug.handle_init(
            {"title": "T", "topic": "t", "path": "/etc/stockfish-should-fail.json"}
        )
    )
    assert raw["ok"] is False
    assert "protected" in raw["error"] or "invalid" in raw["error"]
