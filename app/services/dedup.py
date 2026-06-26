# Deduplicacao de noticias via JSON persistente.

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any


class JsonDeduplicador:
    # Persiste URLs vistas em url_history.json (commitado no Git)
    
    def __init__(self, caminho_historico: Path):
        self.caminho = caminho_historico
        self._historico = self._carregar()
    
    def _carregar(self) -> Dict[str, str]:
        if self.caminho.exists():
            with open(self.caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def _salvar(self):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        with open(self.caminho, "w", encoding="utf-8") as f:
            json.dump(self._historico, f, ensure_ascii=False, indent=2)
    
    def _hash(self, conteudo: str) -> str:
        # Hash MD5 do conteudo para detectar mesma noticia com URL diferente
        texto = (conteudo or "")[:500]
        return hashlib.md5(texto.encode("utf-8")).hexdigest()
    
    def filtrar_novas(self, noticias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        novas = []
        for n in noticias:
            url = n.get("url", "") or ""
            h = self._hash(n.get("conteudo") or n.get("snippet") or "")
            
            # URL ja vista OU conteudo identico = duplicata
            if url in self._historico or h in self._historico.values():
                continue
            
            novas.append(n)
        
        return novas
    
    def registrar(self, noticias: List[Dict[str, Any]]):
        for n in noticias:
            url = n.get("url", "") or ""
            h = self._hash(n.get("conteudo") or n.get("snippet") or "")
            self._historico[url] = h
        
        self._salvar()
    
    def total_vistas(self) -> int:
        return len(self._historico)