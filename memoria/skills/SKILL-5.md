---
name: visual-context-capture
description: Extract structured information from photos of documents or forms and save it as reusable context. Use when the user shares an image of a document, form, invoice, contract, ID, receipt, certificate, or any paper-based content and wants to capture its data for future reference. The agent analyzes the image, identifies the document type, extracts all relevant fields, and saves them in the most appropriate format (Markdown, JSON, or YAML) depending on the content structure.
license: MIT
compatibility: opencode
metadata:
  workflow: context-management
  input: image
---

## What I do

- Analyze photos of documents and forms
- Identify the document type automatically
- Extract all relevant fields and data
- Choose the best output format based on content structure
- Save extracted data as a reusable context file

## When to use me

Use when the user says something like:
- "This is an invoice, extract the data"
- "Save this form as context"
- "Here's a contract, capture the key information"
- "This is a receipt, store it"

The user will typically describe what the document is before or after sharing the image.

## How I work

### Step 1 — Identify the document type

Look at the image and the user's description to determine the document category:

| Category | Examples |
|----------|----------|
| Financial | Invoice, receipt, bank statement, budget |
| Legal | Contract, agreement, NDA, certificate |
| Identity | ID card, passport, license, badge |
| Medical | Prescription, report, insurance card |
| Administrative | Form, application, registration, permit |
| Technical | Spec sheet, datasheet, manual page |
| Other | Any document not fitting above |

### Step 2 — Choose output format based on structure

| Document type | Best format | Reason |
|---------------|-------------|--------|
| Structured forms, invoices, receipts | **JSON** | Machine-readable, clear key-value pairs |
| Contracts, reports, dense text | **Markdown** | Preserves narrative and sections |
| Config-like, settings, metadata | **YAML** | Clean, readable, minimal syntax |
| Mixed content | **Markdown with embedded JSON blocks** | Best of both |

### Step 3 — Extract all fields

Extract everything visible and relevant:
- All labeled fields and their values
- Dates, amounts, names, addresses, IDs
- Signatures or stamps noted as `[signature present]` or `[stamp: text]`
- Illegible parts noted as `[illegible]`
- Important clauses or terms in contracts

### Step 4 — Structure and save

#### Example output for an invoice (JSON)

```json
{
  "document_type": "invoice",
  "captured_at": "2026-02-19",
  "source": "photo",
  "data": {
    "invoice_number": "INV-2024-0847",
    "date": "2024-11-15",
    "due_date": "2024-12-15",
    "vendor": {
      "name": "Acme Corp S.L.",
      "tax_id": "B-12345678",
      "address": "Calle Mayor 10, Madrid"
    },
    "client": {
      "name": "Cliente Ejemplo",
      "tax_id": "12345678-A"
    },
    "line_items": [
      { "description": "Servicio de consultoría", "quantity": 10, "unit_price": 150.00, "total": 1500.00 }
    ],
    "subtotal": 1500.00,
    "tax": 315.00,
    "total": 1815.00,
    "currency": "EUR",
    "payment_method": "Transferencia bancaria",
    "notes": ""
  }
}
```

#### Example output for a contract (Markdown)

```markdown
---
document_type: contract
captured_at: 2026-02-19
source: photo
parties:
  - name: Empresa A
    role: proveedor
  - name: Empresa B
    role: cliente
signed: true
date: 2024-10-01
---

## Object
Service provision agreement for software development.

## Duration
12 months from signing date.

## Key clauses
- Confidentiality: 3 years after contract termination
- Penalty for delay: 1% per week, max 10%
- Jurisdiction: Madrid courts

## Signatures
- Empresa A: [signature present]
- Empresa B: [signature present]
```

### Step 5 — Name and save the context file

Use a descriptive filename based on document type and date:

```
context/
  invoice_acme_2024-11-15.json
  contract_empresa-a_2024-10-01.md
  receipt_amazon_2024-02-10.json
  form_registration_2024-09.yaml
```

Always save inside a `context/` folder at the project root unless the user specifies otherwise.

## Quality rules

- **Never invent data**: if a field is not visible, mark it as `null` or `[not visible]`
- **Preserve original values**: don't convert currencies, dates, or units unless asked
- **Flag ambiguity**: if a value is unclear, add a comment like `// verify this value`
- **Be complete**: extract every field visible, even if it seems minor
- **Respect privacy**: remind the user if the document contains sensitive personal data (IDs, medical info) that the file should be stored securely
