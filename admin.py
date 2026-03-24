"""
Equivest Skiptrace — Admin Portal
Run separately: streamlit run admin.py --server.port 8502
Never expose this publicly.
"""

import pandas as pd
import streamlit as st
import database
from config import ADMIN_PASSWORD

st.set_page_config(page_title="Skiptrace Admin", page_icon="🔐", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&display=swap');
html, body, [class*="css"], .stApp {
  font-family: 'Outfit', sans-serif !important;
  background: #060810 !important;
  color: #E8E4D8 !important;
}
.block-container { padding: 2rem 2rem 4rem !important; max-width: 1200px; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"] { background: #0a0c18 !important; border-right: 1px solid rgba(201,168,76,0.15) !important; }
.admin-title { font-size: 1.8rem; font-weight: 800;
  background: linear-gradient(135deg,#C9A84C,#E2C060);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.admin-label { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.18em;
  text-transform: uppercase; color: rgba(201,168,76,0.55); margin-bottom: 0.5rem; }
.stMetric { background: #0a0c18; border: 1px solid rgba(201,168,76,0.15);
  border-radius: 12px; padding: 1rem 1.2rem; }
.stMetric label { color: rgba(232,228,216,0.45) !important; font-size: 0.78rem !important; }
.stMetric [data-testid="metric-container"] > div:nth-child(2) { color: #C9A84C !important; font-size: 1.8rem !important; font-weight: 800 !important; }
.stButton > button { background: linear-gradient(135deg,#C9A84C,#E2C060) !important;
  color: #060810 !important; font-weight: 700 !important; border: none !important;
  border-radius: 8px !important; }
.stDataFrame { border: 1px solid rgba(201,168,76,0.15) !important; border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)


# ── Password gate ─────────────────────────────────────────────────────────────
if not st.session_state.get("admin_authed"):
    st.markdown('<div class="admin-title">Equivest Admin</div>', unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(232,228,216,0.4);margin-bottom:2rem'>Skiptrace Operations Portal</p>",
                unsafe_allow_html=True)
    pw = st.text_input("Admin Password", type="password", placeholder="••••••••")
    if st.button("Enter"):
        if pw == ADMIN_PASSWORD:
            st.session_state["admin_authed"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()


# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading data..."):
    jobs = database.get_all_jobs(limit=2000)

df_jobs = pd.DataFrame(jobs) if jobs else pd.DataFrame()


# ── Header ────────────────────────────────────────────────────────────────────
c_title, c_logout = st.columns([5, 1])
with c_title:
    st.markdown('<div class="admin-title">⚡ Skiptrace Admin</div>', unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(232,228,216,0.35);font-size:0.85rem;margin-bottom:2rem'>"
                "Equivest Academy LLC — Operations Portal</p>", unsafe_allow_html=True)
with c_logout:
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    if st.button("Log Out"):
        del st.session_state["admin_authed"]
        st.rerun()


# ── KPI metrics ───────────────────────────────────────────────────────────────
if not df_jobs.empty:
    total_rev    = df_jobs["amount_paid"].sum()
    total_jobs   = len(df_jobs)
    total_recs   = df_jobs["record_count"].sum()
    total_found  = df_jobs["found_count"].sum()
    hit_rate     = f"{total_found/total_recs*100:.1f}%" if total_recs else "—"
    unique_users = df_jobs["user_email"].nunique()

    m1,m2,m3,m4,m5,m6 = st.columns(6)
    m1.metric("Total Revenue",  f"${total_rev:,.2f}")
    m2.metric("Total Jobs",     f"{total_jobs:,}")
    m3.metric("Records Run",    f"{int(total_recs):,}")
    m4.metric("Contacts Found", f"{int(total_found):,}")
    m5.metric("Avg Hit Rate",   hit_rate)
    m6.metric("Unique Users",   f"{unique_users:,}")
else:
    st.info("No jobs yet.")

st.divider()


# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="admin-label">Filters</div>', unsafe_allow_html=True)

    job_type_filter = st.selectbox("Job Type", ["All", "single", "batch"])
    email_filter    = st.text_input("User Email (contains)", placeholder="@gmail.com")

    st.markdown('<div class="admin-label" style="margin-top:1.5rem">Export</div>',
                unsafe_allow_html=True)
    if not df_jobs.empty:
        st.download_button(
            "⬇️ Download All Jobs (CSV)",
            data=df_jobs.to_csv(index=False).encode(),
            file_name="skiptrace_jobs.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ── Jobs table ────────────────────────────────────────────────────────────────
if not df_jobs.empty:
    display = df_jobs.copy()

    if job_type_filter != "All":
        display = display[display["job_type"] == job_type_filter]
    if email_filter:
        display = display[display["user_email"].str.contains(email_filter, case=False, na=False)]

    display["created_at"] = pd.to_datetime(display["created_at"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M")
    display["amount_paid"] = display["amount_paid"].apply(lambda x: f"${x:.2f}")
    display["hit_rate"] = display.apply(
        lambda r: f"{r['found_count']/r['record_count']*100:.0f}%" if r['record_count'] else "—", axis=1
    )

    show_cols = ["created_at","user_email","job_type","address","filename",
                 "record_count","found_count","hit_rate","amount_paid"]
    show_cols = [c for c in show_cols if c in display.columns]

    st.markdown(f"<p style='color:rgba(232,228,216,0.4);font-size:0.83rem'>"
                f"Showing {len(display):,} jobs</p>", unsafe_allow_html=True)
    st.dataframe(display[show_cols], use_container_width=True, height=500)

    # Revenue by day chart
    st.divider()
    st.markdown('<div class="admin-label">Revenue Over Time</div>', unsafe_allow_html=True)
    rev_df = df_jobs.copy()
    rev_df["date"] = pd.to_datetime(rev_df["created_at"], errors="coerce").dt.date
    rev_df["amount_paid"] = pd.to_numeric(rev_df["amount_paid"].astype(str).str.replace("$",""), errors="coerce")
    daily = rev_df.groupby("date")["amount_paid"].sum().reset_index()
    daily.columns = ["Date","Revenue ($)"]
    st.bar_chart(daily.set_index("Date"), color="#C9A84C")
