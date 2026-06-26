# Newsletter IA Bolsa

🌐 **Acesse o site:** https://mello-lucas26ds.github.io/newsletter-ia-bolsa/

Newsletter automatizada sobre **Inteligência Artificial e Mercado Financeiro** — atualizada 2× ao dia via GitHub Actions, com notícias acumuladas permanentemente. Nenhuma notícia se perde.

---

## O que é

Um agregador de notícias sobre IA, semicondutores, data centers e movimentações de mercado. As notícias são buscadas em fontes globais confiáveis, processadas por IA para resumo e classificação de sentimento, e exibidas em um site estático com design futurista.

O site exibe **todas as notícias de todas as execuções históricas**, organizadas com filtros por sentimento (Bullish/Bearish/Neutral) e busca por empresa, tag ou palavra-chave.

---

## Diferenciais

| Recurso | Descrição |
|---|---|
| **Dados acumulativos** | Notícias nunca se perdem — cada execução adiciona ao acumulado, não sobrescreve |
| **Sentimento de mercado** | Cada notícia classificada como Bullish 🟢, Bearish 🔴 ou Neutral ⚪ |
| **Busca em tempo real** | Filtros + busca por empresa, tag ou palavra-chave no frontend puro (JavaScript) |
| **Fonte transparente** | Badge no site indica "Dados Reais — Tavily + Groq" vs "Dados de Demonstração" |
| **Modo desenvolvimento** | Flask com dados fake para visualizar o design sem gastar APIs |
| **Observabilidade** | Langfuse opcional para rastrear traces e custos de inferência |

---

## Fontes monitoradas

| Categoria | Exemplos de fontes |
|---|---|
| Notícias financeiras | Bloomberg, Reuters, Financial Times, Wall Street Journal, CNBC, MarketWatch, Investing.com, Benzinga |
| Tecnologia / IA | The Verge, TechCrunch, Ars Technica |
| Mercado brasileiro | Valor Econômico, InfoMoney, Money Times |


As fontes são buscadas via **Tavily API** com `search_depth=advanced` e filtro de domínios confiáveis.

---

## Como funciona — pipeline GitHub Actions

O pipeline roda automaticamente na nuvem, sem precisar do computador ligado:

```
GitHub Actions (cron 06:00 e 23:00 UTC-4)
       ↓
app/services/pipeline.py
       ↓
Tavily API — busca notícias em fontes globais (IA, semicondutores, data centers, mercado)
       ↓
Groq API (llama-3.1-8b-instant) — resume, classifica sentimento e extrai tags
       ↓
Regex fallback — se Groq falhar, usa regex para extração básica (sem custo)
       ↓
Filtra URLs já vistas em data/url_history.json
       ↓
Salva data/news_processed_YYYY-MM-DD.json  (snapshot do dia)
       ↓
Mescla com data/news_processed.json (acumulado permanente)
       ↓
generate_site.py → gera index.html atualizado
       ↓
git commit + push → GitHub Pages atualizado
```

### Agendamento

| Horário UTC-4 | Horário UTC | Dias |
|---|---|---|
| 06:00 | 10:00 | Segunda a domingo |
| 23:00 | 03:00 | Segunda a domingo |

Para rodar fora do agendamento: **Actions → "Newsletter IA Bolsa" → Run workflow**

---

## Stack

| Componente             | Tecnologia                       | Por quê                                                            |
| ---------------------- | -------------------------------- | ------------------------------------------------------------------ |
| **Backend / Pipeline** | **Python 3.12**                  | Orquestra busca, processamento, deduplicação, formatação e geração |
| Busca                  | Tavily API                       | Fontes primárias                                                   |
| Processamento IA       | Groq API                         | Inferência rápida                                                  |
| **Orquestração**       | **Python dataclasses + pathlib** | Config imutável, caminhos robustos, código limpo                   |
| **Testes**             | **pytest**                       | 14 testes automatizados, regressão zero                            |
| Fallback               | Regex (Python puro)              | Sem custo                                                          |
| Template               | Jinja2 + Flask                   | Dev mode                                                           |
| Frontend               | HTML5 + CSS3 + Vanilla JS        | Site estático                                                      |
| Design                 | CSS futurista gamer              | Identidade                                                         |
| Hospedagem             | GitHub Pages                     | Gratuito                                                           |
| Automação              | GitHub Actions (cron)            | Sem servidor                                                       |
| Deduplicação           | `url_history.json`               | URLs vistas                                                        |
| Observabilidade        | Langfuse (opcional)              | Traces                                                             |


---

