"""
Equivest Skiptrace — Member Tool
Pay-and-run skiptracing. Upload list → pay via Stripe → download results.
"""

import io, time, math, requests, stripe, pandas as pd, streamlit as st
import auth, database
from config import (BATCHDATA_URL, PRICE_PER_RECORD, MIN_CHARGE)

def _cfg(key, fallback=""):
    try:
        return st.secrets[key]
    except Exception:
        return fallback

BATCHDATA_TOKEN   = _cfg("BATCHDATA_TOKEN",   "0Y9aFi731oljt8enqlZXhe2yHbHonGZbJS4jgShW")
STRIPE_SECRET_KEY = _cfg("STRIPE_SECRET_KEY", "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")
APP_URL           = _cfg("APP_URL",           "http://localhost:8501")

stripe.api_key = STRIPE_SECRET_KEY

MAX_BATCH_RECORDS = 5_000   # hard cap per upload

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Equivest Skiptrace", page_icon="🔍", layout="centered",
                   initial_sidebar_state="collapsed")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"], .stApp {
  font-family: 'Outfit', sans-serif !important;
  background: #060810 !important;
  color: #E8E4D8 !important;
}
.block-container { padding: 0 1.5rem 4rem !important; max-width: 860px; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }

/* Hero */
.eq-hero { text-align:center; padding:3rem 1rem 2rem; border-bottom:1px solid rgba(201,168,76,0.15); margin-bottom:2.5rem; position:relative; }
.eq-logo-line { font-size:0.72rem; font-weight:700; letter-spacing:0.28em; text-transform:uppercase; color:rgba(201,168,76,0.6); margin-bottom:0.6rem; }
.eq-title { font-size:clamp(2.4rem,6vw,3.8rem); font-weight:900; line-height:1.05;
  background:linear-gradient(135deg,#C9A84C 0%,#E2C060 50%,#C9A84C 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; margin-bottom:0.8rem; }
.eq-subtitle { font-size:1rem; color:rgba(232,228,216,0.55); max-width:520px; margin:0 auto; line-height:1.6; }
.eq-stats { display:flex; justify-content:center; gap:1rem; flex-wrap:wrap; margin:1.8rem 0 0; }
.eq-stat { background:rgba(201,168,76,0.07); border:1px solid rgba(201,168,76,0.2); border-radius:50px;
  padding:0.35rem 1.1rem; font-size:0.8rem; font-weight:600; color:rgba(201,168,76,0.85); }
.eq-user-bar { display:flex; justify-content:space-between; align-items:center;
  padding:0.5rem 0; margin-bottom:0.5rem; }
.eq-user-email { font-size:0.78rem; color:rgba(232,228,216,0.35); }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background:#0a0c18 !important; border-radius:12px !important;
  padding:5px !important; gap:4px !important; border:1px solid rgba(201,168,76,0.15) !important; margin-bottom:2rem; }
.stTabs [data-baseweb="tab"] { border-radius:8px !important; font-family:'Outfit',sans-serif !important;
  font-weight:600 !important; font-size:0.9rem !important; color:rgba(232,228,216,0.45) !important;
  padding:0.6rem 1.5rem !important; transition:all 0.2s !important; }
.stTabs [aria-selected="true"] { background:linear-gradient(135deg,#C9A84C,#E2C060) !important; color:#060810 !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none !important; }

/* Inputs */
.stTextInput > div > div { background:#0a0c18 !important; border:1px solid rgba(201,168,76,0.2) !important;
  border-radius:9px !important; color:#E8E4D8 !important; }
.stTextInput > div > div:focus-within { border-color:rgba(201,168,76,0.7) !important;
  box-shadow:0 0 0 3px rgba(201,168,76,0.08) !important; }
.stTextInput input { color:#E8E4D8 !important; font-family:'Outfit',sans-serif !important; }
label, .stTextInput label { color:rgba(232,228,216,0.6) !important; font-size:0.82rem !important;
  font-weight:600 !important; letter-spacing:0.05em !important; text-transform:uppercase !important; }
.stSelectbox > div > div { background:#0a0c18 !important; border:1px solid rgba(201,168,76,0.2) !important;
  border-radius:9px !important; color:#E8E4D8 !important; }

/* Buttons */
.stButton > button { background:linear-gradient(135deg,#C9A84C 0%,#E2C060 100%) !important;
  color:#060810 !important; font-family:'Outfit',sans-serif !important; font-weight:800 !important;
  font-size:1rem !important; letter-spacing:0.04em !important; border:none !important;
  border-radius:10px !important; padding:0.75rem 2rem !important; width:100% !important; }
.stButton > button:hover { opacity:0.9 !important; transform:translateY(-1px) !important; }
.stDownloadButton > button { background:transparent !important; border:1.5px solid #C9A84C !important;
  color:#C9A84C !important; font-family:'Outfit',sans-serif !important; font-weight:700 !important;
  border-radius:10px !important; width:100% !important; padding:0.7rem 2rem !important; }
.stDownloadButton > button:hover { background:rgba(201,168,76,0.1) !important; }

/* Cards */
.eq-card { background:#0a0c18; border:1px solid rgba(201,168,76,0.18); border-radius:14px; padding:1.4rem 1.6rem; margin-bottom:1rem; }
.eq-card-title { font-size:0.68rem; font-weight:700; letter-spacing:0.18em; text-transform:uppercase;
  color:rgba(201,168,76,0.55); margin-bottom:1rem; padding-bottom:0.6rem; border-bottom:1px solid rgba(201,168,76,0.12); }
.eq-phone { font-size:1.25rem; font-weight:700; color:#E8E4D8; letter-spacing:0.02em; }
.eq-badge { display:inline-block; padding:2px 10px; border-radius:20px; font-size:0.72rem; font-weight:700; margin-left:8px; vertical-align:middle; }
.badge-mobile   { background:rgba(201,168,76,0.15); color:#C9A84C; border:1px solid rgba(201,168,76,0.3); }
.badge-landline { background:rgba(100,100,120,0.2); color:rgba(232,228,216,0.5); border:1px solid rgba(232,228,216,0.1); }
.badge-dnc      { background:rgba(220,60,60,0.12); color:#e05555; border:1px solid rgba(220,60,60,0.25); }
.eq-email  { font-size:1rem; color:rgba(232,228,216,0.75); margin-bottom:0.7rem; }
.eq-owner  { font-size:1.4rem; font-weight:800; color:#C9A84C; margin-bottom:0.3rem; }

/* History card */
.eq-history-row { background:#0a0c18; border:1px solid rgba(201,168,76,0.1); border-radius:10px;
  padding:0.9rem 1.2rem; margin-bottom:0.6rem; display:flex; justify-content:space-between; align-items:center; }
.eq-history-label { font-size:0.88rem; color:rgba(232,228,216,0.7); }
.eq-history-meta  { font-size:0.75rem; color:rgba(232,228,216,0.3); margin-top:2px; }
.eq-history-amt   { font-size:1rem; font-weight:700; color:#C9A84C; }

/* Payment box */
.eq-pay-box { background:linear-gradient(135deg,rgba(201,168,76,0.06),rgba(201,168,76,0.02));
  border:1px solid rgba(201,168,76,0.25); border-radius:16px; padding:2rem; text-align:center; margin:1.5rem 0; }
.eq-pay-amount { font-size:3.5rem; font-weight:900; color:#C9A84C; line-height:1; margin-bottom:0.3rem; }
.eq-pay-label { font-size:0.85rem; color:rgba(232,228,216,0.4); margin-bottom:1.5rem; }
.eq-pay-breakdown { font-size:0.82rem; color:rgba(232,228,216,0.35); margin-bottom:1.5rem; }

/* Section label */
.eq-section-label { font-size:0.72rem; font-weight:700; letter-spacing:0.18em; text-transform:uppercase;
  color:rgba(201,168,76,0.6); margin:2rem 0 0.8rem; }

/* Progress */
.stProgress > div > div { background:linear-gradient(90deg,#C9A84C,#E2C060) !important; border-radius:10px !important; }
.stProgress > div { background:rgba(201,168,76,0.1) !important; border-radius:10px !important; }

/* Alerts */
.stSuccess { background:rgba(201,168,76,0.08) !important; border-left:3px solid #C9A84C !important; color:#E8E4D8 !important; }
.stWarning { background:rgba(220,150,50,0.08) !important; border-left:3px solid #dc9632 !important; }
.stError   { background:rgba(220,60,60,0.08) !important; border-left:3px solid #e05555 !important; }
hr { border-color:rgba(201,168,76,0.12) !important; }
.streamlit-expanderHeader { background:#0a0c18 !important; border:1px solid rgba(201,168,76,0.15) !important;
  border-radius:8px !important; color:rgba(232,228,216,0.5) !important; font-size:0.82rem !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def calc_charge(n: int) -> float:
    return max(round(n * PRICE_PER_RECORD, 2), MIN_CHARGE)

def create_checkout(amount_usd: float, description: str) -> tuple[str, str]:
    """Returns (checkout_url, stripe_session_id)."""
    stripe.api_key = st.secrets.get("STRIPE_SECRET_KEY", "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")
    amount_cents = int(amount_usd * 100)
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "Equivest Skiptrace", "description": description},
                "unit_amount": amount_cents,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{APP_URL}/?paid=true&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{APP_URL}/?paid=false",
    )
    return session.url, session.id

def verify_payment(session_id: str) -> bool:
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return session.payment_status == "paid"
    except:
        return False

def run_skiptrace(records: list[dict]) -> dict:
    payload = [{"propertyAddress": {
        "street": r.get("street",""), "city": r.get("city",""),
        "state":  r.get("state",""),  "zip":  r.get("zip",""),
    }} for r in records]
    resp = requests.post(BATCHDATA_URL,
        headers={"Authorization": f"Bearer {BATCHDATA_TOKEN}", "Content-Type": "application/json"},
        json={"requests": payload}, timeout=60)
    resp.raise_for_status()
    return resp.json()

def parse_person(person: dict) -> dict:
    phones  = person.get("phoneNumbers", [])
    emails  = person.get("emails", [])
    name    = person.get("name", {})
    matched = person.get("meta", {}).get("matched", False)
    phones_sorted = sorted(phones,
        key=lambda p: (0 if p.get("type","").lower()=="mobile" else 1,
                       -int(p.get("score",0) or 0)))
    return {
        "Owner First":  name.get("first","").title(),
        "Owner Last":   name.get("last","").title(),
        "Phone 1":      phones_sorted[0].get("number","") if len(phones_sorted)>0 else "",
        "Phone 1 Type": phones_sorted[0].get("type","")   if len(phones_sorted)>0 else "",
        "Phone 1 DNC":  phones_sorted[0].get("dnc",False) if len(phones_sorted)>0 else False,
        "Phone 2":      phones_sorted[1].get("number","") if len(phones_sorted)>1 else "",
        "Phone 2 Type": phones_sorted[1].get("type","")   if len(phones_sorted)>1 else "",
        "Phone 3":      phones_sorted[2].get("number","") if len(phones_sorted)>2 else "",
        "Phone 3 Type": phones_sorted[2].get("type","")   if len(phones_sorted)>2 else "",
        "Email 1":      emails[0].get("email","") if len(emails)>0 else "",
        "Email 2":      emails[1].get("email","") if len(emails)>1 else "",
        "Status":       "Found" if matched else "Not Found",
    }

def phone_badge(phone_type: str, is_dnc: bool) -> str:
    dnc = '<span class="eq-badge badge-dnc">DNC</span>' if is_dnc else ""
    if "mobile" in phone_type.lower():
        return f'<span class="eq-badge badge-mobile">Mobile</span>{dnc}'
    elif phone_type:
        return f'<span class="eq-badge badge-landline">{phone_type}</span>{dnc}'
    return dnc

def df_to_csv(df): return df.to_csv(index=False).encode()

def _records_from_df(df: pd.DataFrame, cols: dict) -> list[dict]:
    """Extract clean address records from df using column mapping."""
    out = []
    for _, row in df.iterrows():
        out.append({
            "street": str(row.get(cols["street"],"") if cols["street"] else ""),
            "city":   str(row.get(cols["city"],  "") if cols["city"]   else ""),
            "state":  str(row.get(cols["state"], "") if cols["state"]  else ""),
            "zip":    str(row.get(cols["zip"],   "") if cols["zip"]    else ""),
        })
    return out


# ── Handle Stripe redirect (no auth required — payment IS the gate) ───────────
params     = st.query_params
paid_param = params.get("paid", "")
session_id = params.get("session_id", "")

if paid_param == "true" and session_id:
    if not verify_payment(session_id):
        st.error("Payment could not be verified. Please contact support.")
        st.stop()

    # Retrieve pending job saved before checkout
    pending = database.get_pending_job(session_id)

    if not pending:
        st.error("Session expired or already processed. If you were charged, contact support.")
        st.stop()

    job_data   = pending["job_data"]
    user_id    = pending.get("user_id")
    user_email = pending.get("user_email", "unknown")
    job_type   = job_data.get("job_type")
    charge     = job_data.get("amount_paid", 0)

    st.query_params.clear()

    # ── Single result ─────────────────────────────────────────────────────────
    if job_type == "single":
        address = job_data["address"]
        with st.spinner("Running skiptrace..."):
            raw = run_skiptrace([address])
        persons = raw.get("results",{}).get("persons",[])
        result  = parse_person(persons[0]) if persons else {}
        found   = 1 if result.get("Status") == "Found" else 0

        database.log_job(user_id, user_email, "single",
                         address.get("street",""), None, 1, found, charge, session_id)
        database.delete_pending_job(session_id)

        st.markdown("""
        <div class="eq-hero">
          <div class="eq-logo-line">Equivest Academy</div>
          <div class="eq-title">Skiptrace</div>
        </div>""", unsafe_allow_html=True)

        if result and result["Status"] == "Found":
            st.markdown(f'<div class="eq-card"><div class="eq-card-title">Property Owner</div>'
                        f'<div class="eq-owner">{result["Owner First"]} {result["Owner Last"]}</div></div>',
                        unsafe_allow_html=True)
            c_a, c_b = st.columns(2)
            with c_a:
                phones_html = ""
                for i in range(1,4):
                    num = result[f"Phone {i}"]; typ = result[f"Phone {i} Type"]
                    dnc = result.get(f"Phone {i} DNC", False)
                    if num:
                        phones_html += (f'<div style="margin-bottom:1rem">'
                                        f'<div class="eq-phone">{num}{phone_badge(typ,dnc)}</div></div>')
                if not phones_html:
                    phones_html = '<div style="color:rgba(232,228,216,0.3)">No phones found</div>'
                st.markdown(f'<div class="eq-card"><div class="eq-card-title">📞 Phones</div>{phones_html}</div>',
                            unsafe_allow_html=True)
            with c_b:
                emails_html = "".join(f'<div class="eq-email">✉️ {result[f"Email {i}"]}</div>'
                                      for i in range(1,3) if result[f"Email {i}"])
                if not emails_html:
                    emails_html = '<div style="color:rgba(232,228,216,0.3)">No email found</div>'
                st.markdown(f'<div class="eq-card"><div class="eq-card-title">✉️ Email</div>{emails_html}</div>',
                            unsafe_allow_html=True)
        else:
            st.warning("No match found for this address.")

        st.markdown(
            "<p style='text-align:center;font-size:0.82rem;color:rgba(232,228,216,0.3);"
            "margin-top:2rem'>Log back in to run another search.</p>",
            unsafe_allow_html=True
        )
        st.stop()

    # ── Batch result ──────────────────────────────────────────────────────────
    elif job_type == "batch":
        records  = job_data["records"]
        orig_df  = pd.DataFrame(job_data["orig_rows"])
        filename = job_data.get("filename", "list.csv")
        count    = len(records)

        out_df = orig_df.copy()
        for col in ["Owner First","Owner Last","Phone 1","Phone 1 Type",
                    "Phone 2","Phone 2 Type","Phone 3","Phone 3 Type",
                    "Email 1","Email 2","Status"]:
            out_df[col] = ""

        st.markdown("""
        <div class="eq-hero">
          <div class="eq-logo-line">Equivest Academy</div>
          <div class="eq-title">Skiptrace</div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f'<div class="eq-section-label">Running {count:,} records...</div>',
                    unsafe_allow_html=True)
        progress = st.progress(0)
        status   = st.empty()
        found = not_found = 0

        for start in range(0, count, 50):
            batch = records[start:start+50]
            try:
                raw     = run_skiptrace(batch)
                persons = raw.get("results",{}).get("persons",[])
            except Exception as e:
                st.error(f"API error at row {start+1}: {e}")
                break
            for i, person in enumerate(persons):
                result = parse_person(person)
                for col, val in result.items():
                    out_df.at[start+i, col] = val
                if result["Status"] == "Found": found += 1
                else: not_found += 1
            pct = min((start+50)/count, 1.0)
            progress.progress(pct)
            status.markdown(
                f"<p style='color:rgba(201,168,76,0.7);font-size:0.88rem'>"
                f"<strong>{min(start+50,count):,}/{count:,}</strong> — ✅ {found:,} found</p>",
                unsafe_allow_html=True)
            time.sleep(0.2)

        hit = f"{found/count*100:.0f}%" if count else "0%"
        status.markdown(
            f"<p style='color:#C9A84C;font-weight:700;font-size:1rem'>"
            f"✅ Complete — {found:,} matches ({hit} hit rate)</p>",
            unsafe_allow_html=True)

        database.log_job(user_id, user_email, "batch",
                         None, filename, count, found, charge, session_id)
        database.delete_pending_job(session_id)

        s1,s2,s3 = st.columns(3)
        s1.metric("Hit Rate", hit)
        s2.metric("Found", f"{found:,}")
        s3.metric("No Match", f"{not_found:,}")
        st.dataframe(out_df.head(20), use_container_width=True)
        st.download_button("⬇️  Download Full Results", data=df_to_csv(out_df),
                           file_name="equivest_skiptrace_results.csv",
                           mime="text/csv", use_container_width=True)
        st.markdown(
            "<p style='text-align:center;font-size:0.82rem;color:rgba(232,228,216,0.3);"
            "margin-top:2rem'>Log back in to run another batch.</p>",
            unsafe_allow_html=True
        )
        st.stop()

elif paid_param == "false":
    st.query_params.clear()
    st.warning("Payment cancelled. Your list is still saved — refresh and try again.")


# ── Auth gate ─────────────────────────────────────────────────────────────────
if not auth.show_auth_wall():
    st.stop()

user       = auth.get_current_user()
user_id    = user["id"]
user_email = user["email"]


# ── Hero ──────────────────────────────────────────────────────────────────────
col_h, col_out = st.columns([5, 1])
with col_h:
    st.markdown("""
    <div class="eq-hero">
      <div class="eq-logo-line">Equivest Academy</div>
      <div class="eq-title">Skiptrace</div>
      <div class="eq-subtitle">Instant owner lookup — phones, emails, and carrier data.<br>
        Single address or bulk list, results in seconds.</div>
      <div class="eq-stats">
        <span class="eq-stat">⚡ Instant Results</span>
        <span class="eq-stat">📞 Mobile + Landline</span>
        <span class="eq-stat">✉️ Email Included</span>
        <span class="eq-stat">🇺🇸 National Coverage</span>
      </div>
    </div>""", unsafe_allow_html=True)
with col_out:
    st.markdown("<div style='height:3rem'></div>", unsafe_allow_html=True)
    if st.button("Sign Out", key="logout_btn"):
        auth.logout()
        st.rerun()

st.markdown(
    f"<p style='text-align:right;font-size:0.75rem;color:rgba(232,228,216,0.25);"
    f"margin-top:-1rem'>{user_email}</p>",
    unsafe_allow_html=True
)


# ════════════════════════════════════════════════════════════════════════
# MAIN UI — Tabs
# ════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["  🏠   Single Lookup  ", "  📋   Batch Upload  ", "  📂   My History  "])


# ── TAB 1: Single ─────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="eq-section-label">Property Address</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([2,1])
    with c1: street  = st.text_input("Street",   placeholder="1234 W Camelback Rd")
    with c2: city    = st.text_input("City",      placeholder="Phoenix")
    c3, c4 = st.columns(2)
    with c3: state   = st.text_input("State",     placeholder="AZ", max_chars=2)
    with c4: zipcode = st.text_input("Zip Code",  placeholder="85001")

    charge = max(PRICE_PER_RECORD, MIN_CHARGE)
    st.markdown(f"""
    <div class="eq-pay-box">
      <div class="eq-pay-amount">${charge:.2f}</div>
      <div class="eq-pay-label">one-time secure payment</div>
      <div class="eq-pay-breakdown">Includes: owner name · phones · emails · carrier data</div>
    </div>""", unsafe_allow_html=True)

    if st.button("💳  Pay & Run Skiptrace", key="single_pay"):
        if not street or not city or not state:
            st.warning("Street, city, and state are required.")
        else:
            address_data = {"street": street, "city": city, "state": state, "zip": zipcode}
            checkout_url, stripe_sess = create_checkout(
                charge, f"Skiptrace: {street}, {city}, {state}"
            )
            database.save_pending_job(stripe_sess, user_id, user_email, {
                "job_type": "single",
                "address": address_data,
                "amount_paid": charge,
            })
            st.markdown(f'<meta http-equiv="refresh" content="0; url={checkout_url}">',
                        unsafe_allow_html=True)
            st.markdown(f"[Click here if not redirected]({checkout_url})")


# ── TAB 2: Batch ──────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="eq-section-label">Upload Your List</div>', unsafe_allow_html=True)
    st.markdown(
        f"<p style='color:rgba(232,228,216,0.5);font-size:0.9rem;margin-bottom:1.5rem'>"
        f"Upload a CSV or Excel file from any source — PropStream, BatchLeads, your own list. "
        f"Auto-detects columns. Max {MAX_BATCH_RECORDS:,} records.</p>",
        unsafe_allow_html=True
    )

    uploaded = st.file_uploader("Drop file here", type=["csv","xls","xlsx"],
                                label_visibility="collapsed")

    if uploaded:
        try:
            df = (pd.read_csv(uploaded, dtype=str).fillna("") if uploaded.name.endswith(".csv")
                  else pd.read_excel(uploaded, dtype=str).fillna(""))
        except Exception as e:
            st.error(f"Could not read file: {e}"); st.stop()

        if len(df) > MAX_BATCH_RECORDS:
            st.error(f"File has {len(df):,} records. Max allowed is {MAX_BATCH_RECORDS:,}. "
                     "Split your list and upload in batches.")
            st.stop()

        st.success(f"✅  {len(df):,} records loaded")
        st.dataframe(df.head(5), use_container_width=True)

        def find_col(df, kws):
            for col in df.columns:
                if any(k in col.lower() for k in kws): return col
            return None

        det = {
            "street": find_col(df, ["street","address","addr","situs"]),
            "city":   find_col(df, ["city"]),
            "state":  find_col(df, ["state"]),
            "zip":    find_col(df, ["zip","postal"]),
        }

        st.markdown('<div class="eq-section-label" style="margin-top:1.5rem">Column Mapping</div>',
                    unsafe_allow_html=True)
        cols_list = list(df.columns)
        def idx(d, c):
            try: return c.index(d)+1
            except: return 0

        mc1,mc2,mc3,mc4 = st.columns(4)
        with mc1: col_street = st.selectbox("Street", ["(none)"]+cols_list, index=idx(det["street"],cols_list))
        with mc2: col_city   = st.selectbox("City",   ["(none)"]+cols_list, index=idx(det["city"],  cols_list))
        with mc3: col_state  = st.selectbox("State",  ["(none)"]+cols_list, index=idx(det["state"], cols_list))
        with mc4: col_zip    = st.selectbox("Zip",    ["(none)"]+cols_list, index=idx(det["zip"],   cols_list))

        mapped = {
            "street": None if col_street=="(none)" else col_street,
            "city":   None if col_city  =="(none)" else col_city,
            "state":  None if col_state =="(none)" else col_state,
            "zip":    None if col_zip   =="(none)" else col_zip,
        }

        count  = len(df)
        charge = calc_charge(count)

        st.markdown(f"""
        <div class="eq-pay-box">
          <div class="eq-pay-amount">${charge:.2f}</div>
          <div class="eq-pay-label">for {count:,} records · secure one-time payment</div>
          <div class="eq-pay-breakdown">
            ${PRICE_PER_RECORD:.2f}/record · phones + emails + carrier data · ~85% hit rate
          </div>
        </div>""", unsafe_allow_html=True)

        if st.button("💳  Pay & Run Batch Skiptrace", key="batch_pay"):
            if not mapped["street"]:
                st.error("Street address column is required.")
                st.stop()

            records   = _records_from_df(df, mapped)
            orig_rows = df.to_dict("records")   # preserve all original columns
            checkout_url, stripe_sess = create_checkout(
                charge, f"Equivest Skiptrace — {count:,} records"
            )
            database.save_pending_job(stripe_sess, user_id, user_email, {
                "job_type":   "batch",
                "filename":   uploaded.name,
                "records":    records,
                "orig_rows":  orig_rows,
                "amount_paid": charge,
            })
            st.markdown(f'<meta http-equiv="refresh" content="0; url={checkout_url}">',
                        unsafe_allow_html=True)
            st.markdown(f"[Click here if not redirected]({checkout_url})")


# ── TAB 3: History ────────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="eq-section-label">Your Search History</div>', unsafe_allow_html=True)

    jobs = database.get_my_jobs(user_id, limit=30)

    if not jobs:
        st.markdown(
            "<p style='color:rgba(232,228,216,0.3);font-size:0.9rem'>No searches yet.</p>",
            unsafe_allow_html=True
        )
    else:
        total_spent = sum(j.get("amount_paid", 0) for j in jobs)
        total_found = sum(j.get("found_count", 0) for j in jobs)
        total_recs  = sum(j.get("record_count", 0) for j in jobs)

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Spent", f"${total_spent:.2f}")
        m2.metric("Records Run",  f"{total_recs:,}")
        m3.metric("Contacts Found", f"{total_found:,}")

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        for j in jobs:
            jtype = j.get("job_type","")
            icon  = "🏠" if jtype == "single" else "📋"
            label = j.get("address") or j.get("filename") or "—"
            amt   = j.get("amount_paid", 0)
            found = j.get("found_count", 0)
            total = j.get("record_count", 1)
            ts    = (j.get("created_at","")[:10])

            st.markdown(f"""
            <div class="eq-history-row">
              <div>
                <div class="eq-history-label">{icon} {label}</div>
                <div class="eq-history-meta">{ts} · {found}/{total} found</div>
              </div>
              <div class="eq-history-amt">${amt:.2f}</div>
            </div>""", unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:3rem 0 1rem;border-top:1px solid rgba(201,168,76,0.1);margin-top:3rem;">
  <div style="font-size:0.72rem;color:rgba(232,228,216,0.2);letter-spacing:0.1em;text-transform:uppercase;">
    © 2026 Equivest Academy LLC — Member Tool
  </div>
  <div style="font-size:0.68rem;color:rgba(232,228,216,0.15);margin-top:0.4rem;">
    Data used for informational purposes only. FCRA-compliant use required.
  </div>
</div>
""", unsafe_allow_html=True)
