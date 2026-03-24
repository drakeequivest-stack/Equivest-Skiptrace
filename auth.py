"""
Equivest Skiptrace — Auth wall (login / sign-up)
"""
import streamlit as st
import database

# ── FCRA / Terms text ─────────────────────────────────────────────────────────

_TERMS = """
**EQUIVEST SKIPTRACE — TERMS OF USE & FCRA CERTIFICATION**

*Last updated: March 2026 · Equivest Academy LLC*

**1. Permitted Uses Only**
Skip trace data accessed through this tool may only be used for lawful purposes, including but not limited to: locating property owners for real estate investment purposes, business research, and asset location.

**2. FCRA Prohibited Uses**
This service is **NOT** a consumer reporting agency as defined under the Fair Credit Reporting Act (FCRA), 15 U.S.C. § 1681 et seq. Data obtained through this service **CANNOT** be used, in whole or in part, as a factor in:
- Establishing a consumer's eligibility for credit or insurance
- Employment screening or background checks
- Tenant screening or housing decisions
- Any other purpose covered by the FCRA

**3. Your Certification**
By creating an account and using this service, you certify that:
- You are 18 years of age or older
- You will not use data for any FCRA-regulated purpose
- You will comply with all applicable federal, state, and local laws
- You will not resell or redistribute the data obtained
- You have a legitimate business reason for each search

**4. No Guarantee of Accuracy**
Data is sourced from public records and third-party providers. Equivest Academy LLC makes no warranty as to the accuracy, completeness, or timeliness of results.

**5. No Refunds on Completed Searches**
Once a skiptrace has been run and results delivered, the charge is final. Contact equivestacademy@gmail.com for billing disputes.

**6. Account Termination**
Equivest Academy LLC reserves the right to terminate accounts for misuse, suspected FCRA violations, or any other reason at our sole discretion.
"""

# ── CSS (injected once, shared with main app) ─────────────────────────────────

_AUTH_CSS = """
<style>
.auth-wrap {
  max-width: 480px; margin: 3rem auto 0; padding: 0 1rem;
}
.auth-logo {
  text-align: center; margin-bottom: 2.5rem;
}
.auth-logo-label {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.28em;
  text-transform: uppercase; color: rgba(201,168,76,0.6); margin-bottom: 0.5rem;
}
.auth-logo-title {
  font-size: 2.4rem; font-weight: 900; line-height: 1;
  background: linear-gradient(135deg, #C9A84C 0%, #E2C060 50%, #C9A84C 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.auth-card {
  background: #0a0c18; border: 1px solid rgba(201,168,76,0.2);
  border-radius: 16px; padding: 2rem 2rem 1.5rem;
}
.auth-tab-header {
  display: flex; gap: 0; margin-bottom: 1.8rem;
  background: rgba(201,168,76,0.06); border-radius: 10px;
  border: 1px solid rgba(201,168,76,0.15); overflow: hidden;
}
.auth-tab {
  flex: 1; text-align: center; padding: 0.7rem 1rem;
  font-size: 0.88rem; font-weight: 700; letter-spacing: 0.04em;
  cursor: pointer; color: rgba(232,228,216,0.4);
  border: none; background: transparent;
}
.auth-tab.active {
  background: linear-gradient(135deg,#C9A84C,#E2C060);
  color: #060810; border-radius: 8px;
}
.auth-divider {
  height: 1px; background: rgba(201,168,76,0.12); margin: 1.2rem 0;
}
.auth-terms-box {
  background: rgba(255,255,255,0.02); border: 1px solid rgba(201,168,76,0.12);
  border-radius: 8px; padding: 0.9rem 1rem; max-height: 200px;
  overflow-y: auto; font-size: 0.78rem; color: rgba(232,228,216,0.45);
  line-height: 1.6; margin-bottom: 0.8rem;
}
.auth-fcra-badge {
  display: inline-block; background: rgba(201,168,76,0.08);
  border: 1px solid rgba(201,168,76,0.2); border-radius: 6px;
  padding: 0.4rem 0.9rem; font-size: 0.72rem; font-weight: 700;
  letter-spacing: 0.1em; text-transform: uppercase; color: rgba(201,168,76,0.7);
  margin-bottom: 1rem;
}
</style>
"""


# ── Public API ────────────────────────────────────────────────────────────────

def get_current_user() -> dict | None:
    return st.session_state.get("user")


def logout() -> None:
    for k in ["user"]:
        st.session_state.pop(k, None)


def show_auth_wall() -> bool:
    """
    Renders the login/signup wall.
    Returns True if the user is already authenticated (caller can proceed).
    Returns False after rendering the auth UI (caller should st.stop()).
    """
    user = st.session_state.get("user")
    if user:
        return True

    st.markdown(_AUTH_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="auth-wrap">
      <div class="auth-logo">
        <div class="auth-logo-label">Equivest Academy</div>
        <div class="auth-logo-title">Skiptrace</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Center the form
    _, col, _ = st.columns([1, 2.2, 1])
    with col:
        mode = st.radio("", ["Log In", "Create Account"], horizontal=True,
                        label_visibility="collapsed")
        st.markdown('<div class="auth-divider"></div>', unsafe_allow_html=True)

        if mode == "Log In":
            _show_login()
        else:
            _show_signup()

    return False


# ── Internal ──────────────────────────────────────────────────────────────────

def _show_login():
    email    = st.text_input("Email", placeholder="you@example.com",
                             key="login_email")
    password = st.text_input("Password", type="password",
                             placeholder="••••••••", key="login_pw")

    if st.button("Log In →", key="btn_login", use_container_width=True):
        if not email or not password:
            st.warning("Please enter your email and password.")
            return
        with st.spinner("Logging in..."):
            user, err = database.sign_in(email.strip().lower(), password)
        if user:
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error(err)

    st.markdown(
        "<p style='text-align:center;font-size:0.8rem;color:rgba(232,228,216,0.3);"
        "margin-top:1.2rem'>Don't have an account? Select <strong>Create Account</strong> above.</p>",
        unsafe_allow_html=True
    )


def _show_signup():
    st.markdown(
        '<div class="auth-fcra-badge">⚖️ FCRA Certified Use Only</div>',
        unsafe_allow_html=True
    )

    email    = st.text_input("Email", placeholder="you@example.com",
                             key="su_email")
    password = st.text_input("Password (min 6 chars)", type="password",
                             placeholder="••••••••", key="su_pw")
    pw2      = st.text_input("Confirm Password", type="password",
                             placeholder="••••••••", key="su_pw2")

    st.markdown("**Terms of Use & FCRA Certification**", unsafe_allow_html=False)
    st.markdown(
        f'<div class="auth-terms-box">{_TERMS.replace(chr(10), "<br>")}</div>',
        unsafe_allow_html=True
    )

    agreed = st.checkbox(
        "I have read and agree to the Terms of Use. I certify I will NOT use "
        "skip trace data for employment, credit, housing, or any FCRA-regulated purpose.",
        key="su_agree"
    )

    if st.button("Create Account →", key="btn_signup", use_container_width=True):
        if not email or not password:
            st.warning("Please fill in all fields.")
            return
        if password != pw2:
            st.error("Passwords do not match.")
            return
        if len(password) < 6:
            st.error("Password must be at least 6 characters.")
            return
        if not agreed:
            st.error("You must agree to the Terms of Use and FCRA certification to continue.")
            return

        with st.spinner("Creating your account..."):
            user, err = database.sign_up(email.strip().lower(), password)

        if user:
            st.session_state["user"] = user
            st.success("Account created! Welcome to Equivest Skiptrace.")
            st.rerun()
        else:
            st.error(err)
