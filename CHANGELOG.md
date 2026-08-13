# Changelog

## 1.1.1 — 2026-08-13

Lookout follow-up.

- `stockfish_oppose_claims` writes only when `write=true`
- Empty `packet={}` is a packet, not a missing argument
- Current Hermes CLI/skill registration signatures
- Never parse process argv as plugin CLI

## 1.1.0 — 2026-08-13

Production-ready pass.

- Version on validate/oppose/error payloads
- Path guard + 2MB load cap + atomic save
- `init_packet` requires non-empty title/topic
- Handler error envelope `{ok, error, version}`
- Full MIT license, CI, Dependabot, SECURITY/ARCHITECTURE/CONTRIBUTING
- Expanded tests (duplicates, orphans, single-domain, protected writes)

## 1.0.0 — 2026-08-12

Lofoten sprint ship.
