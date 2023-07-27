
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from spotify_script import main

default_args = {
    'owner': 'Matías Rodriguez',
    'start_date': datetime(2023, 7, 27),
}

def spotify_task():
    main()

with DAG(
    'spotify_dag',
    default_args=default_args,
    description='Un DAG que consulta datos de Spotify y los guarda en Redshift',
    schedule_interval='@weekly',
    tags= ['Spotify', 'TOP 50', 'Argentina']
) as dag:

    spotify_operator = PythonOperator(
        task_id='spotify_task',
        python_callable=spotify_task,
    )
