"""Local interactive portfolio demo. Run with: streamlit run streamlit_app.py."""

import os
import sys
from pathlib import Path
import warnings
import re

import streamlit as st

# Ensure repository root is on sys.path for Streamlit Cloud deployment
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Bridge Streamlit Cloud secrets to environment variables if configured
try:
    if hasattr(st, "secrets"):
        for secret_key in ("SARVAM_API_KEY", "AGENTIC_BI_SARVAM_API_KEY", "AGENTIC_BI_ENGINE", "AGENTIC_BI_LLM_API_KEY"):
            if secret_key in st.secrets and secret_key not in os.environ:
                os.environ[secret_key] = str(st.secrets[secret_key])
except Exception:
    pass

from src.web_service import GUIDED_QUESTIONS, execute_question


@st.cache_resource(show_spinner="⚡ Initializing in-memory DuckDB warehouse (550,000+ records)...")
def _warmup_warehouse() -> bool:
    """Preload in-memory DuckDB tables on worker start to eliminate first-query cold lag."""
    try:
        from src.engine.session import WarehouseSession
        WarehouseSession().get_connector()
    except Exception:
        pass
    return True


_warmup_warehouse()


def split_analysis(text: str) -> tuple[str, list[str], list[str], str]:
    """Separate a narrative into its takeaway, evidence, caveats and full text."""
    sections = {"takeaway": [], "key points": [], "caveats": []}
    current = None
    for raw in (text or "").splitlines():
        line = raw.strip()
        heading = re.sub(r"[*:#]", "", line).strip().casefold().rstrip(":")
        if heading in sections:
            current = heading
        elif current and line:
            sections[current].append(re.sub(r"^[-*•]\s*", "", line))
    if any(sections.values()):
        take = " ".join(sections["takeaway"])
        points = sections["key points"]
        caveats = sections["caveats"]
        return take, points, caveats, text
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", (text or "").strip())
    return (sentences[0] if sentences else "", sentences[1:4], [], " ".join(sentences[4:]))

st.set_page_config(page_title="Fieldnote | Analytics assistant", page_icon="◒", layout="wide")

