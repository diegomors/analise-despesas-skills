---
name: consolidar-faturas
description: Consolidate and categorize financial invoices and bank statements from any number of banks in various formats (PDF, OFX, CSV, image). Use when the user needs to extract transactions from bank statements, credit card invoices, or financial files; validate totals; standardize data by origin; generate consolidated reports with automatic categorization; and analyze spending trends by category over time. Trigger this skill whenever the user mentions faturas, extratos, consolidar transações, categorizar despesas, bank statements, invoice processing, OFX files, evolução de gastos, tendência de categoria, or any task involving financial document extraction and reconciliation. Works with any bank, any number of sources, and custom category definitions. Also trigger when the user uploads a ZIP with financial files or asks to organize/classify spending data.
---

# Consolidar Faturas de Cartão de Crédito

## Overview

This skill processes financial invoices and bank statements end-to-end: extracts transaction data from multiple formats, validates totals against document values, standardizes data by origin, generates consolidated reports with automatic categorization, and produces a category evolution analysis showing spending trends across months.

It is bank-agnostic and works with any number of sources.

## Core Principles

Accounting precision, data integrity, and traceability are maximum priority:
- No lost, duplicate, or invented transactions
- Correct financial signs and complete origin tracking
- Automatic total reconciliation with safe failure mode (request user confirmation when reconciliation fails)
- Deterministic extraction wherever possible (CSV, OFX via libraries; PDF/image via LLM only when necessary)

Act simultaneously as: OCR/document parsing specialist, financial file reading expert, financial consistency auditor, data engineer for normalization and consolidation, and financial trend analyst.

## Workflow

Follow this sequential workflow with validation at each stage:

1. **File Type Detection** → Identify format and extraction strategy
2. **Extraction by Format** → Read `references/llm_prompt.md` for detailed per-format rules
3. **Standardization** → Create standardized CSV per origin
4. **Financial Classification** → Apply correct financial signs and types
5. **Validation & Reconciliation** → Verify totals match document values (with user confirmation fallback)
6. **Consolidation** → Merge all sources into single file
7. **Output Generation** → Produce all output files

**Note on categorization**: This skill does NOT categorize transactions. The `categoria` column is left empty in the output. Categorization is performed by the downstream `analise-estrategica-despesas` skill, which has a more sophisticated classification engine optimized for analytical insights. This separation ensures extraction integrity is not coupled to categorization quality.

## Input Requirements

**Source**: A ZIP file (e.g., `uploads.zip`) containing invoice files from any number of banks.

**Supported formats**: PDF, OFX, CSV, JPEG/PNG/WEBP images.

**Structure**: Files can be organized by bank/month or mixed — the system auto-detects bank/origin, document type, and period.

**Totals file (optional)**: A text file with expected totals per bank and period for reconciliation validation. Format is free-form: bank name followed by period/value pairs. The skill will parse it automatically.

## Reference Files — Read Before Processing

Before beginning extraction, read the appropriate reference files:

| File | When to Read | Purpose |
|------|-------------|---------|
| `references/llm_prompt.md` | **Always** — before any extraction | Full extraction workflow, per-format rules, PDF column-split strategy, validation logic, safety rules, bank-specific reconciliation formulas |
| `references/format_specifications.md` | When validating output format | Column specs, data types, validation checklist, encoding rules |
| `templates/output_schema.csv` | For reference on expected output shape | Example rows showing correct format |

## Output Files

### consolidado.csv (single consolidated file)

Columns: `banco`, `periodo_referencia`, `data_transacao`, `cartao`, `descricao`, `parcela`, `valor`, `tipo`, `categoria`, `categoria_nativa`

**Note**: The `categoria` column is left empty. Categorization is handled by the `analise-estrategica-despesas` skill.

### padronizado.zip (one CSV per origin)

Files named `faturas_[origin].csv` with standardized format per bank.

### consolidation_summary.log

Includes: reconciliation results per bank-period, totals by bank, monthly summary by bank, processing statistics.

## Consolidation Script

