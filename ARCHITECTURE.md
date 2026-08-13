# Architecture — stockfish-packet

```
register(ctx)
    tools: stockfish_validate | stockfish_init_packet | stockfish_oppose_claims
packet.py
    init_packet / validate_packet / oppose_claims / load_packet / save_packet
```

Schema: `smf.stockfish_packet.v1`.

Grades: `rotten` (errors), `wet` (no claims), `curing` (warnings), `stockfish` (clean).

Opposition is heuristic-v1 (weasel, absolute+high-conf, single source, single domain, too-long, missing confidence). It is not an LLM judge.

Public tool names are stable. Path write/read is guarded. Handlers never raise.
