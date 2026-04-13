---
name: analise-estrategica-despesas
description: Analyze credit card expenses strategically and generate an actionable cost-reduction plan with an interactive HTML dashboard. Use this skill whenever the user uploads consolidado.csv and/or categorias_evolucao.csv (the outputs of the consolidar-faturas skill) and asks for expense analysis, spending insights, cost reduction strategies, debt reduction plans, or financial optimization. Also trigger when the user mentions análise de despesas, redução de gastos, plano de ação financeiro, cortar despesas, economizar no cartão, otimizar gastos, estratégia financeira, or wants to understand where their money is going and what to cut first. This skill transforms raw transaction data into prioritized, actionable recommendations ranked by effort-vs-impact, plus a polished visual dashboard. Trigger even if the user simply says "analyze my expenses" or "what can I cut?" after uploading financial CSVs.
---

# Análise Estratégica de Despesas

## Purpose

This skill takes the output from the `consolidar-faturas` skill (consolidado.csv with `categoria` column empty) and produces a comprehensive strategic analysis with prioritized, actionable recommendations for expense reduction — plus an interactive HTML dashboard the user can keep and reference.

**This skill is responsible for two things**:
1. **Categorizing** every transaction in consolidado.csv (the upstream skill intentionally leaves this column empty to preserve separation of concerns)
2. **Analyzing** the categorized data strategically and generating the dashboard

The analysis is structured around a simple principle: **maximize savings per unit of effort**. Cancel a subscription in 5 minutes and save R$ 1.000/month forever, vs. slowly reducing grocery trips for marginal gains — the skill ranks and sequences actions accordingly.

## Input Files

The user provides the consolidado.csv from a previous `consolidar-faturas` run:

- **consolidado.csv** — All transactions across banks/cards with columns: `banco`, `periodo_referencia`, `data_transacao`, `cartao`, `descricao`, `parcela`, `valor`, `tipo`, `categoria`, `categoria_nativa`. The `categoria` column will typically be empty — this skill fills it.
- **categorias_evolucao.csv** (optional, legacy) — If provided from an older run that already included categories, use it as supplementary trend data. But always re-categorize from consolidado.csv for the primary analysis.

If consolidado.csv has an empty `categoria` column (the expected case), the skill categorizes all transactions first, then generates the category evolution data internally.

## Workflow

### Stage 1: Categorization

The consolidado.csv arrives with `categoria` column empty. This skill categorizes every transaction before analysis.

Run `scripts/analyze_expenses.py` which handles both categorization and metric extraction:

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path("<skill_path>/scripts")))
from analyze_expenses import ExpenseAnalyzer

