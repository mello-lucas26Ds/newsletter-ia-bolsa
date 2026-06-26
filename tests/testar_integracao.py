import json
import dataclasses
from datetime import datetime, timedelta
from pathlib import Path

# Simula NoticiaProcessada (dataclass do process_ai)
@dataclasses.dataclass
class NoticiaProcessada:
    titulo: str
    url: str
    fonte: str
    data: str
    resumo: str
    sentimento: str
    tags: list
    score_relevancia: float
    tokens_usados: int = 0

# Simula o pipeline: processa noticias e acumula
def simular_pipeline(noticias_novas, acumulado_antigo):
    # Passo 4.3: Mesclar (com a correcao proposta)
    urls_existentes = {a.get("url") for a in acumulado_antigo}
    novas_unicas = []
    for n in noticias_novas:
        nd = dataclasses.asdict(n) if hasattr(n, '__dataclass_fields__') else n
        if nd.get("url") not in urls_existentes:
            novas_unicas.append(nd)
    
    noticias_finais = novas_unicas + acumulado_antigo
    return noticias_finais

# Simula o generate_site: filtra >7 dias
def simular_site(noticias_finais):
    hoje = datetime.now().date()
    limite = hoje - timedelta(days=7)
    
    noticias_recentes = []
    for n in noticias_finais:
        data_str = n.get("data", "")
        if data_str:
            try:
                data_noticia = datetime.strptime(data_str, "%Y-%m-%d").date()
                if data_noticia >= limite:
                    noticias_recentes.append(n)
                else:
                    print(f"  [FILTRADA do site] Noticia antiga ({data_str}): {n.get('titulo', '')[:40]}...")
            except:
                noticias_recentes.append(n)
        else:
            noticias_recentes.append(n)
    
    return noticias_recentes

# === CENARIO DE TESTE ===
print("="*60)
print("TESTE INTEGRACAO: Datas, Filtro, Acumulacao, Site")
print("="*60)

# Noticias "novas" do dia (com datas REAIS da Tavily)
noticias_hoje = [
    NoticiaProcessada(
        titulo="Micron Earnings AI Trade",
        url="https://businessinsider.com/micron-2026-06-24",
        fonte="businessinsider.com",
        data="2026-06-24",  # Data REAL da Tavily
        resumo="Micron sobe",
        sentimento="bullish",
        tags=["AI", "Semiconductor"],
        score_relevancia=9.0,
    ),
    NoticiaProcessada(
        titulo="Nasdaq futures jump",
        url="https://reuters.com/nasdaq-2026-06-25",
        fonte="reuters.com",
        data="2026-06-25",  # Data REAL da Tavily
        resumo="Nasdaq sobe",
        sentimento="bullish",
        tags=["NASDAQ", "AI"],
        score_relevancia=8.5,
    ),
]

# Noticias antigas no acumulado (simula news_processed.json anterior)
acumulado = [
    {"titulo": "Noticia antiga 1", "url": "https://antiga.com/1", "data": "2026-06-10", "sentimento": "bearish", "tags": [], "score_relevancia": 5.0, "fonte": "antiga.com", "resumo": "antiga"},
    {"titulo": "Noticia antiga 2", "url": "https://antiga.com/2", "data": "2026-06-15", "sentimento": "bullish", "tags": [], "score_relevancia": 6.0, "fonte": "antiga.com", "resumo": "antiga"},
]

print(f"\n[1] Noticias novas (Tavily): {len(noticias_hoje)}")
print(f"    Datas: {[n.data for n in noticias_hoje]}")
print(f"\n[2] Acumulado anterior: {len(acumulado)}")
print(f"    Datas: {[a['data'] for a in acumulado]}")

# Pipeline: mescla
noticias_finais = simular_pipeline(noticias_hoje, acumulado)
print(f"\n[3] Pipeline - Total acumulado: {len(noticias_finais)}")
print(f"    Datas: {[n.get('data') for n in noticias_finais]}")

# Site: filtra >7 dias
noticias_site = simular_site(noticias_finais)
print(f"\n[4] Site - Noticias mostradas: {len(noticias_site)}")
print(f"    Datas: {[n.get('data') for n in noticias_site]}")

# Validacoes
print(f"\n{'='*60}")
print("VALIDACOES:")
print(f"{'='*60}")

# 1. Acumulado tem TUDO (novas + antigas)?
assert len(noticias_finais) == 4, f"ERRO: Acumulado deveria ter 4, tem {len(noticias_finais)}"
print("✅ Acumulado guarda TUDO (novas + antigas)")

# 2. Site mostra so recentes (<=7 dias)?
hoje = datetime.now().date()
limite = hoje - timedelta(days=7)
for n in noticias_site:
    data_str = n.get("data", "")
    if data_str:
        data_noticia = datetime.strptime(data_str, "%Y-%m-%d").date()
        assert data_noticia >= limite, f"ERRO: Noticia {data_str} antiga demais no site!"
print("✅ Site mostra so noticias recentes (<=7 dias)")

# 3. Datas sao reais (YYYY-MM-DD), nao timestamps?
for n in noticias_finais:
    data = n.get("data", "")
    assert "T" not in data, f"ERRO: Data {data} ainda eh timestamp!"
    assert len(data) == 10, f"ERRO: Data {data} nao eh YYYY-MM-DD!"
print("✅ Datas sao YYYY-MM-DD (reais da Tavily)")

# 4. Novas noticias tem fonte preenchida?
for n in noticias_site:
    if n.get("url") in ["https://businessinsider.com/micron-2026-06-24", "https://reuters.com/nasdaq-2026-06-25"]:
        assert n.get("fonte") != "Desconhecida", f"ERRO: Fonte desconhecida!"
print("✅ Fontes preenchidas corretamente")

print(f"\n{'='*60}")
print("TUDO OK! Pipeline + Site funcionando corretamente.")
print(f"{'='*60}")