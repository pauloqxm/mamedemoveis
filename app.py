import streamlit as st
import pandas as pd

from marcenaria.migrations import init_database
from marcenaria.db_connector import test_db_connection
from marcenaria import data_access as da
from marcenaria.config import ETAPAS_PRODUCAO, STATUS_ETAPA

st.set_page_config(page_title="Marcenaria | Sistema Interno", layout="wide")

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

if "db_ok" not in st.session_state:
    ok, msg = init_database()
    st.session_state.db_ok = ok
    st.session_state.db_msg = msg


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


def login_ui():
    st.title("Acesso")
    st.caption("Padrão inicial. admin / admin123")

    col1, col2 = st.columns([1, 1])
    with col1:
        username = st.text_input("Usuário", placeholder="admin")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            u = da.autenticar_usuario(username.strip(), senha)
            if u:
                st.session_state.user = u
                st.session_state.page = "Vendas"
                st.rerun()
            st.error("Usuário ou senha inválidos.")

    with col2:
        ok_conn, msg_conn = test_db_connection()
        st.write("Status do banco")
        st.success(msg_conn) if ok_conn else st.error(msg_conn)
        st.write("Migração")
        st.success(st.session_state.db_msg) if st.session_state.db_ok else st.error(st.session_state.db_msg)

    return None


def page_clientes():
    st.header("Cadastro • Clientes")
    colA, colB = st.columns([1.2, 1])

    with colA:
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

    with colB:
        st.subheader("Buscar")
        q = st.text_input("Pesquisar", placeholder="nome, cpf/cnpj, fantasia")
        ativo_only = st.toggle("Somente ativos", value=True)
        rows = da.listar_clientes(ativo_only=ativo_only, q=q.strip() if q else None)
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df[["id","nome","cpf_cnpj","whatsapp","email","ativo"]], use_container_width=True, hide_index=True)
        else:
            st.info("Sem clientes ainda.")
    return None


def page_funcionarios():
    st.header("Cadastro • Funcionários")
    colA, colB = st.columns([1.2, 1])

    with colA:
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

    with colB:
        st.subheader("Buscar")
        q = st.text_input("Pesquisar", key="qfunc", placeholder="nome ou função")
        ativo_only = st.toggle("Somente ativos", value=True, key="func_ativo")
        rows = da.listar_funcionarios(ativo_only=ativo_only, q=q.strip() if q else None)
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df[["id","nome","funcao","telefone","ativo"]], use_container_width=True, hide_index=True)
        else:
            st.info("Sem funcionários ainda.")
    return None


def page_usuarios():
    st.header("Administração • Usuários")
    if not can(["admin"]):
        st.warning("Acesso restrito.")
        return None

    colA, colB = st.columns([1.1, 1])

    with colA:
        st.subheader("Criar usuário")
        with st.form("f_user", clear_on_submit=True):
            nome = st.text_input("Nome")
            email = st.text_input("E-mail")
            username = st.text_input("Username")
            senha = st.text_input("Senha", type="password")
            perfil = st.selectbox("Perfil", ["admin","comercial","producao","leitura"], index=3)
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

    with colB:
        st.subheader("Gerenciar")
        users = da.listar_usuarios()
        if not users:
            st.info("Sem usuários.")
            return None
        df = pd.DataFrame(users)
        st.dataframe(df[["id","nome","username","perfil","setor","ativo"]], use_container_width=True, hide_index=True)

        uid = st.selectbox("Selecionar usuário pelo ID", df["id"].tolist())
        urow = df[df["id"] == uid].iloc[0].to_dict()

        with st.form("f_user_edit"):
            nome = st.text_input("Nome", value=urow.get("nome",""))
            email = st.text_input("E-mail", value=urow.get("email",""))
            username = st.text_input("Username", value=urow.get("username",""))
            perfil = st.selectbox(
                "Perfil",
                ["admin","comercial","producao","leitura"],
                index=["admin","comercial","producao","leitura"].index(urow.get("perfil","leitura"))
            )
            setor = st.text_input("Setor", value=urow.get("setor",""))
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

    return None


