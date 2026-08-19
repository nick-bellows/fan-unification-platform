-- Raw landing tables: payload-as-JSONB keeps landing schemaless so upstream
-- drift (e.g. the merch column rename) never breaks a load; typing happens in
-- staging. In Redshift the equivalent is SUPER columns — see
-- docs/redshift-migration.md.

CREATE TABLE IF NOT EXISTS raw.crm_contacts (
  payload     jsonb NOT NULL,
  batch_id    text NOT NULL,
  source_file text NOT NULL,
  loaded_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.crm_opportunities (LIKE raw.crm_contacts INCLUDING DEFAULTS);
CREATE TABLE IF NOT EXISTS raw.ticketing_orders (LIKE raw.crm_contacts INCLUDING DEFAULTS);
CREATE TABLE IF NOT EXISTS raw.merch_order_items (LIKE raw.crm_contacts INCLUDING DEFAULTS);
CREATE TABLE IF NOT EXISTS raw.email_subscribers (LIKE raw.crm_contacts INCLUDING DEFAULTS);
CREATE TABLE IF NOT EXISTS raw.email_events (LIKE raw.crm_contacts INCLUDING DEFAULTS);
CREATE TABLE IF NOT EXISTS raw.email_campaigns (LIKE raw.crm_contacts INCLUDING DEFAULTS);
CREATE TABLE IF NOT EXISTS raw.fixtures (LIKE raw.crm_contacts INCLUDING DEFAULTS);

CREATE TABLE IF NOT EXISTS raw.quarantine (
  source         text NOT NULL,
  payload        jsonb NOT NULL,
  reason         text NOT NULL,
  batch_id       text NOT NULL,
  source_file    text NOT NULL,
  quarantined_at timestamptz NOT NULL DEFAULT now()
);
