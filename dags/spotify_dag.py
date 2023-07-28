from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from datetime import datetime
from spotify_script import main
from airflow.models import Variable

default_args = {
    'owner': 'Matías Rodriguez',
    'start_date': datetime(2023, 7, 27),
    'email_on_failure': False,  # Para prevenir emails duplicados
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
        python_callable=spotify_task
    )

    failure_email = EmailOperator(
        task_id='failure_email',
        to=Variable.get('SMTP_MAIL_TO'),
        subject='La tarea {{ task_instance.task_id }} ha fallado',
        html_content='La tarea {{ task_instance.task_id }} en el DAG {{ task_instance.dag_id }} ha fallado.',
        trigger_rule='all_failed'  # La tarea se ejecuta si todas las demás fallan
    )

    spotify_operator >> failure_email
