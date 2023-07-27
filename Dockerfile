# imagen oficial de Airflow
FROM apache/airflow:2.2.0-python3.9

# librerias de python
RUN pip install spotipy psycopg2-binary boto3 python-dotenv pandas

# copiar dags en la imagen de Docker
COPY dags/ /opt/airflow/dags/
