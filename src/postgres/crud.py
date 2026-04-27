import psycopg2
import psycopg2.sql as sql
import json
import os.path
from pathlib import Path


def get_credentials():
    FILE_PATH = os.path.dirname(os.path.realpath(__file__))
    CONN_PATH = str(Path(FILE_PATH, "db_credentials.json"))

    with open(CONN_PATH, 'r') as f:
        credentials = json.load(f)
    return credentials


class CRUD:
    def __init__(self, table, key, credentials):
        self.table = table
        self.key = key
        self.credentials = credentials

    def connect(self):
        try:
            connection = psycopg2.connect(**self.credentials)
            cursor = connection.cursor()
        except psycopg2.Error as e:
            print(f"Error connecting to the database: {e}")
        else:
            self.connection = connection
            self.cursor = cursor

    def select(self):
        connection = self.connect()
        try:
            if connection:
                select_query = sql.SQL("SELECT 1")
                self.cursor.execute(select_query)
                print(self.cursor.fetchall())
        except psycopg2.Error as e:
            print(f"Error executing query: {e}")
        finally:
            self.cursor.close()
            self.connection.close()

    def update(self):
        pass

    def delete(self):
        pass

    def insert(self):
        pass
