import psycopg2
import os

DB_CONFIG = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": os.environ.get("PSQL_PASSWORD"),
    "port": 5432,
}

with psycopg2.connect(**DB_CONFIG) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_name = 'tracks';")
        print(cur.fetchall())