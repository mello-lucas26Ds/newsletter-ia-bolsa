# Pipeline completo: busca → deduplica → processa → salva → gera site.

import json
import time     
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from config import CONFIG
from app.services.ingest import TavilySource
from app.services.dedup import JsonDeduplicador
from app.services.process_ai import GroqSummarizer, RegexFallbackSummarizer
from app.services.newsletter import NewsletterFormatter
from app.services.generate_site import gerar_site


def executar_pipeline() -> Dict[str, Any]:
    # Executa o pipeline completo de geracao da newsletter.
    
    hoje = datetime.now().strftime("%Y-%m-%d")
    stats = {"data": hoje, "buscadas": 0, "novas": 0, "processadas": 0, "erros": 0}
    
    print(f"\n{'='*50}")
    print(f"  PIPELINE NEWSLETTER IA BOLSA — {hoje}")
    print(f"{'='*50}\n")
    
    # 1. Busca noticias na Tavily
    print("[1/5] Buscando noticias na Tavily...")
    try:
        ingestor = TavilySource(api_key=CONFIG.tavily_api_key)
        noticias_brutas = ingestor.buscar(max_resultados=CONFIG.max_noticias_por_execucao * 2)
        stats["buscadas"] = len(noticias_brutas)
        print(f"      {stats['buscadas']} noticias encontradas")
    except Exception as e:
        print(f"      ERRO: {type(e).__name__}")
        stats["erros"] += 1
        return stats
    
    # 2. Deduplica por URL + hash
    print("[2/5] Removendo duplicatas...")
    dedup = JsonDeduplicador(caminho_historico=CONFIG.diretorio_dados / "url_history.json")
    noticias_dicts = [
        {"titulo": n.titulo, "url": n.url, "snippet": n.snippet, 
         "conteudo": n.conteudo, "fonte": n.fonte, "data": n.data, "score": n.score}
        for n in noticias_brutas
    ]
    noticias_novas = dedup.filtrar_novas(noticias_dicts)
    stats["novas"] = len(noticias_novas)
    print(f"      {stats['novas']} noticias novas (total no historico: {dedup.total_vistas()})")
    
    if not noticias_novas:
        print("      Nenhuma noticia nova. Encerrando.")
        return stats
    
    # 3. Processa com IA (Groq)
    print("[3/5] Processando com Groq...")
    try:
        summarizer = GroqSummarizer(
            api_key=CONFIG.groq_api_key,
            modelo=CONFIG.groq_model,
            temperature=CONFIG.groq_temperature,
            max_tokens=CONFIG.groq_max_tokens,
        )
    except Exception as e:
        print(f"      ERRO ao inicializar Groq: {e}")
        print("      Usando fallback regex...")
        summarizer = RegexFallbackSummarizer()
    
    noticias_processadas = []
    for i, noticia in enumerate(noticias_novas[:CONFIG.max_noticias_por_execucao], 1):
        time.sleep(0.3)
        try:
            print(f"      [{i}/{min(len(noticias_novas), CONFIG.max_noticias_por_execucao)}] {noticia['titulo'][:60]}...")
            processada = summarizer.resumir(noticia)
            noticias_processadas.append(processada)
            stats["processadas"] += 1
        except Exception as e:
            print(f"      ERRO: {type(e).__name__}: {e}")
            stats["erros"] += 1
    
    # 4. Salva artefatos
    print("[4/5] Salvando artefatos...")
    formatter = NewsletterFormatter()

    # --- 4.1 Snapshot do dia (so as novas, para arquivo) ---
    json_path = CONFIG.diretorio_dados / f"news_processed_{hoje}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(formatter.para_json(noticias_processadas, hoje))
    print(f"      JSON: {json_path.name}")

    # --- 4.2 LER acumulado antigo ANTES de sobrescrever ---
    acumulado = []
    json_atual = CONFIG.diretorio_dados / "news_processed.json"
    if json_atual.exists():
        try:
            with open(json_atual, "r", encoding="utf-8") as f:
                acumulado = json.load(f).get("noticias", [])
        except:
            pass

    # --- 4.3 Mesclar: novas no topo + antigas ---
    urls_existentes = {n.get("url") for n in acumulado}
    novas_unicas = [n for n in noticias_processadas if n.get("url") not in urls_existentes]
    noticias_finais = novas_unicas + acumulado

    # --- 4.4 Salvar acumulado (AGORA sim, depois de ler o antigo) ---
    with open(json_atual, "w", encoding="utf-8") as f:
        f.write(formatter.para_json(noticias_finais, hoje))

    # --- 4.5 Markdown do dia ---
    md_path = CONFIG.diretorio_dados / f"newsletter_{hoje}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(formatter.para_markdown(noticias_processadas, hoje))
    print(f"      Markdown: {md_path.name}")

    # --- 4.6 Registrar URLs no historico ---
    dedup.registrar(noticias_novas[:CONFIG.max_noticias_por_execucao])

    # 5. Gera site estatico (LE o news_processed.json acumulado e cria index.html)
    print("[5/5] Gerando site estatico...")
    caminho_site = gerar_site()
    if caminho_site:
        print(f"      Site: {caminho_site.name}")

    print(f"\n{'='*50}")
    print(f"  CONCLUIDO: {stats['processadas']} noticias novas hoje")
    print(f"  TOTAL ACUMULADO: {len(noticias_finais)} noticias no site")
    print(f"{'='*50}\n")

    return stats