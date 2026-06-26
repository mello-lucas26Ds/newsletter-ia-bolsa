# Deduplicacao de noticias via JSON persistente com janela de 7 dias.

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any


class JsonDeduplicador:
    # Persiste URLs vistas em url_history.json com janela de 7 dias.
    # URLs mais antigas que 7 dias sao automaticamente removidas.

    def __init__(self, caminho_historico: Path):
        self.caminho = caminho_historico
        self._historico = self._carregar()

    def _carregar(self) -> Dict[str, Dict[str, str]]:
        if not self.caminho.exists():
            return {}

        with open(self.caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)

        # Migrar formato antigo {url: "hash"} -> novo {url: {"hash": "...", "visto_em": "YYYY-MM-DD"}}
        resultado = {}
        for url, val in dados.items():
            if isinstance(val, dict):
                resultado[url] = val
            else:
                # Formato antigo: assume data de hoje para nao perder imediatamente
                resultado[url] = {"hash": val, "visto_em": datetime.now().strftime("%Y-%m-%d")}

        return resultado

    def _salvar(self):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        with open(self.caminho, "w", encoding="utf-8") as f:
            json.dump(self._historico, f, ensure_ascii=False, indent=2)

    def _hash(self, conteudo: str) -> str:
        texto = (conteudo or "")[:500]
        return hashlib.md5(texto.encode("utf-8")).hexdigest()

    def _limpar_antigos(self) -> List[str]:
        # Remove URLs com mais de 7 dias
        hoje = datetime.now().date()
        limite = hoje - timedelta(days=7)
        removidos = []

        for url, meta in list(self._historico.items()):
            data_str = meta.get("visto_em", "")
            try:
                data_visto = datetime.strptime(data_str, "%Y-%m-%d").date()
                if data_visto < limite:
                    del self._historico[url]
                    removidos.append(url)
            except ValueError:
                del self._historico[url]  # data invalida = remove
                removidos.append(url)

        return removidos

    def filtrar_novas(self, noticias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Limpa antigos antes de filtrar
        removidos = self._limpar_antigos()
        if removidos:
            print(f"      [DEDUP] {len(removidos)} URLs antigas removidas do history")

        novas = []
        for n in noticias:
            url = n.get("url", "") or ""
            h = self._hash(n.get("conteudo") or n.get("snippet") or "")

            # URL ja vista = duplicata
            if url in self._historico:
                continue

            # Conteudo identico (hash igual) = duplicata
            if any(meta.get("hash") == h for meta in self._historico.values()):
                continue

            novas.append(n)

        return novas

    def registrar(self, noticias: List[Dict[str, Any]]):
        hoje = datetime.now().strftime("%Y-%m-%d")
        for n in noticias:
            url = n.get("url", "") or ""
            h = self._hash(n.get("conteudo") or n.get("snippet") or "")
            self._historico[url] = {"hash": h, "visto_em": hoje}

        self._salvar()

    def total_vistas(self) -> int:
        return len(self._historico)