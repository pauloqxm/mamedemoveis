import io
import streamlit as st
import pandas as pd
from urllib.request import urlopen

from marcenaria.migrations import init_database
from marcenaria.db_connector import test_db_connection
from marcenaria import data_access as da
from marcenaria.config import ETAPAS_PRODUCAO, STATUS_ETAPA

APP_TITLE = "Mamede Móveis Projetados | Sistema Interno"
LOGO_URL = "https://i.ibb.co/FkXDym6H/logo-mamede.png"

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")

# Força tema CLARO sempre
st.markdown("""
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
""", unsafe_allow_html=True)


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


def fmt_date_br(x):
    if x is None or x == "":
        return ""
    try:
        dt = pd.to_datetime(x, errors="coerce")
        if pd.isna(dt):
            return str(x)
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return str(x)


def safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default


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


def inject_css():
    st.markdown("""
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

  --sidebar-bg1:#0B1220;
  --sidebar-bg2:#0F172A;
  --sidebar-line: rgba(255,255,255,.10);
  --sidebar-text:#FFFFFF;
  --sidebar-muted: rgba(255,255,255,.70);
}

.stApp{
  background:
    radial-gradient(1100px 560px at 10% 10%, rgba(242,193,78,.18), transparent 60%),
    radial-gradient(980px 520px at 92% 14%, rgba(234,179,8,.12), transparent 62%),
    linear-gradient(180deg, #FFFFFF, #FFFFFF);
  color: var(--text);
}
.block-container{ padding-top: 1.1rem; padding-bottom: 2rem; }

.stTextInput input, .stTextArea textarea, .stDateInput input, .stSelectbox div[data-baseweb="select"]{
  border-radius: 12px !important;
}

/* Labels e textos do formulário sempre visíveis */
[data-testid="stWidgetLabel"] > div,
[data-testid="stWidgetLabel"] span,
label, .stMarkdown, .stCaption, p{
  color: var(--text) !important;
}

/* Botões */
.stButton>button, .stDownloadButton>button{
  border-radius: 12px !important;
  padding: .65rem .95rem !important;
  border: 1px solid rgba(242,193,78,.55) !important;
  background: linear-gradient(180deg, var(--brand), var(--brand2)) !important;
  color: #0F172A !important;
  font-weight: 900 !important;
  box-shadow: 0 10px 18px rgba(234,179,8,.18);
  transition: transform .08s ease, filter .12s ease;
}
.stButton>button:hover, .stDownloadButton>button:hover{
  filter: brightness(1.02);
  transform: translateY(-1px);
}

/* KPI: força texto escuro (tava ficando branco em alguns temas) */
[data-testid="stMetric"]{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 14px 16px;
  box-shadow: var(--shadow);
}
[data-testid="stMetricLabel"]{
  color: #0F172A !important;
  font-weight: 800 !important;
}
[data-testid="stMetricValue"]{
  color: #0F172A !important;
  font-weight: 1000 !important;
}

/* Dataframe */
.stDataFrame{
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}

/* Cards */
.cardx{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 16px;
  box-shadow: var(--shadow);
}
.muted{ color: var(--muted) !important; font-size: .92rem; }
.section-title{ font-weight: 1000; margin-bottom: 6px; }

/* Topbar */
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
.topbar .brand{ display:flex; align-items:center; gap: 12px; }
.topbar .brand img{
  width: 44px; height: 44px;
  object-fit: contain;
  border-radius: 12px;
  background: #FFF7E6;
  border: 1px solid rgba(242,193,78,.45);
  padding: 6px;
}
.topbar .title{ font-size: 1.05rem; font-weight: 1000; }
.topbar .sub{ font-size: .85rem; color: var(--muted) !important; margin-top: 2px; }
.pill{
  display:inline-flex; align-items:center; gap: 8px;
  padding: 6px 10px; border-radius: 999px;
  background: rgba(242,193,78,.16);
  border: 1px solid rgba(242,193,78,.40);
  color: var(--text) !important;
  font-size: 12px;
  white-space: nowrap;
}
.kbadge{
  display:inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  background: #F1F5F9;
  border: 1px solid #E2E8F0;
  font-size: 12px;
  color: var(--text) !important;
}
.kbadge.ok{ border-color: rgba(34,197,94,.30); background: rgba(34,197,94,.10); }
.kbadge.warn{ border-color: rgba(234,179,8,.40); background: rgba(234,179,8,.12); }

/* Sidebar dark + filtros com fonte branca */
[data-testid="stSidebar"]{
  background: linear-gradient(180deg, var(--sidebar-bg1) 0%, var(--sidebar-bg2) 100%) !important;
  border-right: 1px solid var(--sidebar-line) !important;
}
[data-testid="stSidebar"] *{ color: var(--sidebar-text) !important; }
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small{ color: var(--sidebar-muted) !important; }

/* Inputs da sidebar: fundo escuro, texto branco */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea{
  background: rgba(255,255,255,.06) !important;
  color: #fff !important;
  border: 1px solid rgba(255,255,255,.12) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"]{
  background: rgba(255,255,255,.06) !important;
  border-radius: 12px !important;
  border: 1px solid rgba(255,255,255,.12) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] *{
  color: #fff !important;
}

/* Botão recolher sidebar - garante visível */
[data-testid="stHeader"]{
  background: rgba(255,255,255,.92) !important;
  border-bottom: 1px solid var(--line) !important;
}
button[data-testid="stSidebarCollapseButton"]{
  display: inline-flex !important;
  visibility: visible !important;
  opacity: 1 !important;
  background: transparent !important;
  border: 1px solid var(--line) !important;
  border-radius: 12px !important;
}
button[data-testid="stSidebarCollapseButton"] svg{ fill: #0F172A !important; }
button[data-testid="stSidebarCollapseButton"]:hover{
  background: #F8FAFC !important;
  border-color: #CBD5E1 !important;
}

/* Botões do menu na sidebar */
.navbtn{
  width: 100%;
  border-radius: 14px;
  padding: 10px 12px;
  border: 1px solid rgba(255,255,255,.12);
  background: rgba(255,255,255,.06);
  display:flex; align-items:center; justify-content:space-between;
  margin-bottom: 8px;
}
.navbtn .left{ display:flex; gap:10px; align-items:center; }
.navbtn .tag{
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(242,193,78,.18);
  border: 1px solid rgba(242,193,78,.25);
}
.navbtn.active{
  border-color: rgba(242,193,78,.45);
  background: rgba(242,193,78,.12);
}
</style>
""", unsafe_allow_html=True)


