# Specs

## Source of truth

- **openapi** canonical contract the SDK targets. May be edited (fixes, examples, clarifications), but changes must be validated + diffed.
- **vendor** immutable artifacts (raw drops). **Never edit**.

## Vendored upstream artifacts

Do not edit these files; if they change upstream, add a new version and update hashes.

| File                               | Notes                             | SHA256                                                             |
| ---------------------------------- | --------------------------------- | ------------------------------------------------------------------ |
| `pos-api-3.0.1-user-manual.pdf`    | POS API 3.0 user manual           | `b90a19cdb73d29e57510ddf64253ff48f159e3074f634d86111a59473d662e12` |
| `gs1_gs1.xlsx`                     | GS1 barcode reference data        | `7f4a5b8d38c2839405aec84a9dcad4c52e3dc9fe0d23b8ad3de5ea1f3b37b740` |
| `st_posservice_3.0.12-staging.zip` | POS API 3.0.12 staging installers | `93bb6b5d37c5be74429181dfc929ff3b4585fab45ae25761fb364118c4f7259e` |

Unzipped installers are under `spec/vendor/st_posservice_3.0.12-staging/`.
