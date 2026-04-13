# Categorization Rules and Safety Guidelines

## Overview

This document provides detailed categorization rules with an expanded merchant database covering common Brazilian merchants. The skill uses 18 standard categories that can be customized by providing a custom `categorias.csv` file.

## Critical Safety Principles

1. **Never Invent Categories**: Only use categories from the provided dictionary
2. **Default to "Despesas Diversas"**: When no confident match is found
3. **Preserve Original Categories**: Keep bank's native categories in `categoria_nativa` column
4. **Mark Uncertainty**: If categorization confidence is low, add note to `observacoes_extracao`
5. **Priority Rules Override All**: Apply payment/tax rules before any keyword matching

## Standard Categories (18)

| # | Category | Description |
|---|----------|-------------|
| 1 | Alimentação em Geral | Supermercado, açougue, feiras |
| 2 | Animais de Estimação | Pet shop, alimentação, cuidados veterinários |
| 3 | Atividades Físicas | Academia, esportes, aulas de dança, pilates |
| 4 | Casa e Utilidades | Utensílios domésticos, móveis, eletrodomésticos |
| 5 | Comunicação e Conectividade | Telefone, celular, internet, TV a cabo |
| 6 | Despesas Diversas | Outras despesas sem categoria específica |
| 7 | Doações e Presentes | Doações, dízimos e presentes |
| 8 | Educação e Cursos | Mensalidades, livros, materiais escolares |
| 9 | Investimentos e Poupança | Aplicações financeiras, aportes |
| 10 | Lazer e Entretenimento | Cinema, passeios, viagens, hobbies |
| 11 | Mobilidade e Transporte | Combustível, estacionamento, transporte público |
| 12 | Pagamentos e Créditos | Pagamentos de fatura e estornos |
| 13 | Restaurante e Lanchonete | Restaurantes, lanchonetes, delivery |
| 14 | Saúde e Bem-Estar | Farmácia, consultas, exames, plano de saúde |
| 15 | Seguros em Geral | Carro, casa, vida, saúde complementar |
| 16 | Serviços Recorrentes | Assinaturas: streaming, softwares, clubes |
| 17 | Tributos e Encargos | Impostos, taxas, multas, contribuições |
| 18 | Vestuário e Cuidados Pessoais | Roupas, calçados, beleza, estética |

## Categorization Algorithm

### Step 1: Apply Priority Rules (HIGHEST Priority)

Check for these patterns FIRST, before any other matching. **Order matters** — Tributos is checked before Pagamentos so that "DEVOLUCAO IOF" matches the tax category, not the payment category.

**Rule 1: Tributos e Encargos**
- Keywords: devolucao iof, iof, taxa, tarifa, juros, multa, anuidade, mora, encargo, imposto, contribuicao, estorno tarifa
- Sign: Positive if charge, negative if reversal
- Confidence: 0.95+
- **Critical**: "DEVOLUCAO IOF" must match here (not Pagamentos) because IOF is a tax; its reversal stays in the tax category

**Rule 2: Pagamentos e Créditos**
- Keywords: pagamento, credito, estorno, devolucao, reembolso, antecipacao, saldo anterior, inclusao de pagamento
- Sign: Always negative (credit to account)
- Confidence: 0.95+

### Step 2: Keyword Matching (by category)

**Serviços Recorrentes** (streaming, SaaS, subscriptions):
- Keywords: netflix, spotify, amazon prime, amazonprimebr, assinatura, openai, manus ai, claude.ai, figma, adobe, ebn*adobe, ivpn, openrouter, linkedin, uber *one, cloudflare, shopify, carpuride, manning, jim.com, jim com, nutag, smiles fidel, smiles clube, smiles club, leiturinha, vindi, clubelivelo, clube livelo, melimais, ec *melimais, mp *melimais, planetpay, google workspace, google garena, dl *google youtubeprem, google youtubepremium, pg *agilecode

**Restaurante e Lanchonete**:
- Keywords: restaurante, pizzaria, lanchonete, delivery, ifood, uber eats, rei do frango, reidofrango, mini kalzone, tlb pizzaria, soccer bar, uncle joe, pirata pousa, piratapousadae, rei da costela, padeiro de servilha, panificadora, padaria, santo pao, delicias do para, amazon fruit, amazon ice, adrena camelao, restraurante, rappi, topgunsportbar, casadoastronom, tripdogueria, vo maria, ooxe sushi, big boss barbershop, wow sao jose, tenda da lili, hugao experience, les burguer, ifd*47.903