analyzer = ExpenseAnalyzer(
    consolidado_path=Path("/mnt/user-data/uploads/consolidado.csv"),
    categories_path=Path("<skill_path>/templates/categorias_default.csv"),  # or user-provided
    output_dir=Path("/home/claude/analysis_output")
)
results = analyzer.run()
```

The script:
1. Loads consolidado.csv
2. Categorizes each transaction using the rules in `references/categorization_rules.md`
3. Computes all analytical metrics (including trend data from the categorized transactions)
4. Writes `consolidado_categorizado.csv` (the categorized version, for reference)
5. Outputs `analysis_results.json` with all metrics for dashboard generation

Read `references/categorization_rules.md` for the full categorization algorithm with expanded merchant database, priority rules, and special cases. The categorization engine uses a 3-step priority system:
1. **Priority rules** (highest): payment/credit/tax patterns override everything
2. **Keyword matching**: expanded merchant database with 18 categories
3. **Default fallback**: "Despesas Diversas" — but the goal is to minimize this bucket

**Key categorization quality target**: Less than 10% of expense transactions should end up in "Despesas Diversas". If more than that, investigate the uncategorized descriptions and add keywords.

### Stage 2: Strategic Analysis

Using the metrics from Stage 1, analyze and classify every expense into actionable buckets. Read `references/analysis_framework.md` for the complete analytical framework covering:

- **Effort-vs-Impact Matrix**: How to classify each potential cut
- **Category Deep-Dive Rules**: What to look for in each spending category
- **Recurring vs. Discretionary Detection**: How to identify subscriptions, installments, and one-off purchases
- **Trend Interpretation**: How to read the evolution data for actionable signals
- **Recommendation Prioritization**: The 4-phase system (Immediate Cuts → Containment → Optimization → Review)

Key analytical principles:
1. **Subscriptions first** — They're the highest ROI cuts (5 minutes of effort, 12 months of savings)
2. **Detect duplicates** — Multiple charges from the same service (e.g., 3 LinkedIn plans) are almost always waste
3. **Installments are sunk costs** — Don't recommend "quitting" installments; recommend not creating new ones
4. **Trend matters more than absolutes** — A category at +106% growth is more urgent than a larger stable one
5. **Be specific** — "Cut subscriptions" is useless; "Cancel Manus AI (R$ 1.070/mês)" is actionable

### Stage 3: HTML Dashboard Generation

Generate a single self-contained HTML file with the complete strategic analysis. Read `templates/dashboard_template.md` for the HTML structure, styling, and component specifications.

**CRITICAL**: All aggregate numbers in the dashboard (totals, installment commitments, savings ranges, category breakdowns) MUST come from `analysis_results.json`. Do NOT recompute values from the raw CSV — the script handles deduplication and edge cases that manual recalculation will get wrong (especially installment future commitments, which must be deduplicated across periods).

The dashboard must include:
1. **Scorecards** — Total expenses, future commitments (installments), and projected savings potential
2. **Category Breakdown** — Visual bar chart of top spending categories with amounts and percentages
3. **Alerts** — Highlight categories with alarming trends (>50% growth, unusual spikes)
4. **Phased Action Plan** — 4 phases from quickest wins to long-term habits, each action with:
   - What to do (specific, named items)
   - Why it matters (context)
   - Effort tag (5 min / 15 min / requires negotiation / habit change)
   - Monthly savings estimate
5. **Installment Forecast** — Show future committed amounts and when they expire
6. **Summary Box** — Total projected savings range and prioritized 4-step sequence

### Stage 4: Conversational Insights

After generating the HTML file, provide a concise conversational summary hitting:
1. The single most impactful finding (usually the biggest quick-win)
2. The total savings potential range
3. The top 3 actions ranked by effort-to-impact ratio
4. Any alarming trends that need immediate attention

Keep the conversational part brief — the dashboard has the details. The conversation should be a "here's what jumped out at me" executive briefing, not a repetition of the dashboard.

## Output Files

- **analise_estrategica_despesas.html** — Interactive dashboard (copy to /mnt/user-data/outputs/)
- **consolidado_categorizado.csv** — The consolidado with `categoria` column filled (copy to /mnt/user-data/outputs/)
- **analysis_results.json** — Raw computed metrics (kept in working directory for reference)

## Reference Files

| File | When to Read | Purpose |
|------|-------------|---------|
| `references/categorization_rules.md` | **Always** — before categorization | 18 standard categories, matching algorithm with priority/exact/partial/fuzzy steps, expanded merchant database, confidence scoring, special cases |
| `references/analysis_framework.md` | Before strategic analysis | Effort-vs-impact matrix, category deep-dive rules, 4-phase action system, trend interpretation |
| `templates/categorias_default.csv` | When no user-provided categories file exists | Default 18-category dictionary |
| `templates/dashboard_template.md` | Before HTML generation | Dashboard structure, styling, component specifications |

## Important Notes

- Always identify ALL banks and cards in the data, not just the most recent period. Some banks may be absent from the latest month but still have active installments.
- Installment math: parse the `parcela` field (format "N/M") to compute remaining payments and future commitment.
- Payments/credits (negative values or tipo="Pagamento") should be excluded from expense totals.
- The HTML must be fully self-contained — no external dependencies except Google Fonts (which degrade gracefully).
- Use Portuguese (Brazilian) throughout the dashboard and conversation.
- Never provide investment or financial advisory recommendations — stick to expense analysis and reduction strategies. Include a note that you're not a financial advisor.
- Be sensitive about the tone: the user may be stressed about finances. Be direct and actionable, but not judgmental.
