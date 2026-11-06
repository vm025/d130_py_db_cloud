"""
vmu
mongodb+srv://<db_username>:<db_password>@cluster0.hte6gm5.mongodb.net/

-------------------------------------------------------
app.py - Streamlit UI for the Todo app.

Run with:  streamlit run app.py

Layout of this file:
    1. Page setup & styling (CSS)
    2. UI helpers (HTML snippets for stats and todo cards)
    3. Dialogs (edit / confirm delete)
    4. CREATE  - "Add a task" form
    5. READ    - filters + todo list
    6. Main    - ties everything together
    
"""

from datetime import date
from html import escape
import streamlit as st
import py_supabase.db03 as db

# ==========================================================================
# 1. PAGE SETUP & STYLING
# ==========================================================================
st.set_page_config(page_title="Tasks", page_icon="🗒️", layout="centered")

# Muted teal / sage palette. All colours live in CSS variables so they are
# easy to tweak in one place.
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root {
    --bg: #F2F5F4;        --surface: #FFFFFF;   --ink: #26343B;
    --muted: #6A7A82;     --line: #DCE4E3;
    --primary: #3E6B73;   --primary-soft: #E3EEEE;
    --high: #B0625C;      --high-soft: #F6E7E5;
    --med: #A67D33;       --med-soft: #F6EEDC;
    --low: #55876B;       --low-soft: #E3F0E8;
}

html, body, .stApp, button, input, textarea, select {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
}
.stApp { background: var(--bg); color: var(--ink); }
#MainMenu, footer { visibility: hidden; }

/* Page width + responsive padding */
.block-container { max-width: 820px; padding: 2.5rem 1.25rem 4rem; }
@media (max-width: 640px) { .block-container { padding: 1.25rem .75rem 3rem; } }

/* Header */
.app-title { font-size: 2rem; font-weight: 700; margin: 0; letter-spacing: -0.02em; }
.app-sub   { color: var(--muted); margin: .15rem 0 1.25rem; font-size: .95rem; }

/* Summary tiles: auto-wrap into 2x2 on phones, 4x1 on desktop */
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: .75rem; }
.stat  { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: .8rem 1rem; }
.stat b { display: block; font-size: 1.5rem; font-weight: 700; line-height: 1.2; }
.stat span { color: var(--muted); font-size: .82rem; }
.stat.overdue b { color: var(--high); }
.progress { height: 6px; background: var(--line); border-radius: 99px; margin: .9rem 0 1.4rem; overflow: hidden; }
.progress > div { height: 100%; background: var(--primary); border-radius: 99px; }

/* Cards (st.container(border=True)) and forms */
[data-testid="stVerticalBlockBorderWrapper"], [data-testid="stForm"] {
    background: var(--surface); border: 1px solid var(--line) !important;
    border-radius: 14px !important; box-shadow: none !important;
}
[data-testid="stExpander"] { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; }
[data-testid="stExpander"] details { border: none; }

/* Todo row: keep checkbox | text | edit | delete on ONE line, even on phones */
[data-testid="stHorizontalBlock"]:has(.row-marker) { flex-wrap: nowrap !important; gap: .35rem; }
[data-testid="stHorizontalBlock"]:has(.row-marker) > [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; }
[data-testid="stHorizontalBlock"]:has(.row-marker) > [data-testid="stColumn"]:nth-child(2) { flex: 1 1 0 !important; }
[data-testid="stHorizontalBlock"]:has(.row-marker) > [data-testid="stColumn"]:not(:nth-child(2)) { flex: 0 0 auto !important; }
[data-testid="stElementContainer"]:has(.row-marker) { display: none; }

/* Todo text */
.todo-title { font-weight: 600; font-size: 1rem; overflow-wrap: anywhere; }
.todo-desc  { color: var(--muted); font-size: .88rem; margin-top: .1rem; overflow-wrap: anywhere; }
.todo-meta  { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .5rem; }
.done .todo-title { text-decoration: line-through; color: var(--muted); font-weight: 500; }
.done .todo-desc  { opacity: .7; }

/* Chips */
.chip { font-size: .74rem; font-weight: 600; padding: .15rem .6rem; border-radius: 99px;
        background: var(--primary-soft); color: var(--primary); }
