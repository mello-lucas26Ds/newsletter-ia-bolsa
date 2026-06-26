# Rotas Flask (modo desenvolvimento). Nao roda em producao (GitHub Pages).

from flask import Blueprint, render_template, jsonify, abort
from pathlib import Path
import json
from datetime import datetime

from config import CONFIG


bp = Blueprint("principal", __name__)


@bp.route("/")
def pagina_inicial():
    caminho_dados = CONFIG.diretorio_dados / "news_processed.json"
    noticias = []
    data_newsletter = datetime.now().strftime("%Y-%m-%d")
    fonte_dados = "FAKE"

    if caminho_dados.exists():
        try:
            with open(caminho_dados, "r", encoding="utf-8") as f:
                dados = json.load(f)
                noticias = dados.get("noticias", [])
                data_newsletter = dados.get("data", data_newsletter)
                if noticias:
                    fonte_dados = "REAL"
                    print(f"[FLASK] Dados REAIS: {len(noticias)} noticias de {data_newsletter}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"[FLASK] ERRO ao ler JSON: {e}")

    if not noticias:
        noticias = _gerar_dados_fake()
        data_newsletter = datetime.now().strftime("%Y-%m-%d")
        fonte_dados = "FAKE"
        print(f"[FLASK] Fallback FAKE: {len(noticias)} noticias")

    return render_template(
        "index.html",
        noticias=noticias,
        data=data_newsletter,
        total=len(noticias),
        fonte_dados=fonte_dados
    )


@bp.route("/newsletter/<string:data>")
def pagina_newsletter(data: str):
    # Valida formato YYYY-MM-DD
    try:
        datetime.strptime(data, "%Y-%m-%d")
    except ValueError:
        abort(404)
    
    caminho_md = CONFIG.diretorio_dados / f"newsletter_{data}.md"
    caminho_json = CONFIG.diretorio_dados / f"news_processed_{data}.json"
    
    noticias = []
    conteudo_md = ""
    
    if caminho_json.exists():
        try:
            with open(caminho_json, "r", encoding="utf-8") as f:
                conteudo = f.read().strip()
                if conteudo:
                    noticias = json.loads(conteudo).get("noticias", [])
                else:
                    print(f"[FLASK] JSON vazio: {caminho_json.name}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"[FLASK] ERRO ao ler JSON: {e}")
    elif caminho_md.exists():
        try:
            with open(caminho_md, "r", encoding="utf-8") as f:
                conteudo_md = f.read()
        except IOError as e:
            print(f"[FLASK] ERRO ao ler Markdown: {e}")
    else:
        noticias = _gerar_dados_fake()
    
    return render_template(
        "newsletter.html",
        data=data,
        noticias=noticias,
        conteudo_md=conteudo_md
    )


@bp.route("/api/health")
def health_check():
    return jsonify({
        "status": "ok",
        "ambiente": CONFIG.flask_env,
        "timestamp": datetime.now().isoformat(),
        "versao": "1.0.0-fase1"
    })


@bp.route("/api/config-check")
def verificar_configuracao():
    # Nunca expoe chaves reais, apenas booleanos de confirmacao
    return jsonify({
        "tavily_configurado": bool(CONFIG.tavily_api_key and "sua_chave" not in CONFIG.tavily_api_key),
        "groq_configurado": bool(CONFIG.groq_api_key and "sua_chave" not in CONFIG.groq_api_key),
        "langfuse_configurado": bool(CONFIG.langfuse_secret_key),
        "max_noticias": CONFIG.max_noticias_por_execucao,
        "modelo_groq": CONFIG.groq_model,
    })


@bp.route("/dev/panel")
def painel_desenvolvimento():
    # Dashboard de status para desenvolvedores
    arquivos_json = list(CONFIG.diretorio_dados.glob("news_processed*.json"))
    arquivos_md = list(CONFIG.diretorio_dados.glob("newsletter_*.md"))
    
    stats = {
        "total_json": len(arquivos_json),
        "total_md": len(arquivos_md),
        "ultimo_json": max((f.name for f in arquivos_json), default="Nenhum"),
        "diretorio_dados": str(CONFIG.diretorio_dados),
    }
    
    return render_template("dev/panel.html", stats=stats, config=CONFIG)


def _gerar_dados_fake():
    # Dados ficticios para visualizar o template sem gastar APIs
    return [
        {
            "titulo": "NVIDIA anuncia novo superchip para data centers de IA",
            "url": "https://example.com/nvidia-superchip",
            "fonte": "Bloomberg",
            "data": "2026-06-25",
            "resumo": "A NVIDIA revelou o Blackwell Ultra, superchip com 288GB de HBM3e, prometendo 4x mais performance em treinamento de LLMs. O anuncio impulsionou as acoes em 3,2% no pre-market.",
            "sentimento": "bullish",
            "tags": ["Semiconductor", "AI", "Data Center"],
            "score_relevancia": 9.5,
        },
        {
            "titulo": "Microsoft investe US$ 10 bi em parceria com OpenAI",
            "url": "https://example.com/ms-openai",
            "fonte": "Reuters",
            "data": "2026-06-25",
            "resumo": "A Microsoft ampliou sua parceria estrategica com a OpenAI, investindo mais US$ 10 bilhoes em infraestrutura de nuvem. O movimento reforca a aposta em agentes de IA corporativos.",
            "sentimento": "bullish",
            "tags": ["Partnership", "Cloud", "AI"],
            "score_relevancia": 9.2,
        },
        {
            "titulo": "Ibovespa recua com tensao em semicondutores asiaticos",
            "url": "https://example.com/ibovespa-queda",
            "fonte": "Valor Economico",
            "data": "2026-06-25",
            "resumo": "O Ibovespa operou em queda de 0,8% nesta sessao, pressionado por preocupacoes com restricoes de exportacao de chips para a China. O setor de tecnologia liderou as perdas.",
            "sentimento": "bearish",
            "tags": ["B3", "Ibovespa", "Semiconductor"],
            "score_relevancia": 8.7,
        },
        {
            "titulo": "Google Cloud expande data centers no Brasil",
            "url": "https://example.com/google-brasil",
            "fonte": "TechCrunch",
            "data": "2026-06-25",
            "resumo": "O Google anunciou a expansao de sua regiao cloud no Brasil, com novo data center em Sao Paulo. A iniciativa visa atender demanda crescente por IA generativa na America Latina.",
            "sentimento": "bullish",
            "tags": ["Data Center", "Infrastructure", "Cloud"],
            "score_relevancia": 8.4,
        },
        {
            "titulo": "AMD perde contrato de supercomputacao para Intel",
            "url": "https://example.com/amd-intel",
            "fonte": "MarketWatch",
            "data": "2026-06-25",
            "resumo": "A Intel venceu licitacao para fornecer CPUs Xeon para supercomputador do Departamento de Energia dos EUA, no valor de US$ 500 milhoes. A AMD, favorita ate entao, viu suas acoes recuarem 2,1%.",
            "sentimento": "bearish",
            "tags": ["Semiconductor", "Competition"],
            "score_relevancia": 7.9,
        },
        {
            "titulo": "B3 lanca indice de empresas de IA",
            "url": "https://example.com/b3-ia",
            "fonte": "InfoMoney",
            "data": "2026-06-25",
            "resumo": "A B3 anunciou o B3 IA Index, composto por 20 empresas brasileiras com exposicao a inteligencia artificial. O indice tera replicacao via ETF ainda no terceiro trimestre.",
            "sentimento": "bullish",
            "tags": ["B3", "Index", "AI"],
            "score_relevancia": 8.1,
        },
        {
            "titulo": "Tesla reporta queda de 15% em vendas na China",
            "url": "https://example.com/tesla-china",
            "fonte": "CNBC",
            "data": "2026-06-25",
            "resumo": "As vendas da Tesla na China despencaram 15% no ultimo trimestre, pressionadas por concorrencia da BYD e Xiaomi. O resultado abaixo do esperado afetou o sentimento em acoes de EVs.",
            "sentimento": "bearish",
            "tags": ["EV", "China", "Market"],
            "score_relevancia": 7.5,
        },
        {
            "titulo": "Amazon Web Services anuncia chips de inferencia proprios",
            "url": "https://example.com/aws-chips",
            "fonte": "The Verge",
            "data": "2026-06-25",
            "resumo": "A AWS apresentou os chips Trainium3 e Inferentia3, projetados para treinamento e inferencia de modelos de IA. A empresa afirma que o custo de inferencia caira 40%.",
            "sentimento": "bullish",
            "tags": ["Semiconductor", "Cloud", "AI"],
            "score_relevancia": 8.8,
        },
        {
            "titulo": "Nasdaq atinge recorde historico com rally de tech",
            "url": "https://example.com/nasdaq-recorde",
            "fonte": "Financial Times",
            "data": "2026-06-25",
            "resumo": "O Nasdaq Composite fechou em novo recorde historico, impulsionado por resultados acima do esperado de empresas de software. O setor de IA generativa liderou os ganhos.",
            "sentimento": "bullish",
            "tags": ["NASDAQ", "Tech", "Rally"],
            "score_relevancia": 9.0,
        },
        {
            "titulo": "TSMC aumenta investimento em fabrica do Arizona",
            "url": "https://example.com/tsmc-arizona",
            "fonte": "Wall Street Journal",
            "data": "2026-06-25",
            "resumo": "A TSMC anunciou aumento de US$ 8 bilhoes em investimentos na fabrica do Arizona, totalizando US$ 65 bilhoes. A producao de chips de 2nm deve iniciar em 2028.",
            "sentimento": "bullish",
            "tags": ["Semiconductor", "Infrastructure", "TSMC"],
            "score_relevancia": 8.3,
        },
    ]