**Saúde e Bem-Estar**:
- Keywords: farmacia, raia, farmacianovafarma, consulta, medico, exame, laboratorio, hospital, clinica, extra farma, amapharma, extrafarma, cia da saude, imune, natural foods, farmacia preco popular, drogaria, panvel, fisioterapia, quiroederaldo, asaas *dr team, e cosmeceutica

**Mobilidade e Transporte**:
- Keywords: combustivel, gasolina, estacionamento, uber, taxi, passagem, abastec, parking, camelao parking, facar park, ponto gas, moto panther, via porto motos, shellbox, petrobrasprem, dubelas comercio

**Educação e Cursos**:
- Keywords: escola, universidade, curso, livro, livraria, escola de tiro, clube de tiro, tiro 38, clube top gun, colibrin papelaria, ticketmais, anhanguera, epic school

**Alimentação em Geral**:
- Keywords: supermercado, mercado, bistek, feira, combo atacadista, atacadao, merkatu, hortifruti, casa dos ovos, mercadodafamilia, papenborgalimento, central conveniencia, safiragaspalh, safira gas, vo ruth, cappta *peixaria, chocolates di agustini, mp *safira, mk continente, mdpsthscontinente, mdpsthshcontinente, cooper filial, direto do campo, eskimoatacadao, hippo supermercado, imperatr

**Animais de Estimação**:
- Keywords: cobasi, petshop, pet shop, veterinario, meu mundo pet

**Atividades Físicas**:
- Keywords: academia, decathlon, centauro, esporte, pilates, yoga, crossfit, fisia, academia de lutas, mizuno, rede pratique, pratique bel, nort academia

**Casa e Utilidades**:
- Keywords: havan, colchoes ortobom, electronic store, microshop, milium, balaroti, shopee, simoes andrade tintas, pintou belem, coelho tintas, oplima, 216 liv ctba, electrolux, lojaxiaomi, lavanderia, nossa lavanderia, ri happy, eletrosol

**Doações e Presentes**:
- Keywords: doacao, dizimo, get church, hna*oboticario, hna*o boticario, presente, boticario

**Vestuário e Cuidados Pessoais**:
- Keywords: roupa, beleza, salao, cabelereiro, barbearia, francinirodrigues, moosebabykids, youcom, renner, lojas franca, unifuckner, munnabrechooutlet, michelegonzalezda, studio maicon araujo, lepostiche

**Comunicação e Conectividade**:
- Keywords: telefone, celular, internet, vivo, claro, tim

**Lazer e Entretenimento**:
- Keywords: cinema, viagem, hotel, airbnb, parque, oceanicaquariumecom, lirio mimoso, amazon marketplace, amazon br, amazonmktplc, mercadolivre, beto carrero, amazon, ivanisegradimdo, cascata encantada, zoo pomerode, cotinente park

**Seguros em Geral**:
- Keywords: seguro, seguradora, sul america seg

**Investimentos e Poupança**:
- Keywords: investimento, aplicacao, aporte

### Step 3: Default Category

If no match found:
- **Category**: Despesas Diversas
- **Action**: Add note to `observacoes_extracao`: "Sem categoria definida; revisar"

## Text Normalization for Matching

Before comparing keywords, normalize the transaction description:
1. Convert to lowercase
2. Remove Unicode accents (NFD decomposition)
3. Strip whitespace
4. Match using substring containment (`keyword in normalized_description`)

## Special Cases

### "DEVOLUCAO IOF"
- Category: Tributos e Encargos (NOT Pagamentos e Créditos)
- Sign: Negative (credit/reversal)
- Reason: IOF is a tax; its reversal stays in the tax category

### "UBER EATS" vs "UBER"
- "UBER EATS", "UBER *EATS" → Restaurante e Lanchonete
- "UBER *TRIP", "UBER" (without EATS) → Mobilidade e Transporte
- "UBER *ONE" → Serviços Recorrentes (subscription)
- The categorization engine must check "uber eats" and "uber *one" BEFORE generic "uber"

### Marketplace Purchases
- AMAZON MARKETPLACE, AMAZON BR, AMAZONMKTPLC, MERCADOLIVRE → Lazer e Entretenimento (general purchases)
- AMAZONPRIMEBR → Serviços Recorrentes (subscription)

## Custom Categories

Users can provide custom `categorias.csv` file:

```csv
Minha Categoria 1,"Descrição e padrões"
Minha Categoria 2,"Descrição e padrões"
```

When custom file is provided, use those categories instead of defaults. Same matching algorithm applies.
