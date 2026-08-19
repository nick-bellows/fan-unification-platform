-- The single input to unification: one row per identity-bearing source
-- record, on a common column set. The unifier reads only this table.
DROP TABLE IF EXISTS staging.identity_records;
CREATE TABLE staging.identity_records AS
SELECT 'crm'          AS source_system,
       contact_id     AS source_record_id,
       first_name, last_name, email, phone, city, state, zip,
       dob,
       extract(year FROM dob)::int AS birth_year,
       modified_at    AS observed_at
FROM staging.stg_crm_contacts
UNION ALL
SELECT 'ticketing', order_id, first_name, last_name, email, phone,
       NULL, NULL, zip, NULL::date, NULL::int, purchased_at
FROM staging.stg_ticketing_orders
UNION ALL
SELECT 'merch', order_number, first_name, last_name, email, NULL,
       NULL, NULL, zip, NULL::date, NULL::int, created_at
FROM staging.stg_merch_orders
UNION ALL
SELECT 'email', subscriber_id, first_name, last_name, email, NULL,
       NULL, NULL, zip, NULL::date, birth_year, signup_date::timestamptz
FROM staging.stg_email_subscribers;
