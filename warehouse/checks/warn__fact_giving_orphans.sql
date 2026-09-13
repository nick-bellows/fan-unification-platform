-- Opportunities whose contact never resolved to a fan (for example a contact
-- quarantined while its opportunities loaded under the separate watermark)
-- drop out of fact_giving on the xref join. Surface the revenue they carry
-- rather than letting it vanish from the revenue marts unnoticed.
SELECT o.opportunity_id, o.contact_id, o.type, o.amount
FROM staging.stg_crm_opportunities o
LEFT JOIN identity.fan_xref x
  ON x.source_system = 'crm' AND x.source_record_id = o.contact_id
WHERE x.fan_id IS NULL
