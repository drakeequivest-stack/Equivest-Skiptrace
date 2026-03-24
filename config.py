# Equivest Skiptrace — Config
# All secrets come from st.secrets (Streamlit Cloud) or .streamlit/secrets.toml (local)

import streamlit as st

def _s(key):
    return st.secrets[key]

# BatchData
BATCHDATA_TOKEN = _s("BATCHDATA_TOKEN")
BATCHDATA_URL   = "https://api.batchdata.com/api/v1/property/skip-trace"

# Stripe
STRIPE_PUBLIC_KEY = _s("STRIPE_PUBLIC_KEY")
STRIPE_SECRET_KEY = _s("STRIPE_SECRET_KEY")

# Pricing
PRICE_PER_RECORD = 0.13
COST_PER_RECORD  = 0.09
MIN_CHARGE       = 1.00

# App URL
APP_URL = _s("APP_URL")

# Supabase
SUPABASE_URL         = _s("SUPABASE_URL")
SUPABASE_ANON_KEY    = _s("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = _s("SUPABASE_SERVICE_KEY")

# Admin
ADMIN_PASSWORD = _s("ADMIN_PASSWORD")
