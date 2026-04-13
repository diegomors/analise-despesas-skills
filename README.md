# analise-despesas-skills

Skills para agentes (Cursor, Claude, etc.) que tratam de **extrato e faturas de cartão** no Brasil: primeiro **consolidar** transações de várias fontes com rastreio e reconciliação; depois **analisar** gastos com categorização, priorização (esforço × impacto) e um **dashboard HTML** acionável.

## Fluxo recomendado

```text
ZIP com PDF / OFX / CSV / imagens
        │
        ▼
  consolidar-faturas
        │
        ├─ consolidado.csv          (transações unificadas; coluna categoria vazia)
        ├─ padronizado.zip          (um CSV padronizado por origem)
        └─ consolidation_summary.log
        │
        ▼
analise-estrategica-despesas
        │
        ├─ analise_estrategica_despesas.html
        ├─ consolidado_categorizado.csv
        └─ analysis_results.json
```

O desenho separa **integridade de extração** (consolidação) da **qualidade analítica da categorização** (análise estratégica). A coluna `categoria` fica vazia na saída da primeira skill de propósito; a segunda skill preenche e gera métricas e recomendações.

---

## `consolidar-faturas`

**Função:** processar faturas e extratos de **qualquer banco** e **várias origens** — detectar formato, extrair linhas de transação, padronizar, classificar sinais (débito/crédito), **reconciliar totais** com o documento (com modo seguro de pedir confirmação ao usuário se não bater) e **consolidar** tudo em um único arquivo.

**Formatos de entrada:** PDF, OFX, CSV, imagens (JPEG/PNG/WEBP), em geral entregues em um **ZIP**.

**O que não faz:** **não categoriza** despesas para análise estratégica. A coluna `categoria` em `consolidado.csv` sai **vazia** para a skill seguinte tratar com regras e dicionário próprios.

**Principais saídas:**

| Arquivo | Descrição |
|--------|-----------|
| `consolidado.csv` | Todas as transações com colunas padronizadas (`banco`, `periodo_referencia`, `data_transacao`, `cartao`, `descricao`, `parcela`, `valor`, `tipo`, `categoria`, `categoria_nativa`) |
| `padronizado.zip` | CSVs por origem (`faturas_[origem].csv`) |
| `consolidation_summary.log` | Reconciliação, totais, estatísticas |

**Script:** `consolidar-faturas/scripts/consolidate_invoices.py` — normalização de banco, deduplicação (incluindo `parcela`), normalização de valores (BR/internacional), resumo mensal e log.

**Instruções completas:** [consolidar-faturas/SKILL.md](consolidar-faturas/SKILL.md) (workflow, regras por formato, PDF em duas colunas, fórmulas de reconciliação por tipo de banco).

**Quando usar (resumo):** faturas, extratos, consolidar transações, OFX, ZIP com arquivos financeiros, validar totais, padronizar dados por banco — antes de qualquer análise de “onde cortar”.

---

## `analise-estrategica-despesas`

**Função:** receber o **`consolidado.csv`** produzido por `consolidar-faturas` (com `categoria` vazia), **categorizar** todas as transações (regras em `references/categorization_rules.md`), **calcular métricas** e produzir **análise estratégica** com plano de ação em fases (cortes imediatos → contenção → otimização → revisão), priorizando **economia por esforço** (ex.: assinaturas primeiro).

**Entrada principal:** `consolidado.csv`. Opcional: `categorias_evolucao.csv` legado como apoio de tendência; a categorização principal deve partir do consolidado.

**Principais saídas:**

| Arquivo | Descrição |
|--------|-----------|
| `analise_estrategica_despesas.html` | Dashboard HTML autocontido (números agregados devem vir de `analysis_results.json`, não recalculados à mão a partir do CSV cru) |
| `consolidado_categorizado.csv` | Mesmo consolidado com `categoria` preenchida |
| `analysis_results.json` | Métricas para o dashboard e referência |

**Script:** `analise-estrategica-despesas/scripts/analyze_expenses.py` — categorização + extração de métricas.

**Instruções completas:** [analise-estrategica-despesas/SKILL.md](analise-estrategica-despesas/SKILL.md) (framework de análise, template do dashboard, tom em português (BR), limites: não é assessoria de investimento).

**Quando usar (resumo):** após ter `consolidado.csv`; pedidos de análise de despesas, redução de gastos, plano financeiro, “o que cortar primeiro”, insights e dashboard visual.

---

## Estrutura do repositório

```text
analise-despesas-skills/
├── README.md
├── consolidar-faturas/
│   ├── SKILL.md
│   ├── scripts/consolidate_invoices.py
│   ├── references/llm_prompt.md, format_specifications.md
│   └── templates/output_schema.csv
└── analise-estrategica-despesas/
    ├── SKILL.md
    ├── scripts/analyze_expenses.py
    ├── references/categorization_rules.md, analysis_framework.md
    └── templates/categorias_default.csv, dashboard_template.md
```

Para configurar cada skill no agente, use o frontmatter `name` e `description` de cada `SKILL.md` — eles já descrevem gatilhos e escopo para o roteador do modelo.
