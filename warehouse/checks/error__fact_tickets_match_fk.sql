-- Orders referencing a fixture the dim doesn't know about.
SELECT order_id
FROM core.fact_ticket_sales
WHERE match_key IS NULL
