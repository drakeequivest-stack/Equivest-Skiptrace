-- ============================================================
-- Equivest Skiptrace — Supabase Table Setup
-- Run this once in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================


-- 1. Job history (permanent log of every paid search)
CREATE TABLE IF NOT EXISTS skiptrace_jobs (
  id               uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id          uuid,
  user_email       text NOT NULL,
  job_type         text NOT NULL CHECK (job_type IN ('single', 'batch')),
  address          text,          -- single lookups
  filename         text,          -- batch uploads
  record_count     integer NOT NULL DEFAULT 1,
  found_count      integer NOT NULL DEFAULT 0,
  amount_paid      numeric(10,2) NOT NULL,
  stripe_session_id text UNIQUE,
  created_at       timestamptz DEFAULT now()
);


-- 2. Pending jobs (bridge across Stripe redirect — cleared after use)
CREATE TABLE IF NOT EXISTS pending_jobs (
  session_id   text PRIMARY KEY,
  user_id      uuid,
  user_email   text,
  job_data     jsonb NOT NULL,
  created_at   timestamptz DEFAULT now()
);


-- 3. Row Level Security (service role bypasses this automatically)
ALTER TABLE skiptrace_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_jobs   ENABLE ROW LEVEL SECURITY;

-- Authenticated users can read only their own jobs
CREATE POLICY "Users read own jobs"
  ON skiptrace_jobs FOR SELECT TO authenticated
  USING (auth.uid() = user_id);

-- Authenticated users can read their own pending jobs
CREATE POLICY "Users read own pending"
  ON pending_jobs FOR SELECT TO authenticated
  USING (auth.uid() = user_id::uuid);


-- 4. Auto-cleanup: delete pending jobs older than 24h
--    (optional but keeps the table clean)
-- If you have pg_cron enabled in Supabase, uncomment:
-- SELECT cron.schedule('cleanup-pending-jobs', '0 * * * *',
--   $$DELETE FROM pending_jobs WHERE created_at < now() - interval '24 hours'$$);
