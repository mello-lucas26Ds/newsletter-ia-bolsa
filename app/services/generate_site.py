# Gera site estatico (index.html + static/) para GitHub Pages.
# Copia CSS para static/ na raiz para caminhos relativos funcionarem.

import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import json

from config import CONFIG


def gerar_site():
    caminho_json = CONFIG.diretorio_dados / "news_processed.json"
    
    if not caminho_json.exists():
        print("ERRO: news_processed.json nao encontrado. Rode o pipeline primeiro.")
        return None
    
    with open(caminho_json, "r", encoding="utf-8") as f:
        dados = json.load(f)
    
    noticias = dados.get("noticias", [])
    data_newsletter = dados.get("meta", {}).get("data", datetime.now().strftime("%Y-%m-%d"))
    
    total = len(noticias)
    bullish = sum(1 for n in noticias if n.get("sentimento") == "bullish")
    bearish = sum(1 for n in noticias if n.get("sentimento") == "bearish")
    
    # Copia CSS para static/ na raiz (GitHub Pages)
    raiz = CONFIG.diretorio_dados.parent
    static_src = CONFIG.diretorio_static
    static_dst = raiz / "static"
    
    if static_dst.exists():
        shutil.rmtree(static_dst)
    shutil.copytree(static_src, static_dst)
    
    # Renderiza index.html
    env = Environment(loader=FileSystemLoader(str(CONFIG.diretorio_templates)))
    template = env.get_template("index.html")
    
    html = template.render(
        noticias=noticias,
        data=data_newsletter,
        total=total,
        bullish=bullish,
        bearish=bearish,
        url_for=None,
        fonte_dados="REAL" if noticias else "VAZIO"
    )
    
    caminho_saida = raiz / "index.html"
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Site gerado: {caminho_saida}")
    print(f"CSS copiado: {static_dst / 'css/style.css'}")
    return caminho_saida


if __name__ == "__main__":
    gerar_site()