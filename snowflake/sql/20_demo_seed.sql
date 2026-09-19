-- Non-production demonstration data only. It is designed to prove the CDC,
-- Dynamic Table, and reconciliation controls without representing customer data.

INSERT INTO LEKHASIGNAL.RAW.INVOICE_EVENTS
  (event_id, invoice_id, customer_id, invoice_status, invoice_total, issued_at, source_lsn, payload)
SELECT
  'INV_EVT_' || n,
  'INV_' || LPAD(TO_VARCHAR(n), 5, '0'),
  'CUST_' || LPAD(TO_VARCHAR(MOD(n, 75)), 3, '0'),
  IFF(MOD(n, 11) = 0, 'PAST_DUE', 'OPEN'),
  (100 + MOD(n * 37, 9000))::NUMBER(18, 2),
  DATEADD('minute', -n, CURRENT_TIMESTAMP()),
  n,
  OBJECT_CONSTRUCT('source', 'simulated_erp', 'event_type', 'invoice')
FROM (
  SELECT ROW_NUMBER() OVER (ORDER BY SEQ4()) AS n
  FROM TABLE(GENERATOR(ROWCOUNT => 500))
);

INSERT INTO LEKHASIGNAL.RAW.PAYMENT_EVENTS
  (event_id, payment_id, invoice_id, customer_id, amount, currency, event_ts, source_lsn, payload)
SELECT
  'PAY_EVT_' || n,
  'PAY_' || LPAD(TO_VARCHAR(n), 5, '0'),
  'INV_' || LPAD(TO_VARCHAR(n), 5, '0'),
  'CUST_' || LPAD(TO_VARCHAR(MOD(n, 75)), 3, '0'),
  (100 + MOD(n * 37, 9000))::NUMBER(18, 2),
  IFF(MOD(n, 7) = 0, 'CAD', 'USD'),
  DATEADD('minute', -n, CURRENT_TIMESTAMP()),
  n,
  OBJECT_CONSTRUCT('source', 'simulated_settlement', 'event_type', 'payment')
FROM (
  SELECT ROW_NUMBER() OVER (ORDER BY SEQ4()) AS n
  FROM TABLE(GENERATOR(ROWCOUNT => 500))
);

-- Five records (given the default 500-row seed) intentionally reuse a payment
-- identifier. The triggered task keeps the event with the newest source LSN.
INSERT INTO LEKHASIGNAL.RAW.PAYMENT_EVENTS
  (event_id, payment_id, invoice_id, customer_id, amount, currency, event_ts, source_lsn, payload)
SELECT
  event_id || '_DUP', payment_id, invoice_id, customer_id, amount, currency,
  DATEADD('minute', 5, event_ts), source_lsn + 10000,
  OBJECT_CONSTRUCT('source', 'simulated_settlement', 'event_type', 'duplicate_payment_test')
FROM LEKHASIGNAL.RAW.PAYMENT_EVENTS
WHERE MOD(source_lsn, 97) = 0;

ALTER TASK LEKHASIGNAL.CONTROL.MERGE_PAYMENT_CDC RESUME;
EXECUTE TASK LEKHASIGNAL.CONTROL.MERGE_PAYMENT_CDC;
ALTER DYNAMIC TABLE LEKHASIGNAL.MART.FCT_REVENUE_RECOGNITION REFRESH;

CREATE OR REPLACE VIEW LEKHASIGNAL.CONTROL.REVENUE_RECONCILIATION AS
SELECT
  (SELECT COUNT(*) FROM LEKHASIGNAL.RAW.INVOICE_EVENTS) AS raw_invoice_events,
  (SELECT COUNT(*) FROM LEKHASIGNAL.RAW.PAYMENT_EVENTS) AS raw_payment_events,
  (SELECT COUNT(*) FROM LEKHASIGNAL.CORE.PAYMENT_LEDGER) AS canonical_payment_events,
  (SELECT COUNT(*) FROM LEKHASIGNAL.MART.FCT_REVENUE_RECOGNITION) AS revenue_mart_rows,
  (SELECT COUNT(*) - COUNT(DISTINCT payment_id) FROM LEKHASIGNAL.RAW.PAYMENT_EVENTS) AS duplicate_payment_rows,
  (SELECT COUNT(*) FROM LEKHASIGNAL.RAW.PAYMENT_EVENTS WHERE currency <> 'USD') AS non_usd_payment_rows;

SELECT * FROM LEKHASIGNAL.CONTROL.REVENUE_RECONCILIATION;