def render_topbar(title: str, subtitle: str = ""):
    u = st.session_state.get("user") or {}
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
          <div class="pill">👤 {u.get('nome','Usuário')} <span style="opacity:.6">|</span> {u.get('perfil','-')}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def filter_by_month(rows, date_col="created_at"):
    month = st.session_state.get("flt_month", "Todos")
    year = st.session_state.get("flt_year", None)
    if month == "Todos" or not year:
        return rows

    m = int(month)
    y = int(year)

    out = []
    for r in (rows or []):
        dt = pd.to_datetime(r.get(date_col), errors="coerce")
        if pd.isna(dt):
            continue
        if dt.month == m and dt.year == y:
            out.append(r)
    return out


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
        total += safe_float(r.get("qtd"), 0) * safe_float(r.get("valor_unit"), 0)

    logo_bytes = _try_fetch_bytes(LOGO_URL, timeout=10)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

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
    c.drawRightString(w - 14 * mm, h - 18 * mm, f"Cliente: {orc.get('cliente_nome','-')}")

    y = h - 55 * mm
    c.setFillColorRGB(0.08, 0.10, 0.14)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(14 * mm, y, "Itens")
    y -= 7 * mm

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

    if df_it.empty:
        c.drawString(16 * mm, y, "Sem itens cadastrados.")
        y -= 6 * mm
    else:
        for _, r in df_it.iterrows():
            if y < 25 * mm:
                c.showPage()
                y = h - 20 * mm
                c.setFont("Helvetica", 9)
            c.drawString(16 * mm, y, str(r.get("descricao") or "")[:70])
            c.drawRightString(w - 70 * mm, y, str(r.get("qtd") or 0))
            c.drawRightString(w - 48 * mm, y, str(r.get("unidade") or "")[:8])
            c.drawRightString(w - 14 * mm, y, brl(r.get("valor_unit") or 0))
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


