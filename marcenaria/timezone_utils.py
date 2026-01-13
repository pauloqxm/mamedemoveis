from datetime import datetime, date, timedelta
import pytz
from .config import FORTALEZA_TZ

def agora_fortaleza() -> datetime:
    return datetime.now(FORTALEZA_TZ)

def converter_para_fortaleza(dt: datetime) -> datetime:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(FORTALEZA_TZ)

def formatar_data_hora_fortaleza(dt: datetime, formato: str = "%d/%m/%Y %H:%M") -> str:
    if not dt:
        return ""
    return converter_para_fortaleza(dt).strftime(formato)
