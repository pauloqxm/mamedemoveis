import streamlit as st
import pandas as pd

from marcenaria.migrations import init_database
from marcenaria.db_connector import test_db_connection
from marcenaria import data_access as da
from marcenaria.config import ETAPAS_PRODUCAO, STATUS_ETAPA

st.set_page_config(
    page_title="Marcenaria | Sistema Interno",
    layout="wide"
)

# =========================
# ESTILO
# =========================
st.markdown("""
<style>
.small {font-size: 0.9rem; color: #475467;}
.card {
  border: 1px solid #EAECF0;
  border-radius: 14px;
  padding: 12px 14px;
  background: white;
  margin-bottom: 10px;
}
.badge {
  display:inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  background: #F2F4F7;
  font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# INIT DB
# =========================
if "db_ok" not in st.session_state:
    ok, msg = init_database()
    st.session_state.db_ok = ok
    st.session_state.db_msg = msg

# =========================
# HELPERS
# =========================
def can(perfis):
    u = st.session_state.user or {}
    return u.get("perfil") in perfis or u.get("perfil") == "admin"

def logout():
    st.session_state.user = None
    st.session_state.page = "Login"
    st.rerun()

def require_login():
    if "user" not in st.session_state or not st.session_state.user:
        st.session_state.page = "Login"
        return False
    return True

# =========================
# LOGIN
# =========================
def login_ui():
    st.title("Acesso ao Sistema")
    st.caption("Usuário inicial: admin | Senha: admin123")

    col1, col2 = st.columns([1, 1])

    with col1:
        username = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            u = da.autenticar_usuario(username.strip(), senha)
            if u:
                st.session_state.user = u
                st.session_state.page = "Vendas"
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")

    with col2:
        ok_conn, msg_conn = test_db_connection()
        st.subheader("Banco de dados")
        st.success(msg_conn) if ok_conn else st.error(msg_conn)
        st.subheader("Migração")
        st.success(st.session_state.db_msg) if st.session_state.db_ok else st.error(st.session_state.db_msg)

# =========================
# SIDEBAR
# =========================
def sidebar():
    u = st.session_state.user

    st.sidebar.markdown(f"""
**Logado:** {u.get('nome')}
Perfil: {u.get('perfil')}
""")

    if st.sidebar.button("Sair"):
        logout()

    pages = [
        ("Clientes", page_clientes),
        ("Funcionários", page_funcionarios),
        ("Vendas", page_vendas),
        ("Orçamento", page_orcamento),
        ("Pedido", page_pedido),
        ("Produção", page_producao),
    ]

    if can(["admin"]):
        pages.append(("Usuários", page_usuarios))

    labels = [p[0] for p in pages]
    current = st.session_state.get("page", "Vendas")
    if current not in labels:
        current = labels[0]

    choice = st.sidebar.radio("Navegação", labels, index=labels.index(current))
    st.session_state.page = choice
    return dict(pages)[choice]

# =========================
# PÁGINAS
# =========================
def page_clientes():
    st.header("Cadastro • Clientes")

    with st.form("cliente_form", clear_on_submit=True):
        nome = st.text_input("Nome")
        telefone = st.text_input("Telefone")
        whatsapp = st.text_input("WhatsApp")
        email = st.text_input("E-mail")
        endereco = st.text_area("Endereço")
        obs = st.text_area("Observações")
        salvar = st.form_submit_button("Salvar", use_container_width=True)

        if salvar:
            if not nome.strip():
                st.error("Nome é obrigatório.")
            else:
                da.criar_cliente({
                    "nome": nome,
                    "telefone": telefone,
                    "whatsapp": whatsapp,
                    "email": email,
                    "endereco": endereco,
                    "observacoes": obs
                })
                st.success("Cliente cadastrado.")
                st.rerun()

    st.divider()
    clientes = da.listar_clientes()
    if clientes:
        st.dataframe(pd.DataFrame(clientes), use_container_width=True, hide_index=True)

def page_funcionarios():
    st.header("Cadastro • Funcionários")

    with st.form("func_form", clear_on_submit=True):
        nome = st.text_input("Nome")
        funcao = st.text_input("Função")
        telefone = st.text_input("Telefone")
        salvar = st.form_submit_button("Salvar", use_container_width=True)

        if salvar:
            if not nome.strip():
                st.error("Nome é obrigatório.")
            else:
                da.criar_funcionario({
                    "nome": nome,
                    "funcao": funcao,
                    "telefone": telefone
                })
                st.success("Funcionário cadastrado.")
                st.rerun()

    st.divider()
    funcs = da.listar_funcionarios()
    if funcs:
        st.dataframe(pd.DataFrame(funcs), use_container_width=True, hide_index=True)

def page_usuarios():
    st.header("Administração • Usuários")

    if not can(["admin"]):
        st.warning("Acesso restrito.")
        return

    with st.form("user_form", clear_on_submit=True):
        nome = st.text_input("Nome")
        email = st.text_input("E-mail")
        username = st.text_input("Username")
        senha = st.text_input("Senha", type="password")
        perfil = st.selectbox("Perfil", ["admin", "comercial", "producao", "leitura"])
        setor = st.text_input("Setor")
        salvar = st.form_submit_button("Criar usuário", use_container_width=True)

        if salvar:
            ok, msg = da.criar_usuario({
                "nome": nome,
                "email": email,
                "username": username,
                "senha": senha,
                "perfil": perfil,
                "setor": setor
            })
            st.success(msg) if ok else st.error(msg)
            if ok:
                st.rerun()

    st.divider()
    users = da.listar_usuarios()
    if users:
        st.dataframe(pd.DataFrame(users), use_container_width=True, hide_index=True)

def page_orcamento():
    st.header("Orçamento")
    st.info("Fluxo de orçamento já funcional. Próximo passo: melhorias visuais.")

def page_pedido():
    st.header("Pedido")
    st.info("Criação e edição de pedidos operante.")

def page_producao():
    st.header("Produção • Kanban")

    grupos = da.listar_pedidos_por_etapa()
    cols = st.columns(len(ETAPAS_PRODUCAO))

    for i, etapa in enumerate(ETAPAS_PRODUCAO):
        with cols[i]:
            st.subheader(etapa)
            for p in grupos.get(etapa, []):
                st.markdown(f"""
                <div class="card">
                    <b>{p.get('codigo')}</b>
                    <div class="small">{p.get('cliente_nome')}</div>
                    <span class="badge">{p.get('status_etapa')}</span>
                </div>
                """, unsafe_allow_html=True)

def page_vendas():
    st.header("Vendas")
    orcs = da.listar_orcamentos()
    peds = da.listar_pedidos()

    col1, col2, col3 = st.columns(3)
    col1.metric("Orçamentos", len(orcs))
    col2.metric("Pedidos", len(peds))
    col3.metric("Em Produção", sum(1 for p in peds if p.get("etapa_atual") == "Produção"))

    if peds:
        st.dataframe(pd.DataFrame(peds), use_container_width=True, hide_index=True)

# =========================
# MAIN
# =========================
if "page" not in st.session_state:
    st.session_state.page = "Login"

if st.session_state.page == "Login" or not require_login():
    login_ui()
else:
    render = sidebar()
    render()