# CSS
inject_css()

# Init DB
if "db_ok" not in st.session_state:
    ok, msg = init_database()
    st.session_state.db_ok = ok
    st.session_state.db_msg = msg


def login_ui():
    st.markdown("""
    <div class="cardx" style="max-width:980px;margin:22px auto;padding:20px;border-radius:22px;">
      <div style="display:flex;gap:14px;align-items:center;">
        <img src="%s" style="width:64px;height:64px;object-fit:contain;border-radius:18px;background:#FFF7E6;border:1px solid rgba(242,193,78,.45);padding:10px;" />
        <div>
          <div style="font-size:1.4rem;font-weight:1000;">Mamede Móveis Projetados</div>
          <div style="color:#64748B;margin-top:2px;">Acesso ao sistema interno. Padrão inicial: admin / admin123</div>
        </div>
      </div>
    </div>
    """ % LOGO_URL, unsafe_allow_html=True)

    col1, col2 = st.columns([1.05, .95])

    with col1:
        st.markdown('<div class="cardx">', unsafe_allow_html=True)
        st.subheader("Entrar")
        username = st.text_input("Usuário", placeholder="admin")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            u = da.autenticar_usuario(username.strip(), senha)
            if u:
                st.session_state.user = u
                st.session_state.page = "Vendas"
                st.rerun()
            st.error("Usuário ou senha inválidos.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="cardx">', unsafe_allow_html=True)
        st.subheader("Infraestrutura")
        ok_conn, msg_conn = test_db_connection()
        msg_conn = msg_conn if isinstance(msg_conn, str) else ("Conectado." if ok_conn else "Falha na conexão.")
        db_msg = st.session_state.db_msg if isinstance(st.session_state.db_msg, str) else "Status indisponível."

        st.markdown("**Status do banco**")
        st.success(msg_conn) if ok_conn else st.error(msg_conn)

        st.markdown("**Migração**")
        st.success(db_msg) if st.session_state.db_ok else st.error(db_msg)
        st.markdown("</div>", unsafe_allow_html=True)


def page_clientes():
    render_topbar("Clientes", "Cadastro e consulta")
    colA, colB = st.columns([1.3, 1])

    with colA:
        st.markdown('<div class="cardx">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🧾 Novo cliente</div>', unsafe_allow_html=True)

        with st.form("f_cliente", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nome = st.text_input("Nome", placeholder="Ex: João da Silva")
                fantasia = st.text_input("Fantasia", placeholder="Ex: João Móveis")
                cpf_cnpj = st.text_input("CPF/CNPJ", placeholder="Somente números ou com máscara")
            with c2:
                telefone = st.text_input("Telefone", placeholder="Ex: (88) 9xxxx-xxxx")
                whatsapp = st.text_input("WhatsApp", placeholder="Ex: (88) 9xxxx-xxxx")
                email = st.text_input("E-mail", placeholder="Ex: contato@dominio.com")

            endereco = st.text_area("Endereço", placeholder="Rua, número, bairro, cidade", height=80)
            observacoes = st.text_area("Observações", placeholder="Detalhes importantes do cliente", height=80)

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
        st.markdown('<div class="section-title">🔎 Buscar</div>', unsafe_allow_html=True)

        q = st.text_input("Pesquisar", placeholder="nome, cpf/cnpj, fantasia")
        ativo_only = st.toggle("Somente ativos", value=True)

        rows = da.listar_clientes(ativo_only=ativo_only, q=q.strip() if q else None)
        if rows:
            df = pd.DataFrame(rows)
            cols = [c for c in ["id","nome","cpf_cnpj","whatsapp","email","ativo","created_at"] if c in df.columns]
            if "created_at" in cols:
                df["created_at"] = df["created_at"].apply(fmt_date_br)
            st.dataframe(df[cols], use_container_width=True, hide_index=True)
        else:
            st.info("Sem clientes ainda.")
        st.markdown("</div>", unsafe_allow_html=True)


def page_funcionarios():
    render_topbar("Funcionários", "Cadastro e consulta")
    colA, colB = st.columns([1.3, 1])

    with colA:
        st.markdown('<div class="cardx">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">👷 Novo funcionário</div>', unsafe_allow_html=True)

        with st.form("f_func", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nome = st.text_input("Nome", placeholder="Ex: Maria Oliveira")
                funcao = st.text_input("Função", placeholder="Ex: Marceneiro, Montador, Comercial")
            with c2:
                telefone = st.text_input("Telefone", placeholder="Ex: (88) 9xxxx-xxxx")
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
        st.markdown('<div class="section-title">🔎 Buscar</div>', unsafe_allow_html=True)

        q = st.text_input("Pesquisar", key="qfunc", placeholder="nome ou função")
        ativo_only = st.toggle("Somente ativos", value=True, key="func_ativo")

        rows = da.listar_funcionarios(ativo_only=ativo_only, q=q.strip() if q else None)
        if rows:
            df = pd.DataFrame(rows)
            cols = [c for c in ["id","nome","funcao","telefone","ativo","created_at"] if c in df.columns]
            if "created_at" in cols:
                df["created_at"] = df["created_at"].apply(fmt_date_br)
            st.dataframe(df[cols], use_container_width=True, hide_index=True)
        else:
            st.info("Sem funcionários ainda.")
        st.markdown("</div>", unsafe_allow_html=True)


def page_vendas():
    render_topbar("Dashboard", "Visão rápida do sistema com filtro de mês")
    orcs_all = da.listar_orcamentos() or []
    peds_all = da.listar_pedidos() or []

    orcs = filter_by_month(orcs_all, date_col="created_at")
    peds = filter_by_month(peds_all, date_col="created_at")

    total_orc = len(orcs)
    total_ped = len(peds)
    total_ped_valor = sum(safe_float(p.get("total"), 0) for p in peds)
    total_orc_valor = sum(safe_float(o.get("total_estimado"), 0) for o in orcs)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🧾 Orçamentos", total_orc)
    c2.metric("📦 Pedidos", total_ped)
    c3.metric("💰 Total em pedidos", brl(total_ped_valor))
    c4.metric("📊 Total em orçamentos", brl(total_orc_valor))

    st.markdown('<div class="cardx" style="margin-top:14px;">', unsafe_allow_html=True)
    st.subheader("Últimos pedidos")
    if peds:
        df = pd.DataFrame(peds)
        if "data_entrega_prevista" in df.columns:
            df["data_entrega_prevista"] = df["data_entrega_prevista"].apply(fmt_date_br)
        if "created_at" in df.columns:
            df["created_at"] = df["created_at"].apply(fmt_date_br)
        if "total" in df.columns:
            df["total"] = df["total"].apply(brl)

        cols = [c for c in ["codigo","cliente_nome","status","etapa_atual","status_etapa","data_entrega_prevista","total","created_at"] if c in df.columns]
        st.dataframe(df[cols].head(50), use_container_width=True, hide_index=True)
    else:
        st.info("Sem pedidos no filtro selecionado.")
    st.markdown("</div>", unsafe_allow_html=True)


def page_orcamento():
    render_topbar("Orçamento", "Crie e edite. Pedido só nasce na página Pedido.")
    clientes = da.listar_clientes(ativo_only=True)
    if not clientes:
        st.info("Cadastre um cliente primeiro.")
        return

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
                    "status": "Aberto"
                })
                st.success(f"Orçamento criado. Código {cod}")
                st.session_state.orcamento_id = oid
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="cardx" style="margin-top:14px;">', unsafe_allow_html=True)
        st.subheader("Lista de orçamentos")
        q = st.text_input("Buscar orçamento", placeholder="código ou observação")

        rows_all = da.listar_orcamentos(q=q.strip() if q else None) or []
        rows = filter_by_month(rows_all, date_col="created_at")

        if rows:
            df = pd.DataFrame(rows)
            if "created_at" in df.columns:
                df["created_at"] = df["created_at"].apply(fmt_date_br)
            if "total_estimado" in df.columns:
                df["total_estimado"] = df["total_estimado"].apply(brl)

            cols = [c for c in ["id","codigo","cliente_nome","status","total_estimado","created_at"] if c in df.columns]
            st.dataframe(df[cols], use_container_width=True, hide_index=True)

            pick = st.selectbox("Selecionar orçamento (ID)", df["id"].tolist())
            if st.button("Abrir para editar", use_container_width=True):
                st.session_state.orcamento_id = int(pick)
                st.rerun()
        else:
            st.info("Sem orçamentos no filtro selecionado.")
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown('<div class="cardx">', unsafe_allow_html=True)
        st.subheader("Editor do orçamento")

        oid = st.session_state.get("orcamento_id")
        if not oid:
            st.info("Selecione um orçamento.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        orc = da.obter_orcamento_por_id(int(oid))
        if not orc:
            st.warning("Orçamento não encontrado.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        status = (orc.get("status") or "Aberto").strip()
        badge_class = "ok" if status == "Aprovado" else "warn"
        st.markdown(
            f"""
            <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
              <span class="kbadge {badge_class}">Código <b>{orc.get('codigo')}</b></span>
              <span class="kbadge">Status <b>{status}</b></span>
              <span class="kbadge">Cliente <b>{orc.get('cliente_nome')}</b></span>
              <span class="kbadge">Total <b>{brl(orc.get('total_estimado') or 0)}</b></span>
            </div>
            """, unsafe_allow_html=True
        )

        itens = da.listar_orcamento_itens(int(oid))
        df_it = pd.DataFrame(itens) if itens else pd.DataFrame(columns=["descricao","qtd","unidade","valor_unit"])
        df_it = df_it[[c for c in ["descricao","qtd","unidade","valor_unit"] if c in df_it.columns]]

        disabled_edit = (status == "Aprovado")
        edited = st.data_editor(df_it, num_rows="dynamic", use_container_width=True, key="orc_itens", disabled=disabled_edit)

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Salvar itens", use_container_width=True, disabled=disabled_edit):
                total = da.salvar_orcamento_itens(int(oid), edited.to_dict("records"))
                st.success(f"Itens salvos. Total {brl(total)}")
                st.rerun()
        with c2:
            if st.button("Aprovar orçamento", use_container_width=True, disabled=(status == "Aprovado")):
                ok_ap = da.aprovar_orcamento(int(oid))
                st.success("Orçamento aprovado.") if ok_ap else st.error("Falha ao aprovar.")
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


def page_pedido():
    render_topbar("Pedido", "KPIs em Real + geração a partir de orçamento aprovado")

    peds_all = da.listar_pedidos() or []
    peds = filter_by_month(peds_all, date_col="created_at")

    total_peds = len(peds)
    total_valor = sum(safe_float(p.get("total"), 0) for p in peds)
    abertos = sum(1 for p in peds if (p.get("status") or "").lower() in ["aberto", "abertos"])
    concluidos = sum(1 for p in peds if (p.get("status_etapa") or "").lower().startswith("concl"))

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📦 Pedidos no período", total_peds)
    k2.metric("💰 Total em pedidos", brl(total_valor))
    k3.metric("🟡 Pedidos abertos", abertos)
    k4.metric("✅ Etapas concluídas", concluidos)

    st.markdown('<div class="cardx" style="margin-top:14px;">', unsafe_allow_html=True)
    st.subheader("Gerar pedido a partir de orçamento aprovado")

    rows_orc_all = da.listar_orcamentos() or []
    rows_orc = filter_by_month(rows_orc_all, date_col="created_at")
    aprovados = [r for r in rows_orc if (r.get("status") == "Aprovado")]

    if not aprovados:
        st.info("Nenhum orçamento aprovado dentro do filtro selecionado.")
    else:
        df_ap = pd.DataFrame(aprovados)
        if "created_at" in df_ap.columns:
            df_ap["created_at"] = df_ap["created_at"].apply(fmt_date_br)
        if "total_estimado" in df_ap.columns:
            df_ap["total_estimado"] = df_ap["total_estimado"].apply(brl)

        cols = [c for c in ["id","codigo","cliente_nome","total_estimado","created_at"] if c in df_ap.columns]
        st.dataframe(df_ap[cols], use_container_width=True, hide_index=True)

        pick_orc = st.selectbox("Escolher orçamento aprovado (ID)", df_ap["id"].tolist())

        funcionarios = da.listar_funcionarios(ativo_only=True) or []
        f_map = {"Sem responsável": None}
        for f in funcionarios:
            f_map[f"{f['nome']} (ID {f['id']})"] = f["id"]

        c1, c2 = st.columns(2)
        with c1:
            resp = st.selectbox("Responsável", list(f_map.keys()))
        with c2:
            entrega_prev = st.date_input("Entrega prevista", value=None)

        if st.button("Gerar pedido agora", use_container_width=True):
            ok, msg, pid, pcod = da.gerar_pedido_a_partir_orcamento(
                int(pick_orc),
                responsavel_id=f_map[resp],
                data_entrega_prevista=entrega_prev,
                observacoes=f"Gerado a partir do orçamento aprovado ID {pick_orc}"
            )
            st.success(msg) if ok else st.error(msg)
            if ok:
                st.session_state.pedido_id = pid
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="cardx" style="margin-top:14px;">', unsafe_allow_html=True)
    st.subheader("Lista de pedidos (filtrados)")
    q = st.text_input("Buscar pedido", placeholder="código ou observação", key="q_ped")

    rows_q = da.listar_pedidos(q=q.strip() if q else None) or []
    rows_q = filter_by_month(rows_q, date_col="created_at")

    if rows_q:
        df = pd.DataFrame(rows_q)
        if "data_entrega_prevista" in df.columns:
            df["data_entrega_prevista"] = df["data_entrega_prevista"].apply(fmt_date_br)
        if "created_at" in df.columns:
            df["created_at"] = df["created_at"].apply(fmt_date_br)
        if "total" in df.columns:
            df["total"] = df["total"].apply(brl)

        cols = [c for c in ["id","codigo","cliente_nome","status","etapa_atual","status_etapa","responsavel_nome","data_entrega_prevista","total","created_at"] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, hide_index=True)
    else:
        st.info("Sem pedidos no filtro selecionado.")
    st.markdown("</div>", unsafe_allow_html=True)


def page_producao():
    render_topbar("Produção", "Kanban com etapas essenciais")

    etapas = [e for e in ETAPAS_PRODUCAO if str(e).strip().lower() not in ["expedição", "expedicao", "transporte"]]
    if not etapas:
        etapas = ETAPAS_PRODUCAO

    funcionarios = da.listar_funcionarios(ativo_only=True) or []
    f_map = {"Sem responsável": None}
    for f in funcionarios:
        f_map[f"{f['nome']} (ID {f['id']})"] = f["id"]

    grupos = da.listar_pedidos_por_etapa() or {}
    cols = st.columns(len(etapas))

    for i, etapa in enumerate(etapas):
        with cols[i]:
            st.markdown('<div class="cardx">', unsafe_allow_html=True)
            st.markdown(f"<b>🧱 {etapa}</b>", unsafe_allow_html=True)

            pedidos = grupos.get(etapa, []) or []
            pedidos = filter_by_month(pedidos, date_col="updated_at")

            if not pedidos:
                st.caption("Sem pedidos aqui.")
                st.markdown("</div>", unsafe_allow_html=True)
                continue

            for p in pedidos:
                status_et = p.get("status_etapa") or "A fazer"
                cls = "ok" if str(status_et).lower().startswith("concl") else "warn"

                st.markdown(f"""
                    <div class="cardx" style="margin:10px 0;">
                      <div style="display:flex;justify-content:space-between;gap:10px;align-items:center;">
                        <div style="font-weight:1000;">{p.get('codigo')}</div>
                        <span class="kbadge {cls}">{status_et}</span>
                      </div>
                      <div class="muted" style="margin-top:4px;">{p.get('cliente_nome','')}</div>
                      <div class="muted">Resp. <b>{p.get('responsavel_nome') or 'Não definido'}</b></div>
                      <div class="muted">Total <b>{brl(p.get('total') or 0)}</b></div>
                    </div>
                """, unsafe_allow_html=True)

                with st.expander("Mover e atualizar", expanded=False):
                    nova_etapa = st.selectbox("Etapa", etapas, index=etapas.index(etapa), key=f"et_{p['id']}")
                    status_et2 = st.selectbox(
                        "Status", STATUS_ETAPA,
                        index=STATUS_ETAPA.index(p.get("status_etapa") or STATUS_ETAPA[0]),
                        key=f"st_{p['id']}"
                    )
                    resp = st.selectbox("Responsável", list(f_map.keys()), key=f"rp_{p['id']}")
                    obs = st.text_area("Observação", key=f"ob_{p['id']}", height=70)
                    if st.button("Salvar", key=f"sv_{p['id']}", use_container_width=True):
                        ok, msg = da.mover_pedido_etapa(p["id"], nova_etapa, status_et2, f_map[resp], obs)
                        st.success(msg) if ok else st.error(msg)
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)


def sidebar_nav_button(label: str, page_name: str, emoji: str, current: str):
    active = (current == page_name)
    tag = "ATIVO" if active else "ABRIR"
    css = "navbtn active" if active else "navbtn"
    st.sidebar.markdown(
        f"""
        <div class="{css}">
          <div class="left">
            <div style="font-size:18px;">{emoji}</div>
            <div style="font-weight:900;">{label}</div>
          </div>
          <div class="tag">{tag}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.sidebar.button(f"{emoji} {label}", key=f"nav_{page_name}", use_container_width=True):
        st.session_state.page = page_name
        st.rerun()


def sidebar():
    u = st.session_state.user or {}
    st.sidebar.image(LOGO_URL, use_container_width=True)
    st.sidebar.markdown(f"**{u.get('nome','Usuário')}**")
    st.sidebar.caption(f"Perfil: {u.get('perfil','-')}")

    # Navegação em cima dos filtros
    st.sidebar.divider()
    st.sidebar.markdown("### Navegação")

    current = st.session_state.get("page", "Vendas")

    sidebar_nav_button("Dashboard", "Vendas", "📊", current)
    sidebar_nav_button("Clientes", "Clientes", "🧾", current)
    sidebar_nav_button("Funcionários", "Funcionários", "👷", current)
    sidebar_nav_button("Orçamentos", "Orçamento", "🧮", current)
    sidebar_nav_button("Pedidos", "Pedido", "📦", current)
    sidebar_nav_button("Produção", "Produção", "🧱", current)

    st.sidebar.divider()

    # ======== Filtro Mês/Ano (global) ========
    st.sidebar.markdown("### Filtro por mês")

    peds_all = da.listar_pedidos() or []
    orcs_all = da.listar_orcamentos() or []
    years = set()

    for r in (peds_all + orcs_all):
        dt = pd.to_datetime(r.get("created_at"), errors="coerce")
        if not pd.isna(dt):
            years.add(int(dt.year))

    years = sorted(years) if years else [pd.Timestamp.now().year]
    if "flt_year" not in st.session_state:
        st.session_state.flt_year = str(years[-1])

    year = st.sidebar.selectbox("Ano", [str(y) for y in years], index=[str(y) for y in years].index(st.session_state.flt_year))
    st.session_state.flt_year = year

    month_labels = ["Todos"] + [str(i).zfill(2) for i in range(1, 13)]
    if "flt_month" not in st.session_state:
        st.session_state.flt_month = "Todos"

    month = st.sidebar.selectbox("Mês", month_labels, index=month_labels.index(st.session_state.flt_month))
    st.session_state.flt_month = month

    st.sidebar.caption("Filtra KPIs e listas por criação (mês/ano).")

    st.sidebar.divider()
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        logout()


# Router
if "page" not in st.session_state:
    st.session_state.page = "Login"

if st.session_state.page == "Login" or not require_login():
    login_ui()
else:
    sidebar()

    # Render page
    page = st.session_state.get("page", "Vendas")
    routes = {
        "Vendas": page_vendas,
        "Clientes": page_clientes,
        "Funcionários": page_funcionarios,
        "Orçamento": page_orcamento,
        "Pedido": page_pedido,
        "Produção": page_producao,
    }
    routes.get(page, page_vendas)()
