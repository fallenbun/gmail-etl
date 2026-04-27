import psycopg2
import psycopg2.sql as sql
import json
import os.path
from pathlib import Path


class CRUD:
    __conn_path = str(Path(os.path.dirname(
        os.path.realpath(__file__)), "config.json"))

    with open(__conn_path, 'r') as f:
        __file = json.load(f)
        __credentials = __file["postgres"]

    def __init__(self, table, primary_key):
        self.table = table
        self.primary_key = primary_key

    def connect(self):
        try:
            connection = psycopg2.connect(**CRUD.__credentials)
            cursor = connection.cursor()
        except psycopg2.Error as e:
            print(f"Error connecting to the database: {e}")
        else:
            self.connection = connection
            self.cursor = cursor

    def select(self, columns, primary_key_value=None):
        try:   
            if primary_key_value == None:
                select_query = sql.SQL("SELECT {} FROM {}").format(
                    sql.SQL(',').join(map(sql.Identifier, columns)),
                    sql.Identifier(self.table))
                self.cursor.execute(select_query)
            else:
                select_query = sql.SQL("SELECT {} FROM {} WHERE {} = {}").format(
                    sql.SQL(',').join(map(sql.Identifier, columns)),
                    sql.Identifier(self.table),
                    sql.Identifier(self.primary_key),
                    sql.Placeholder()
                )
                self.cursor.execute(select_query, (primary_key_value,))
            selected = self.cursor.fetchall()
        except psycopg2.Error as e:
            print(f"Error executing query: {e}")
        else:
            return selected
        
    def select_all(self, primary_key_value=None):
        try:   
            if primary_key_value == None:
                select_query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(self.table))         
                self.cursor.execute(select_query)
            else:
                select_query = sql.SQL("SELECT * FROM {} WHERE {} = {}").format(
                    sql.Identifier(self.table),
                    sql.Identifier(self.primary_key),
                    sql.Placeholder())
                self.cursor.execute(select_query, (primary_key_value,))
            selected = self.cursor.fetchall()
        except psycopg2.Error as e:
            print(f"Error executing query: {e}")
        else:
            return selected

    def insert(self, columns, rows):
        try:
            insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(self.table),
                sql.SQL(',').join(map(sql.Identifier, columns)),
                sql.SQL(',').join(sql.Placeholder() * len(rows[0]))
            )
            for row in rows:          
                print(insert_query.as_string(self.connection), row)
                #self.cursor.execute(insert_query, row)
        except psycopg2.Error as e:
            print(f"Error executing query: {e}")

    def update(self):
        try:
            update_query = sql.SQL("UPDATE {} SET {} WHERE {} = {}").format(
                sql.Identifier(self.table),
                sql.SQL(',').join(map(sql.Identifier, columns)),
                sql.SQL(',').join(sql.Placeholder() * len(rows[0]))
            )
            for row in rows:          
                print(insert_query.as_string(self.connection), row)
                #self.cursor.execute(insert_query, row)
        except psycopg2.Error as e:
            print(f"Error executing query: {e}")

    def delete(self):
        pass
