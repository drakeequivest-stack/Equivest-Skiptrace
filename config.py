# Equivest Skiptrace — Config
# Reads from Streamlit Cloud secrets when deployed, falls back to local values.

import streamlit as st

def _s(key, default=""):
    try:
        return st.secrets[key]
    except Exception:
        return default

# BatchData (skiptracing)
BATCHDATA_TOKEN = _s("BATCHDATA_TOKEN", "0Y9aFi731oljt8enqlZXhe2yHbHonGZbJS4jgShW")
BATCHDATA_URL   = "https://api.batchdata.com/api/v1/property/skip-trace"

# Stripe (payments)
STRIPE_PUBLIC_KEY = _s("STRIPE_PUBLIC_KEY", "pk_live_51T6nzxLt5c2HciK1wa2meadmuDhDwPobt9l6d8Wqry1pGwY58bSjTY7Srh7Hx9G7Pxs3XotVisQLf1yeGQVhwMo300E6nU9jPS")
STRIPE_SECRET_KEY = _s("STRIPE_SECRET_KEY", "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")

# Pricing
PRICE_PER_RECORD = 0.13   # what you charge members
COST_PER_RECORD  = 0.09   # what BatchData charges you
MIN_CHARGE       = 1.00   # minimum charge (Stripe floor)

# App URL — updated automatically based on environment
APP_URL = _s("APP_URL", "http://localhost:8501")

# Supabase (auth + job history)
SUPABASE_URL         = _s("SUPABASE_URL",         "https://ynqrcefaokyysrzqkqdm.supabase.co")
SUPABASE_ANON_KEY    = _s("SUPABASE_ANON_KEY",    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlucXJjZWZhb2t5eXNyenFrcWRtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4OTk4MjksImV4cCI6MjA4OTQ3NTgyOX0.6nmNGlfRpWWwxzMl85WikuvmGjP0h_9VvVeAVXkFqXw")
SUPABASE_SERVICE_KEY = _s("SUPABASE_SERVICE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlucXJjZWZhb2t5eXNyenFrcWRtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Mzg5OTgyOSwiZXhwIjoyMDg5NDc1ODI5fQ.PpGpykzNLNfcWAIJokN5Wa2BMF_8X0j7GaoePGKGmDw")

# Admin portal
ADMIN_PASSWORD = _s("ADMIN_PASSWORD", "EquivestDolphin1$")