.chip.High   { background: var(--high-soft); color: var(--high); }
.chip.Medium { background: var(--med-soft);  color: var(--med); }
.chip.Low    { background: var(--low-soft);  color: var(--low); }
.chip.cat    { background: #ECEFEF; color: var(--muted); }
.chip.late   { background: var(--high-soft); color: var(--high); }

/* Empty state */
.empty { text-align: center; color: var(--muted); padding: 2.5rem 1rem; }
.empty b { color: var(--ink); display: block; font-size: 1.05rem; margin-bottom: .25rem; }

/* Primary buttons in the app's teal */
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"] {
    background: var(--primary); border-color: var(--primary); color: #fff; border-radius: 10px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

PRIORITIES = ["High", "Medium", "Low"]


# ==========================================================================
# 2. UI HELPERS
# ==========================================================================
def flash(message: str, icon: str = "✅") -> None:
    """Queue a toast to show after the next rerun (a toast fired right before
    st.rerun() would be lost)."""
    st.session_state["flash"] = (message, icon)


def format_day(d) -> str:
    """'12 Nov' (adds the year when it isn't the current one)."""
    fmt = "%d %b" if d.year == date.today().year else "%d %b %Y"
    return d.strftime(fmt)


def render_stats() -> None:
    """Summary tiles + overall progress bar."""
    s = db.get_stats()
    pct = round(100 * s["done"] / s["total"]) if s["total"] else 0
    st.markdown(
        f"""<div class="stats">
            <div class="stat"><b>{s['total']}</b><span>Total</span></div>
            <div class="stat"><b>{s['open']}</b><span>Open</span></div>
            <div class="stat"><b>{s['done']}</b><span>Completed</span></div>
            <div class="stat overdue"><b>{s['overdue']}</b><span>Overdue</span></div>
        </div>
        <div class="progress"><div style="width:{pct}%"></div></div>""",
        unsafe_allow_html=True,
    )


def todo_html(todo: dict) -> str:
    """Build the HTML for a todo's text block (all user text is escaped)."""
    chips = [f'<span class="chip {todo["priority"]}">{todo["priority"]}</span>']
    if todo.get("category"):
        chips.append(f'<span class="chip cat">{escape(todo["category"])}</span>')
    if todo.get("due_date"):
        due = todo["due_date"].date()
        late = (not todo["completed"]) and due < date.today()
        label = f"Overdue since {format_day(due)}" if late else f"Due {format_day(due)}"
        chips.append(f'<span class="chip {"late" if late else "cat"}">{label}</span>')

    desc = f'<div class="todo-desc">{escape(todo["description"])}</div>' if todo.get("description") else ""
    css_class = "done" if todo["completed"] else ""
    return (
        f'<div class="{css_class}"><div class="todo-title">{escape(todo["title"])}</div>'
        f'{desc}<div class="todo-meta">{"".join(chips)}</div></div>'
    )


# ==========================================================================
# 3. DIALOGS  (modal pop-ups used by UPDATE and DELETE)
# ==========================================================================
@st.dialog("Edit task")
def edit_dialog(todo: dict) -> None:
    """UPDATE: pre-filled form in a modal."""
    with st.form("edit_form", border=False):
        title = st.text_input("Title", value=todo["title"])
        description = st.text_area("Description", value=todo.get("description", ""))
        col1, col2 = st.columns(2)
        priority = col1.selectbox("Priority", PRIORITIES, index=PRIORITIES.index(todo["priority"]))
        category = col2.text_input("Category", value=todo.get("category", ""))
        due = st.date_input(
            "Due date", value=todo["due_date"].date() if todo.get("due_date") else None
        )
        saved = st.form_submit_button("Save changes", type="primary", use_container_width=True)

    if saved:
        if not title.strip():
            st.error("A task needs a title.")
            return
        db.update_todo(str(todo["_id"]), title, description, priority, category, due)
        flash("Changes saved")
        st.rerun()


@st.dialog("Please confirm")
def confirm_dialog(message: str, confirm_label: str, on_confirm) -> None:
    """DELETE: generic confirmation modal. `on_confirm` runs only if confirmed."""
    st.write(message)
    col1, col2 = st.columns(2)
    if col1.button(confirm_label, type="primary", use_container_width=True):
        on_confirm()
        st.rerun()
    if col2.button("Cancel", use_container_width=True):
        st.rerun()


# ==========================================================================
# 4. CREATE
# ==========================================================================
def render_add_form() -> None:
    """Collapsible form that inserts a new todo."""
    with st.expander("➕  Add a task", expanded=db_is_empty()):
        with st.form("add_form", clear_on_submit=True, border=False):
            title = st.text_input("Title", placeholder="What needs doing?")
            description = st.text_area("Description (optional)", height=80)
            col1, col2, col3 = st.columns(3)
            priority = col1.selectbox("Priority", PRIORITIES, index=1)
            category = col2.text_input("Category", placeholder="Work, Home...")
            due = col3.date_input("Due date", value=None)
            submitted = st.form_submit_button("Add task", type="primary")

        if submitted:
            if not title.strip():
                st.warning("Give the task a title first.")
            else:
                db.create_todo(title, description, priority, category, due)
                flash("Task added")
                st.rerun()


def db_is_empty() -> bool:
    """Expand the add form automatically for a brand-new, empty list."""
    return db.get_stats()["total"] == 0


# ==========================================================================
# 5. READ  (filters + list) with inline UPDATE (toggle) and DELETE buttons
# ==========================================================================
def toggle_done(todo_id: str) -> None:
    """UPDATE callback for the checkbox: flips the completed flag."""
    db.set_completed(todo_id, st.session_state[f"done_{todo_id}"])


def render_filters() -> tuple[str, str, str, str]:
    """Search / filter / sort controls. Returns the chosen values."""
    search = st.text_input(
        "Search", placeholder="Search tasks...", label_visibility="collapsed"
    )
    c1, c2, c3 = st.columns(3)
    status = c1.selectbox("Status", ["All", "Open", "Completed"])
    priority = c2.selectbox("Priority", ["Any"] + PRIORITIES)
    sort_by = c3.selectbox("Sort by", ["Newest", "Oldest", "Due date", "Priority"])
    return status, priority, search, sort_by


def render_todo(todo: dict) -> None:
    """One todo card: checkbox | text | edit | delete."""
    todo_id = str(todo["_id"])
    with st.container(border=True):
        c_check, c_body, c_edit, c_del = st.columns([1, 12, 1, 1], vertical_alignment="center")

        with c_check:
            st.markdown('<span class="row-marker"></span>', unsafe_allow_html=True)  # CSS hook
            st.checkbox(
                "Done", value=todo["completed"], key=f"done_{todo_id}",
                on_change=toggle_done, args=(todo_id,), label_visibility="collapsed",
            )
        c_body.markdown(todo_html(todo), unsafe_allow_html=True)

        if c_edit.button("", icon=":material/edit:", key=f"edit_{todo_id}", type="tertiary", help="Edit"):
            edit_dialog(todo)

        if c_del.button("", icon=":material/delete:", key=f"del_{todo_id}", type="tertiary", help="Delete"):
            def _delete(tid=todo_id):
                db.delete_todo(tid)
                flash("Task deleted", "🗑️")

            confirm_dialog(f"Delete “{todo['title']}”? This can't be undone.", "Delete", _delete)


def render_todo_list(todos: list[dict], filtered: bool) -> None:
    """READ: render every todo, or a friendly empty state."""
    if not todos:
        message = (
            ("No matching tasks", "Try a different search or clear the filters.")
            if filtered
            else ("Nothing here yet", "Add your first task above to get started.")
        )
        st.markdown(f'<div class="empty"><b>{message[0]}</b>{message[1]}</div>', unsafe_allow_html=True)
        return

    for todo in todos:
        render_todo(todo)


def render_clear_completed() -> None:
    """DELETE (bulk): remove all completed tasks at once."""
    done = db.get_stats()["done"]
    if done and st.button(f"Clear {done} completed", icon=":material/done_all:"):
        def _clear():
            count = db.delete_completed()
            flash(f"Removed {count} completed task{'s' if count != 1 else ''}", "🧹")

        confirm_dialog(f"Delete all {done} completed tasks?", "Clear them", _clear)


# ==========================================================================
# 6. MAIN
# ==========================================================================
def main() -> None:
    # Show any toast queued by the previous run.
    if "flash" in st.session_state:
        message, icon = st.session_state.pop("flash")
        st.toast(message, icon=icon)

    st.markdown('<h1 class="app-title">Tasks</h1>', unsafe_allow_html=True)
    st.markdown('<p class="app-sub">Plan it, tick it off, move on.</p>', unsafe_allow_html=True)

    # Connect once; show a helpful message instead of a stack trace on failure.
    try:
        db.get_collection()
    except Exception as exc:
        st.error(
            "Couldn't connect to MongoDB. Check `.streamlit/secrets.toml` and that your "
            "IP address is allowed under *Network Access* in Atlas."
        )
        st.caption(f"Details: {exc}")
        st.stop()

    render_stats()
    render_add_form()

    status, priority, search, sort_by = render_filters()
    filtered = status != "All" or priority != "Any" or bool(search.strip())
    render_todo_list(db.get_todos(status, priority, search, sort_by), filtered)
    render_clear_completed()


main()