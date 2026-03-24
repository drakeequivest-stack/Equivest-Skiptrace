"""
Equivest Skiptrace — Supabase database operations
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY


def _anon() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def _admin() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# ── Auth ──────────────────────────────────────────────────────────────────────

def sign_in(email: str, password: str) -> tuple[dict | None, str]:
    """Returns (user_dict, error_msg). user_dict is None on failure."""
    try:
        resp = _anon().auth.sign_in_with_password({"email": email, "password": password})
        if resp.user:
            return {"id": str(resp.user.id), "email": resp.user.email}, ""
        return None, "Login failed. Please try again."
    except Exception as e:
        msg = str(e)
        if "Invalid login credentials" in msg:
            return None, "Invalid email or password."
        if "Email not confirmed" in msg:
            return None, "Please check your email to confirm your account first."
        return None, "Login error. Please try again."


def sign_up(email: str, password: str) -> tuple[dict | None, str]:
    """Returns (user_dict, error_msg). user_dict is None on failure."""
    try:
        resp = _anon().auth.sign_up({"email": email, "password": password})
        if resp.user:
            return {"id": str(resp.user.id), "email": resp.user.email}, ""
        return None, "Sign-up failed. Please try again."
    except Exception as e:
        msg = str(e)
        if "already registered" in msg or "already exists" in msg:
            return None, "An account with that email already exists. Please log in."
        if "Password should be at least" in msg:
            return None, "Password must be at least 6 characters."
        return None, f"Sign-up error: {msg}"


# ── Pending jobs (bridge across Stripe redirect) ───────────────────────────────

def save_pending_job(session_id: str, user_id: str | None,
                     user_email: str, job_data: dict) -> None:
    try:
        _admin().table("pending_jobs").upsert({
            "session_id": session_id,
            "user_id": user_id,
            "user_email": user_email,
            "job_data": job_data,
        }).execute()
    except Exception as e:
        print(f"[DB] save_pending_job error: {e}")


def get_pending_job(session_id: str) -> dict | None:
    try:
        resp = _admin().table("pending_jobs").select("*").eq("session_id", session_id).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        print(f"[DB] get_pending_job error: {e}")
        return None


def delete_pending_job(session_id: str) -> None:
    try:
        _admin().table("pending_jobs").delete().eq("session_id", session_id).execute()
    except Exception as e:
        print(f"[DB] delete_pending_job error: {e}")


# ── Job history ───────────────────────────────────────────────────────────────

def log_job(user_id: str | None, user_email: str, job_type: str,
            address: str | None, filename: str | None,
            record_count: int, found_count: int,
            amount_paid: float, stripe_session_id: str) -> None:
    try:
        _admin().table("skiptrace_jobs").insert({
            "user_id": user_id,
            "user_email": user_email,
            "job_type": job_type,
            "address": address,
            "filename": filename,
            "record_count": record_count,
            "found_count": found_count,
            "amount_paid": round(float(amount_paid), 2),
            "stripe_session_id": stripe_session_id,
        }).execute()
    except Exception as e:
        print(f"[DB] log_job error: {e}")


def get_my_jobs(user_id: str, limit: int = 30) -> list[dict]:
    try:
        resp = (
            _admin()
            .table("skiptrace_jobs")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        print(f"[DB] get_my_jobs error: {e}")
        return []


# ── Admin ─────────────────────────────────────────────────────────────────────

def get_all_jobs(limit: int = 1000) -> list[dict]:
    try:
        resp = (
            _admin()
            .table("skiptrace_jobs")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        print(f"[DB] get_all_jobs error: {e}")
        return []


def get_all_users() -> list:
    try:
        resp = _admin().auth.admin.list_users()
        return resp or []
    except Exception as e:
        print(f"[DB] get_all_users error: {e}")
        return []
