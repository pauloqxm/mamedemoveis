import io
from datetime import date

import streamlit as st
import pandas as pd
from urllib.request import urlopen

from marcenaria.migrations import init_database
from marcenaria.db_connector import test_db_connection
from marcenaria import data_access as da
from marcenaria.config import ETAPAS_PRODUCAO, STATUS_ETAPA

# =========================
# Config
# =========================
APP_TITLE = "Mamede Móveis Projetados | Sistema Interno"
LOGO_URL = "https://i.ibb.co/FkXDym6H/logo-mamede.png"

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")

# Força tema claro sempre (mesmo se o usuário estiver em dark mode)
st.markdown(
    """
<script>
const theme = {
  base: "light",
  primaryColor: "#F2C14E",
  backgroundColor: "#FFFFFF",
  secondaryBackgroundColor: "#F8FAFC",
  textColor: "#0F172A",
  font: "sans serif"
};
window.parent.postMessage({ type: "streamlit:setTheme", theme: theme }, "*");
</script>
""",
    unsafe_allow_html=True,
)


# =========================
# Helpers
# =========================
def _try_fetch_bytes(url: str, timeout: int = 10):
    try:
        with urlopen(url, timeout=timeout) as r:
            return r.read()
    except Exception:
        return None


def brl(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def can(perfis):
    u = st.session_state.get("user") or {}
    return u.get("perfil") in perfis or u.get("perfil") == "admin"


def logout():
    st.session_state.user = None
    st.session_state.page = "Login"
    st.rerun()


def require_login():
    if "user" not in st.session_state or not st.session_state.user:
        st.session_state.user = None
        st.session_state.page = "Login"
        return False
    return True


def inject_css_light():
    st.markdown(
        """
<style>
:root{
  --bg:#FFFFFF;
  --muted:#64748B;
  --text:#0F172A;
  --panel:#F8FAFC;
  --card:#FFFFFF;
  --line:#E5E7EB;
  --brand:#F2C14E;
  --brand2:#EAB308;
  --radius:16px;
  --shadow: 0 10px 26px rgba(15,23,42,.08);
}

/* Base */
.stApp{
  background:
    radial-gradient(1100px 560px at 10% 10%, rgba(242,193,78,.18), transparent 60%),
    radial-gradient(980px 520px at 92% 14%, rgba(234,179,8,.12), transparent 62%),
    linear-gradient(180deg, #FFFFFF, #FFFFFF);
  color: var(--text);
}
.block-container{ padding-top: 1.1rem; padding-bottom: 2rem; }

/* Sidebar */
[data-testid="stSidebar"]{
  background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
  border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] .block-container{ padding-top: 1rem; }

/* Inputs */
.stTextInput input, .stTextArea textarea, .stDateInput input, .stSelectbox div[data-baseweb="select"]{
  border-radius: 12px !important;
}

/* Buttons */
.stButton>button, .stDownloadButton>button{
  border-radius: 12px !important;
  padding: .65rem .95rem !important;
  border: 1px solid rgba(242,193,78,.55) !important;
  background: linear-gradient(180deg, var(--brand), var(--brand2)) !important;
  color: #0F172A !important;
  font-weight: 700 !important;
  box-shadow: 0 10px 18px rgba(234,179,8,.18);
  transition: transform .08s ease, filter .12s ease;
}
.stButton>button:hover, .stDownloadButton>button:hover{
  filter: brightness(1.02);
  transform: translateY(-1px);
}

/* Metric */
[data-testid="stMetric"]{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 14px 16px;
  box-shadow: var(--shadow);
}

/* DataFrame */
.stDataFrame{
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}

/* Custom UI */
.topbar{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap: 14px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 14px 16px;
  box-shadow: var(--shadow);
  margin-bottom: 14px;
}
.topbar .brand{
  display:flex;
  align-items:center;
  gap: 12px;
}
.topbar .brand img{
  width: 44px;
  height: 44px;
  object-fit: contain;
  border-radius: 12px;
  background: #FFF7E6;
  border: 1px solid rgba(242,193,78,.45);
  padding: 6px;
}
.topbar .title{
  font-size: 1.05rem;
  font-weight: 900;
  letter-spacing: .2px;
}
.topbar .sub{
  font-size: .85rem;
  color: var(--muted);
  margin-top: 2px;
}
.pill{
  display:inline-flex;
  align-items:center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(242,193,78,.16);
  border: 1px solid rgba(242,193,78,.40);
  color: var(--text);
  font-size: 12px;
  white-space: nowrap;
}

.cardx{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 16px;
  box-shadow: var(--shadow);
}
.muted{ color: var(--muted); font-size: .92rem; }

.kbadge{
  display:inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  background: #F1F5F9;
  border: 1px solid #E2E8F0;
  font-size: 12px;
  color: var(--text);
}
.kbadge.ok{ border-color: rgba(34,197,94,.30); background: rgba(34,197,94,.10); }
.kbadge.warn{ border-color: rgba(234,179,8,.40); background: rgba(234,179,8,.12); }
.kbadge.bad{ border-color: rgba(239,68,68,.30); background: rgba(239,68,68,.10); }

.coltitle{
  font-weight: 900;
  letter-spacing: .2px;
  margin-bottom: 10px;
}

/* Login */
.login-wrap{
  max-width: 980px;
  margin: 0 auto;
  padding: 30px 0 10px 0;
}
.login-hero{
  display:grid;
  grid-template-columns: 1.1fr .9fr;
  gap: 18px;
  align-items: stretch;
}
.login-card{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 20px;
  box-shadow: var(--shadow);
}
.login-logo{
  display:flex;
  align-items:center;
  gap: 12px;
  margin-bottom: 10px;
}
.login-logo img{
  width: 58px;
  height: 58px;
  object-fit: contain;
  border-radius: 16px;
  border: 1px solid rgba(242,193,78,.45);
  background: #FFF7E6;
  padding: 8px;
}
.login-title{ font-size: 1.35rem; font-weight: 1000; }
.login-desc{ color: var(--muted); margin-top: 2px; }
</style>
""",
        unsafe_allow_html=True,
    )


def render_topbar(title: str, subtitle: str = ""):
    u = st.session_state.get("user") or {}
    perfil = u.get("perfil", "-")
    nome = u.get("nome", "Usuário")

    st.markdown(
        f"""
        <div class="topbar">
          <div class="brand">
            <img src="{LOGO_URL}" />
            <div>
              <div class="title">{title}</div>
              <div class="sub">{subtitle}</div>
            </div>
          </div>
          <div class="pill">👤 {nome} <span style="opacity:.6">|</span> {perfil}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================
# PDF Orçamento
# =========================
def gerar_pdf_orcamento_bytes(orcamento_id: int) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader

    orc = da.obter_orcamento_por_id(int(orcamento_id))
    if not orc:
        raise ValueError("Orçamento não encontrado.")

    itens = da.listar_orcamento_itens(int(orcamento_id)) or []
    df_it = pd.DataFrame(itens) if itens else pd.DataFrame(columns=["descricao", "qtd", "unidade", "valor_unit"])

    total = 0.0
    for _, r in df_it.iterrows():
        try:
            q = float(r.get("qtd") or 0)
            vu = float(r.get("valor_unit") or 0)
            total += q * vu
        except Exception:
            pass

    logo_bytes = _try_fetch_bytes(LOGO_URL, timeout=10)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # header claro
    c.setFillColorRGB(0.95, 0.95, 0.98)
    c.rect(0, h - 42 * mm, w, 42 * mm, stroke=0, fill=1)

    if logo_bytes:
        try:
            img = ImageReader(io.BytesIO(logo_bytes))
            c.drawImage(img, 14 * mm, h - 34 * mm, width=28 * mm, height=28 * mm, mask="auto")
        except Exception:
            pass

    c.setFillColorRGB(0.06, 0.09, 0.16)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(46 * mm, h - 18 * mm, "ORÇAMENTO")
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.25, 0.32, 0.42)
    c.drawString(46 * mm, h - 26 * mm, f"Código: {orc.get('codigo', '-')}")
    c.drawString(46 * mm, h - 32 * mm, f"Status: {orc.get('status', '-')}")
    c.drawRightString(w - 14 * mm, h - 18 * mm, f"Data: {str(orc.get('created_at', '')).split(' ')[0]}")

    y = h - 52 * mm
    c.setFillColorRGB(0.91, 0.76, 0.31)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(14 * mm, y, "Cliente")
    c.setFillColorRGB(0.08, 0.10, 0.14)
    c.setFont("Helvetica", 11)
    y -= 6 * mm
    c.drawString(14 * mm, y, str(orc.get("cliente_nome", "-")))

    y -= 10 * mm
    c.setFillColorRGB(0.91, 0.76, 0.31)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(14 * mm, y, "Observações")
    c.setFillColorRGB(0.08, 0.10, 0.14)
    c.setFont("Helvetica", 10)
    y -= 6 * mm
    obs = (orc.get("observacoes") or "").strip() or "-"
    max_chars = 95
    lines = [obs[i : i + max_chars] for i in range(0, len(obs), max_chars)]
    for line in lines[:4]:
        c.drawString(14 * mm, y, line)
        y -= 5 * mm

    y -= 6 * mm
    c.setFillColorRGB(0.06, 0.09, 0.16)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(14 * mm, y, "Itens")
    y -= 7 * mm

    # tabela cabeçalho
    c.setFillColorRGB(0.95, 0.95, 0.96)
    c.rect(14 * mm, y - 5 * mm, w - 28 * mm, 8 * mm, stroke=0, fill=1)
    c.setFillColorRGB(0.08, 0.10, 0.14)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(16 * mm, y, "Descrição")
    c.drawRightString(w - 70 * mm, y, "Qtd")
    c.drawRightString(w - 48 * mm, y, "Unid")
    c.drawRightString(w - 14 * mm, y, "Vlr Unit")
    y -= 8 * mm

    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.08, 0.10, 0.14)

    if df_it.empty:
        c.drawString(16 * mm, y, "Sem itens cadastrados.")
        y -= 6 * mm
    else:
        for _, r in df_it.iterrows():
            desc = str(r.get("descricao") or "")[:70]
            qtd = r.get("qtd") or 0
            un = str(r.get("unidade") or "")[:8]
            vu = r.get("valor_unit") or 0

            if y < 25 * mm:
                c.showPage()
                y = h - 20 * mm
                c.setFont("Helvetica", 9)
                c.setFillColorRGB(0.08, 0.10, 0.14)

            c.drawString(16 * mm, y, desc)
            c.drawRightString(w - 70 * mm, y, str(qtd))
            c.drawRightString(w - 48 * mm, y, un)
            c.drawRightString(w - 14 * mm, y, brl(vu))
            y -= 6 * mm

    y -= 4 * mm
    c.setFillColorRGB(0.91, 0.76, 0.31)
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(w - 14 * mm, y, f"Total estimado: {brl(total)}")

    c.setFillColorRGB(0.35, 0.42, 0.52)
    c.setFont("Helvetica", 8)
    c.drawString(14 * mm, 12 * mm, "Mamede Móveis Projetados. Orçamento gerado pelo sistema interno.")

    c.showPage()
    c.save()
    return buf.getvalue()


# =========================
# Init
# =========================
inject_css_light()

if "db_ok" not in st.session_state:
    ok, msg = init_database()
    st.session_state.db_ok = ok
    st.session_state.db_msg = msg


# =========================
# Pages
# =========================
def login_ui():
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="login-hero">
          <div class="login-card">
            <div class="login-logo">
              <img src="{LOGO_URL}" />
              <div>
                <div class="login-title">Mamede Móveis Projetados</div>
                <div class="login-desc">Acesso ao sistema interno de vendas e produção.</div>
              </div>
            </div>
            <div class="muted">Dica: padrão inicial admin / admin123</div>
        """,
        unsafe_allow_html=True,
    )

    username = st.text_input("Usuário", placeholder="admin")
    senha = st.text_input("Senha", type="password")

    c1, c2 = st.columns([1, 1])
    with c1:
        entrar = st.button("Entrar", use_container_width=True)
    with c2:
        st.markdown('<div class="muted" style="padding-top:8px;">Sistema leve, rápido e organizado.</div>', unsafe_allow_html=True)

    if entrar:
        u = da.autenticar_usuario(username.strip(), senha)
        if u:
            st.session_state.user = u
            st.session_state.page = "Vendas"
            st.rerun()
        st.error("Usuário ou senha inválidos.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    ok_conn, msg_conn = test_db_connection()
    st.markdown("### Infraestrutura")
    a, b = st.columns(2)
    with a:
        st.markdown("**Status do banco**")
        st.success(msg_conn) if ok_conn else st.error(msg_conn)
    with b:
        st.markdown("**Migração**")
        st.success(st.session_state.db_msg) if st.session_state.db_ok else st.error(st.session_state.db_msg)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    return None


def page_clientes():
    render_topbar("Clientes", "Cadastro e busca")
    colA, colB = st.columns([1.2, 1])

    with colA:
        st.markdown('<div class="cardx">', unsafe_allow_html=True)
        st.subheader("Novo cliente")
        with st.form("f_cliente", clear_on_submit=True):
            nome = st.text_input("Nome")
            fantasia = st.text_input("Fantasia")
            cpf_cnpj = st.text_input("CPF/CNPJ")
            telefone = st.text_input("Telefone")
            whatsapp = st.text_input("WhatsApp")
            email = st.text_input("E-mail")
            endereco = st.text_area("Endereço")
            observacoes = st.text_area("Observações")
            ok = st.form_submit_button("Salvar", use_container_width=True)
            if ok:
                if not nome.strip():
                    st.error("Nome é obrigatório.")
                else:
                    da.criar_cliente({
                        "nome": nome.strip(),
                        "fantasia": fantasia.strip(),
                        "cpf_cnpj": cpf_cnpj.strip(),
                        "telefone": telefone.strip(),
                        "whatsapp": whatsapp.strip(),
                        "email": email.strip(),
                        "endereco": endereco.strip(),
                        "observacoes": observacoes.strip()
                    })
                    st.success("Cliente cadastrado.")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown('<div class="cardx">', unsafe_allow_html=True)
        st.subheader("Buscar")
        q = st.text_input("Pesquisar", placeholder="nome, cpf/cnpj, fantasia")
        ativo_only = st.toggle("Somente ativos", value=True)
        rows = da.listar_clientes(ativo_only=ativo_only, q=q.strip() if q else None)
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df[["id", "nome", "cpf_cnpj", "whatsapp", "email", "ativo"]], use_container_width=True, hide_index=True)
        else:
            st.info("Sem clientes ainda.")
        st.markdown("</div>", unsafe_allow_html=True)

    return None


def page_funcionarios():
    render_topbar("Funcionários", "Cadastro e busca")
    colA, colB = st.columns([1.2, 1])

    with colA:
        st.markdown('<div class="cardx">', unsafe_allow_html=True)
        st.subheader("Novo funcionário")
        with st.form("f_func", clear_on_submit=True):
            nome = st.text_input("Nome")
            funcao = st.text_input("Função")
            telefone = st.text_input("Telefone")
            data_adm = st.date_input("Data de admissão", value=None)
            ok = st.form_submit_button("Salvar", use_container_width=True)
            if ok:
                if not nome.strip():
                    st.error("Nome é obrigatório.")
                else:
                    da.criar_funcionario({
                        "nome": nome.strip(),
                        "funcao": funcao.strip(),
                        "telefone": telefone.strip(),
                        "data_admissao": data_adm
                    })
                    st.success("Funcionário cadastrado.")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown('<div class="cardx">', unsafe_allow_html=True)
        st.subheader("Buscar")
        q = st.text_input("Pesquisar", key="qfunc", placeholder="nome ou função")
        ativo_only = st.toggle("Somente ativos", value=True, key="func_ativo")
        rows = da.listar_funcionarios(ativo_only=ativo_only, q=q.strip() if q else None)
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df[["id", "nome", "funcao", "telefone", "ativo"]], use_container_width=True, hide_index=True)
        else:
            st.info("Sem funcionários ainda.")
        st.markdown("</div>", unsafe_allow_html=True)
    return None


