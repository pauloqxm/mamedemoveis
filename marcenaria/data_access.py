import json
from datetime import date, datetime
from decimal import Decimal
from psycopg2.extras import RealDictCursor
import streamlit as st

from .db_connector import get_db_connection
from .auth import hash_password, verificar_senha
from .timezone_utils import agora_fortaleza
from .config import ETAPAS_PRODUCAO, STATUS_ETAPA

def json_safe(obj):
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_safe(v) for v in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return obj

def dumps_safe(payload) -> str:
    return json.dumps(json_safe(payload), ensure_ascii=False, default=str)

# ---- Auth
def autenticar_usuario(username: str, senha: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, nome, email, username, senha_hash, perfil, setor, ativo
                    FROM usuarios
                    WHERE username=%s AND ativo=TRUE
                """, (username,))
                u = cur.fetchone()
                if u and verificar_senha(senha, u["senha_hash"]):
                    cur.execute("UPDATE usuarios SET ultimo_login=CURRENT_TIMESTAMP WHERE id=%s", (u["id"],))
                    conn.commit()
                    return u
                return None
    except Exception as e:
        st.error(f"Erro autenticação: {e}")
        return None

def listar_usuarios():
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, nome, email, username, perfil, setor, ativo, data_cadastro, ultimo_login
                FROM usuarios
                ORDER BY nome
            """)
            return cur.fetchall()

def criar_usuario(d):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM usuarios WHERE username=%s OR email=%s", (d["username"], d["email"]))
            if cur.fetchone()[0] > 0:
                return False, "Username ou email já existe."
            cur.execute("""
                INSERT INTO usuarios (nome,email,username,senha_hash,perfil,setor,ativo)
                VALUES (%s,%s,%s,%s,%s,%s,TRUE)
            """, (d["nome"], d["email"], d["username"], hash_password(d["senha"]), d["perfil"], d.get("setor","")))
            conn.commit()
            return True, "Usuário criado."

def atualizar_usuario(uid: int, d):
    sets, vals = [], []
    for k, v in d.items():
        if k == "senha":
            if v:
                sets.append("senha_hash=%s")
                vals.append(hash_password(v))
        else:
            sets.append(f"{k}=%s")
            vals.append(v)
    if not sets:
        return True, "Nada pra atualizar."
    vals.append(uid)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE usuarios SET {', '.join(sets)} WHERE id=%s", vals)
            conn.commit()
            return True, "Usuário atualizado."

def desativar_usuario(uid: int):
    if uid == 1:
        return False, "Não dá pra desativar o admin principal."
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE usuarios SET ativo=FALSE WHERE id=%s", (uid,))
            conn.commit()
            return True, "Usuário desativado."

# ---- Clientes
def listar_clientes(ativo_only=True, q=None):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            where = "WHERE 1=1"
            params = []
            if ativo_only:
                where += " AND ativo=TRUE"
            if q:
                where += " AND (nome ILIKE %s OR fantasia ILIKE %s OR cpf_cnpj ILIKE %s)"
                params += [f"%{q}%", f"%{q}%", f"%{q}%"]
            cur.execute(f"SELECT * FROM clientes {where} ORDER BY nome", params)
            return cur.fetchall()

def criar_cliente(d):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO clientes (nome,fantasia,cpf_cnpj,telefone,whatsapp,email,endereco,observacoes,ativo)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,TRUE)
                RETURNING id
            """, (d["nome"], d.get("fantasia",""), d.get("cpf_cnpj",""), d.get("telefone",""),
                  d.get("whatsapp",""), d.get("email",""), d.get("endereco",""), d.get("observacoes","")))
            cid = cur.fetchone()[0]
            conn.commit()
            return cid

def atualizar_cliente(cid: int, d):
    sets, vals = [], []
    for k, v in d.items():
        sets.append(f"{k}=%s")
        vals.append(v)
    sets.append("updated_at=CURRENT_TIMESTAMP")
    vals.append(cid)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE clientes SET {', '.join(sets)} WHERE id=%s", vals)
            conn.commit()
            return True

# ---- Funcionários
def listar_funcionarios(ativo_only=True, q=None):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            where = "WHERE 1=1"
            params = []
            if ativo_only:
                where += " AND ativo=TRUE"
            if q:
                where += " AND (nome ILIKE %s OR funcao ILIKE %s)"
                params += [f"%{q}%", f"%{q}%"]
            cur.execute(f"SELECT * FROM funcionarios {where} ORDER BY nome", params)
            return cur.fetchall()

def criar_funcionario(d):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO funcionarios (nome,funcao,telefone,data_admissao,ativo)
                VALUES (%s,%s,%s,%s,TRUE)
                RETURNING id
            """, (d["nome"], d.get("funcao",""), d.get("telefone",""), d.get("data_admissao")))
            fid = cur.fetchone()[0]
            conn.commit()
            return fid

# ---- Orçamentos / Pedidos
def _codigo(prefix="ORC"):
    return f"{prefix}{agora_fortaleza().strftime('%y%m%d%H%M%S')}"

def criar_orcamento(d):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            codigo = d.get("codigo") or _codigo("ORC")
            cur.execute("""
                INSERT INTO orcamentos (codigo,cliente_id,status,total_estimado,validade,observacoes)
                VALUES (%s,%s,%s,%s,%s,%s)
                RETURNING id, codigo
            """, (codigo, d["cliente_id"], d.get("status","Rascunho"), d.get("total_estimado",0),
                  d.get("validade"), d.get("observacoes","")))
            oid, cod = cur.fetchone()
            conn.commit()
            return oid, cod

