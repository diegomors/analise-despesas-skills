# Format Specifications and Validation

## Output Schema (Single Source of Truth)

All output files share this unified column specification. There is ONE schema — padronizado files and consolidado use the same columns.

### Column Specifications

| Column | Type | Format | Required | Example |
|--------|------|--------|----------|---------|
| banco | String | Bank name (Title Case) | Yes | Santander |
| periodo_referencia | String | Mmm/YYYY | Yes | Jan/2026 |
| data_transacao | String | DD/MM/YYYY | Yes | 15/01/2026 |
| cartao | String | Last digits | No | 5349 |
| descricao | String | Transaction description | Yes | BISTEK SUPERMERCADOS |
| parcela | String | N/M format | No | 02/06 |
| valor | Decimal | -999999.99 | Yes | 150.50 |
| tipo | String | Transaction type | Yes | Despesa/Parcelamento |
| categoria | String | Standard category | No | *(left empty — filled by analise-estrategica-despesas)* |
| categoria_nativa | String | Bank's native category | No | Supermercados |

### Field Validation Rules

**banco**: Any string in Title Case. Agnostic — no predefined list.

**periodo_referencia**: Format `Mmm/YYYY` where Mmm is: Jan, Fev, Mar, Abr, Mai, Jun, Jul, Ago, Set, Out, Nov, Dez.

**data_transacao**: `DD/MM/YYYY`. May be empty for synthetic transactions (Saldo Anterior).

**cartao**: Card final digits or empty.

**descricao**: Non-empty string, max 200 characters.

**parcela**: Format `N/M` (e.g., 02/06) or empty. NOT "Única" (leave empty for single purchases).

**valor**: Decimal with exactly 2 places. Positive for expenses, negative for credits/payments.

**tipo**: One of: `Despesa/Parcelamento`, `Pagamento`, `Crédito`, `Saldo Anterior`.

**categoria**: Left empty by this skill. Will be populated by the `analise-estrategica-despesas` skill downstream.

**categoria_nativa**: Bank's original category string or empty.

### Sorting Order

1. Primary: banco (alphabetical)
2. Secondary: periodo_referencia (chronological)
3. Tertiary: data_transacao (chronological)

## File Encoding

All files must be UTF-8 encoded:
- No BOM (Byte Order Mark)
- Proper handling of accented characters (é, ã, ç, etc.)
- CSV delimiter: comma
- Line ending: LF (Unix style)
- Header row present in all files

## Deduplication Key

```
(banco, data_transacao, descricao.upper().strip(), valor, cartao, parcela)
```

Note: `parcela` is included in the key to prevent false deduplication of installment payments with the same amount and description but different installment numbers.

## Decimal Precision

All monetary values must be precise to 2 decimal places:
- Valid: 100.00, 150.50, 1234.99, 0.01
- Invalid: 100, 150.5, 1234.999

When summing for validation, compare with tolerance of R$0.02 (to account for OFX floating-point rounding).
