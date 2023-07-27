
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import psycopg2
from psycopg2 import extras
import os
from dotenv import load_dotenv
from datetime import date
import sys
from airflow.models import Variable

def main():
    load_dotenv('credenciales.env')

    # credenciales Spotify
    CLIENT_ID = Variable.get("SPOTIFY_CLIENT_ID")
    CLIENT_SECRET = Variable.get("SPOTIFY_CLIENT_SECRET")

    # credenciales Amazon Redshift
    HOST = Variable.get("REDSHIFT_HOST")
    PORT = Variable.get("REDSHIFT_PORT")
    USER = Variable.get("REDSHIFT_USER")
    PASSWORD = Variable.get("REDSHIFT_PASSWORD")
    DATABASE = Variable.get("REDSHIFT_DATABASE")

    # objeto Spotify
    client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    # hoy
    today = date.today()

    # conexión con Redshift
    conn = psycopg2.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        dbname=DATABASE
    )

    # SQL query crear tabla de canciones
    create_table_tracks_query = """
    CREATE TABLE IF NOT EXISTS davila_spotify_tracks (
        id VARCHAR(255) PRIMARY KEY,
        name VARCHAR(255),
        artist VARCHAR(255),
        artist_id VARCHAR(255),
        album VARCHAR(255),
        popularity INT,
        duration_ms INT,
        ranking INT,
        date DATE
    );
    """

    # SQL query crear tabla de artistas
    create_table_artists_query = """
    CREATE TABLE IF NOT EXISTS davila_spotify_artists (
        id VARCHAR(255) PRIMARY KEY,
        name VARCHAR(255),
        followers INT,
        genres VARCHAR(255),
        popularity INT
    );
    """

    # crear tabla de canciones
    with conn.cursor() as cursor:
        cursor.execute(create_table_tracks_query)
        conn.commit()

    # crear tabla de artistas
    with conn.cursor() as cursor:
        cursor.execute(create_table_artists_query)
        conn.commit()

    # SQL query chequear si ya esta cargado el día
    check_date_query = """
    SELECT date FROM davila_spotify_tracks WHERE date = %s LIMIT 1;
    """

    with conn.cursor() as cursor:
        cursor.execute(check_date_query, (today,))
        date_in_db = cursor.fetchone()

    # si ya existe el dia, exit
    if date_in_db:
        print("Las canciones de hoy ya estan en la lista.")
        sys.exit()

    # si no existe el día, API request
    results = sp.playlist_tracks('37i9dQZEVXbMMy2roB9myp')

    # SQL query para obtener artistas existentes en tabla de artistas
    existing_artists_query = "SELECT id FROM davila_spotify_artists;"
    with conn.cursor() as cursor:
        cursor.execute(existing_artists_query)
        existing_artists = cursor.fetchall()
    existing_artists = set([item[0] for item in existing_artists])

    # SQL query insertar canciones en la tabla de canciones
    insert_tracks_query = """
    INSERT INTO davila_spotify_tracks (id, name, artist, artist_id, album, popularity, duration_ms, ranking, date)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    # SQL query insertar artistas en la tabla de artistas
    insert_artists_query = """
    INSERT INTO davila_spotify_artists (id, name, followers, genres, popularity) VALUES (%s, %s, %s, %s, %s);
    """

    # listas de canciones y artistas
    data_values_tracks = []
    data_values_artists = []

    for idx, track in enumerate(results['items']):
        track_data = (
            track['track']['id'],
            track['track']['name'],
            track['track']['artists'][0]['name'],
            track['track']['artists'][0]['id'],
            track['track']['album']['name'],
            track['track']['popularity'],
            track['track']['duration_ms'],
            idx + 1,
            today
        )
        data_values_tracks.append(track_data)

        artist_id = track['track']['artists'][0]['id']

        # chequear si el artista ya existe
        if artist_id in existing_artists:
            continue

        # obtener informacion adicional del artista
        artist = sp.artist(artist_id)
        artist_data = (
            artist['id'],
            artist['name'],
            artist['followers']['total'],
            ",".join(artist['genres']),
            artist['popularity']
        )
        data_values_artists.append(artist_data)

        # agregar el artista a los artistas existentes
        existing_artists.add(artist_id)

    # insertar los datos de canciones en la tabla de canciones
    with conn.cursor() as cursor:
        for track_data in data_values_tracks:
            cursor.execute(insert_tracks_query, track_data)
        conn.commit()

    # insertar los datos de artistas en la tabla de artistas
    if data_values_artists:
        with conn.cursor() as cursor:
            for artist_data in data_values_artists:
                cursor.execute(insert_artists_query, artist_data)
            conn.commit()

    # cerrar la conexión con la base de datos
    conn.close()

if __name__ == "__main__":
    main()
