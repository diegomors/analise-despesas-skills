"""
Expense Analyzer v2 — Categorizes transactions and extracts all metrics
from consolidado.csv for the strategic expense reduction skill.

This script is the SOLE owner of transaction categorization. The upstream
consolidar-faturas skill produces consolidado.csv with an empty `categoria`
column. This script fills it using keyword-based rules, then computes all
analytical metrics.

Outputs:
  - analysis_results.json — all computed metrics for dashboard generation
  - consolidado_categorizado.csv — categorized version of the input
"""

import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Optional


# ═══════════════════════════════════════════════════════════════
# CATEGORIZATION ENGINE
# ═══════════════════════════════════════════════════════════════
MONTH_MAP = {
    'jan': '01', 'fev': '02', 'mar': '03', 'abr': '04', 'mai': '05', 'jun': '06',
    'jul': '07', 'ago': '08', 'set': '09', 'out': '10', 'nov': '11', 'dez': '12',
}
MONTH_NAMES = {v: k.capitalize() for k, v in MONTH_MAP.items()}


def _norm(text: str) -> str:
    """Normalize text for keyword matching: lowercase, strip accents."""
    text = text.lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))


# Category rules: (category_name, is_priority, [keywords])
# Priority rules are checked first (payments, taxes). Then keyword rules.
CATEGORY_RULES = [
    # === PRIORITY RULES (checked first) ===
    ('Tributos e Encargos', True, [
        'devolucao iof', 'iof', 'taxa', 'tarifa', 'juros', 'multa', 'anuidade',
        'mora', 'encargo', 'imposto', 'contribuicao', 'estorno tarifa',
    ]),
    ('Pagamentos e Créditos', True, [
        'pagamento', 'credito', 'estorno', 'devolucao', 'reembolso',
        'antecipacao', 'saldo anterior', 'inclusao de pagamento',
    ]),
    # === KEYWORD RULES (checked in order) ===
    ('Serviços Recorrentes', False, [
        'netflix', 'spotify', 'amazon prime', 'amazonprimebr',
        'assinatura', 'openai', 'manus ai', 'claude.ai', 'figma', 'adobe', 'ebn*adobe',
        'ivpn', 'openrouter', 'linkedin', 'uber *one', 'cloudflare', 'shopify',
        'carpuride', 'manning', 'jim.com', 'jim com', 'nutag', 'smiles fidel',
        'smiles clube', 'smiles club', 'leiturinha', 'vindi', 'clubelivelo', 'clube livelo',
        'melimais', 'ec *melimais', 'mp *melimais', 'planetpay',
        'google workspace', 'google garena', 'dl *google youtubeprem',
        'google youtubepremium', 'pg *agilecode',
    ]),
    ('Restaurante e Lanchonete', False, [
        'restaurante', 'pizzaria', 'lanchonete', 'delivery',
        'ifood', 'uber eats', 'rei do frango', 'reidofrango', 'mini kalzone',
        'tlb pizzaria', 'soccer bar', 'uncle joe', 'pirata pousa', 'piratapousadae',
        'rei da costela', 'padeiro de servilha', 'panificadora', 'padaria', 'santo pao',
        'delicias do para', 'amazon fruit', 'amazon ice', 'adrena camelao',
        'restraurante', 'rappi', 'topgunsportbar', 'casadoastronom',
        'tripdogueria', 'vo maria', 'ooxe sushi', 'big boss barbershop',
        'wow sao jose', 'tenda da lili', 'hugao experience',
        'les burguer', 'ifd*47.903',
    ]),
    ('Saúde e Bem-Estar', False, [
        'farmacia', 'raia', 'farmacianovafarma', 'consulta',
        'medico', 'exame', 'laboratorio', 'hospital', 'clinica', 'extra farma',
        'amapharma', 'extrafarma', 'cia da saude', 'imune', 'natural foods',
        'farmacia preco popular', 'drogaria', 'panvel', 'fisioterapia',
        'quiroederaldo', 'asaas *dr team', 'e cosmeceutica',
    ]),
    ('Mobilidade e Transporte', False, [
        'combustivel', 'gasolina', 'estacionamento', 'uber',
        'taxi', 'passagem', 'abastec', 'parking', 'camelao parking', 'facar park',
        'ponto gas', 'moto panther', 'via porto motos', 'shellbox', 'petrobrasprem',
        'dubelas comercio',
    ]),
    ('Educação e Cursos', False, [
        'escola', 'universidade', 'curso', 'livro', 'livraria',
        'escola de tiro', 'clube de tiro', 'tiro 38', 'clube top gun',
        'colibrin papelaria', 'ticketmais', 'anhanguera', 'epic school',
    ]),
    ('Alimentação em Geral', False, [
        'supermercado', 'mercado', 'bistek', 'feira',
        'combo atacadista', 'atacadao', 'merkatu', 'hortifruti', 'casa dos ovos',
        'mercadodafamilia', 'papenborgalimento', 'central conveniencia',
        'safiragaspalh', 'safira gas', 'vo ruth', 'cappta *peixaria',
        'chocolates di agustini', 'mp *safira', 'mk continente', 'mdpsthscontinente',
        'mdpsthshcontinente', 'cooper filial', 'direto do campo',
        'eskimoatacadao', 'hippo supermercado', 'imperatr',
    ]),
    ('Animais de Estimação', False, [
        'cobasi', 'petshop', 'pet shop', 'veterinario', 'meu mundo pet',
    ]),
    ('Atividades Físicas', False, [
        'academia', 'decathlon', 'centauro', 'esporte', 'pilates',
        'yoga', 'crossfit', 'fisia', 'academia de lutas', 'mizuno',
        'rede pratique', 'pratique bel', 'nort academia',
    ]),
    ('Casa e Utilidades', False, [
        'havan', 'colchoes ortobom', 'electronic store', 'microshop',
        'milium', 'balaroti', 'shopee', 'simoes andrade tintas', 'pintou belem',
        'coelho tintas', 'oplima', '216 liv ctba', 'electrolux', 'lojaxiaomi',
        'lavanderia', 'nossa lavanderia', 'ri happy', 'eletrosol',
    ]),
    ('Doações e Presentes', False, [
        'doacao', 'dizimo', 'get church', 'hna*oboticario', 'hna*o boticario',
        'presente', 'boticario',
    ]),
    ('Vestuário e Cuidados Pessoais', False, [
        'roupa', 'beleza', 'salao', 'cabelereiro',
        'barbearia', 'francinirodrigues', 'moosebabykids', 'youcom', 'renner',
        'lojas franca', 'unifuckner', 'munnabrechooutlet', 'michelegonzalezda',
        'studio maicon araujo', 'lepostiche',
    ]),
    ('Comunicação e Conectividade', False, [
        'telefone', 'celular', 'internet', 'vivo', 'claro', 'tim',
    ]),
    ('Lazer e Entretenimento', False, [
        'cinema', 'viagem', 'hotel', 'airbnb', 'parque',
        'oceanicaquariumecom', 'lirio mimoso', 'amazon marketplace', 'amazon br',
        'amazonmktplc', 'mercadolivre', 'beto carrero', 'amazon',
        'ivanisegradimdo', 'cascata encantada', 'zoo pomerode',
        'cotinente park',
    ]),
    ('Seguros em Geral', False, [
        'seguro', 'seguradora', 'sul america seg',
    ]),
    ('Investimentos e Poupança', False, [
        'investimento', 'aplicacao', 'aporte',
    ]),
]