def listar_orcamentos(q=None):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            where="WHERE 1=1"
            params=[]
            if q:
                where += " AND (o.codigo ILIKE %s OR o.observacoes ILIKE %s)"
                params += [f"%{q}%", f"%{q}%"]
            cur.execute(f"""
                SELECT o.*, c.nome as cliente_nome
                FROM orcamentos o
                LEFT JOIN clientes c ON c.id=o.cliente_id
                {where}
                ORDER BY o.created_at DESC
            """, params)
            return cur.fetchall()

def listar_orcamento_itens(orcamento_id:int):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM orcamento_itens WHERE orcamento_id=%s ORDER BY id", (orcamento_id,))
            return cur.fetchall()

def salvar_orcamento_itens(orcamento_id:int, itens:list):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM orcamento_itens WHERE orcamento_id=%s", (orcamento_id,))
            total = 0
            for it in itens:
                qtd = float(it.get("qtd") or 1)
                vu = float(it.get("valor_unit") or 0)
                sub = round(qtd*vu, 2)
                total += sub
                cur.execute("""
                    INSERT INTO orcamento_itens (orcamento_id,descricao,qtd,unidade,valor_unit,subtotal)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (orcamento_id, it.get("descricao",""), qtd, it.get("unidade","Unid."), vu, sub))
            cur.execute("UPDATE orcamentos SET total_estimado=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s", (total, orcamento_id))
            conn.commit()
            return total

def criar_pedido(d):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            codigo = d.get("codigo") or _codigo("PED")
            cur.execute("""
                INSERT INTO pedidos (codigo,cliente_id,orcamento_id,status,etapa_atual,status_etapa,responsavel_id,data_entrega_prevista,total,observacoes)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id, codigo
            """, (codigo, d["cliente_id"], d.get("orcamento_id"), d.get("status","Aberto"),
                  d.get("etapa_atual",ETAPAS_PRODUCAO[0]), d.get("status_etapa",STATUS_ETAPA[0]),
                  d.get("responsavel_id"), d.get("data_entrega_prevista"),
                  d.get("total",0), d.get("observacoes","")))
            pid, cod = cur.fetchone()
            conn.commit()
            return pid, cod

def listar_pedidos(q=None):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            where="WHERE 1=1"
            params=[]
            if q:
                where += " AND (p.codigo ILIKE %s OR p.observacoes ILIKE %s)"
                params += [f"%{q}%", f"%{q}%"]
            cur.execute(f"""
                SELECT p.*, c.nome as cliente_nome, f.nome as responsavel_nome
                FROM pedidos p
                LEFT JOIN clientes c ON c.id=p.cliente_id
                LEFT JOIN funcionarios f ON f.id=p.responsavel_id
                {where}
                ORDER BY p.created_at DESC
            """, params)
            return cur.fetchall()

def listar_pedido_itens(pedido_id:int):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM pedido_itens WHERE pedido_id=%s ORDER BY id", (pedido_id,))
            return cur.fetchall()

def salvar_pedido_itens(pedido_id:int, itens:list):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM pedido_itens WHERE pedido_id=%s", (pedido_id,))
            total=0
            for it in itens:
                qtd=float(it.get("qtd") or 1)
                vu=float(it.get("valor_unit") or 0)
                sub=round(qtd*vu, 2)
                total+=sub
                cur.execute("""
                    INSERT INTO pedido_itens (pedido_id,descricao,qtd,unidade,valor_unit,subtotal)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (pedido_id, it.get("descricao",""), qtd, it.get("unidade","Unid."), vu, sub))
            cur.execute("UPDATE pedidos SET total=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s", (total, pedido_id))
            conn.commit()
            return total

# ---- Produção Kanban
def listar_pedidos_por_etapa():
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT p.*, c.nome as cliente_nome, f.nome as responsavel_nome
                FROM pedidos p
                LEFT JOIN clientes c ON c.id=p.cliente_id
                LEFT JOIN funcionarios f ON f.id=p.responsavel_id
                WHERE p.status <> 'Cancelado'
                ORDER BY p.updated_at DESC
            """)
            rows = cur.fetchall()
            grupos = {e: [] for e in ETAPAS_PRODUCAO}
            for r in rows:
                etapa = r.get("etapa_atual") or ETAPAS_PRODUCAO[0]
                if etapa not in grupos:
                    grupos[etapa] = []
                grupos[etapa].append(r)
            return grupos

def mover_pedido_etapa(pedido_id:int, nova_etapa:str, status_etapa:str, responsavel_id=None, observacoes:str=""):
    if nova_etapa not in ETAPAS_PRODUCAO:
        return False, "Etapa inválida."
    if status_etapa not in STATUS_ETAPA:
        return False, "Status inválido."
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE pedidos
                SET etapa_atual=%s, status_etapa=%s, responsavel_id=%s, updated_at=CURRENT_TIMESTAMP
                WHERE id=%s
            """, (nova_etapa, status_etapa, responsavel_id, pedido_id))
            cur.execute("""
                INSERT INTO producao_etapas (pedido_id, etapa, status, responsavel_id, inicio_em, observacoes)
                VALUES (%s,%s,%s,%s,CURRENT_TIMESTAMP,%s)
            """, (pedido_id, nova_etapa, status_etapa, responsavel_id, observacoes or ""))
            conn.commit()
            return True, "Movido."
