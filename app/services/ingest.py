# Coleta de noticias via Tavily API.

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None


@dataclass
class NoticiaBruta:
    titulo: str
    url: str
    snippet: str
    conteudo: str
    fonte: str
    data: str
    score: float


class TavilySource:
    # Queries refinadas: IA + Mercado Financeiro (cruzado, nao generico)
    QUERIES_PADRAO = [
        "AI stock market investment earnings report",
        "NVIDIA AMD TSMC semiconductor stock earnings",
        "data center REIT cloud infrastructure stock",
        "AI partnership deal merger acquisition tech",
        "NASDAQ tech stock rally AI sector",
        "Ibovespa B3 Brazil tech stocks AI",
    ]
    
    # Whitelist de fontes confiaveis
    DOMINIOS_CONFIAVEIS = [
        "bloomberg.com", "reuters.com", "ft.com", "wsj.com",
        "cnbc.com", "marketwatch.com", "investing.com",
        "valor.globo.com", "infomoney.com.br", "moneytimes.com.br",
        "seekingalpha.com", "theverge.com", "techcrunch.com",
        "forbes.com", "economictimes.com", "benzinga.com",
        "financialpost.com", "businessinsider.com", "yahoo.com"
    ]
    
    def __init__(self, api_key: str):
        if not api_key or api_key == "dev-mode-no-key":
            raise ValueError("TAVILY_API_KEY invalida.")
        
        if TavilyClient is None:
            raise ImportError("tavily-python nao instalado. Rode: pip install tavily-python")
        
        self.client = TavilyClient(api_key=api_key)
    
    def buscar(self, queries: List[str] = None, max_resultados: int = 10) -> List[NoticiaBruta]:
        queries = queries or self.QUERIES_PADRAO
        todos_resultados: List[Dict[str, Any]] = []
        
        for query in queries:
            resposta = None
            
            # Tenta com topic="news" primeiro (tem published_date)
            try:
                resposta = self.client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=5,
                    include_domains=self.DOMINIOS_CONFIAVEIS,
                    topic="news",
                )
            except Exception as e:
                print(f"      [Tavily] topic=news falhou para '{query[:30]}...': {e}")
            
            # Se falhou ou veio vazio, fallback para general
            if not resposta or not resposta.get("results"):
                try:
                    resposta = self.client.search(
                        query=query,
                        search_depth="advanced",
                        max_results=5,
                        include_domains=self.DOMINIOS_CONFIAVEIS,
                    )
                except Exception as e:
                    print(f"      [Tavily] fallback general tambem falhou: {e}")
                    continue
            
            # ADICIONA OS RESULTADOS NA LISTA
            todos_resultados.extend(resposta.get("results", []))
            time.sleep(0.5)
        
        # Remove duplicatas por URL antes de processar
        vistos = set()
        unicos = []
        for r in todos_resultados:
            url = r.get("url", "")
            if url and url not in vistos:
                vistos.add(url)
                unicos.append(r)
        
        # Ordena por score e pega os melhores
        unicos.sort(key=lambda x: x.get("score", 0), reverse=True)
        melhores = unicos[:max_resultados]
        
        return [self._normalizar(r) for r in melhores]
    
    def _normalizar(self, resultado: Dict[str, Any]) -> NoticiaBruta:
        from urllib.parse import urlparse
        from email.utils import parsedate_to_datetime
        
        raw_fonte = resultado.get("source", "")
        url = resultado.get("url", "")
        
        if not raw_fonte or not raw_fonte.strip():
            if url:
                dominio = urlparse(url).netloc.replace("www.", "")
                raw_fonte = dominio or "Desconhecida"
            else:
                raw_fonte = "Desconhecida"
        
        # Parseia published_date real (ex: "Wed, 24 Jun 2026 23:50:24 GMT")
        data_raw = resultado.get("published_date", "")
        data_final = ""
        if data_raw:
            try:
                dt = parsedate_to_datetime(data_raw)
                data_final = dt.strftime("%Y-%m-%d")
            except:
                data_final = ""
        
        # Se nao conseguiu parsear, tenta extrair da URL
        if not data_final and url:
            import re
            match = re.search(r'/(20\d{2})[/-](\d{2})[/-](\d{2})', url)
            if match:
                ano, mes, dia = match.groups()
                data_final = f"{ano}-{mes}-{dia}"
        
        # Fallback: deixa vazio (pipeline filtra ou usa hoje se necessario)
        if not data_final:
            data_final = ""
        
        return NoticiaBruta(
            titulo=resultado.get("title", "Sem titulo"),
            url=url,
            snippet=resultado.get("content", ""),
            conteudo=resultado.get("raw_content", resultado.get("content", "")),
            fonte=raw_fonte,
            data=data_final,
            score=float(resultado.get("score", 0)),
        )