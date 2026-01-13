import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verificar_senha(senha_digitada: str, senha_hash: str) -> bool:
    return hash_password(senha_digitada) == (senha_hash or "")