The `scripts/consolidate_invoices.py` script handles the final consolidation stage programmatically. It provides:
- Agnostic bank name normalization (works with any bank)
- Transaction deduplication (key includes parcela)
- Value normalization (Brazilian and international formats)
- Monthly summary
- Summary log writing

**Note**: The script no longer performs categorization or category evolution analysis. The `categoria` column is left empty for downstream processing by `analise-estrategica-despesas`.

Run it after all per-bank standardized CSVs have been produced:

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path("<skill_path>/scripts")))
from consolidate_invoices import InvoiceConsolidator

consolidator = InvoiceConsolidator(
    padronizado_dir=Path("./padronizado"),
    output_dir=Path("./output")
)
consolidator.run()
```

## Key Processing Rules

### PDF Column-Split Strategy (Critical for Santander-type layouts)

Many Brazilian bank invoice PDFs use a two-column layout in the transaction detail pages. Standard `extract_text()` merges columns incorrectly. The correct approach:

1. Detect detail pages (contain "Detalhamento da Fatura" or start with page number "N/N")
2. Calculate page midpoint: `mid = page.width / 2`
3. Crop and extract each half separately: `page.crop((0, 0, mid, height))` then `page.crop((mid, 0, width, height))`
4. Process left column lines first, then right column lines
5. Strip trailing single characters from column bleed: `re.sub(r'\s+[A-Z]$', '', line)`

### Bank-Specific Reconciliation Formulas

Each bank calculates the "Total a Pagar" differently. The reconciliation must use the correct formula:

- **CSV-based banks (C6 Bank)**: Total = sum(expenses) + sum(credits), **excluding** payment lines ("Inclusao de Pagamento"). Payments reduce the previous balance, not the current period's charges.
- **OFX-based banks (NuBank)**: Total = abs(BALAMT) from the OFX file. Transaction signs are flipped (OFX negative = our positive expense). Rounding differences of up to R$0.01 are expected from floating-point in OFX format.
- **PDF-based banks with Saldo Anterior (Santander, Porto Seguro)**: Total = sum(all_extracted_transactions) + Saldo_Anterior. The Saldo Anterior is extracted from the Resumo section of the PDF and added as a synthetic transaction.
- **Special case — antecipated payments**: When a month has an early/extra payment (e.g., "pagamento antecipado"), the Saldo da Fatura may be misleadingly low. In this case, the user's expected total represents the period charges (Despesas - Créditos, excluding payments), not the saldo.

### Porto Seguro PDF Section Detection

Porto Seguro PDFs split "Detalhamento" and "da fatura" across two lines. Detection must handle both `s == 'Detalhamento'` and the combined form. Critical: the "Data Estabelecimento" header line must be SKIPPED (continue), not treated as a section terminator. Only "Contestações", "Detalhamento geral", "Confira nossos", "Boleto", and "Opções" should reset the section to None.

### Bank Name Normalization

Agnostic — first occurrence sets the canonical form (Title Case). All variations auto-map. No predefined bank list needed.

### Value Normalization

Handles both Brazilian (1.234,56) and international (1,234.56) formats automatically.

### Financial Sign Conventions

- Positive = debits (expenses, charges)
- Negative = credits (payments, refunds, reversals)

### Deduplication

Unique key: bank + date + description + amount + card digits + parcela. Duplicates logged in summary.

## Safety Mechanisms

**Never invent data.** If extraction is uncertain: mark with low confidence, add note to `observacoes_extracao`, request user confirmation.

**Reconciliation failure:** Add detailed note with extracted vs. document totals, difference amount/percentage, list of uncertain transactions, and ask the user to confirm.

**Validation checkpoints** at every stage: extraction → normalization → deduplication → consolidation → categorization → trend analysis.

## Quick Usage Example

Input:
```
uploads.zip
├── Santander_Dec2025.pdf
├── NuBank_Dec2025.ofx
├── C6Bank_Jan2026.csv
└── Porto_Seguro_Dec2025.png
```

Output:
```
consolidado.csv              (all transactions, categoria column empty)
consolidation_summary.log    (reconciliation, totals, statistics)
padronizado.zip              (standardized CSVs by bank)
```
