from packet import init_packet, validate_packet, oppose_claims


def test_init_and_empty_validate():
    p = init_packet("T", "topic", place="Lofoten")
    v = validate_packet(p)
    assert v["ok"] is True
    assert v["grade"] in ("wet", "curing", "stockfish")


def test_broken_support():
    p = init_packet("T", "t")
    p["claims"] = [{"id": "c1", "text": "X", "support": ["missing"]}]
    v = validate_packet(p)
    assert v["ok"] is False


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
