# Testes de configuracao.

import pytest
import os
import sys
from unittest.mock import patch
from dataclasses import FrozenInstanceError

# Adiciona raiz ao path antes de qualquer import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config as config_module


class TestConfiguracao:
    
    def test_config_carrega_sem_erro(self):
        env = {"FLASK_ENV": "development", "FLASK_DEBUG": "1"}
        with patch.dict(os.environ, env, clear=True):
            cfg = config_module.carregar_configuracao()
            assert cfg.flask_env == "development"
            assert cfg.flask_debug is True
            assert cfg.groq_model == "llama-3.1-8b-instant"
    
    def test_modo_producao_requer_chaves(self):
        env = {
            "FLASK_ENV": "production",
            "TAVILY_API_KEY": "",
            "GROQ_API_KEY": "",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError):
                from config import carregar_configuracao
                carregar_configuracao()
    
    def test_valores_validos(self):
        env = {
            "TAVILY_API_KEY": "tvly-teste123",
            "GROQ_API_KEY": "gsk-teste456",
            "SECRET_KEY": "minha-chave",
            "FLASK_ENV": "testing",
            "FLASK_DEBUG": "0",
            "MAX_NOTICIAS_POR_EXECUCAO": "15",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = config_module.carregar_configuracao()
            assert cfg.tavily_api_key == "tvly-teste123"
            assert cfg.groq_api_key == "gsk-teste456"
            assert cfg.flask_env == "testing"
            assert cfg.flask_debug is False
            assert cfg.max_noticias_por_execucao == 15
            assert cfg.groq_model == "llama-3.1-8b-instant"
    
    def test_imutavel(self):
        env = {"TAVILY_API_KEY": "tvly", "GROQ_API_KEY": "gsk"}
        with patch.dict(os.environ, env, clear=True):
            cfg = config_module.carregar_configuracao()
            with pytest.raises(FrozenInstanceError):
                cfg.max_noticias_por_execucao = 999
    
    def test_limites_max_noticias(self):
        env = {"TAVILY_API_KEY": "tvly", "GROQ_API_KEY": "gsk", "MAX_NOTICIAS_POR_EXECUCAO": "100"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="1 e 50"):
                config_module.carregar_configuracao()
    
    def test_langfuse_pode_estar_configurado(self):
        env = {"TAVILY_API_KEY": "tvly", "GROQ_API_KEY": "gsk"}
        with patch.dict(os.environ, env, clear=True):
            cfg = config_module.carregar_configuracao()
            assert cfg.langfuse_secret_key is None or isinstance(cfg.langfuse_secret_key, str)