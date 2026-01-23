# ebarimt-pos-sdk (POS API 3.0)

Python SDK for **Ebarimt POS API 3.0**.

## Principles
- **Contract-first**: OpenAPI is the SDK source of truth.
- **Strict models**: validate inputs/outputs (Pydantic).
- **Explicit errors**: typed exceptions with actionable details.
- **Async-first**: `httpx.AsyncClient`, with an optional sync facade.

## Repo layout
- `spec/vendor/` — upstream artifacts (PDF, excel, installers)
- `spec/openapi/` — OpenAPI spec we maintain (`posapi-3.0.1.yaml`)
- `src/ebarimt_pos/` — library code
- `tests/contract/` — schema/contract tests against a running PosAPI
- `examples/` — runnable examples

## Next steps
1. Review/iterate the OpenAPI contract at `spec/openapi/posapi-3.0.1.yaml`.
2. Implement a single vertical slice: `POST /rest/receipt`.
3. Add contract tests that validate responses against the OpenAPI schema.