def page_orcamento():
    st.header("Orçamento")

    clientes = da.listar_clientes(ativo_only=True)
    if not clientes:
        st.info("Cadastre um cliente primeiro.")
        return None

    c_map = {f"{c['nome']} (ID {c['id']})": c["id"] for c in clientes}

    colA, colB = st.columns([1, 1])

    with colA:
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
                    "observacoes": observacoes
                })
                st.success(f"Orçamento criado. Código {cod}")
                st.session_state.orcamento_id = oid
                st.rerun()

    with colB:
        st.subheader("Itens do orçamento")
        oid = st.session_state.get("orcamento_id")

        if not oid:
            st.info("Crie ou selecione um orçamento abaixo.")
        else:
            orc = da.obter_orcamento_por_id(int(oid))
            if not orc:
                st.warning("Orçamento não encontrado.")
                return None

            st.markdown(
                f"**Código:** {orc.get('codigo')}  \n"
                f"**Status:** {orc.get('status')}  \n"
                f"**Cliente:** {orc.get('cliente_nome')}"
            )

            itens = da.listar_orcamento_itens(int(oid))
            df_it = pd.DataFrame(itens) if itens else pd.DataFrame(columns=["descricao","qtd","unidade","valor_unit"])
            df_it = df_it[[c for c in ["descricao","qtd","unidade","valor_unit"] if c in df_it.columns]]

            disabled_edit = (orc.get("status") == "Aprovado")
            edited = st.data_editor(
                df_it,
                num_rows="dynamic",
                use_container_width=True,
                key="orc_itens",
                disabled=disabled_edit
            )

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Salvar itens", use_container_width=True, disabled=disabled_edit):
                    total = da.salvar_orcamento_itens(int(oid), edited.to_dict("records"))
                    st.success(f"Itens salvos. Total estimado R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X","."))
                    st.rerun()

            with c2:
                disabled_aprov = (orc.get("status") == "Aprovado")
                if st.button("Aprovar e gerar Pedido", use_container_width=True, disabled=disabled_aprov):
                    ok, msg, pedido_id, pedido_codigo = da.gerar_pedido_a_partir_orcamento(
                        int(oid),
                        responsavel_id=None,
                        data_entrega_prevista=None,
                        observacoes=f"Gerado a partir do orçamento {orc.get('codigo')}"
                    )
                    if ok:
                        st.success(msg)
                        st.session_state.pedido_id = pedido_id
                        st.session_state.page = "Pedido"
                        st.rerun()
                    else:
                        st.error(msg)

    st.divider()
    st.subheader("Lista de orçamentos")
    q = st.text_input("Buscar orçamento", placeholder="código ou observação")
    rows = da.listar_orcamentos(q=q.strip() if q else None)
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df[["id","codigo","cliente_nome","status","total_estimado","created_at"]], use_container_width=True, hide_index=True)
        pick = st.selectbox("Selecionar orçamento (ID)", df["id"].tolist())
        if st.button("Abrir para editar", use_container_width=True):
            st.session_state.orcamento_id = int(pick)
            st.rerun()
    else:
        st.info("Sem orçamentos ainda.")
    return None