def categorize(desc: str) -> str:
    """Categorize a transaction description using keyword matching."""
    d = _norm(desc)
    # Step 1: Priority rules first
    for cat, is_priority, keywords in CATEGORY_RULES:
        if is_priority:
            for kw in keywords:
                if _norm(kw) in d:
                    return cat
    # Step 2: Keyword rules
    for cat, is_priority, keywords in CATEGORY_RULES:
        if not is_priority:
            for kw in keywords:
                if _norm(kw) in d:
                    return cat
    # Step 3: Default
    return 'Despesas Diversas'


class ExpenseAnalyzer:
    def __init__(
        self,
        consolidado_path: Path,
        categories_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ):
        self.consolidado_path = consolidado_path
        self.categories_path = categories_path
        self.output_dir = output_dir or Path(".")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.rows = []
        self.periods_ordered = []
        self.latest_period = None

    def run(self) -> dict:
        """Run full pipeline: categorize → analyze → output."""
        self._load_data()
        self._categorize_transactions()
        self._write_categorized_csv()
        self._build_category_period_matrix()
        results = {
            "overview": self._compute_overview(),
            "categories": self._compute_categories(),
            "banks_and_cards": self._compute_banks_cards(),
            "installments": self._compute_installments(),
            "recurring_services": self._compute_recurring(),
            "top_expenses": self._compute_top_expenses(),
            "category_details": self._compute_category_details(),
            "trends": self._compute_trends(),
            "savings_potential": self._compute_savings_potential(),
        }

        output_path = self.output_dir / "analysis_results.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        return results

    def _load_data(self):
        """Load and parse consolidado CSV."""
        with open(self.consolidado_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    r["valor"] = float(r.get("valor", "0").replace(",", ".") or "0")
                except (ValueError, AttributeError):
                    r["valor"] = 0.0
                self.rows.append(r)

        # Determine period ordering
        period_set = set()
        for r in self.rows:
            p = r.get("periodo_referencia", "")
            if p:
                period_set.add(p)

        def period_sort_key(p):
            month_map = {
                "Jan": 1, "Fev": 2, "Mar": 3, "Abr": 4, "Mai": 5, "Jun": 6,
                "Jul": 7, "Ago": 8, "Set": 9, "Out": 10, "Nov": 11, "Dez": 12,
            }
            parts = p.split("/")
            if len(parts) == 2:
                m = month_map.get(parts[0], 0)
                y = int(parts[1]) if parts[1].isdigit() else 0
                return (y, m)
            return (0, 0)

        self.periods_ordered = sorted(period_set, key=period_sort_key)
        self.latest_period = self.periods_ordered[-1] if self.periods_ordered else None

    def _categorize_transactions(self):
        """Fill empty `categoria` column for all transactions."""
        categorized_count = 0
        diversas_count = 0
        for r in self.rows:
            existing = (r.get("categoria") or "").strip()
            if not existing:
                cat = categorize(r.get("descricao", ""))
                r["categoria"] = cat
                categorized_count += 1
                if cat == "Despesas Diversas":
                    diversas_count += 1
        total_expenses = sum(1 for r in self.rows if r["valor"] > 0 and r.get("tipo") != "Pagamento")
        pct_diversas = (diversas_count / total_expenses * 100) if total_expenses > 0 else 0
        print(f"  Categorized {categorized_count} transactions ({diversas_count} as 'Despesas Diversas' = {pct_diversas:.1f}%)")

    def _write_categorized_csv(self):
        """Write the categorized consolidado back to CSV."""
        output_path = self.output_dir / "consolidado_categorizado.csv"
        fieldnames = [
            "banco", "periodo_referencia", "data_transacao", "cartao",
            "descricao", "parcela", "valor", "tipo", "categoria", "categoria_nativa",
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in self.rows:
                row = {k: r.get(k, "") for k in fieldnames}
                # Write valor as formatted number
                row["valor"] = f"{r['valor']:.2f}"
                w.writerow(row)
        print(f"  consolidado_categorizado.csv")

    def _build_category_period_matrix(self):
        """Build category × period matrix in memory for trend analysis.
        No file output — just populates self._cat_period for _compute_trends."""
        self._cat_period = defaultdict(lambda: defaultdict(float))
        for t in self.rows:
            val = t["valor"]
            if val > 0 and t.get("tipo") not in ("Pagamento", "Saldo Anterior"):
                self._cat_period[t["categoria"]][t["periodo_referencia"]] += val

    def _get_expenses(self, period=None):
        """Get expense rows (positive values, excluding payments)."""
        rows = self.rows
        if period:
            rows = [r for r in rows if r.get("periodo_referencia") == period]
        return [r for r in rows if r["valor"] > 0 and r.get("tipo", "") != "Pagamento"]

    def _compute_overview(self) -> dict:
        """Compute high-level overview metrics."""
        all_expenses = self._get_expenses()
        latest_expenses = self._get_expenses(self.latest_period)
        total_latest = sum(r["valor"] for r in latest_expenses)

        # Count banks and cards
        banks = set()
        cards = set()
        for r in latest_expenses:
            b = r.get("banco", "")
            c = r.get("cartao", "")
            if b:
                banks.add(b)
            if c and b:
                cards.add(f"{b}-{c}")

        # Also check all periods for banks with active installments
        all_banks = set()
        for r in self.rows:
            b = r.get("banco", "")
            if b:
                all_banks.add(b)

        # Banks missing from latest period
        missing_banks = all_banks - banks

        # Installments vs a vista in latest period
        parcelas = [r for r in latest_expenses if r.get("parcela") and "/" in r.get("parcela", "")]
        avista = [r for r in latest_expenses if not r.get("parcela") or "/" not in r.get("parcela", "")]

        return {
            "latest_period": self.latest_period,
            "all_periods": self.periods_ordered,
            "total_latest": round(total_latest, 2),
            "transaction_count_latest": len(latest_expenses),
            "banks_latest": sorted(banks),
            "banks_all": sorted(all_banks),
            "banks_missing_latest": sorted(missing_banks),
            "card_count": len(cards),
            "installment_total": round(sum(r["valor"] for r in parcelas), 2),
            "installment_count": len(parcelas),
            "avista_total": round(sum(r["valor"] for r in avista), 2),
            "avista_count": len(avista),
        }

    def _compute_categories(self) -> list:
        """Compute per-category totals for latest period."""
        expenses = self._get_expenses(self.latest_period)
        cat_data = defaultdict(lambda: {"total": 0.0, "count": 0})
        total = sum(r["valor"] for r in expenses)

        for r in expenses:
            cat = r.get("categoria", "Sem Categoria")
            cat_data[cat]["total"] += r["valor"]
            cat_data[cat]["count"] += 1

        result = []
        for cat, data in sorted(cat_data.items(), key=lambda x: -x[1]["total"]):
            result.append({
                "categoria": cat,
                "total": round(data["total"], 2),
                "count": data["count"],
                "pct": round(data["total"] / total * 100, 1) if total > 0 else 0,
            })
        return result

    def _compute_banks_cards(self) -> list:
        """Compute per-bank totals for latest period + historical."""
        expenses = self._get_expenses(self.latest_period)
        bank_data = defaultdict(lambda: {"total": 0.0, "count": 0, "cards": set()})
        total = sum(r["valor"] for r in expenses)

        for r in expenses:
            b = r.get("banco", "Desconhecido")
            bank_data[b]["total"] += r["valor"]
            bank_data[b]["count"] += 1
            c = r.get("cartao", "")
            if c:
                bank_data[b]["cards"].add(c)

        result = []
        for b, data in sorted(bank_data.items(), key=lambda x: -x[1]["total"]):
            result.append({
                "banco": b,
                "total": round(data["total"], 2),
                "count": data["count"],
                "pct": round(data["total"] / total * 100, 1) if total > 0 else 0,
                "card_count": len(data["cards"]),
            })
        return result

    def _compute_installments(self) -> dict:
        """Analyze installment commitments.
        
        Strategy: collect installments from the latest period first, then
        add installments from missing banks (using their most recent period).
        Deduplicate by keeping only the most advanced parcela (lowest remaining).
        """
        # Step 1: installments from latest period
        active_installments = []
        expenses = self._get_expenses(self.latest_period)
        for r in expenses:
            parcela = r.get("parcela", "")
            if not parcela or "/" not in parcela:
                continue
            match = re.match(r"(\d+)/(\d+)", parcela)
            if not match:
                continue
            current = int(match.group(1))
            total_p = int(match.group(2))
            remaining = total_p - current
            if remaining > 0:
                active_installments.append({
                    "descricao": r.get("descricao", "").strip(),
                    "valor_mensal": round(r["valor"], 2),
                    "parcela_atual": current,
                    "parcela_total": total_p,
                    "restantes": remaining,
                    "comprometido_futuro": round(r["valor"] * remaining, 2),
                    "categoria": r.get("categoria", ""),
                    "banco": r.get("banco", ""),
                    "cartao": r.get("cartao", ""),
                    "periodo": r.get("periodo_referencia", ""),
                })

        # Step 2: for banks missing from latest period, find their most recent
        # period and add installments from there (they still have active commitments)
        overview = self._compute_overview()
        for bank in overview["banks_missing_latest"]:
            bank_rows = [r for r in self.rows if r.get("banco") == bank and r["valor"] > 0]
            # Group by (descricao, parcela_total, cartao, valor) and keep only the most recent parcela
            best = {}
            for r in bank_rows:
                parcela = r.get("parcela", "")
                if not parcela or "/" not in parcela:
                    continue
                match = re.match(r"(\d+)/(\d+)", parcela)
                if not match:
                    continue
                current = int(match.group(1))
                total_p = int(match.group(2))
                remaining = total_p - current
                if remaining <= 0:
                    continue
                # Key by (desc, total installments, card, rounded valor) — same plan across
                # months, absorbing R$0.01 rounding differences without losing distinction
                # between different-value purchases on the same card.
                key = (r.get("descricao", "").strip(), total_p, r.get("cartao", ""), round(r["valor"]))
                if key not in best or current > best[key]["parcela_atual"]:
                    best[key] = {
                        "descricao": r.get("descricao", "").strip(),
                        "valor_mensal": round(r["valor"], 2),
                        "parcela_atual": current,
                        "parcela_total": total_p,
                        "restantes": remaining,
                        "comprometido_futuro": round(r["valor"] * remaining, 2),
                        "categoria": r.get("categoria", ""),
                        "banco": bank,
                        "cartao": r.get("cartao", ""),
                        "periodo": r.get("periodo_referencia", ""),
                        "nota": f"Dado do período {r.get('periodo_referencia', '?')} — pode já ter avançado",
                    }
            active_installments.extend(best.values())

        # Step 3: Deduplicate — keep the one with the lowest remaining
        # (most recent / most advanced parcela)
        best_by_key = {}
        for inst in active_installments:
            key = (inst["descricao"], inst["valor_mensal"], inst["banco"], inst.get("cartao", ""))
            if key not in best_by_key or inst["restantes"] < best_by_key[key]["restantes"]:
                best_by_key[key] = inst
        unique = sorted(best_by_key.values(), key=lambda x: -x["comprometido_futuro"])

        total_future = sum(i["comprometido_futuro"] for i in unique)

        # Group by timeline
        ending_soon = [i for i in unique if i["restantes"] <= 2]
        ending_medium = [i for i in unique if 3 <= i["restantes"] <= 6]
        ending_late = [i for i in unique if i["restantes"] > 6]

        return {
            "total_comprometido_futuro": round(total_future, 2),
            "count": len(unique),
            "items": unique[:20],  # top 20
            "ending_soon": {
                "count": len(ending_soon),
                "total_monthly": round(sum(i["valor_mensal"] for i in ending_soon), 2),
            },
            "ending_medium": {
                "count": len(ending_medium),
                "total_monthly": round(sum(i["valor_mensal"] for i in ending_medium), 2),
            },
            "ending_late": {
                "count": len(ending_late),
                "total_monthly": round(sum(i["valor_mensal"] for i in ending_late), 2),
            },
        }

    def _compute_recurring(self) -> list:
        """Identify recurring/subscription charges in latest period."""
        expenses = self._get_expenses(self.latest_period)
        recurring = [
            r for r in expenses
            if r.get("categoria", "") in ("Serviços Recorrentes",)
        ]
        result = []
        for r in sorted(recurring, key=lambda x: -x["valor"]):
            result.append({
                "descricao": r.get("descricao", "").strip(),
                "valor": round(r["valor"], 2),
                "parcela": r.get("parcela", ""),
                "categoria_nativa": r.get("categoria_nativa", ""),
            })
        total = sum(r["valor"] for r in result)
        return {
            "items": result,
            "total": round(total, 2),
            "count": len(result),
            "annualized": round(total * 12, 2),
        }

    def _compute_top_expenses(self) -> list:
        """Get top 25 expenses in latest period."""
        expenses = self._get_expenses(self.latest_period)
        expenses.sort(key=lambda x: -x["valor"])
        result = []
        for r in expenses[:25]:
            result.append({
                "descricao": r.get("descricao", "").strip(),
                "valor": round(r["valor"], 2),
                "categoria": r.get("categoria", ""),
                "parcela": r.get("parcela", ""),
                "banco": r.get("banco", ""),
            })
        return result

    def _compute_category_details(self) -> dict:
        """Compute detailed breakdown for each major category in latest period."""
        expenses = self._get_expenses(self.latest_period)
        cat_items = defaultdict(list)

        for r in expenses:
            cat = r.get("categoria", "Sem Categoria")
            cat_items[cat].append({
                "descricao": r.get("descricao", "").strip(),
                "valor": round(r["valor"], 2),
                "parcela": r.get("parcela", ""),
            })

        result = {}
        for cat, items in cat_items.items():
            items.sort(key=lambda x: -x["valor"])
            result[cat] = {
                "items": items[:15],  # top 15 per category
                "total": round(sum(i["valor"] for i in items), 2),
                "count": len(items),
            }
        return result

    def _compute_trends(self) -> list:
        """Compute trend data from in-memory category × period matrix."""
        if not hasattr(self, '_cat_period') or not self._cat_period:
            return []

        result = []
        for cat in sorted(self._cat_period.keys(), key=lambda c: -sum(self._cat_period[c].values())):
            total = sum(self._cat_period[cat].values())
            monthly = {}
            vals = []
            for period in self.periods_ordered:
                v = round(self._cat_period[cat].get(period, 0), 2)
                monthly[period] = v
                vals.append(v)

            # Trend: compare average of last 2 non-zero months vs first 2
            nonzero = [(i, v) for i, v in enumerate(vals) if v > 0]
            if len(nonzero) >= 3:
                first_avg = sum(v for _, v in nonzero[:2]) / 2
                last_avg = sum(v for _, v in nonzero[-2:]) / 2
                trend = f"{((last_avg - first_avg) / first_avg) * 100:+.1f}%" if first_avg > 0 else "novo"
            elif len(nonzero) == 2:
                trend = f"{((nonzero[1][1] - nonzero[0][1]) / nonzero[0][1]) * 100:+.1f}%" if nonzero[0][1] > 0 else "novo"
            else:
                trend = "—"

            result.append({
                "categoria": cat,
                "total": round(total, 2),
                "tendencia": trend,
                "monthly": monthly,
                "growing": "+" in (trend or ""),
            })
        return result

    def _compute_savings_potential(self) -> dict:
        """Estimate savings potential across categories."""
        recurring = self._compute_recurring()
        categories = self._compute_categories()
        total_latest = sum(c["total"] for c in categories)

        # Conservative: only recurring services cuts (assume 50% can be cut)
        conservative = round(recurring["total"] * 0.5, 2)

        # Moderate: recurring + top discretionary categories reduced by 20%
        discretionary_cats = {
            "Despesas Diversas", "Restaurante e Lanchonete",
            "Lazer e Entretenimento", "Vestuário e Cuidados Pessoais",
        }
        discretionary_total = sum(
            c["total"] for c in categories if c["categoria"] in discretionary_cats
        )
        moderate = round(conservative + discretionary_total * 0.2, 2)

        # Optimistic: recurring + discretionary + food optimization
        food_total = sum(
            c["total"] for c in categories if c["categoria"] in ("Alimentação em Geral",)
        )
        optimistic = round(moderate + food_total * 0.15, 2)

        return {
            "conservative": conservative,
            "moderate": moderate,
            "optimistic": optimistic,
            "total_expenses": round(total_latest, 2),
            "conservative_pct": round(conservative / total_latest * 100, 1) if total_latest > 0 else 0,
            "moderate_pct": round(moderate / total_latest * 100, 1) if total_latest > 0 else 0,
            "optimistic_pct": round(optimistic / total_latest * 100, 1) if total_latest > 0 else 0,
        }


if __name__ == "__main__":
    import sys

    consolidado = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("consolidado.csv")
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")

    analyzer = ExpenseAnalyzer(consolidado, output_dir=output)
    results = analyzer.run()
    print(json.dumps(results, ensure_ascii=False, indent=2)[:3000])
    print(f"\n... Full results saved to {output / 'analysis_results.json'}")
