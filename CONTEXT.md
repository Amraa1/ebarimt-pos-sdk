# Ebarimt POS

The vocabulary of Mongolia's e-receipt system (e-баримт, PosAPI 3.0) as this SDK speaks it: who issues receipts, for whom, and through which POS.

## Parties

**Operator**:
The company that supplies the POS system and issues receipts on merchants' behalf (Хэрэглэгчийн систем нийлүүлэгч).
_Avoid_: system supplier, vendor, provider

**Merchant**:
A business, identified by its TIN, whose sales are receipted through an operator's POS (Борлуулагч).
_Avoid_: seller, CPO, customer

**TIN**:
The 11-digit taxpayer identification number eBarimt uses to identify a merchant; resolved from a register number.
_Avoid_: tax ID, register number (a different, shorter identifier)

## POS

**POS**:
An operator's receipting installation, known to eBarimt by its POS number (`posNo`), under which one or more merchants are registered.
_Avoid_: terminal, device, POS box

## Onboarding

**Merchant registration**:
An operator's request to add one or more merchants to its POS. It is *pending* until eBarimt approves it and *approved* once the merchant's TIN appears in the POS's info; there is no way to query a registration's status directly.
_Avoid_: merchant save, operator merchant, merchant onboarding
