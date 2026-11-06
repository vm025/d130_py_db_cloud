import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")
print(f"SUPABASE_URL: {url}")


if url is None or key is None:
	raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")

supabase: Client = create_client(url, key)  # initialize supabase client.


def get_todos():
    response = supabase.table('todos').select('*').execute()
    return response.data


def add_todo(task):
    supabase.table('todos').insert({'task': task}).execute()

st.title("Supabase Todo App")

task = st.text_input("Add a new task:")
if st.button("Add Task"):
    if task:
        add_todo(task)
        st.success("Task added!")
    else:
        st.error("Please enter a task.")

st.write("### Todo List:")
todos = get_todos()

if todos:
    for todo in todos:
        if isinstance(todo, dict):
            task = todo.get("task")
            if task is not None:
                st.write(f"- {task}")
else:
    st.write("No tasks available.")