# Gera site estatico (index.html + static/) para GitHub Pages.
# LE todos os news_processed_YYYY-MM-DD.json dos ultimos 7 dias.
# Suporta filtro por EDICAO (data do arquivo) via JavaScript.

import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta
import json

from config import CONFIG


def _parse_data(data_str):
    if not data_str:
        return None
    data_str = str(data_str).strip()
    try:
        return datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(data_str.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    try:
        return datetime.strptime(data_str[:10], "%Y-%m-%d").date()
    except ValueError:
        pass
    return None


def _carregar_noticias_com_datas(diretorio_dados):
    hoje = datetime.now().date()
    limite = hoje - timedelta(days=7)

    noticias_por_edicao = {}  # { "2026-06-26": [noticias], ... }
    noticias_todas = []
    arquivos_lidos = []

    for arquivo in sorted(diretorio_dados.glob("news_processed_*.json")):
        nome = arquivo.stem
        try:
            data_arquivo = datetime.strptime(nome.replace("news_processed_", ""), "%Y-%m-%d").date()
        except ValueError:
            continue

        if data_arquivo < limite:
            continue

        edicao = data_arquivo.strftime("%Y-%m-%d")

        with open(arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)
            noticias = dados.get("noticias", [])

        # Filtrar noticias com data de publicacao valida
        noticias_validas = []
        for n in noticias:
            data_pub = _parse_data(n.get("data", ""))
            if data_pub and data_pub >= limite:
                noticias_validas.append(n)

        if edicao not in noticias_por_edicao:
            noticias_por_edicao[edicao] = []
        noticias_por_edicao[edicao].extend(noticias_validas)

        # Adicionar edicao a cada noticia para o template
        for n in noticias_validas:
            n["_edicao"] = edicao
            noticias_todas.append(n)

        arquivos_lidos.append((arquivo.name, len(noticias_validas)))

    # Remover duplicatas por URL
    vistas = set()
    noticias_unicas = []
    for n in noticias_todas:
        url = n.get("url", "")
        if url and url not in vistas:
            vistas.add(url)
            noticias_unicas.append(n)

    noticias_unicas.sort(
        key=lambda x: _parse_data(x.get("data", "")) or datetime.min.date(),
        reverse=True,
    )

    datas_disponiveis = sorted(noticias_por_edicao.keys(), reverse=True)

    return noticias_unicas, arquivos_lidos, datas_disponiveis, noticias_por_edicao


def gerar_site():
    diretorio_dados = CONFIG.diretorio_dados

    noticias, arquivos_lidos, datas_disponiveis, noticias_por_edicao = _carregar_noticias_com_datas(
        diretorio_dados
    )

    if not noticias:
        print("AVISO: nenhuma noticia encontrada nos ultimos 7 dias.")
        caminho_fixo = diretorio_dados / "news_processed.json"
        if caminho_fixo.exists():
            with open(caminho_fixo, "r", encoding="utf-8") as f:
                dados = json.load(f)
                noticias = dados.get("noticias", [])
            print(f"Fallback: carregado {len(noticias)} do arquivo fixo.")

    data_newsletter = datetime.now().strftime("%Y-%m-%d")

    total = len(noticias)
    bullish = sum(1 for n in noticias if n.get("sentimento") == "bullish")
    bearish = sum(1 for n in noticias if n.get("sentimento") == "bearish")
    neutral = total - bullish - bearish

    raiz = CONFIG.diretorio_dados.parent
    static_src = CONFIG.diretorio_static
    static_dst = raiz / "static"

    if static_dst.exists():
        shutil.rmtree(static_dst)
    shutil.copytree(static_src, static_dst)

    env = Environment(loader=FileSystemLoader(str(CONFIG.diretorio_templates)))
    template = env.get_template("index.html")

    html = template.render(
        noticias=noticias,
        data=data_newsletter,
        total=total,
        bullish=bullish,
        bearish=bearish,
        neutral=neutral,
        url_for=None,
        fonte_dados="REAL" if noticias else "VAZIO",
        arquivos_lidos=arquivos_lidos,
        datas_disponiveis=datas_disponiveis,
        noticias_por_data=noticias_por_edicao,
    )

    caminho_saida = raiz / "index.html"
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Site gerado: {caminho_saida}")
    print(f"CSS copiado: {static_dst / 'css/style.css'}")
    print(f"Arquivos lidos: {arquivos_lidos}")
    print(f"Datas disponiveis: {datas_disponiveis}")
    print(f"Noticias no site: {total} (filtradas dos ultimos 7 dias)")
    return caminho_saida


if __name__ == "__main__":
    gerar_site()