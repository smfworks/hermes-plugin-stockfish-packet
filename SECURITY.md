# Security Policy

## Reporting

Use GitHub Security Advisories on this repository. Do not open a public issue for path-escape or secret-handling bugs.

## Guards

- `safe_user_path` rejects null bytes and writes under `/etc`, `/proc`, `/sys`, `/dev`, `/root`, `/boot`.
- Packet files are capped at 2MB.
- Saves are atomic (`mkstemp` + `os.replace`).
- Paths are operator input. Do not point this plugin at untrusted trees.

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.1.x   | Yes |
| 1.0.x   | Best-effort |
