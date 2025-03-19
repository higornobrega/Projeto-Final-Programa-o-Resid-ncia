import sqlite3
import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import messagebox

import psycopg2
from psycopg2 import sql

POSTGRES_CONFIG = {
    "dbname": "todo_list",
    "user": "todo_list",
    "password": "todo_list",
    "host": "localhost",
    "port": "5432"
}


class DatabaseBase(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def execute_query(self, query, params=None, fetch=False):
        pass

    @abstractmethod
    def close(self):
        pass


class SQLiteDatabase(DatabaseBase):
    def __init__(self, db_name="tasks.db"):
        self.db_name = db_name
        self.conn = self.connect()
        self.cur = self.conn.cursor()
        self._create_table()

    def connect(self):
        return sqlite3.connect(self.db_name)

    def _create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL
        )"""
        self.execute_query(query)

    def execute_query(self, query, params=None, fetch=False):
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(query, params or ())
            return cur.fetchall() if fetch else None

    def close(self):
        self.conn.close()


class TaskModel:
    def __init__(self, db: DatabaseBase):
        self.db = db

    def add_task(self, title: str, description: str):
        query = "INSERT INTO tasks (title, description) VALUES (?, ?)"
        self.db.execute_query(query, (title, description))

    def get_tasks(self):
        return self.db.execute_query("SELECT id, title, description FROM tasks ORDER BY id", fetch=True)

    def delete_task(self, task_id: int):
        query = "DELETE FROM tasks WHERE id = ?"
        self.db.execute_query(query, (task_id,))

    def update_task(self, task_id: int, new_title: str, new_description: str):
        query = "UPDATE tasks SET title = ?, description = ? WHERE id = ?"
        self.db.execute_query(query, (new_title, new_description, task_id))

# Interface gráfica
