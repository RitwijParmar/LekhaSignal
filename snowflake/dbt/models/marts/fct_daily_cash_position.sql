{{ config(unique_key='cash_date') }}
select date_trunc('day', event_ts)::date as cash_date,
       currency,
       sum(amount) as settled_cash,
       count(*) as payment_events
from {{ ref('stg_payment_events') }}
{% if is_incremental() %}
where event_ts >= (select coalesce(dateadd(day, -2, max(cash_date)), '1900-01-01') from {{ this }})
{% endif %}
group by 1, 2
