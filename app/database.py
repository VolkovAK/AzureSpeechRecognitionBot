import psycopg2
from datetime import datetime, timedelta


connection_args = {
    "user": "postgres",
    "password": "postgres",
    "host": "database",
    "port": 5432,
    "database": "asrdb"
}


def get_current_time() -> datetime:
    dt = datetime.now()
    timezone = timedelta(hours=3)  # Russian костыли
    return dt + timezone


def touch_record(filename: str) -> bool:
    # updates date and return True if record exists
    # and returns False if record does not exist
    submit_datetime = get_current_time()
    with psycopg2.connect(**connection_args) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM asr_data WHERE name=%s", (filename,))
            result = cursor.fetchall()
            if len(result) == 1:
                pk = result[0][0]
                cursor.execute("UPDATE asr_data SET submit_datetime = %s WHERE id = %s", (submit_datetime, pk))
                conn.commit()
                return True
            else:
                return False

def update_field(filename: str, column: str, value: str):
    with psycopg2.connect(**connection_args) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM asr_data WHERE name=%s", (filename,))
            result = cursor.fetchall()
            if len(result) == 1:
                pk = result[0][0]
                cursor.execute(f"UPDATE asr_data SET {column} = %s WHERE id = %s", (value, pk))
                conn.commit()


def create_record(filename: str, duration: str, status: str) -> None:
    submit_datetime = get_current_time()
    with psycopg2.connect(**connection_args) as conn:
        with conn.cursor() as cursor:
            args = (submit_datetime, filename, duration, status)
            cursor.execute("INSERT INTO asr_data (submit_datetime, name, duration, status) VALUES (%s, %s, %s, %s)", args)
            conn.commit()


def get_all_records_sort_date() -> list:
    with psycopg2.connect(**connection_args) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM asr_data ORDER BY submit_datetime DESC")
            return cursor.fetchall()


def create_table_if_not_exists() -> None:
    with psycopg2.connect(**connection_args) as conn:
        with conn.cursor() as cursor:
            cursor.execute("select exists(select * from information_schema.tables where table_name='asr_data')")
            exist = cursor.fetchone()[0]
            if not exist:
                cursor.execute("CREATE TABLE asr_data (id SERIAL PRIMARY KEY, submit_datetime timestamp, name varchar, duration varchar, status varchar)")
                conn.commit()


def drop_table():
    with psycopg2.connect(**connection_args) as conn:
        with conn.cursor() as cursor:
            cursor.execute("DROP TABLE asr_data")
            conn.commit()