def page_usuarios():
    render_topbar("Usuários", "Administração e permissões")
    if not can(["admin"]):
        st.warning("Acesso restrito.")
        return None

    colA, colB = st.columns([1.1, 1])

    with colA:
        st.markdown('<div class="cardx">', unsafe_allow_html=True)
        st.subheader("Criar usuário")
        with st.form("f_user", clear_on_submit=True):
            nome = st.text_input("Nome")
            email = st.text_input("E-mail")
            username = st.text_input("Username")
            senha = st.text_input("Senha", type="password")
            perfil = st.selectbox("Perfil", ["admin", "comercial", "producao", "leitura"], index=3)
            setor = st.text_input("Setor")
            ok = st.form_submit_button("Criar", use_container_width=True)
            if ok:
                if not (nome.strip() and email.strip() and username.strip() and senha):
                    st.error("Preenche tudo. Nome, e-mail, username e senha.")
                else:
                    okc, msg = da.criar_usuario({
                        "nome": nome.strip(),
                        "email": email.strip(),
                        "username": username.strip(),
                        "senha": senha,
                        "perfil": perfil,
                        "setor": setor.strip()
                    })
                    st.success(msg) if okc else st.error(msg)
                    if okc:
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown('<div class="cardx">', unsafe_allow_html=True)
        st.subheader("Gerenciar")
        users = da.listar_usuarios()
        if not users:
            st.info("Sem usuários.")
            st.markdown("</div>", unsafe_allow_html=True)
            return None

        df = pd.DataFrame(users)
        st.dataframe(df[["id", "nome", "username", "perfil", "setor", "ativo"]], use_container_width=True, hide_index=True)

        uid = st.selectbox("Selecionar usuário pelo ID", df["id"].tolist())
        urow = df[df["id"] == uid].iloc[0].to_dict()

        with st.form("f_user_edit"):
            nome = st.text_input("Nome", value=urow.get("nome", ""))
            email = st.text_input("E-mail", value=urow.get("email", ""))
            username = st.text_input("Username", value=urow.get("username", ""))
            perfil = st.selectbox(
                "Perfil",
                ["admin", "comercial", "producao", "leitura"],
                index=["admin", "comercial", "producao", "leitura"].index(urow.get("perfil", "leitura"))
            )
            setor = st.text_input("Setor", value=urow.get("setor", ""))
            ativo = st.toggle("Ativo", value=bool(urow.get("ativo", True)))
            senha = st.text_input("Nova senha (opcional)", type="password")
            ok = st.form_submit_button("Salvar alterações", use_container_width=True)
            if ok:
                ok2, msg2 = da.atualizar_usuario(uid, {
                    "nome": nome.strip(),
                    "email": email.strip(),
                    "username": username.strip(),
                    "perfil": perfil,
                    "setor": setor.strip(),
                    "ativo": ativo,
                    "senha": senha
                })
                st.success(msg2) if ok2 else st.error(msg2)
                if ok2:
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    return None