## Estrutura do repositório

```
newsletter-ia-bolsa/
├── .github/
│   └── workflows/
│       └── newsletter.yml        ← workflow GitHub Actions (cron 2×/dia)
├── app/
│   ├── __init__.py               ← factory Flask
│   ├── routes.py                 ← rotas de desenvolvimento
│   ├── services/
│   │   ├── pipeline.py           ← pipeline principal (busca → processa → salva)
│   │   ├── ingest.py             ← TavilySource (busca em fontes)
│   │   ├── process_ai.py         ← GroqSummarizer + RegexFallback
│   │   ├── dedup.py              ← JsonDeduplicador (url_history.json)
│   │   ├── newsletter.py         ← NewsletterFormatter (JSON, Markdown, HTML)
│   │   └── generate_site.py      ← gera index.html estático
│   ├── static/
│   │   └── css/
│   │       └── style.css         ← design futurista gamer
│   └── templates/
│       ├── base.html             ← layout base
│       ├── index.html            ← template da newsletter (Flask + estático)
│       ├── newsletter.html       ← página individual por data
│       └── dev/
│           └── panel.html        ← dashboard de desenvolvimento
├── data/
│   ├── news_processed.json       ← acumulado permanente (todas as notícias)
│   ├── news_processed_YYYY-MM-DD.json  ← snapshot do dia
│   ├── newsletter_YYYY-MM-DD.md      ← newsletter em Markdown
│   └── url_history.json          ← histórico de URLs para deduplicação
├── tests/                        ← testes pytest (14 testes)
├── index.html                    ← site gerado (GitHub Pages)
├── static/                       ← CSS copiado para GitHub Pages
├── config.py                     ← configuração centralizada (dataclass frozen)
├── config_editor.py              ← configuração alteracoes
├── run.py                        ← ponto de entrada Flask (dev)
├── requirements.txt            ← dependências Python
├── .env.example                ← template de variáveis de ambiente
└── README.md                     ← este arquivo
```

---

## Configuração (primeira vez)

### 1. Secrets necessários

Acesse **Settings → Secrets → Actions** no repositório e adicione:

| Secret | Onde obter | Custo | Obrigatório |
|---|---|---|---|
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) | Gratuito (1.000 buscas/mês) | ✅ Sim |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | Gratuito (rate limit generoso) | ✅ Sim |
| `LANGFUSE_SECRET_KEY` | [langfuse.com](https://langfuse.com) | Gratuito (tier hobby) | ❌ Opcional |
| `LANGFUSE_PUBLIC_KEY` | [langfuse.com](https://langfuse.com) | Gratuito (tier hobby) | ❌ Opcional |

> **Sem `GROQ_API_KEY`**: o pipeline usa regex fallback automaticamente, sem custo, mas com qualidade reduzida.

### 2. GitHub Pages

Em **Settings → Pages**, confirme que a fonte é o branch `main`, pasta raiz `/`.

### 3. Variáveis de ambiente (local)

```bash
cp .env.example .env
# Edite .env com suas chaves
```

---

## Execução local

### Modo desenvolvimento (Flask + dados fake)

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar servidor Flask
python run.py
# Acesse http://127.0.0.1:5000
```

O Flask carrega dados reais se existirem; senão, usa dados fake para visualizar o design.

### Pipeline manual (dados reais)

```bash
# Rodar pipeline completo (busca → processa → gera site)
python -m app.services.pipeline

# O index.html na raiz será atualizado automaticamente
```

### Testes

```bash
python -m pytest tests/ -v
```

---

## Decisões arquiteturais

### Por que dados acumulativos?

Diferente de newsletters que sobrescrevem o conteúdo diário, o **IA Bolsa** mantém um histórico permanente. Isso permite:
- Análise de tendências ao longo do tempo
- Busca em notícias antigas por empresa ou tag
- Site mais rico e valioso a cada execução

### Por que Groq em vez de Claude/GPT?

- **Velocidade**: inferência em edge, sem fila
- **Custo**: tokens significativamente mais baratos
- **Fallback**: regex nativo garante funcionamento mesmo sem API

### Por que Flask + site estático?

- **Flask**: dev mode rápido com hot-reload e dados fake
- **Site estático**: GitHub Pages gratuito, sem servidor, sem manutenção

### Por que sentimento de mercado?

Classificar notícias como Bullish/Bearish/Neutral permite que investidores filtrem rapidamente o que importa para suas estratégias — diferencial que agregadores genéricos não oferecem.

---

## Licença

MIT © 2026 — IA Bolsa
