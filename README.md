# hermes-plugin-stockfish-packet

Grounded research packets with claim-citation integrity and a heuristic oppositional pass.

Named for Lofoten stockfish (torrfisk): preservation by exposure.

Current version: **1.1.0**.

## Install

`install` is not `enable`.

```bash
hermes plugins install smfworks/hermes-plugin-stockfish-packet
hermes plugins enable stockfish-packet
```

## Usage

```bash
hermes stockfish init --title "Lofoten" --topic geography --out packet.json
hermes stockfish validate packet.json
hermes stockfish oppose packet.json
hermes stockfish version
```

Agent tools: `stockfish_init_packet`, `stockfish_validate`, `stockfish_oppose_claims`.

Grades: `rotten` | `wet` | `curing` | `stockfish`.

Writes refuse protected system paths. Packet JSON must be an object, max 2MB.

## Develop

```bash
python -m pytest -q
```

## License

MIT — SMF Works
