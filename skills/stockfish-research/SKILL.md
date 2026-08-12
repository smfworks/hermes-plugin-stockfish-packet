---
name: stockfish-research
description: "Use when doing grounded place/domain research. Claim-citation packets + oppose pass."
version: 1.0.0
author: SMF Works / Team Skrei
license: MIT
metadata:
  hermes:
    tags: [research, citations, lofoten, stockfish, grounded]
    related_skills: [grounded-citations, research-workflow, arxiv]
---

# Stockfish Research

## Overview

Produce research that cures like Lofoten stockfish: hung in cold wind (public sources), unsalted by hype, durable enough to ship into blogs, skills, and decisions.

Uses the `stockfish-packet` plugin schema `smf.stockfish_packet.v1`.

## When to Use

- Place / culture / history / systems research that will be cited in public writing
- Any brief where research claims must survive oppositional review
- Multi-agent Scout role outputs

Don't use for: pure code debugging, or vibes-only ideation with no truth claims.

## Procedure

1. `stockfish_init_packet` with title, topic, optional place.
2. Gather sources via web_search / web_extract. Each source: id, url, title, accessed_at.
3. Write atomic claims with support source ids and confidence 0..1.
4. `stockfish_validate` until ok=true (grade curing or stockfish).
5. `stockfish_oppose_claims` — fix weasel, single-domain clusters, compound claims.
6. Record method.tools and bridge_mode.
7. Draft prose only from packet claims.

## Completion criteria

- [ ] validate ok
- [ ] oppose status pass or pass_with_fixes with fixes applied
- [ ] every public factual sentence maps to a claim id
- [ ] open_questions listed rather than silently guessed

## Pitfalls

1. Wikipedia-only monoculture (single_domain finding).
2. Tourism copy treated as primary historical evidence.
3. Contested indigenous / political claims without contest_note.
4. Confusing the chess engine Stockfish with torrfisk — this skill is the fish.

## Lofoten anchors (example domain)

Skrei migrations, Vagar/Kabelvag, Borg longhouse (~83m), rorbu, Moskstraumen, Gulf Stream mildness north of Arctic Circle, Sami presence in broader Nordland/Sapmi context — each needs its own claim+source row.
