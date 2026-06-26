# Pipeline completo: busca → deduplica → processa → salva → gera site.

import json
import time
import dataclasses
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from config import CONFIG
from app.services.ingest import TavilySource
from app.services.dedup import JsonDeduplicador
from app.services.process_ai import GroqSummarizer, RegexFallbackSummarizer
from app.services.newsletter import NewsletterFormatter
from app.services.generate_site import gerar_site


def _normalizar_data(data_str, hoje_str):
    """Converte qualquer formato de data para YYYY-MM-DD."""
    if not data_str:
        return hoje_str
    data_str = str(data_str).strip()
    try:
        datetime.strptime(data_str, "%Y-%m-%d")
        return data_str
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(data_str.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except ValueError:
        pass
    try:
        return datetime.strptime(data_str[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return hoje_str


def _extrair_data(noticia, hoje_str):
    """Extrai campo 'data' de dict ou dataclass."""
    if hasattr(noticia, '__dataclass_fields__'):
        return getattr(noticia, 'data', '') or ''
    return noticia.get("data", "") or ""


def executar_pipeline() -> Dict[str, Any]:
    hoje = datetime.now().strftime("%Y-%m-%d")
    hoje_date = datetime.now().date()
    limite = hoje_date - timedelta(days=7)
    stats = {"data": hoje, "buscadas": 0, "novas": 0, "processadas": 0, "erros": 0}

    print(f"\n{'='*50}")
    print(f"  PIPELINE NEWSLETTER IA BOLSA — {hoje}")
    print(f"{'='*50}\n")

    # 1. Busca
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

    # 2. Deduplica
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

    # 3. Processa com IA
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

    # --- 4.0 Normalizar campo 'data' ---
    for n in noticias_processadas:
        data_raw = _extrair_data(n, hoje)
        data_norm = _normalizar_data(data_raw, hoje)
        if hasattr(n, '__dataclass_fields__'):
            # Dataclass: criar novo objeto com data normalizada
            nd = dataclasses.asdict(n)
            nd["data"] = data_norm
            # Recriar o objeto (assumindo que NoticiaProcessada aceita **kwargs)
            # Como nao sabemos o constructor exato, vamos modificar o dict
            # e deixar o formatter lidar com isso
            for field in dataclasses.fields(n):
                if field.name == 'data':
                    object.__setattr__(n, 'data', data_norm)
                    break
        else:
            n["data"] = data_norm

    # --- 4.1 Snapshot do dia ---
    json_path = CONFIG.diretorio_dados / f"news_processed_{hoje}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(formatter.para_json(noticias_processadas, hoje))
    print(f"      JSON snapshot: {json_path.name}")

    # --- 4.2 LER acumulado antigo ---
    acumulado = []
    json_atual = CONFIG.diretorio_dados / "news_processed.json"
    if json_atual.exists():
        try:
            with open(json_atual, "r", encoding="utf-8") as f:
                acumulado = json.load(f).get("noticias", [])
        except:
            pass

    # --- 4.3 Normalizar datas do acumulado ---
    for a in acumulado:
        a["data"] = _normalizar_data(a.get("data", ""), hoje)

    # --- 4.4 Mesclar: novas no topo + antigas (limite 7 dias) ---
    urls_existentes = {a.get("url") for a in acumulado}
    novas_unicas = []
    for n in noticias_processadas:
        url = getattr(n, 'url', '') if hasattr(n, '__dataclass_fields__') else n.get("url", "")
        if url not in urls_existentes:
            novas_unicas.append(dataclasses.asdict(n) if hasattr(n, '__dataclass_fields__') else n)

    acumulado_filtrado = []
    for a in acumulado:
        try:
            data_pub = datetime.strptime(a.get("data", hoje), "%Y-%m-%d").date()
            if data_pub >= limite:
                acumulado_filtrado.append(a)
            else:
                print(f"      [LIMPOU] Noticia antiga ({a.get('data')}): {a.get('titulo', '')[:40]}...")
        except ValueError:
            print(f"      [LIMPOU] Data invalida: {a.get('titulo', '')[:40]}...")

    noticias_finais = novas_unicas + acumulado_filtrado

    # --- 4.5 Salvar acumulado ---
    with open(json_atual, "w", encoding="utf-8") as f:
        f.write(formatter.para_json(noticias_finais, hoje))
    print(f"      JSON acumulado: {json_atual.name} ({len(noticias_finais)} noticias)")

    # --- 4.6 Markdown ---
    noticias_md = []
    for n in noticias_processadas:
        data_raw = _extrair_data(n, hoje)
        data_norm = _normalizar_data(data_raw, hoje)
        try:
            data_pub = datetime.strptime(data_norm, "%Y-%m-%d").date()
            if data_pub >= limite:
                noticias_md.append(n)
        except ValueError:
            pass

    md_path = CONFIG.diretorio_dados / f"newsletter_{hoje}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(formatter.para_markdown(noticias_md, hoje))
    print(f"      Markdown: {md_path.name}")

    # --- 4.7 Registrar URLs ---
    dedup.registrar(noticias_novas[:CONFIG.max_noticias_por_execucao])

    # 5. Gera site
    print("[5/5] Gerando site estatico...")
    caminho_site = gerar_site()
    if caminho_site:
        print(f"      Site: {caminho_site.name}")

    print(f"\n{'='*50}")
    print(f"  CONCLUIDO: {stats['processadas']} noticias novas hoje")
    print(f"  TOTAL ACUMULADO: {len(noticias_finais)} noticias no site")
    print(f"{'='*50}\n")

    return stats


if __name__ == "__main__":
    executar_pipeline()