import streamlit as st
import pandas as pd
import datetime
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import plotly.express as px
from streamlit_modal import Modal

st.set_page_config(page_title="Team Activity Dashboard", layout="wide")
# Load environment variables
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL)

# Load tasks from database
def load_tasks():
    return pd.read_sql("SELECT id, task_name, assigned_unit, start_date, due_date, status, completed_activities, pending_activities FROM tasks", engine)

# Streamlit UI
st.title("📌 Team Activity Dashboard")

# Load task data
tasks_df = load_tasks()

# Process multiple units
def expand_units(df):
    expanded_rows = []
    for _, row in df.iterrows():
        units = row["assigned_unit"].split(" & ")
        for unit in units:
            new_row = row.copy()
            new_row["expanded_unit"] = unit
            expanded_rows.append(new_row)
    return pd.DataFrame(expanded_rows)

tasks_expanded_df = expand_units(tasks_df)

# --- TOP ROW WITH METRICS ---
st.subheader("📊 Task Overview")
col1, col2, col3, col4 = st.columns(4)  # Now 4 columns

# Task status count
status_counts = tasks_df["status"].value_counts()
total_tasks = len(tasks_df)  # Total number of tasks
completed = status_counts.get("Completed", 0)
in_progress = status_counts.get("In Progress", 0)
not_started = status_counts.get("Not Started", 0)  # Assuming "Not Started" is the correct label

col1.metric("📌 Total Tasks", total_tasks)
col2.metric("✅ Completed", completed)
col3.metric("⚙️ In Progress", in_progress)
col4.metric("🚧 Not Started", not_started)  # Updated from "Pending"

# --- GRAPHS ---
st.subheader("📈 Task Statistics")
col1, col2 = st.columns(2)

# 📊 Pie Chart - Task Distribution
fig_pie = px.pie(
    names=status_counts.index,
    values=status_counts.values,
    title="Task Distribution by Status",
    color_discrete_sequence=px.colors.qualitative.Safe  # Optional: Add a donut style
)

# Show both percentage and count
fig_pie.update_traces(textinfo="label+percent+value")  

col1.plotly_chart(fig_pie, use_container_width=True)

# Aggregate the task count for each unit-status combination
tasks_grouped_df = tasks_expanded_df.groupby(["expanded_unit", "status"]).size().reset_index(name="task_count")

# 📊 Bar Chart - Tasks by Assigned Unit
fig_bar = px.bar(
    tasks_grouped_df,
    x="expanded_unit",
    y="task_count",  # Use the aggregated count
    color="status",
    title="Tasks by Assigned Unit",
    barmode="group",
    text="task_count",  # Show the actual count on the bars
    color_discrete_map={
        "Completed": "green",
        "In Progress": "orange",
        "Pending": "red"
    }
).update_layout(
    xaxis_title="Divisi",
    yaxis_title="Jumlah"
)

col2.plotly_chart(fig_bar, use_container_width=True)


# --- FILTER SECTION ---
st.sidebar.header("🔎 Filter Tasks")
status_filter = st.sidebar.multiselect("Filter by Status", options=tasks_df["status"].unique(), default=tasks_df["status"].unique())

# Unique unit filter options
distinct_units = sorted(set(tasks_expanded_df["expanded_unit"].unique()))
unit_filter = st.sidebar.multiselect("Filter by Assigned Unit", options=distinct_units, default=distinct_units)

# Define custom sorting order for status
status_order = {"Not Started": 0, "In Progress": 1, "Completed": 2}

# Apply filters
filtered_df = tasks_df[
    (tasks_df["status"].isin(status_filter)) &  # Status filter
    (tasks_df["assigned_unit"].apply(lambda x: any(unit in x for unit in unit_filter)))  # Unit filter
]

# Apply sorting
filtered_df["status_order"] = filtered_df["status"].map(status_order)
filtered_df = filtered_df.sort_values(by=["status_order", "id"]).drop(columns=["status_order"])


def show_task_details(task):
    modal = Modal("Task Details", key=f"modal_{task['id']}")
    with modal.container():
        st.write(f"**Task Name:** {task['task_name']}")
        st.write(f"**Assigned Unit:** {task['assigned_unit']}")
        st.write(f"**Start Date:** {task['start_date']}")
        st.write(f"**Due Date:** {task['due_date']}")
        
        st.write("### ✅ Completed Activities")
        completed_activities = task["completed_activities"]
        if completed_activities:
            st.markdown(completed_activities.replace('\n', '<br>'), unsafe_allow_html=True)
        else:
            st.write("None")

        st.write("### ⏳ Pending Activities")
        pending_activities = task["pending_activities"]
        if pending_activities:
            st.markdown(pending_activities.replace('\n', '<br>'), unsafe_allow_html=True)
        else:
            st.write("None")

# Display task table with action buttons
# Display filtered task table
def render_task_table(filtered_df):
    st.write("### 📋 Task List")
    
    col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 2, 1])
    col1.write("**Task Name**")
    col2.write("**Assigned Unit**")
    col3.write("**Start Date**")
    col4.write("**Due Date**")
    col5.write("**Status**")
    col6.write("**Actions**")

    for _, task in filtered_df.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 2, 1])
        col1.write(task["task_name"])
        col2.write(task["assigned_unit"])  # Keep original format
        col3.write(task["start_date"])
        col4.write(task["due_date"])
        col5.write(task["status"])
        
        action_button = col6.button("Details", key=f"btn_{task['id']}")
        if action_button:
            show_task_details(task)

# Call function with the filtered DataFrame
render_task_table(filtered_df)


# --- ADD TASK BUTTON ---
if st.button("➕ Add Task"):
    with st.form("add_task_form", clear_on_submit=True):
        task_name = st.text_input("Task Name")
        assigned_unit = st.text_input("Assigned Unit (Use ' & ' for multiple units)")
        start_date = st.date_input("Start Date", datetime.date.today())
        due_date = st.date_input("Due Date", datetime.date.today())
        status = st.selectbox("Status", ["Pending", "In Progress", "Completed"])
        
        if st.form_submit_button("Add Task"):
            with engine.connect() as conn:
                query = text("""
                    INSERT INTO tasks (task_name, assigned_unit, start_date, due_date, status, completed_activities, pending_activities)
                    VALUES (:task_name, :assigned_unit, :start_date, :due_date, :status, '', '')
                """)
                conn.execute(query, {
                    "task_name": task_name,
                    "assigned_unit": assigned_unit,
                    "start_date": start_date,
                    "due_date": due_date,
                    "status": status
                })
                conn.commit()
                st.success("Task added successfully!")
                st.experimental_rerun()
