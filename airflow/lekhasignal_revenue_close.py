"""Airflow blueprint: orchestration belongs here; Snowflake transformations stay in dbt/Dynamic Tables."""
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG("lekhasignal_revenue_close", start_date=datetime(2026, 1, 1), schedule="0 8 * * *", catchup=False, tags=["finance", "snowflake", "reliability"]) as dag:
    run_contracts = BashOperator(task_id="validate_source_contracts", bash_command="python -m lekh_signal.contracts_check")
    run_dbt = BashOperator(task_id="run_dbt_marts", bash_command="cd /opt/lekhasignal/snowflake/dbt && dbt build --select marts")
    reconcile = BashOperator(task_id="reconcile_finance_controls", bash_command="python -m lekh_signal.reconcile")
    publish = BashOperator(task_id="publish_after_control_pass", bash_command="python -m lekh_signal.publish --requires-control-pass")
    run_contracts >> run_dbt >> reconcile >> publish
