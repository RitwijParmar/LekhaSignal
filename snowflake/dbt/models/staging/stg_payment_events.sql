with ranked as (
  select *, row_number() over (partition by payment_id order by source_lsn desc, event_ts desc) as rn
  from {{ source('raw', 'payment_events') }}
)
select event_id, payment_id, invoice_id, customer_id, amount, currency, event_ts, source_lsn
from ranked where rn = 1
