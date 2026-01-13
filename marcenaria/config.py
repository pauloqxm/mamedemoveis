import os
import pytz
from urllib.parse import urlparse
import streamlit as st

FORTALEZA_TZ = pytz.timezone("America/Fortaleza")

DB_SCHEMA = (os.environ.get("DB_SCHEMA") or "bd_marcenaria").strip()

TEMA_CORES = {
    "primary": "#0B5FFF",
    "secondary": "#F3F6FF",
    "info": "#2BB0FF",
    "warning": "#FFB020",
    "danger": "#E5484D",
    "success": "#2ECC71",
    "text": "#101828",
    "background": "#FFFFFF",
}

CORES_STATUS_PEDIDO = {
    "Aberto": TEMA_CORES["info"],
    "Em produção": TEMA_CORES["warning"],
    "Pronto": TEMA_CORES["success"],
    "Entregue": "#475467",
    "Cancelado": "#98A2B3",
}

ETAPAS_PRODUCAO = [
    "Medição técnica",
    "Projeto técnico",
    "Produção",
    "Expedição",
    "Transporte",
    "Montagem",
]

STATUS_ETAPA = ["A fazer", "Em andamento", "Pausado", "Concluído"]

def _env_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "y", "sim", "on")

def _env_int(name: str, default: int) -> int:
    try:
        return int(str(os.environ.get(name, str(default))).strip())
    except Exception:
        return default

def _env_list(name: str) -> list:
    raw = os.environ.get(name, "") or ""
    itens = [x.strip() for x in raw.replace(";", ",").split(",")]
    return [x for x in itens if x]

DATABASE_URL = (
    os.environ.get("DATABASE_PUBLIC_URL")
    or os.environ.get("DATABASE_URL_PUBLIC")
    or os.environ.get("DATABASE_URL")
)

def _safe_st_secrets_get(key: str, default=None):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default

def get_db_config():
    if DATABASE_URL:
        url = urlparse(DATABASE_URL)
        return {
            "host": url.hostname,
            "database": url.path[1:],
            "user": url.username,
            "password": url.password,
            "port": url.port or 5432,
            "sslmode": "require",
        }

    return {
        "host": os.environ.get("DB_HOST") or _safe_st_secrets_get("DB_HOST", "localhost"),
        "database": os.environ.get("DB_NAME") or _safe_st_secrets_get("DB_NAME", "railway"),
        "user": os.environ.get("DB_USER") or _safe_st_secrets_get("DB_USER", "postgres"),
        "password": os.environ.get("DB_PASSWORD") or _safe_st_secrets_get("DB_PASSWORD", ""),
        "port": int(os.environ.get("DB_PORT") or _safe_st_secrets_get("DB_PORT", 5432)),
        "sslmode": os.environ.get("DB_SSLMODE") or _safe_st_secrets_get("DB_SSLMODE", "prefer"),
    }

# MVP: e-mail opcional (não usado)
def get_email_config() -> dict:
    smtp_password = (os.environ.get("SMTP_PASSWORD") or os.environ.get("SMTP_PASS") or "").strip()
    return {
        "enabled_new": _env_bool("MAIL_ON_NEW_DEMANDA", False),
        "host": os.environ.get("SMTP_HOST", "").strip(),
        "port": _env_int("SMTP_PORT", 587),
        "user": os.environ.get("SMTP_USER", "").strip(),
        "password": smtp_password,
        "starttls": _env_bool("SMTP_STARTTLS", True),
        "from": (os.environ.get("MAIL_FROM") or "").strip(),
        "to": _env_list("MAIL_TO"),
        "cc": _env_list("MAIL_CC"),
        "bcc": _env_list("MAIL_BCC"),
        "subject_prefix": os.environ.get("MAIL_SUBJECT_PREFIX", "Marcenaria").strip(),
        "timeout": _env_int("MAIL_SEND_TIMEOUT", 20),
    }

def get_brevo_config() -> dict:
    return {
        "api_key": (os.environ.get("BREVO_API_KEY") or "").strip(),
        "sender_email": (os.environ.get("BREVO_SENDER") or "").strip(),
        "sender_name": (os.environ.get("BREVO_SENDER_NAME") or "Marcenaria").strip(),
        "to": _env_list("BREVO_TO") or _env_list("MAIL_TO"),
        "timeout": _env_int("BREVO_TIMEOUT", 20),
        "subject_prefix": os.environ.get("MAIL_SUBJECT_PREFIX", "Marcenaria").strip(),
    }
