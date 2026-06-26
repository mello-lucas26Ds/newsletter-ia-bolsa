# Formatacao de noticias processadas em JSON, Markdown e HTML.

import dataclasses
import json
from datetime import datetime
from typing import List, Any


def _para_dict(obj: Any) -> Any:
    """Converte dataclass NoticiaProcessada para dict nativo."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, dict):
        return dataclasses.asdict(obj)
    return obj


class NewsletterFormatter:
    
    def para_json(self, noticias: List[Any], data: str) -> str:
        noticias_dicts = [_para_dict(n) for n in noticias]
        
        estrutura = {
            "meta": {
                "versao": "1.0",
                "data": data,
                "total_noticias": len(noticias_dicts),
                "gerado_em": datetime.now().isoformat(),
            },
            "noticias": noticias_dicts,
        }
        return json.dumps(estrutura, ensure_ascii=False, indent=2)
    
    def para_markdown(self, noticias: List[Any], data: str) -> str:
        linhas = [
            f"# Newsletter IA Bolsa — {data}",
            "",
            f"**Gerado em:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            f"**Total:** {len(noticias)} noticias",
            f"**Fonte dos dados:** Tavily API + Groq AI",
            "",
            "---",
            "",
        ]
        
        for i, n in enumerate(noticias, 1):
            d = _para_dict(n)
            emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(d.get("sentimento", "neutral"), "⚪")
            fonte = d.get("fonte") or d.get("source") or d.get("domain") or "Fonte nao informada pela API"
            linhas.extend([
                f"## {i}. {d.get('titulo', 'Sem titulo')}",
                "",
                f"**Fonte:** {fonte}  ",
                f"**Sentimento:** {emoji} {d.get('sentimento', 'neutral').upper()}  ",
                f"**Relevancia:** {d.get('score_relevancia', 0)}/10  ",
                f"**Tags:** {', '.join(d.get('tags', []))}",
                "",
                f"{d.get('resumo', 'Sem resumo.')}",
                "",
                f"[Ler noticia completa]({d.get('url', '#')})",
                "",
                "---",
                "",
            ])
        
        return "\n".join(linhas)
    
    def para_html(self, noticias: List[Any], data: str) -> str:
        return "<html><body>HTML na Fase 3</body></html>"