# Configuracao centralizada. Imutavel (frozen dataclass).

import os
import secrets
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Configuracao:
    tavily_api_key: str
    groq_api_key: str
    langfuse_secret_key: Optional[str]
    langfuse_public_key: Optional[str]
    langfuse_host: str
    secret_key: str
    flask_env: str
    flask_debug: bool
    max_noticias_por_execucao: int
    groq_model: str
    groq_temperature: float
    groq_max_tokens: int
    diretorio_dados: Path = BASE_DIR / "data"
    diretorio_templates: Path = BASE_DIR / "app" / "templates"
    diretorio_static: Path = BASE_DIR / "app" / "static"
    
    def __post_init__(self):
        # Valida limites
        if self.max_noticias_por_execucao < 1 or self.max_noticias_por_execucao > 50:
            raise ValueError("MAX_NOTICIAS_POR_EXECUCAO deve estar entre 1 e 50.")
        
        # Em producao, chaves nao podem ser dummy
        if self.flask_env == "production":
            if not self.tavily_api_key or "dev-mode" in self.tavily_api_key:
                raise ValueError("TAVILY_API_KEY nao configurada.")
            if not self.groq_api_key or "dev-mode" in self.groq_api_key:
                raise ValueError("GROQ_API_KEY nao configurada.")
        
        self.diretorio_dados.mkdir(parents=True, exist_ok=True)


def carregar_configuracao() -> Configuracao:
    try:
        from dotenv import load_dotenv
        env_path = BASE_DIR / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass
    
    secret = os.getenv("SECRET_KEY", "")
    if not secret:
        secret = secrets.token_hex(32)
    
    tavily = os.getenv("TAVILY_API_KEY", "")
    groq = os.getenv("GROQ_API_KEY", "")
    
    # Em dev, aceita sem chaves (usa dummy)
    env = os.getenv("FLASK_ENV", "development")
    if env == "development":
        if not tavily:
            tavily = "dev-mode-no-key"
        if not groq:
            groq = "dev-mode-no-key"
    
    return Configuracao(
        tavily_api_key=tavily,
        groq_api_key=groq,
        langfuse_secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        langfuse_public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        langfuse_host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        secret_key=secret,
        flask_env=env,
        flask_debug=os.getenv("FLASK_DEBUG", "1") == "1",
        max_noticias_por_execucao=int(os.getenv("MAX_NOTICIAS_POR_EXECUCAO", "10")),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        groq_temperature=0.3,
        groq_max_tokens=1024,
    )


CONFIG = carregar_configuracao()