def page_orcamento():
    render_topbar("Orçamento", "Crie, edite itens, aprove e gere PDF. Pedido só nasce na aba Pedido.")

    clientes = da.listar_clientes(ativo_only=True)
    if not clientes:
        st.info("Cadastre um cliente primeiro.")
        return None

    c_map = {f"{c['nome']} (ID {c['id']})": c["id"] for c in clientes}

    colA, colB = st.columns([1, 1])

    with colA:
        st.markdown('<div class="cardx">', unsafe_allow_html=True)
        st.subheader("Criar orçamento")
        with st.form("f_orc", clear_on_submit=False):
            cli = st.selectbox("Cliente", list(c_map.keys()))
            validade = st.date_input("Validade", value=None)
            observacoes = st.text_area("Observações")
            criar = st.form_submit_button("Criar orçamento", use_container_width=True)
            if criar:
                oid, cod = da.criar_orcamento({
                    "cliente_id": c_map[cli],
                    "validade": validade,
                    "observacoes": observacoes,
                    "status": "Aberto",
                })
                st.success(f"Orçamento criado. Código {cod}")
                st.session_state.orcamento_id = oid
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="cardx" style="margin-top:14px;">', unsafe_allow_html=True)
        st.subheader("Lista de orçamentos")
        q = st.text_input("Buscar orçamento", placeholder="código ou observação")
        rows = da.listar_orcamentos(q=q.strip() if q else None)
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df[["id", "codigo", "cliente_nome", "status", "total_estimado", "created_at"]], use_container_width=True, hide_index=True)
            pick = st.selectbox("Selecionar orçamento (ID)", df["id"].tolist())
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Abrir para editar", use_container_width=True):
                    st.session_state.orcamento_id = int(pick)
                    st.rerun()
            with c2:
                if st.button("Limpar seleção", use_container_width=True):
                    st.session_state.orcamento_id = None
                    st.rerun()
        else:
            st.info("Sem orçamentos ainda.")
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown('<div class="cardx">', unsafe_allow_html=True)
        st.subheader("Editor do orçamento")
        oid = st.session_state.get("orcamento_id")

        if not oid:
            st.info("Crie ou selecione um orçamento na lista.")
            st.markdown("</div>", unsafe_allow_html=True)
            return None

        orc = da.obter_orcamento_por_id(int(oid))
        if not orc:
            st.warning("Orçamento não encontrado.")
            st.markdown("</div>", unsafe_allow_html=True)
            return None

        status = (orc.get("status") or "Aberto").strip()
        badge_class = "ok" if status == "Aprovado" else "warn" if status == "Aberto" else ""

        st.markdown(
            f"""
            <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
              <span class="kbadge {badge_class}">Código <b>{orc.get('codigo')}</b></span>
              <span class="kbadge">Status <b>{status}</b></span>
              <span class="kbadge">Cliente <b>{orc.get('cliente_nome')}</b></span>
            </div>
            """,
            unsafe_allow_html=True
        )

        itens = da.listar_orcamento_itens(int(oid))
        df_it = pd.DataFrame(itens) if itens else pd.DataFrame(columns=["descricao", "qtd", "unidade", "valor_unit"])
        df_it = df_it[[c for c in ["descricao", "qtd", "unidade", "valor_unit"] if c in df_it.columns]]

        disabled_edit = (status == "Aprovado")

        edited = st.data_editor(
            df_it,
            num_rows="dynamic",
            use_container_width=True,
            key="orc_itens",
            disabled=disabled_edit
        )

        c1, c2, c3 = st.columns([1, 1, 1])

        with c1:
            if st.button("Salvar itens", use_container_width=True, disabled=disabled_edit):
                total = da.salvar_orcamento_itens(int(oid), edited.to_dict("records"))
                st.success(f"Itens salvos. Total estimado {brl(total)}")
                st.rerun()

        with c2:
            if st.button("Aprovar orçamento", use_container_width=True, disabled=(status == "Aprovado")):
                ok2, msg2 = da.atualizar_status_orcamento(int(oid), "Aprovado")
                st.success(msg2) if ok2 else st.error(msg2)
                if ok2:
                    st.rerun()

        with c3:
            try:
                pdf_bytes = gerar_pdf_orcamento_bytes(int(oid))
                st.download_button(
                    "Baixar PDF",
                    data=pdf_bytes,
                    file_name=f"orcamento_{orc.get('codigo','')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.button("Baixar PDF", use_container_width=True, disabled=True)
                st.caption(f"PDF indisponível: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

    return None


def page_pedido():
    render_topbar("Pedido", "Crie pedidos manuais ou gere a partir de orçamentos aprovados.")

    st.markdown('<div class="cardx">', unsafe_allow_html=True)
    st.subheader("Gerar pedido a partir de orçamento aprovado")

    rows_orc = da.listar_orcamentos(q=None) or []
    aprovados = [r for r in rows_orc if (r.get("status") == "Aprovado")]
    if not aprovados:
        st.info("Nenhum orçamento aprovado ainda. Aprova na aba Orçamento e volta aqui.")
    else:
        df_ap = pd.DataFrame(aprovados)
        st.dataframe(df_ap[["id", "codigo", "cliente_nome", "status", "total_estimado", "created_at"]], use_container_width=True, hide_index=True)
        pick_orc = st.selectbox("Escolher orçamento aprovado (ID)", df_ap["id"].tolist())

        c1, c2 = st.columns([1, 1])
        with c1:
            funcionarios = da.listar_funcionarios(ativo_only=True) or []
            f_map = {"Sem responsável": None}
            for f in funcionarios:
                f_map[f"{f['nome']} (ID {f['id']})"] = f["id"]
            resp = st.selectbox("Responsável", list(f_map.keys()), key="resp_orc_to_ped")
            responsavel_id = f_map[resp]

        with c2:
            entrega_prev = st.date_input("Entrega prevista", value=None, key="entrega_orc_to_ped")

        if st.button("Gerar pedido agora", use_container_width=True):
            ok, msg, pedido_id, pedido_codigo = da.gerar_pedido_a_partir_orcamento(
                int(pick_orc),
                responsavel_id=responsavel_id,
                data_entrega_prevista=entrega_prev,
                observacoes=f"Gerado a partir do orçamento aprovado ID {pick_orc}"
            )
            if ok:
                st.success(f"{msg} Pedido {pedido_codigo}")
                st.session_state.pedido_id = pedido_id
                st.rerun()
            else:
                st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    st.markdown('<div class="cardx">', unsafe_allow_html=True)
    st.subheader("Criar pedido manual")

    clientes = da.listar_clientes(ativo_only=True)
    if not clientes:
        st.info("Cadastre um cliente primeiro.")
        st.markdown("</div>", unsafe_allow_html=True)
        return None

    funcionarios = da.listar_funcionarios(ativo_only=True) or []
    f_map = {"Sem responsável": None}
    for f in funcionarios:
        f_map[f"{f['nome']} (ID {f['id']})"] = f["id"]

    c_map = {f"{c['nome']} (ID {c['id']})": c["id"] for c in clientes}

    colA, colB = st.columns([1, 1])

    with colA:
        with st.form("f_ped", clear_on_submit=False):
            cli = st.selectbox("Cliente", list(c_map.keys()))
            resp = st.selectbox("Responsável", list(f_map.keys()))
            entrega = st.date_input("Entrega prevista", value=None, key="entrega_prev")
            observacoes = st.text_area("Observações", key="obs_ped")
            criar = st.form_submit_button("Criar pedido", use_container_width=True)
            if criar:
                pid, cod = da.criar_pedido({
                    "cliente_id": c_map[cli],
                    "responsavel_id": f_map[resp],
                    "data_entrega_prevista": entrega,
                    "observacoes": observacoes,
                    "etapa_atual": ETAPAS_PRODUCAO[0],
                    "status_etapa": STATUS_ETAPA[0],
                    "status": "Aberto",
                })
                st.success(f"Pedido criado. Código {cod}")
                st.session_state.pedido_id = pid
                st.rerun()

    with colB:
        st.subheader("Itens do pedido")
        pid = st.session_state.get("pedido_id")
        if not pid:
            st.info("Crie ou selecione um pedido abaixo.")
        else:
            itens = da.listar_pedido_itens(pid)
            df_it = pd.DataFrame(itens) if itens else pd.DataFrame(columns=["descricao", "qtd", "unidade", "valor_unit"])
            df_it = df_it[[c for c in ["descricao", "qtd", "unidade", "valor_unit"] if c in df_it.columns]]
            edited = st.data_editor(df_it, num_rows="dynamic", use_container_width=True, key="ped_itens")
            if st.button("Salvar itens do pedido", use_container_width=True):
                total = da.salvar_pedido_itens(pid, edited.to_dict("records"))
                st.success(f"Itens salvos. Total {brl(total)}")
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    st.markdown('<div class="cardx">', unsafe_allow_html=True)
    st.subheader("Lista de pedidos")
    q = st.text_input("Buscar pedido", placeholder="código ou observação", key="q_ped")
    rows = da.listar_pedidos(q=q.strip() if q else None)
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df[["id", "codigo", "cliente_nome", "status", "etapa_atual", "status_etapa", "responsavel_nome", "data_entrega_prevista", "total"]], use_container_width=True, hide_index=True)
        pick = st.selectbox("Selecionar pedido (ID)", df["id"].tolist())
        if st.button("Abrir pedido", use_container_width=True):
            st.session_state.pedido_id = int(pick)
            st.rerun()
    else:
        st.info("Sem pedidos ainda.")
    st.markdown("</div>", unsafe_allow_html=True)

    return None


def page_producao():
    render_topbar("Produção", "Kanban com etapas essenciais e cards mais bonitos.")

    # Remove Expedição e Transporte do Kanban
    etapas_filtradas = [e for e in ETAPAS_PRODUCAO if str(e).strip().lower() not in ["expedição", "expedicao", "transporte"]]
    if not etapas_filtradas:
        etapas_filtradas = ETAPAS_PRODUCAO

    funcionarios = da.listar_funcionarios(ativo_only=True) or []
    f_map = {"Sem responsável": None}
    for f in funcionarios:
        f_map[f"{f['nome']} (ID {f['id']})"] = f["id"]

    grupos = da.listar_pedidos_por_etapa() or {}
    cols = st.columns(len(etapas_filtradas))

    for i, etapa in enumerate(etapas_filtradas):
        with cols[i]:
            st.markdown('<div class="cardx">', unsafe_allow_html=True)
            st.markdown(f'<div class="coltitle">{etapa}</div>', unsafe_allow_html=True)

            pedidos = grupos.get(etapa, []) or []
            if not pedidos:
                st.caption("Sem pedidos aqui.")
                st.markdown("</div>", unsafe_allow_html=True)
                continue

            for p in pedidos:
                status_et = p.get("status_etapa") or "A fazer"
                cls = "ok" if str(status_et).lower().startswith("concl") else "warn" if str(status_et).lower().startswith("em") else ""

                st.markdown(
                    f"""
                    <div class="cardx" style="margin-bottom:10px;">
                      <div style="display:flex;justify-content:space-between;gap:10px;align-items:center;">
                        <div style="font-weight:1000;">{p.get('codigo')}</div>
                        <span class="kbadge {cls}">{status_et}</span>
                      </div>
                      <div class="muted" style="margin-top:4px;">{p.get('cliente_nome','')}</div>
                      <div class="muted">Resp. <b>{p.get('responsavel_nome') or 'Não definido'}</b></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                with st.expander("Mover e atualizar", expanded=False):
                    nova_etapa = st.selectbox(
                        "Etapa",
                        etapas_filtradas,
                        index=etapas_filtradas.index(etapa),
                        key=f"et_{p['id']}"
                    )
                    status_et2 = st.selectbox(
                        "Status",
                        STATUS_ETAPA,
                        index=STATUS_ETAPA.index(p.get("status_etapa") or STATUS_ETAPA[0]),
                        key=f"st_{p['id']}"
                    )
                    resp = st.selectbox("Responsável", list(f_map.keys()), index=0, key=f"rp_{p['id']}")
                    obs = st.text_area("Observação", key=f"ob_{p['id']}", height=70)
                    if st.button("Salvar", key=f"sv_{p['id']}", use_container_width=True):
                        ok, msg = da.mover_pedido_etapa(p["id"], nova_etapa, status_et2, f_map[resp], obs)
                        st.success(msg) if ok else st.error(msg)
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    return None


def page_vendas():
    render_topbar("Dashboard", "Visão rápida de orçamentos, pedidos e produção.")

    orcs = da.listar_orcamentos() or []
    peds = da.listar_pedidos() or []

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Orçamentos", len(orcs))
    col2.metric("Pedidos", len(peds))
    col3.metric("Orçamentos aprovados", sum(1 for o in orcs if o.get("status") == "Aprovado"))
    col4.metric("Na etapa Produção", sum(1 for p in peds if p.get("etapa_atual") == "Produção"))

    st.markdown('<div class="cardx" style="margin-top:14px;">', unsafe_allow_html=True)
    st.subheader("Últimos pedidos")
    if peds:
        df = pd.DataFrame(peds)
        st.dataframe(
            df[["codigo", "cliente_nome", "status", "etapa_atual", "status_etapa", "data_entrega_prevista", "total"]].head(50),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Sem pedidos ainda.")
    st.markdown("</div>", unsafe_allow_html=True)

    return None


def sidebar():
    u = st.session_state.user or {}
    st.sidebar.image(LOGO_URL, use_container_width=True)
    st.sidebar.markdown(f"**{u.get('nome', 'Usuário')}**")
    st.sidebar.caption(f"Perfil: {u.get('perfil', '-')}")
    if st.sidebar.button("Sair", use_container_width=True):
        logout()

    st.sidebar.divider()

    pages = [
        ("Vendas", page_vendas),
        ("Orçamento", page_orcamento),
        ("Pedido", page_pedido),
        ("Produção", page_producao),
        ("Clientes", page_clientes),
        ("Funcionários", page_funcionarios),
    ]
    if can(["admin"]):
        pages.append(("Usuários", page_usuarios))

    labels = [p[0] for p in pages]
    current = st.session_state.get("page", "Vendas")
    if current not in labels:
        current = "Vendas"

    choice = st.sidebar.radio("Navegação", labels, index=labels.index(current))
    st.session_state.page = choice
    return dict(pages)[choice]


# =========================
# Router
# =========================
if "page" not in st.session_state:
    st.session_state.page = "Login"

if st.session_state.page == "Login" or not require_login():
    _ = login_ui()
else:
    render = sidebar()
    _ = render()
