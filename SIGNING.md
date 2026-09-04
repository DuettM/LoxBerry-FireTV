# Release signing

Fire TV Control uses SHA-256 and Ed25519 signatures for published update ZIP files.

## Current trust key

Public Ed25519 key used by `bin/secure_update.py` from v0.3.11 onward:

`ffe30e90c006712a29dae4e3cdbbdf81c745d64b9a002a263444ae98fc088eb1`

The corresponding private key must **never** be committed to this repository, attached to an issue, pasted into logs, or included in plugin packages.

## GitHub Actions secret

The private signing key is stored once in the repository as the Actions secret:

`FIRETV_ED25519_PRIVATE_KEY`

The value must be the complete PEM private key including the BEGIN/END lines. GitHub masks the secret in workflow logs. Keep an additional encrypted/offline backup of the key.

If the private key is lost, existing installations cannot validate releases signed by a replacement key. A key rotation then requires a one-time manual plugin update that embeds the new public key.

If the private key is exposed, treat it as compromised immediately. Stop publishing with it, rotate the trust key, and document the incident and migration path.

## Automated release procedure

1. Finalize source code, update `VERSION` in `plugin.cfg`, and add the matching section to `CHANGELOG.md`.
2. Trigger `Publish FireTV Release` from GitHub Actions or update `.publish-trigger-firetv-current`.
3. GitHub Actions validates the sources and refuses an already existing version.
4. The workflow builds the deterministic ZIP and SHA-256 checksum.
5. The ZIP is signed automatically with the private key from `FIRETV_ED25519_PRIVATE_KEY`.
6. Before publishing, the workflow derives the public key from the secret and checks that it matches the public key embedded in `bin/secure_update.py`.
7. The generated Ed25519 signature is verified again with the plugin verifier.
8. GitHub creates the Release with ZIP, `.sha256` and `.sig`.
9. `release.cfg` and `prerelease.cfg` are updated automatically to the new release and committed back to `main`.
10. The complete signed package is also retained as a GitHub Actions artifact.

Historical files under `release-signatures/` may remain for traceability, but new releases no longer require manually generated signature files in the repository.

## Important

Never reuse a version number for different ZIP contents. Any source or packaged documentation change alters the ZIP and therefore requires a new plugin version.
