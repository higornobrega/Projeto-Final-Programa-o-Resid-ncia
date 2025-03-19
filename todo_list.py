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


class TaskView(tk.Frame):
    def __init__(self, root: tk.Tk, controller):
        super().__init__(root)
        self.controller = controller
        self.root = root
        self.root.title("To-Do List")
        self.selected_task_id = None
        self._build_ui()
        self.load_tasks()

    def _build_ui(self):
        self.pack(padx=10, pady=10)
        self.title_entry = tk.Entry(self, width=40)
        self.title_entry.grid(row=0, column=0, padx=5, pady=5)

        self.task_entry = tk.Entry(self, width=40)
        self.task_entry.grid(row=1, column=0, padx=5, pady=5)

        self.add_edit_button = tk.Button(
            self, text="Adicionar", command=self.add_or_edit_task)
        self.add_edit_button.grid(row=2, column=0, padx=5, pady=5)

        self.task_list = tk.Listbox(self, width=50, height=10)
        self.task_list.grid(row=3, column=0, columnspan=2, pady=10)
        self.task_list.bind("<<ListboxSelect>>", self.fill_fields)

        tk.Button(self, text="Remover", command=self.delete_task).grid(
            row=4, column=0, columnspan=2, pady=5)

    def add_or_edit_task(self):
        title = self.title_entry.get().strip()
        task = self.task_entry.get().strip()
        if title and task:
            if self.selected_task_id:
                self.controller.update_task(self.selected_task_id, title, task)
                self.selected_task_id = None
                self.add_edit_button.config(text="Adicionar")
            else:
                self.controller.add_task(title, task)
            self.title_entry.delete(0, tk.END)
            self.task_entry.delete(0, tk.END)
            self.load_tasks()
        else:
            messagebox.showwarning(
                "Aviso", "O título e a descrição da tarefa não podem estar vazios!")

    def fill_fields(self, event):
        try:
            selection = self.task_list.curselection()
            if not selection:  # Verifica se há uma seleção antes de acessar
                return

            selected_task = self.task_list.get(selection[0])
            if selected_task:
                task_id, title_desc = selected_task.split(" - ", 1)
                title, desc = title_desc.split(": ", 1)
                self.selected_task_id = int(task_id)

                # Preenche os campos com os dados da tarefa selecionada
                self.title_entry.delete(0, tk.END)
                self.task_entry.delete(0, tk.END)
                self.title_entry.insert(0, title)
                self.task_entry.insert(0, desc)

                self.add_edit_button.config(text="Editar")
        except (IndexError, ValueError):
            pass  # Se houver um erro inesperado, ignora e não altera nada

    def load_tasks(self):
        self.task_list.delete(0, tk.END)
        for task in self.controller.get_tasks():
            self.task_list.insert(tk.END, f"{task[0]} - {task[1]}: {task[2]}")

    def delete_task(self):
        try:
            selected_task = self.task_list.get(self.task_list.curselection())
            if selected_task:
                task_id = int(selected_task.split(" - ")[0])
                self.controller.delete_task(task_id)
                self.selected_task_id = None
                self.add_edit_button.config(text="Adicionar")
                self.load_tasks()
        except (IndexError, ValueError):
            messagebox.showwarning(
                "Aviso", "Selecione uma tarefa para remover!")


class TaskController:
    def __init__(self, model: TaskModel):
        self.model = model

    def add_task(self, title: str, description: str):
        self.model.add_task(title, description)

    def get_tasks(self):
        return self.model.get_tasks()

    def delete_task(self, task_id: int):
        self.model.delete_task(task_id)

    def update_task(self, task_id: int, new_title: str, new_description: str):
        self.model.update_task(task_id, new_title, new_description)
