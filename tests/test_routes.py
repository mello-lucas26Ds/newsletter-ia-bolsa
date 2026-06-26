# Testes das rotas Flask.

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import criar_app


@pytest.fixture
def cliente():
    app = criar_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestRotasPublicas:
    
    def test_pagina_inicial_200(self, cliente):
        resposta = cliente.get("/")
        assert resposta.status_code == 200
        assert b"IA BOLSA" in resposta.data
    
    def test_pagina_inicial_contem_dados(self, cliente):
        resposta = cliente.get("/")
        html = resposta.data.decode("utf-8")
        assert resposta.status_code == 200
        assert "news-grid" in html or "noticia-card" in html or "newsletter" in html.lower()
        assert "IA" in html or "Bolsa" in html or "newsletter" in html.lower()
    
    def test_newsletter_valida(self, cliente):
        resposta = cliente.get("/newsletter/2026-06-25")
        assert resposta.status_code == 200
        assert b"2026-06-25" in resposta.data
    
    def test_newsletter_invalida_404(self, cliente):
        resposta = cliente.get("/newsletter/data-invalida")
        assert resposta.status_code == 404
    
    def test_health_check(self, cliente):
        resposta = cliente.get("/api/health")
        dados = resposta.get_json()
        assert resposta.status_code == 200
        assert dados["status"] == "ok"
        assert "timestamp" in dados
    
    def test_config_check_seguro(self, cliente):
        resposta = cliente.get("/api/config-check")
        dados = resposta.get_json()
        assert resposta.status_code == 200
        assert isinstance(dados["tavily_configurado"], bool)
        assert isinstance(dados["groq_configurado"], bool)


class TestRotasDev:
    
    def test_painel_200(self, cliente):
        resposta = cliente.get("/dev/panel")
        assert resposta.status_code == 200
        assert b"Painel de Desenvolvimento" in resposta.data
    
    def test_painel_contem_stats(self, cliente):
        resposta = cliente.get("/dev/panel")
        html = resposta.data.decode("utf-8")
        assert "Arquivos JSON" in html
        assert "Configuracoes" in html