def page_pedido():
    st.header("Pedido")

    clientes = da.listar_clientes(ativo_only=True)
    if not clientes:
        st.info("Cadastre um cliente primeiro.")
        return None

    funcionarios = da.listar_funcionarios(ativo_only=True)
    f_map = {"Sem responsável": None}
    for f in funcionarios:
        f_map[f"{f['nome']} (ID {f['id']})"] = f["id"]

    c_map = {f"{c['nome']} (ID {c['id']})": c["id"] for c in clientes}

    colA, colB = st.columns([1, 1])

    with colA:
        st.subheader("Criar pedido")
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
            df_it = pd.DataFrame(itens) if itens else pd.DataFrame(columns=["descricao","qtd","unidade","valor_unit"])
            df_it = df_it[[c for c in ["descricao","qtd","unidade","valor_unit"] if c in df_it.columns]]
            edited = st.data_editor(df_it, num_rows="dynamic", use_container_width=True, key="ped_itens")
            if st.button("Salvar itens do pedido", use_container_width=True):
                total = da.salvar_pedido_itens(pid, edited.to_dict("records"))
                st.success(f"Itens salvos. Total R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X","."))
                st.rerun()

    st.divider()
    st.subheader("Lista de pedidos")
    q = st.text_input("Buscar pedido", placeholder="código ou observação", key="q_ped")
    rows = da.listar_pedidos(q=q.strip() if q else None)
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df[["id","codigo","cliente_nome","status","etapa_atual","status_etapa","responsavel_nome","data_entrega_prevista","total"]], use_container_width=True, hide_index=True)
        pick = st.selectbox("Selecionar pedido (ID)", df["id"].tolist())
        if st.button("Abrir pedido", use_container_width=True):
            st.session_state.pedido_id = int(pick)
            st.rerun()
    else:
        st.info("Sem pedidos ainda.")
    return None


def page_producao():
    st.header("Produção • Kanban")

    funcionarios = da.listar_funcionarios(ativo_only=True)
    f_map = {"Sem responsável": None}
    for f in funcionarios:
        f_map[f"{f['nome']} (ID {f['id']})"] = f["id"]

    grupos = da.listar_pedidos_por_etapa()
    cols = st.columns(len(ETAPAS_PRODUCAO))

    for i, etapa in enumerate(ETAPAS_PRODUCAO):
        with cols[i]:
            st.subheader(etapa)
            for p in grupos.get(etapa, []):
                st.markdown(f"""
                <div class="card">
                    <div><b>{p.get('codigo')}</b> <span class="badge">{p.get('status_etapa','')}</span></div>
                    <div class="small">{p.get('cliente_nome','')}</div>
                    <div class="small">Resp. {p.get('responsavel_nome') or 'Não definido'}</div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("Mover", expanded=False):
                    nova_etapa = st.selectbox("Etapa", ETAPAS_PRODUCAO, index=ETAPAS_PRODUCAO.index(etapa), key=f"et_{p['id']}")
                    status_et = st.selectbox("Status", STATUS_ETAPA, index=STATUS_ETAPA.index(p.get("status_etapa") or "A fazer"), key=f"st_{p['id']}")
                    resp = st.selectbox("Responsável", list(f_map.keys()), index=0, key=f"rp_{p['id']}")
                    obs = st.text_area("Observação", key=f"ob_{p['id']}", height=70)
                    if st.button("Salvar", key=f"sv_{p['id']}", use_container_width=True):
                        ok, msg = da.mover_pedido_etapa(p["id"], nova_etapa, status_et, f_map[resp], obs)
                        st.success(msg) if ok else st.error(msg)
                        st.rerun()
    return None


def page_vendas():
    st.header("Vendas")
    orcs = da.listar_orcamentos()
    peds = da.listar_pedidos()

    col1, col2, col3 = st.columns(3)
    col1.metric("Orçamentos", len(orcs))
    col2.metric("Pedidos", len(peds))
    col3.metric("Na etapa Produção", sum(1 for p in peds if p.get("etapa_atual") == "Produção"))

    if peds:
        df = pd.DataFrame(peds)
        st.subheader("Últimos pedidos")
        st.dataframe(df[["codigo","cliente_nome","status","etapa_atual","status_etapa","data_entrega_prevista","total"]].head(50), use_container_width=True, hide_index=True)
    return None


def sidebar():
    u = st.session_state.user
    st.sidebar.markdown(f"**Logado:** {u.get('nome')}\n\nPerfil: {u.get('perfil')}")

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


if "page" not in st.session_state:
    st.session_state.page = "Login"

if st.session_state.page == "Login" or not require_login():
    _ = login_ui()
else:
    render = sidebar()
    _ = render()
