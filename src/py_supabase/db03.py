"""
db.py - MongoDB data-access layer for the Todo app.

Everything that touches the database lives here, so the UI (app.py) never
needs to know about pymongo. Operations are grouped as:

    CONNECTION  -> get_collection()
    CREATE      -> create_todo()
    READ        -> get_todos(), get_stats()
    UPDATE      -> update_todo(), set_completed()
    DELETE      -> delete_todo(), delete_completed()

Document shape (one document per todo):
    {
        "_id":          ObjectId,
        "title":        str,
        "description":  str,
        "priority":     "High" | "Medium" | "Low",
        "priority_rank": int,            # 0 = High ... 2 = Low (handy for sorting)
        "category":     str,
        "due_date":     datetime | None, # midnight of the due day
        "completed":    bool,
        "created_at":   datetime (UTC),
        "updated_at":   datetime (UTC),
        "completed_at": datetime | None,
    }
"""

import re
from datetime import date, datetime, time, timezone
from typing import Optional
from urllib.parse import quote_plus

import streamlit as st
from bson import ObjectId 
from pymongo import ASCENDING, DESCENDING, MongoClient

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
CLUSTER_HOST = "cluster0.hte6gm5.mongodb.net"
DB_NAME = "todo_app"
COLLECTION_NAME = "todos"

PRIORITY_RANK = {"High": 0, "Medium": 1, "Low": 2}


# ==========================================================================
# CONNECTION
# ==========================================================================
def _secret(*names: str) -> str:
    """Look up a value in .streamlit/secrets.toml.

    Checks the [mongodb] section first, then the top level, and accepts
    several possible key names (e.g. 'username' or 'db_username').
    """
    for section in (st.secrets.get("mongodb", {}), st.secrets):
        for name in names:
            if name in section:
                return section[name]
    raise KeyError(f"Missing secret: one of {names} in .streamlit/secrets.toml")


def _build_uri() -> str:
    """Build the Atlas connection string, URL-encoding the credentials."""
    user = quote_plus(_secret("username", "db_username"))
    password = quote_plus(_secret("password", "db_password"))
    # print(f"Connecting to MongoDB cluster {CLUSTER_HOST} as user {user}, {password}")
    # return (f"mongodb+srv://{user}:{password}@{CLUSTER_HOST}/")
    # format reqd:  mongodb+srv://<db_username>:<db_password>@cluster0.hte6gm5.mongodb.net/


    return (
        f"mongodb+srv://{user}:{password}@{CLUSTER_HOST}/"
        "?retryWrites=true&w=majority&appName=Cluster0"
    )

    


@st.cache_resource(show_spinner="Connecting to MongoDB...")
def get_collection():
    """Return the todos collection. Cached so the client is created only once
    per server process, not on every Streamlit rerun."""
    client = MongoClient(_build_uri(), serverSelectionTimeoutMS=5000)
    client.admin.command("ping")  # fail fast if credentials / network are wrong

    collection = client[DB_NAME][COLLECTION_NAME]
    # Indexes keep the common queries (sorting by date, filtering by status) fast.
    collection.create_index([("created_at", DESCENDING)])
    collection.create_index([("completed", ASCENDING), ("due_date", ASCENDING)])
    return collection


# ==========================================================================
# Helpers
# ==========================================================================
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _day_to_datetime(day: Optional[date]) -> Optional[datetime]:
    """MongoDB stores datetimes, not plain dates, so convert date -> midnight."""
    return datetime.combine(day, time.min) if day else None


# ==========================================================================
# CREATE
# ==========================================================================
def create_todo(
    title: str,
    description: str = "",
    priority: str = "Medium",
    category: str = "",
    due_date: Optional[date] = None,
) -> str:
    """Insert a new todo and return its id as a string."""
    now = _now()
    document = {
        "title": title.strip(),
        "description": description.strip(),
        "priority": priority,
        "priority_rank": PRIORITY_RANK[priority],
        "category": category.strip(),
        "due_date": _day_to_datetime(due_date),
        "completed": False,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }
    result = get_collection().insert_one(document)
    return str(result.inserted_id)


# ==========================================================================
# READ
# ==========================================================================
def get_todos(
    status: str = "All",
    priority: str = "Any",
    search: str = "",
    sort_by: str = "Newest",
) -> list[dict]:
    """Return todos matching the filters.

    Filtering is done by MongoDB (query document). Sorting is done in Python
    so that todos without a due date can be pushed to the end, and open
    todos always appear above completed ones.
    """
    query: dict = {}

    if status == "Open":
        query["completed"] = False
    elif status == "Completed":
        query["completed"] = True

    if priority != "Any":
        query["priority"] = priority

    if search.strip():
        # Case-insensitive match on title, description or category.
        pattern = {"$regex": re.escape(search.strip()), "$options": "i"}
        query["$or"] = [{"title": pattern}, {"description": pattern}, {"category": pattern}]

    todos = list(get_collection().find(query))

    # Python's sort is stable: sort by the secondary key first, then the primary.
    todos.sort(key=lambda t: t["created_at"], reverse=True)  # newest first (default)
    if sort_by == "Oldest":
        todos.sort(key=lambda t: t["created_at"])
    elif sort_by == "Due date":
        todos.sort(key=lambda t: (t.get("due_date") is None, t.get("due_date") or datetime.max))
    elif sort_by == "Priority":
        todos.sort(key=lambda t: t["priority_rank"])

    todos.sort(key=lambda t: t["completed"])  # open todos first
    return todos


def get_stats() -> dict:
    """Return counts used by the summary tiles at the top of the page."""
    collection = get_collection()
    today = datetime.combine(date.today(), time.min)

    total = collection.count_documents({})
    done = collection.count_documents({"completed": True})
    overdue = collection.count_documents({"completed": False, "due_date": {"$lt": today}})
    return {"total": total, "open": total - done, "done": done, "overdue": overdue}


# ==========================================================================
# UPDATE
# ==========================================================================
def update_todo(
    todo_id: str,
    title: str,
    description: str,
    priority: str,
    category: str,
    due_date: Optional[date],
) -> bool:
    """Overwrite the editable fields of a todo. Returns True if it existed."""
    result = get_collection().update_one(
        {"_id": ObjectId(todo_id)},
        {
            "$set": {
                "title": title.strip(),
                "description": description.strip(),
                "priority": priority,
                "priority_rank": PRIORITY_RANK[priority],
                "category": category.strip(),
                "due_date": _day_to_datetime(due_date),
                "updated_at": _now(),
            }
        },
    )
    return result.matched_count == 1


def set_completed(todo_id: str, completed: bool) -> bool:
    """Mark a todo as done / not done."""
    now = _now()
    result = get_collection().update_one(
        {"_id": ObjectId(todo_id)},
        {
            "$set": {
                "completed": completed,
                "completed_at": now if completed else None,
                "updated_at": now,
            }
        },
    )
    return result.matched_count == 1


# ==========================================================================
# DELETE
# ==========================================================================
def delete_todo(todo_id: str) -> bool:
    """Delete a single todo. Returns True if something was removed."""
    result = get_collection().delete_one({"_id": ObjectId(todo_id)})
    return result.deleted_count == 1


def delete_completed() -> int:
    """Delete every completed todo and return how many were removed."""
    result = get_collection().delete_many({"completed": True})
    return result.deleted_count