st.markdown("""
<style>
    .stApp {background: #f7f7f2; color: #1e2b27;}
    [data-testid="stSidebar"] {background: #edf1ea;}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {color: #263c30;}
    [data-testid="stHeader"] {background: #f7f7f2;}
    [data-testid="stBottom"] {background: #f7f7f2;}
    .block-container {max-width: 1160px; padding-top: 1.5rem; padding-bottom: 6rem;}
    .eyebrow {color: #467463; font-size: .72rem; letter-spacing: .15em; font-weight: 700; text-transform: uppercase;}
    .hero-title {font-size: clamp(2.3rem, 4vw, 3.6rem); line-height: 1.08; font-weight: 650; letter-spacing: -.045em; color: #1d3028; margin: .35rem 0 .8rem;}
    .hero-copy {font-size: 1.05rem; line-height: 1.6; max-width: 620px; color: #596b61;}
    .section-label {font-weight: 700; color: #273d31; font-size: 1.05rem; margin-top: .5rem;}
    .small-note {color: #6a7b70; font-size: .83rem; line-height: 1.5;}
    div.stButton > button {border-radius: 10px; border: 1px solid #ccd9ce; background: #fff; text-align: left; color: #213c2d; min-height: 3.2rem;}
    div.stButton > button:hover {border-color: #428069; color: #285c46;}
    [data-testid="stChatMessage"] {border: 1px solid #e1e8df; border-radius: 14px; background: #fff;}
    [data-testid="stChatInput"] {border-radius: 14px;}
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# First-load welcome modal & readiness banner
if hasattr(st, "dialog"):
    @st.dialog("🚀 Analytical Workspace Ready", width="large")
    def show_first_load_modal():
        st.markdown("""
        ### Welcome to Fieldnote
        Fieldnote connects an AI analytics assistant to an **in-memory DuckDB analytical warehouse** pre-loaded with **550,000+ real-world Brazilian e-commerce orders** (Olist, 2016–2018).

        **System Highlights & Guardrails:**
        - 🛡️ **Zero-Trust Security**: Multi-stage AST query sanitization blocks unauthorized statements, file/system functions, and Cartesian joins.
        - ⚡ **In-Memory Speed**: Sub-second execution over 550,000 records without external database dependencies.
        - 🧠 **Governed Metrics**: Deterministic semantic layer formulas for GMV, AOV, delivery delay rates, and customer cohorts.

        You can explore using the **4 guided questions** or by typing any analytical query in the box below.
        """)
        st.success("✅ **DuckDB analytical engine warmed up and ready.**")
        if st.button("Start Exploring ➔", type="primary", use_container_width=True):
            st.session_state.first_load_seen = True
            st.rerun()

    if "first_load_seen" not in st.session_state:
        st.session_state.first_load_seen = True
        show_first_load_modal()
        if hasattr(st, "toast"):
            st.toast("⚡ Warehouse ready! 550,000+ records loaded in DuckDB.", icon="✅")

with st.sidebar:
    st.markdown("<div class='eyebrow'>◒ &nbsp; Fieldnote / Analytics</div>", unsafe_allow_html=True)
    st.markdown("### Your workspace")
    st.caption("A local demo built for clearer business decisions.")
    st.caption("🟢 **Status**: In-Memory DuckDB (550k records ready)")
    if hasattr(st, "dialog"):
        if st.button("ℹ️ Workspace Overview", use_container_width=True):
            show_first_load_modal()
    st.divider()
    protection = st.toggle("Protect customer IDs", value=False,
                           help="When on, queries referencing the repeat-customer identifier are blocked.")
    st.caption("Off by default. Other query checks still apply.")
    st.caption("Questions and relevant data may be sent to your configured model provider. Review answers before use.")
    st.divider()
    st.markdown("**About the data**")
    st.caption("Olist · Brazilian e-commerce\n\nHistorical orders from 2016–2018. Product names are not included.")
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("<div class='small-note'>A portfolio demonstration · Local DuckDB</div>", unsafe_allow_html=True)

st.markdown("<div class='eyebrow'>Your data, in conversation</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-title'>Better questions.<br>Clearer answers.</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-copy'>Explore an online store in plain language. See the story behind the numbers, the data they came from, and the query that brought it together.</div>", unsafe_allow_html=True)
st.write("")

st.markdown("<div class='section-label'>Start with a question</div>", unsafe_allow_html=True)
st.caption("Choose an example, or ask your own question below.")
cards = [
    ("↗  Sales by state", GUIDED_QUESTIONS[0]),
    ("◷  Late deliveries", GUIDED_QUESTIONS[1]),
    ("◒  New vs. repeat buyers", GUIDED_QUESTIONS[5]),
    ("◎  Average order value", GUIDED_QUESTIONS[3]),
]
selected = None
columns = st.columns(4)
for index, (label, question) in enumerate(cards):
    if columns[index].button(label, use_container_width=True, key=f"example_{index}"):
        selected = question

def render_assistant_result(result: dict) -> None:
    """Render the structured assistant analysis result."""
    if result.get("error"):
        st.error(result["error"])
    elif result.get("clarification"):
        st.info(result["clarification"])
    else:
        st.caption(result.get("label", "Defined metric"))
        st.markdown("**What I found**")
        if result.get("summary"):
            takeaway, points, narrative_caveats, full_text = split_analysis(result["summary"])
            if takeaway:
                st.info(takeaway)
            for point in points:
                st.markdown(f"- {point}")
            for caveat in narrative_caveats:
                st.caption("Caveat: " + caveat)
            if full_text:
                with st.expander("Read the full explanation"):
                    st.write(full_text)
        if result.get("data") is not None:
            frame = result["data"].to_pandas()
            st.markdown("**The numbers**")
            product_columns = {"product_id", "category", "revenue", "orders", "new_orders", "repeat_orders", "new_revenue", "repeat_revenue", "new_order_pct", "repeat_order_pct"}
            if product_columns.issubset(frame.columns):
                overview, orders, sales = st.tabs(["Overview", "Orders & customers", "Units & revenue"])
                def show_columns(names):
                    selected_frame = frame[[col for col in names if col in frame.columns]].copy()
                    selected_frame.columns = [col.replace("_", " ").title() for col in selected_frame.columns]
                    st.dataframe(selected_frame, use_container_width=True, hide_index=True)
                with overview:
                    show_columns(["product_id", "category", "revenue", "orders", "new_order_pct", "repeat_order_pct"])
                with orders:
                    st.caption("Percentages are based on orders containing each product.")
                    show_columns(["product_id", "category", "orders", "new_orders", "repeat_orders", "new_order_pct", "repeat_order_pct"])
                with sales:
                    st.caption("Revenue is in Brazilian reais (R$); freight is excluded.")
                    show_columns(["product_id", "category", "units", "new_units", "repeat_units", "revenue", "new_revenue", "repeat_revenue"])
            else:
                frame.columns = [col.replace("_", " ").title() for col in frame.columns]
                st.dataframe(frame, use_container_width=True, hide_index=True)
            st.caption(f"{len(frame):,} result {'row' if len(frame) == 1 else 'rows'} · Use the table controls to explore the data.")
        with st.expander("How this was calculated"):
            if result.get("method"):
                st.write(result["method"])
            if result.get("sources"):
                st.caption("Source tables: " + ", ".join(result["sources"]))
            for caveat in result.get("caveats", []):
                st.caption("Note: " + caveat)
            if result.get("sql"):
                st.markdown("**SQL used**")
                st.code(result["sql"], language="sql")


st.divider()
st.markdown("<div class='section-label'>Your analysis</div>", unsafe_allow_html=True)

chat_container = st.container()
with chat_container:
    if not st.session_state.messages:
        st.caption("Your results will appear here, with the SQL available to inspect.")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["content"])
            else:
                render_assistant_result(message["result"])

st.caption("💡 *Type or paste your question below and press **Enter** (or click **Send ➔**) to run.*")
typed = st.chat_input("Ask about sales, orders, deliveries, or customers (press Enter to run)…")
active_question = (selected or typed or "").strip()
if active_question:
    # 1. Store user message in history
    st.session_state.messages.append({"role": "user", "content": active_question})
    with chat_container:
        with st.chat_message("user"):
            st.write(active_question)

        # 2. Execute and display assistant response with prominent status
        with st.chat_message("assistant"):
            with st.status("🔍 Looking into the data…", expanded=True) as status:
                st.write("📊 Resolving analytical query and validating security constraints...")
                try:
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", message="Arrow output on a DB-API result makes an extra copy.*", category=UserWarning)
                        answer = execute_question(active_question, "auto", protection)
                except Exception as exc:
                    answer = {"error": f"The question could not be completed: {exc}"}
                status.update(label="✅ Analysis complete!", state="complete", expanded=False)
            try:
                render_assistant_result(answer)
            except Exception as exc:
                st.error(f"Display error: {exc}")
    st.session_state.messages.append({"role": "assistant", "result": answer})
