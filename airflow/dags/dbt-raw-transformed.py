from datetime import datetime
import logging
import os
from airflow.sdk import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.providers.standard.sensors.external_task import ExternalTaskSensor
from docker.types import Mount

logger = logging.getLogger(__name__)

HOST_DBT_DIR = os.environ.get('HOST_PROJECT_DIR') + '/dbt'

with DAG(
    dag_id="dbt-raw-transformed",
    start_date=datetime(2026, 9, 1),
    schedule="@once",
    catchup=False,
    tags=["dbt", "transformed"],
) as dag:
    wait_for_load_receipts = ExternalTaskSensor(
        task_id='wait_for_load_receipts',
        external_dag_id='gmail-receipts-pg-stg_raw',
        external_task_id='load_receipts',
        allowed_states=['success'],
        failed_states=['failed', 'skipped'],
        mode='reschedule',
        poke_interval=120,
        timeout=360
    )

    dbt_run = DockerOperator(
        task_id='dbt_run',
        image='dbt-image',
        command='run',
        docker_url='unix://var/run/docker.sock',
        network_mode='dwh_network',
        auto_remove='success',
        working_dir='/usr/dbt',
        environment={
            'DB_HOST': '{{conn.retail.host}}',
            'DB_PORT': '{{conn.retail.port}}',
            'DB_NAME': '{{conn.retail.schema}}',
            'DB_USER': '{{conn.retail.login}}',
            'DB_PASSWORD': '{{conn.retail.password}}'
        },
        mounts=[
            Mount(source=HOST_DBT_DIR, target='/usr/dbt', type='bind'),
            Mount(source=f'{HOST_DBT_DIR}/profiles.yml',
                  target='/usr/dbt/profiles.yml', type='bind')
        ],
        mount_tmp_dir=False
)   
    wait_for_load_receipts >> dbt_run