# Editor de configuracao da newsletter.
# Rode: python config_editor.py

import json
from pathlib import Path
from datetime import datetime


CONFIG_FILE = Path("newsletter_config.json")


DEFAULT_CONFIG = {
    "nome": "Newsletter IA Bolsa",
    "descricao": "Inteligencia Artificial e Mercado Financeiro",
    "queries": [
        "AI stock market investment earnings report",
        "NVIDIA AMD TSMC semiconductor stock earnings",
        "data center REIT cloud infrastructure stock",
        "AI partnership deal merger acquisition tech",
        "NASDAQ tech stock rally AI sector",
        "Ibovespa B3 Brazil tech stocks AI",
    ],
    "max_noticias": 10,
    "dominios": [
        "bloomberg.com", "reuters.com", "ft.com", "wsj.com",
        "cnbc.com", "marketwatch.com", "investing.com",
        "valor.globo.com", "infomoney.com.br", "moneytimes.com.br",
        "seekingalpha.com", "theverge.com", "techcrunch.com",
        "forbes.com", "economictimes.com", "benzinga.com",
        "financialpost.com", "businessinsider.com", "yahoo.com"
    ],
    "tags_permitidas": ["AI", "Semiconductor", "Data Center", "Cloud", "NASDAQ", "B3", "Ibovespa", "Partnership", "Merger", "Acquisition", "Infrastructure", "Tech", "Market", "Rally", "Earnings"],
    "idioma_resumo": "portugues",
    "tema": "dark",  # dark ou light
    "cores": {
        "primaria": "#00f0ff",
        "secundaria": "#76ff03",
        "alerta": "#ff0055"
    }
}


def carregar_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()


def salvar_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"Configuracao salva em {CONFIG_FILE}")


def listar_queries(config):
    print(f"\n{'='*50}")
    print("  QUERIES ATIVAS")
    print(f"{'='*50}")
    for i, q in enumerate(config["queries"], 1):
        print(f"  {i}. {q}")
    print(f"{'='*50}\n")


def adicionar_query(config):
    print("\n--- Adicionar Query ---")
    print("Exemplos de formato:")
    print("  'AI agents enterprise automation stock'")
    print("  'robotics automation market investment'")
    print("  'machine learning healthcare stocks'")
    print("(cruza tecnologia + termo financeiro para melhores resultados)\n")
    
    nova = input("Digite a nova query: ").strip()
    if not nova:
        print("Query vazia. Cancelado.")
        return
    
    config["queries"].append(nova)
    print(f"Adicionada: {nova}")
    print(f"Total de queries: {len(config['queries'])}")


def remover_query(config):
    listar_queries(config)
    try:
        idx = int(input("Numero da query para remover: ")) - 1
        if 0 <= idx < len(config["queries"]):
            removida = config["queries"].pop(idx)
            print(f"Removida: {removida}")
        else:
            print("Numero invalido.")
    except ValueError:
        print("Entrada invalida.")


def editar_max_noticias(config):
    atual = config["max_noticias"]
    print(f"\nMax noticias atual: {atual}")
    novo = input("Novo valor (1-50): ").strip()
    if novo.isdigit():
        val = int(novo)
        if 1 <= val <= 50:
            config["max_noticias"] = val
            print(f"Atualizado para {val}")
        else:
            print("Fora do limite 1-50.")
    else:
        print("Valor invalido.")


def editar_nome(config):
    print(f"\nNome atual: {config['nome']}")
    novo = input("Novo nome: ").strip()
    if novo:
        config["nome"] = novo
        print(f"Atualizado: {novo}")


def resetar_padrao():
    confirm = input("Tem certeza? Isso apaga sua configuracao customizada (s/n): ").lower()
    if confirm == "s":
        salvar_config(DEFAULT_CONFIG)
        print("Configuracao resetada para padrao.")
        return DEFAULT_CONFIG.copy()
    print("Cancelado.")
    return None


def menu():
    config = carregar_config()
    
    while True:
        print(f"\n{'='*50}")
        print(f"  EDITOR DE CONFIGURACAO")
        print(f"  Newsletter: {config['nome']}")
        print(f"{'='*50}")
        print("  1. Listar queries")
        print("  2. Adicionar query")
        print("  3. Remover query")
        print("  4. Editar max noticias")
        print("  5. Editar nome da newsletter")
        print("  6. Ver configuracao completa")
        print("  7. Salvar e sair")
        print("  8. Resetar para padrao")
        print(f"{'='*50}")
        
        opcao = input("Escolha: ").strip()
        
        if opcao == "1":
            listar_queries(config)
        elif opcao == "2":
            adicionar_query(config)
        elif opcao == "3":
            remover_query(config)
        elif opcao == "4":
            editar_max_noticias(config)
        elif opcao == "5":
            editar_nome(config)
        elif opcao == "6":
            print(json.dumps(config, ensure_ascii=False, indent=2))
        elif opcao == "7":
            salvar_config(config)
            print("Configuracao salva. Execute o pipeline para aplicar.")
            break
        elif opcao == "8":
            novo = resetar_padrao()
            if novo:
                config = novo
        else:
            print("Opcao invalida.")


if __name__ == "__main__":
    menu()