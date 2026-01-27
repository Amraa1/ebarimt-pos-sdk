# Contributing to ebarimt-pos-sdk

First of all — thank you for considering contributing 🙏  
This SDK exists to make integrating with **PosAPI 3.0 (eBarimt)** simple, stable, and predictable.

Because this is a **government API**, we follow a few very intentional design rules.
Please read this document carefully before submitting changes.

---

## 🎯 Project Philosophy

> **Validate structure, not policy.**

Government APIs frequently change **business rules** (dates, conditions, legal logic),
but rarely change **request/response structure**.

This SDK is designed to:

- Be **stable across API rule changes**
- Avoid frequent breaking releases
- Provide excellent developer experience (DX)

---

## ✅ What the SDK SHOULD do

### 1. Strict on JSON shape

- Required vs optional fields must match the official API
- Field names must match exactly
- Unknown fields are rejected (`extra="forbid"`)

### 2. Light validation for obvious mistakes

Allowed:

- Regex for identifiers (e.g. TIN, branchNo, consumerNo)
- Enum validation for fields with fixed values
- Basic numeric sanity (e.g. `>= 0`)

### 3. Accept real-world input

- Use normal Python types (`str`, `int`, `Decimal`, `bool`)
- Accept `int | float | str` for numeric fields where reasonable
- Convert internally when needed (e.g. to `Decimal`)

### 4. Bubble up server errors cleanly

- Do **not** hide or reinterpret server responses
- Preserve error codes, messages, and payloads
- Raise SDK-specific exceptions with original context

---

## ❌ What the SDK MUST NOT do

### 1. Do NOT implement government business rules

Examples of **forbidden validations**:

- Date window checks (e.g. “only between 1–7”)
- Receipt-type conditional rules
- VAT or tax recomputation
- Reference-table validation (district codes, tax product codes, etc.)

These rules:

- Change frequently
- Belong to the server
- Will break the SDK if enforced client-side

### 2. Do NOT over-validate

Avoid:

- Cross-field dependency rules
- Legal interpretations
- Assumptions about future API behavior

If the server can reject it — let the server reject it.

---

## 🧱 Pydantic Model Guidelines

### Use

- `extra="forbid"`
- Enums for documented fixed-value fields
- Regex for stable identifier formats
- `Decimal` for monetary values

### Avoid

- `StrictStr`, `StrictInt`, `StrictFloat`
- Heavy use of `description=`
- Business-rule validators

### Example (good)

```python
branchNo: str = Field(pattern=r"^\d{3}$")
```
