USE DATABASE LEKHASIGNAL;

-- Stream + triggered task are intentionally used for the imperative, audited CDC merge.
CREATE OR REPLACE STREAM RAW.PAYMENT_EVENTS_STREAM ON TABLE RAW.PAYMENT_EVENTS;
CREATE OR REPLACE TABLE CORE.PAYMENT_LEDGER LIKE RAW.PAYMENT_EVENTS;
CREATE OR REPLACE TASK CONTROL.MERGE_PAYMENT_CDC
  WAREHOUSE = LEKHASIGNAL_TRANSFORM_WH
  WHEN SYSTEM$STREAM_HAS_DATA('RAW.PAYMENT_EVENTS_STREAM')
AS
MERGE INTO CORE.PAYMENT_LEDGER target
USING (
  SELECT * FROM RAW.PAYMENT_EVENTS_STREAM
  QUALIFY ROW_NUMBER() OVER (PARTITION BY payment_id ORDER BY source_lsn DESC, event_ts DESC) = 1
) source
ON target.payment_id = source.payment_id
WHEN MATCHED AND source.METADATA$ACTION = 'DELETE' THEN DELETE
WHEN MATCHED THEN UPDATE SET amount=source.amount, event_ts=source.event_ts, source_lsn=source.source_lsn, payload=source.payload
WHEN NOT MATCHED AND source.METADATA$ACTION = 'INSERT' THEN INSERT (event_id,payment_id,invoice_id,customer_id,amount,currency,event_ts,source_lsn,payload,ingest_ts)
VALUES (source.event_id,source.payment_id,source.invoice_id,source.customer_id,source.amount,source.currency,source.event_ts,source.source_lsn,source.payload,source.ingest_ts);

-- Dynamic Tables are used for pure, declarative finance marts and their freshness SLO.
CREATE OR REPLACE DYNAMIC TABLE MART.FCT_REVENUE_RECOGNITION
  TARGET_LAG = '15 minutes'
  WAREHOUSE = LEKHASIGNAL_TRANSFORM_WH
AS
SELECT invoice_id, customer_id, invoice_status, invoice_total, DATE_TRUNC('day', issued_at) AS revenue_date,
       CURRENT_TIMESTAMP() AS refreshed_at
FROM RAW.INVOICE_EVENTS
QUALIFY ROW_NUMBER() OVER (PARTITION BY invoice_id ORDER BY source_lsn DESC, issued_at DESC) = 1;

-- DMF examples. Associate in a live account and surface results in the event table/alerting path.
ALTER TABLE RAW.PAYMENT_EVENTS ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.DUPLICATE_COUNT ON (event_id);
ALTER TABLE RAW.PAYMENT_EVENTS ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT ON (payment_id);
ALTER TABLE RAW.INVOICE_EVENTS ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.ROW_COUNT ON (invoice_id);

ALTER TASK CONTROL.MERGE_PAYMENT_CDC RESUME;
