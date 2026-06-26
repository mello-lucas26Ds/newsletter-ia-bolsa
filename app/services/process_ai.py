# Processamento de IA com Groq (LangChain) + fallback regex.

from dataclasses import dataclass
from typing import Dict, Any

try:
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    LANGCHAIN_OK = True
except ImportError:
    LANGCHAIN_OK = False

try:
    from langfuse import Langfuse
    LANGFUSE_OK = True
except ImportError:
    LANGFUSE_OK = False


@dataclass
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


class GroqSummarizer:
    def __init__(self, api_key: str, modelo: str = "llama-3.1-8b-instant",
                 temperature: float = 0.3, max_tokens: int = 1024):
        self.api_key = api_key
        self.modelo = modelo
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.chain = None
        
        if not LANGCHAIN_OK:
            raise ImportError("langchain-groq nao instalado.")
        
        if api_key and api_key != "dev-mode-no-key":
            self._inicializar_chain()
        
        # Langfuse (opcional)
        self.langfuse = None
        if LANGFUSE_OK:
            try:
                self.langfuse = Langfuse()
            except Exception:
                pass
    
    def _inicializar_chain(self):
        llm = ChatGroq(
            api_key=self.api_key,
            model=self.modelo,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Voce e um analista financeiro especializado em IA e tecnologia.
Resuma a noticia em 3 paragrafos curtos em portugues.
Extraia:
- sentimento: bullish (positivo), bearish (negativo) ou neutral
- tags: 3-5 categorias relevantes (ex: AI, Semiconductor, NASDAQ)
- score_relevancia: nota 0-10 para investidores em IA

Responda EXATAMENTE neste formato:
RESUMO: [texto]
SENTIMENTO: [bullish|bearish|neutral]
TAGS: [tag1, tag2, tag3]
SCORE: [0-10]"""),
            ("human", "Titulo: {titulo}\nFonte: {fonte}\nConteudo: {conteudo}")
        ])
        
        self.chain = prompt | llm | StrOutputParser()
    
    def resumir(self, noticia_bruta: Dict[str, Any]) -> NoticiaProcessada:
        if not self.chain:
            return RegexFallbackSummarizer().resumir(noticia_bruta)
        
        trace = None
        try:
            if self.langfuse:
                trace = self.langfuse.trace(name="resumir_noticia")
            
            # Garante que nenhum campo seja None
            titulo = noticia_bruta.get("titulo") or "Sem titulo"
            conteudo = noticia_bruta.get("conteudo") or noticia_bruta.get("snippet") or ""
            fonte = noticia_bruta.get("fonte") or "Desconhecida"
            
            resposta = self.chain.invoke({
                "titulo": titulo,
                "fonte": fonte,
                "conteudo": conteudo[:3000]
            })
            
            resumo, sentimento, tags, score = self._parse_resposta(resposta)
            
            if trace:
                trace.update(output=resumo, metadata={"sentimento": sentimento, "score": score})
            
            return NoticiaProcessada(
                titulo=titulo,
                url=noticia_bruta.get("url") or "",
                fonte=fonte,
                data=noticia_bruta.get("data") or "",
                resumo=resumo,
                sentimento=sentimento,
                tags=tags,
                score_relevancia=score,
                tokens_usados=len(resposta.split())
            )
            
        except Exception as e:
            if trace:
                trace.update(output=str(e), metadata={"erro": True})
            return RegexFallbackSummarizer().resumir(noticia_bruta)
    
    def _parse_resposta(self, texto: str) -> tuple:
        resumo = ""
        sentimento = "neutral"
        tags = ["AI", "Market"]
        score = 5.0
        
        if not texto:
            return "Resumo indisponivel.", sentimento, tags, score
        
        linhas = texto.strip().split("\n")
        for linha in linhas:
            linha = linha.strip()
            if linha.startswith("RESUMO:"):
                resumo = linha.replace("RESUMO:", "").strip()
            elif linha.startswith("SENTIMENTO:"):
                s = linha.replace("SENTIMENTO:", "").strip().lower()
                if s in ("bullish", "bearish", "neutral"):
                    sentimento = s
            elif linha.startswith("TAGS:"):
                t = linha.replace("TAGS:", "").strip()
                tags = [x.strip() for x in t.split(",") if x.strip()]
            elif linha.startswith("SCORE:"):
                try:
                    score = float(linha.replace("SCORE:", "").strip())
                except ValueError:
                    pass
        
        if not resumo:
            resumo = texto[:500]
        
        return resumo, sentimento, tags, min(max(score, 0), 10)
    
    def health_check(self) -> bool:
        return self.chain is not None


class RegexFallbackSummarizer:
    def resumir(self, noticia_bruta: Dict[str, Any]) -> NoticiaProcessada:
        import re
        
        conteudo = noticia_bruta.get("conteudo") or noticia_bruta.get("snippet") or ""
        frases = re.split(r'[.!?]+', conteudo)
        resumo = ". ".join(frases[:3]).strip() + "." if frases else "Resumo indisponivel."
        
        texto_lower = conteudo.lower()
        positivas = ["rally", "surge", "gain", "bull", "record", "high", "sobe", "alta", "cresce"]
        negativas = ["crash", "drop", "bear", "loss", "fall", "queda", "cai", "baixa", "retrai"]
        
        score_pos = sum(1 for p in positivas if p in texto_lower)
        score_neg = sum(1 for n in negativas if n in texto_lower)
        
        sentimento = "bullish" if score_pos > score_neg else "bearish" if score_neg > score_pos else "neutral"
        
        return NoticiaProcessada(
            titulo=noticia_bruta.get("titulo") or "Sem titulo",
            url=noticia_bruta.get("url") or "",
            fonte=noticia_bruta.get("fonte") or "Desconhecida",
            data=noticia_bruta.get("data") or "",
            resumo=resumo,
            sentimento=sentimento,
            tags=["AI", "Market"],
            score_relevancia=5.0,
            tokens_usados=0,
        )