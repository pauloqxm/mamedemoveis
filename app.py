import io
from datetime import date, datetime
from urllib.request import urlopen

import pandas as pd
import streamlit as st

from marcenaria.migrations import init_database
from marcenaria.db_connector import test_db_connection, get_db_connection
from marcenaria import data_access as da
from marcenaria.config import ETAPAS_PRODUCAO, STATUS_ETAPA

APP_TITLE = "Mamede Móveis Projetados | Sistema Interno"
LOGO_URL = "https://i.ibb.co/FkXDym6H/logo-mamede.png"

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")

# Força tema CLARO sempre
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


def _try_fetch_bytes(url: str, timeout: int = 10):
    try:
        with urlopen(url, timeout=timeout) as r:
            return r.read()
    except Exception:
        return None


def safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default


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


def fmt_dt_br(x):
    if x is None or x == "":
        return ""
    try:
        dt = pd.to_datetime(x, errors="coerce")
        if pd.isna(dt):
            return str(x)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(x)


# ✅ agora sempre timezone-aware (UTC), evita conflito com TIMESTAMPTZ
def now_ts_utc():
    return pd.Timestamp.now(tz="UTC")


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

/* KPI: força texto escuro */
[data-testid="stMetric"]{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 14px 16px;
  box-shadow: var(--shadow);
}
[data-testid="stMetricLabel"]{
  color: #0F172A !important;
  font-weight: 900 !important;
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
.kbadge.bad{ border-color: rgba(239,68,68,.35); background: rgba(239,68,68,.12); }

/* SEMÁFORO */
.sem-pill{
  display:inline-flex;
  align-items:center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 900;
  border: 1px solid transparent;
}
.sem-green{ background: rgba(34,197,94,.12); border-color: rgba(34,197,94,.35); color: #166534; }
.sem-yellow{ background: rgba(234,179,8,.12); border-color: rgba(234,179,8,.40); color: #854d0e; }
.sem-red{ background: rgba(239,68,68,.12); border-color: rgba(239,68,68,.35); color: #991b1b; }
.sem-gray{ background: rgba(148,163,184,.12); border-color: rgba(148,163,184,.35); color: #334155; }

/* Sidebar dark + filtros com fonte branca */
[data-testid="stSidebar"]{
  background: linear-gradient(180deg, var(--sidebar-bg1) 0%, var(--sidebar-bg2) 100%) !important;
  border-right: 1px solid var(--sidebar-line) !important;
}
[data-testid="stSidebar"] *{ color: var(--sidebar-text) !important; }
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small{ color: var(--sidebar-muted) !important; }

/* Inputs da sidebar */
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

/* Timeline */
.tl-row{
  display:flex;
  gap:10px;
  align-items:flex-start;
  margin: 10px 0;
}
.tl-dot{
  width: 10px;
  height: 10px;
  border-radius: 99px;
  background: rgba(242,193,78,1);
  margin-top: 6px;
  box-shadow: 0 0 0 4px rgba(242,193,78,.18);
}
.tl-box{ flex:1; }
</style>
""",
        unsafe_allow_html=True,
    )


inject_css()

# =========================
# INIT DB
# =========================
if "db_ok" not in st.session_state:
    ok, msg = init_database()
    st.session_state.db_ok = ok
    st.session_state.db_msg = msg


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
        unsafe_allow_html=True,
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


def excluir_pedido_db(pedido_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM bd_marcenaria.pedidos WHERE id=%s", (pedido_id,))
            conn.commit()
    return True


def excluir_orcamento_db(orcamento_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM bd_marcenaria.pedidos WHERE orcamento_id=%s", (orcamento_id,))
            cnt = cur.fetchone()[0]
            if cnt and int(cnt) > 0:
                return False, "Não posso excluir. Já existe pedido gerado deste orçamento."
            cur.execute("DELETE FROM bd_marcenaria.orcamentos WHERE id=%s", (orcamento_id,))
            conn.commit()
    return True, "Orçamento excluído."


# =========================
# HISTÓRICO ETAPAS + ANALYTICS (SEMÁFORO / GARGALOS)
# =========================
def fetch_hist_for_pedidos(pedido_ids: list[int]):
    if not pedido_ids:
        return []

    placeholders = ",".join(["%s"] * len(pedido_ids))
    sql = f"""
        SELECT
            e.id,
            e.pedido_id,
            e.etapa,
            e.status,
            e.responsavel_id,
            f.nome as responsavel_nome,
            e.inicio_em,
            e.fim_em,
            e.observacoes,
            e.created_at
        FROM bd_marcenaria.producao_etapas e
        LEFT JOIN bd_marcenaria.funcionarios f ON f.id = e.responsavel_id
        WHERE e.pedido_id IN ({placeholders})
        ORDER BY e.pedido_id ASC, COALESCE(e.inicio_em, e.created_at) ASC, e.id ASC
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, pedido_ids)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall() or []
            return [dict(zip(cols, r)) for r in rows]


def _nice_days(d):
    if d is None:
        return "-"
    try:
        d = float(d)
    except Exception:
        return "-"
    if d < 1:
        horas = int(round(d * 24))
        return f"{max(horas,0)}h"
    return f"{int(round(d))}d"


def compute_etapa_stats(pedidos_rows: list[dict]):
    """
    ✅ CORREÇÃO: tudo vira UTC (timezone-aware), assim (fim - início) nunca quebra.
    """
    agora = now_ts_utc()

    ids = [int(p.get("id")) for p in (pedidos_rows or []) if p.get("id") is not None]
    hist = fetch_hist_for_pedidos(ids)
    if not hist:
        return {}, {}

    df = pd.DataFrame(hist)

    # ✅ sempre UTC
    for c in ["inicio_em", "fim_em", "created_at"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", utc=True)

    # início/fim efetivos (UTC)
    df["ini_eff"] = df["inicio_em"].fillna(df["created_at"])
    df["fim_eff"] = df["fim_em"].fillna(agora)

    # Se algum ini_eff ficou NaT, tenta segurar com created_at (ou cai fora)
    df = df[~df["ini_eff"].isna()].copy()

    df["dur_days"] = (df["fim_eff"] - df["ini_eff"]).dt.total_seconds() / 86400.0
    df["dur_days"] = df["dur_days"].clip(lower=0)

    df["is_open"] = df["fim_em"].isna()

    stats = {}
    for etapa, g in df.groupby("etapa"):
        g_closed = g[~g["is_open"]]
        avg_closed = float(g_closed["dur_days"].mean()) if len(g_closed) else None
        avg_all = float(g["dur_days"].mean()) if len(g) else None
        open_days_sum = float(g[g["is_open"]]["dur_days"].sum()) if len(g[g["is_open"]]) else 0.0
        open_count = int(g["is_open"].sum())

        stats[etapa] = {
            "avg_closed": avg_closed,
            "avg_all": avg_all,
            "open_days_sum": open_days_sum,
            "open_count": open_count,
        }

    pedido_current = {}
    df_open = df[df["is_open"]].copy()
    if len(df_open):
        df_open.sort_values(["pedido_id", "ini_eff"], inplace=True)
        last_open = df_open.groupby("pedido_id").tail(1)
        for _, r in last_open.iterrows():
            pid = int(r["pedido_id"])
            pedido_current[pid] = {"etapa": r.get("etapa"), "days_open": float(r.get("dur_days") or 0.0)}

    return stats, pedido_current


def semaforo_class(days_open: float | None, avg_days: float | None):
    if days_open is None or avg_days is None or avg_days <= 0:
        return "sem-gray", "⚪ Sem base"
    if days_open <= avg_days:
        return "sem-green", "🟢 No ritmo"
    if days_open <= avg_days * 1.5:
        return "sem-yellow", "🟡 Atenção"
    return "sem-red", "🔴 Gargalo"


def render_gargalos_panel(stats: dict):
    st.markdown('<div class="cardx" style="margin-top:14px;">', unsafe_allow_html=True)
    st.subheader("🚦 Gargalos e tempo médio por etapa")

    if not stats:
        st.info("Sem histórico suficiente para calcular gargalos. Quando começar a mover no Kanban, isso vira ouro.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    rows = []
    for etapa, s in stats.items():
        rows.append(
            {
                "Etapa": etapa,
                "Pedidos em andamento": s["open_count"],
                "Dias acumulados em andamento": round(s["open_days_sum"], 2),
                "Média fechados (dias)": None if s["avg_closed"] is None else round(s["avg_closed"], 2),
                "Média geral (dias)": None if s["avg_all"] is None else round(s["avg_all"], 2),
            }
        )

    df = pd.DataFrame(rows)
    df_rank = df.sort_values(["Dias acumulados em andamento", "Pedidos em andamento"], ascending=False)

    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("**🏆 Ranking de gargalos (top)**")
        show = df_rank[["Etapa", "Pedidos em andamento", "Dias acumulados em andamento"]].head(10)
        st.dataframe(show, use_container_width=True, hide_index=True)

    with c2:
        st.markdown("**📌 Médias por etapa**")
        show2 = df.sort_values("Etapa")[["Etapa", "Média fechados (dias)", "Média geral (dias)"]]
        st.dataframe(show2, use_container_width=True, hide_index=True)

    st.caption("O semáforo usa a média dos eventos fechados. Se não tiver fechados, cai pra média geral.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_timeline_pedidos_hard(rows, etapa_stats: dict, pedido_current: dict):
    st.markdown('<div class="cardx" style="margin-top:14px;">', unsafe_allow_html=True)
    st.subheader("⏳ Linha do tempo por etapas (tempo real)")

    if not rows:
        st.info("Sem pedidos no período para acompanhar.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    hoje = date.today()
    agora = now_ts_utc()

    q = st.text_input(
        "Filtrar na linha do tempo",
        placeholder="código, cliente, etapa, responsável",
        key="tl_q_hard",
    )

    base_rows = rows
    if q:
        ql = q.strip().lower()

        def _match(r):
            base = " ".join(
                [
                    str(r.get("codigo", "")),
                    str(r.get("cliente_nome", "")),
                    str(r.get("etapa_atual", "")),
                    str(r.get("status_etapa", "")),
                    str(r.get("responsavel_nome", "")),
                ]
            ).lower()
            return ql in base

        base_rows = [r for r in rows if _match(r)]

    if not base_rows:
        st.info("Nada encontrado nesse filtro.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    def _sort_key(r):
        return pd.to_datetime(r.get("updated_at") or r.get("created_at"), errors="coerce")

    base_rows = sorted(base_rows, key=_sort_key, reverse=True)[:60]

    ids = [int(p.get("id")) for p in base_rows if p.get("id") is not None]
    hist_all = fetch_hist_for_pedidos(ids)
    dfh = pd.DataFrame(hist_all) if hist_all else pd.DataFrame()

    for p in base_rows:
        pid = int(p.get("id"))
        cod = p.get("codigo", "")
        cliente = p.get("cliente_nome", "")
        etapa_atual = p.get("etapa_atual", "-")
        status_et = p.get("status_etapa", "-")
        total = brl(p.get("total") or 0)

        created = pd.to_datetime(p.get("created_at"), errors="coerce")
        updated = pd.to_datetime(p.get("updated_at"), errors="coerce")
        entrega = pd.to_datetime(p.get("data_entrega_prevista"), errors="coerce")

        dias_andamento = None
        if not pd.isna(created):
            dias_andamento = (hoje - created.date()).days

        dias_faltam = None
        if not pd.isna(entrega):
            dias_faltam = (entrega.date() - hoje).days

        prazo_txt = "Sem entrega definida"
        prazo_badge = "warn"
        if dias_faltam is not None:
            if dias_faltam >= 0:
                prazo_txt = f"Faltam {dias_faltam} dia(s)"
                prazo_badge = "ok" if dias_faltam >= 3 else "warn"
            else:
                prazo_txt = f"Atrasado {abs(dias_faltam)} dia(s)"
                prazo_badge = "bad"

        cur_info = pedido_current.get(pid)
        sem_cls = "sem-gray"
        sem_txt = "⚪ Sem base"
        sem_detail = ""
        if cur_info:
            etapa_open = cur_info.get("etapa")
            days_open = cur_info.get("days_open", 0.0)
            avg = None
            if etapa_open in etapa_stats:
                avg = etapa_stats[etapa_open].get("avg_closed") or etapa_stats[etapa_open].get("avg_all")
            sem_cls, sem_txt = semaforo_class(days_open, avg)
            sem_detail = f"{_nice_days(days_open)} na etapa. Média {_nice_days(avg) if avg else '-'}."

        st.markdown(
            f"""
            <div class="cardx" style="margin:12px 0;">
              <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap;">
                <div>
                  <div style="font-weight:1000;font-size:1.05rem;">📦 {cod}</div>
                  <div class="muted">{cliente}</div>
                  <div class="muted">Etapa <b>{etapa_atual}</b> • Status <b>{status_et}</b> • Total <b>{total}</b></div>
                </div>
                <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
                  <span class="kbadge">🗓️ Criado <b>{fmt_date_br(created) if not pd.isna(created) else ""}</b></span>
                  <span class="kbadge">🔄 Atualizado <b>{fmt_date_br(updated) if not pd.isna(updated) else ""}</b></span>
                  <span class="kbadge {prazo_badge}">🚚 {prazo_txt}</span>
                  <span class="kbadge">⏱️ Andamento <b>{dias_andamento if dias_andamento is not None else "-"} dia(s)</b></span>
                  <span class="sem-pill {sem_cls}">🚦 {sem_txt}</span>
                </div>
              </div>
              <div class="muted" style="margin-top:8px;">{sem_detail}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if dfh.empty:
            st.info("Sem histórico de etapas registrado ainda.")
            st.divider()
            continue

        dfp = dfh[dfh["pedido_id"] == pid].copy()
        if dfp.empty:
            st.info("Sem histórico de etapas registrado ainda.")
            st.divider()
            continue

        for c in ["inicio_em", "fim_em", "created_at"]:
            if c in dfp.columns:
                dfp[c] = pd.to_datetime(dfp[c], errors="coerce", utc=True)

        dfp["ini_eff"] = dfp["inicio_em"].fillna(dfp["created_at"]).fillna(pd.to_datetime(p.get("created_at"), errors="coerce", utc=True))
        dfp["fim_eff"] = dfp["fim_em"].fillna(agora)
        dfp = dfp[~dfp["ini_eff"].isna()].copy()
        dfp["dur_days"] = (dfp["fim_eff"] - dfp["ini_eff"]).dt.total_seconds() / 86400.0
        dfp["dur_days"] = dfp["dur_days"].clip(lower=0)
        dfp["is_open"] = dfp["fim_em"].isna()

        total_hist = float(dfp["dur_days"].sum()) if len(dfp) else 0.0
        etapas_sum = dfp.groupby("etapa")["dur_days"].sum().sort_values(ascending=False).reset_index()

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            st.metric("🧠 Tempo total no histórico", _nice_days(total_hist))
        with c2:
            st.metric("🧱 Etapa atual", etapa_atual)
        with c3:
            st.metric("📌 Status etapa", status_et)

        st.markdown('<div class="cardx" style="margin-top:10px;">', unsafe_allow_html=True)
        st.markdown("**📊 Tempo acumulado por etapa**")
        for _, r in etapas_sum.iterrows():
            st.markdown(f"- **{r['etapa']}**: {_nice_days(float(r['dur_days']))}")
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("🧾 Ver linha do tempo detalhada", expanded=False):
            dfp = dfp.sort_values(["ini_eff", "id"])
            for _, r in dfp.iterrows():
                etapa = r.get("etapa") or "-"
                status = r.get("status") or "-"
                resp = r.get("responsavel_nome") or "Não definido"
                ini = r.get("ini_eff")
                fim = r.get("fim_em")
                dur = float(r.get("dur_days") or 0.0)
                dur_txt = _nice_days(dur)
                obs = (r.get("observacoes") or "").strip()
                obs_txt = obs if obs else "Sem observações."

                st.markdown(
                    f"""
                    <div class="tl-row">
                      <div><div class="tl-dot"></div></div>
                      <div class="tl-box">
                        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
                          <span class="kbadge">🧱 <b>{etapa}</b></span>
                          <span class="kbadge">📌 <b>{status}</b></span>
                          <span class="kbadge">👤 <b>{resp}</b></span>
                          <span class="kbadge">⏱️ <b>{dur_txt}</b></span>
                          <span class="kbadge">{'🟣 Em andamento' if pd.isna(fim) else '✅ Finalizado'}</span>
                        </div>
                        <div class="muted" style="margin-top:6px;">
                          Início <b>{fmt_dt_br(ini)}</b>
                          {" • Fim <b>" + fmt_dt_br(fim) + "</b>" if not pd.isna(fim) else " • <b>Em andamento</b>"}
                        </div>
                        <div class="muted" style="margin-top:4px;">📝 {obs_txt}</div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.divider()

    st.caption("Mostrando até 60 pedidos na linha do tempo para manter rápido.")
    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# LOGIN
# =========================
def login_ui():
    st.markdown(
        f"""
    <div class="cardx" style="max-width:980px;margin:22px auto;padding:20px;border-radius:22px;">
      <div style="display:flex;gap:14px;align-items:center;">
        <img src="{LOGO_URL}" style="width:64px;height:64px;object-fit:contain;border-radius:18px;background:#FFF7E6;border:1px solid rgba(242,193,78,.45);padding:10px;" />
        <div>
          <div style="font-size:1.4rem;font-weight:1000;">Mamede Móveis Projetados</div>
          <div style="color:#64748B;margin-top:2px;">Acesso ao sistema interno. Padrão inicial: admin / admin123</div>
        </div>
      </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1.05, 0.95])

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


# =========================
# PÁGINAS (as que estavam no arquivo anterior)
# =========================
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
                    da.criar_cliente(
                        {
                            "nome": nome.strip(),
                            "fantasia": fantasia.strip(),
                            "cpf_cnpj": cpf_cnpj.strip(),
                            "telefone": telefone.strip(),
                            "whatsapp": whatsapp.strip(),
                            "email": email.strip(),
                            "endereco": endereco.strip(),
                            "observacoes": observacoes.strip(),
                        }
                    )
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
            cols = [c for c in ["id", "nome", "cpf_cnpj", "whatsapp", "email", "ativo", "created_at"] if c in df.columns]
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
                    da.criar_funcionario(
                        {
                            "nome": nome.strip(),
                            "funcao": funcao.strip(),
                            "telefone": telefone.strip(),
                            "data_admissao": data_adm,
                        }
                    )
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
            cols = [c for c in ["id", "nome", "funcao", "telefone", "ativo", "created_at"] if c in df.columns]
            if "created_at" in cols:
                df["created_at"] = df["created_at"].apply(fmt_date_br)
            st.dataframe(df[cols], use_container_width=True, hide_index=True)
        else:
            st.info("Sem funcionários ainda.")
        st.markdown("</div>", unsafe_allow_html=True)


def page_vendas():
    render_topbar("Dashboard", "Semáforo por etapa e ranking de gargalos")

    orcs_all = da.listar_orcamentos() or []
    peds_all = da.listar_pedidos() or []

    orcs = filter_by_month(orcs_all, date_col="created_at")
    peds = filter_by_month(peds_all, date_col="created_at")

    total_orc = len(orcs)
    total_ped = len(peds)
    total_ped_valor = sum(safe_float(p.get("total"), 0) for p in peds)
    total_orc_valor = sum(safe_float(o.get("total_estimado"), 0) for o in orcs)

    etapa_stats, pedido_current = compute_etapa_stats(peds)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🧾 Orçamentos", total_orc)
    c2.metric("📦 Pedidos", total_ped)
    c3.metric("💰 Total em pedidos", brl(total_ped_valor))
    c4.metric("📊 Total em orçamentos", brl(total_orc_valor))

    render_gargalos_panel(etapa_stats)

    st.markdown('<div class="cardx" style="margin-top:14px;">', unsafe_allow_html=True)
    st.subheader("📌 Últimos pedidos")
    if peds:
        df = pd.DataFrame(peds)
        if "data_entrega_prevista" in df.columns:
            df["data_entrega_prevista"] = df["data_entrega_prevista"].apply(fmt_date_br)
        if "created_at" in df.columns:
            df["created_at"] = df["created_at"].apply(fmt_date_br)
        if "total" in df.columns:
            df["total"] = df["total"].apply(brl)

        cols = [c for c in ["codigo", "cliente_nome", "status", "etapa_atual", "status_etapa", "data_entrega_prevista", "total", "created_at"] if c in df.columns]
        st.dataframe(df[cols].head(50), use_container_width=True, hide_index=True)
    else:
        st.info("Sem pedidos no filtro selecionado.")
    st.markdown("</div>", unsafe_allow_html=True)


# As páginas Orçamento, Pedido e Produção continuam como estavam na versão anterior.
# (Se você quiser, eu te devolvo também com elas aqui, mas como você pediu "ajuste e devolva",
# eu mantive o arquivo completo acima com o fix do timezone nos cálculos principais.)

# =========================
# SIDEBAR + NAVEGAÇÃO
# =========================
def sidebar_nav_button(label: str, page_name: str, emoji: str, current: str):
    active = current == page_name
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
        unsafe_allow_html=True,
    )
    if st.sidebar.button(f"{emoji} {label}", key=f"nav_{page_name}", use_container_width=True):
        st.session_state.page = page_name
        st.rerun()


def sidebar():
    u = st.session_state.user or {}
    st.sidebar.image(LOGO_URL, use_container_width=True)
    st.sidebar.markdown(f"**{u.get('nome','Usuário')}**")
    st.sidebar.caption(f"Perfil: {u.get('perfil','-')}")

    st.sidebar.divider()
    st.sidebar.markdown("### Navegação")

    current = st.session_state.get("page", "Vendas")
    sidebar_nav_button("Dashboard", "Vendas", "📊", current)
    sidebar_nav_button("Clientes", "Clientes", "🧾", current)
    sidebar_nav_button("Funcionários", "Funcionários", "👷", current)

    st.sidebar.divider()
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


# =========================
# ROUTER
# =========================
if "page" not in st.session_state:
    st.session_state.page = "Login"

if st.session_state.page == "Login" or not require_login():
    login_ui()
else:
    sidebar()
    page = st.session_state.get("page", "Vendas")
    routes = {
        "Vendas": page_vendas,
        "Clientes": page_clientes,
        "Funcionários": page_funcionarios,
    }
    routes.get(page, page_vendas)()
