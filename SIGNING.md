# Release signing

Fire TV Control uses SHA-256 and Ed25519 signatures for published update ZIP files.

## Current trust key

Public Ed25519 key used by `bin/secure_update.py` from v0.3.11 onward:

`ffe30e90c006712a29dae4e3cdbbdf81c745d64b9a002a263444ae98fc088eb1`

The corresponding private key must **never** be committed to this repository, attached to an issue, pasted into logs, or included in plugin packages.

## Private-key storage

Keep at least one encrypted/offline backup of the private signing key. Recommended locations are an encrypted password-manager/file vault and a separate offline backup. Access should be limited to the release maintainer.

If the private key is lost, existing installations cannot validate releases signed by a replacement key. A key rotation then requires a one-time manual plugin update that embeds the new public key.

If the private key is exposed, treat it as compromised immediately. Stop publishing with it, rotate the trust key, and document the incident and migration path.

## Release procedure

1. Finalize source code, version, README and changelog before signing.
2. Build the deterministic release ZIP with the repository release workflow.
3. Calculate SHA-256 over the exact ZIP that will be published.
4. Sign the exact ZIP bytes with the current Ed25519 private key.
5. Store only the resulting `.sha256` and `.sig` files under `release-signatures/`.
6. Run the publish workflow. It must rebuild the ZIP, compare the SHA-256 value and verify the Ed25519 signature before creating the GitHub Release.
7. Only after the GitHub Release exists, point `release.cfg` and `prerelease.cfg` to that release.

## Important

Never create a signature for a different ZIP with the same version number. Any source or packaged documentation change alters the ZIP and therefore requires a new signature; normally it should also use a new plugin version.
