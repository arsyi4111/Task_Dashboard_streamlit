import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
from streamlit_modal import Modal

st.set_page_config(page_title="Team Activity Dashboard", layout="wide")

TASK_FILE = "task.csv"  # Define the CSV file path

# --- LOAD & SAVE TASKS ---
def load_tasks():
    if os.path.exists(TASK_FILE):
        return pd.read_csv(TASK_FILE)
    else:
        return pd.DataFrame(columns=["id", "task_name", "assigned_unit", "start_date", "due_date", "status", "completed_activities", "pending_activities"])

def save_tasks(df):
    df.to_csv(TASK_FILE, index=False)

# Load task data
tasks_df = load_tasks()

# Expand multiple units
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
col1, col2, col3, col4 = st.columns(4)

# Task status count
status_counts = tasks_df["status"].value_counts()
total_tasks = len(tasks_df)
completed = status_counts.get("Completed", 0)
in_progress = status_counts.get("In Progress", 0)
not_started = status_counts.get("Not Started", 0)

col1.metric("📌 Total Tasks", total_tasks)
col2.metric("✅ Completed", completed)
col3.metric("⚙️ In Progress", in_progress)
col4.metric("🚧 Not Started", not_started)

# --- GRAPHS ---
st.subheader("📈 Task Statistics")
col1, col2 = st.columns(2)

# 📊 Pie Chart - Task Distribution
fig_pie = px.pie(
    names=status_counts.index,
    values=status_counts.values,
    title="Task Distribution by Status",
    color_discrete_sequence=px.colors.qualitative.Safe
)
fig_pie.update_traces(textinfo="label+percent+value")  
col1.plotly_chart(fig_pie, use_container_width=True)

# 📊 Bar Chart - Tasks by Assigned Unit
tasks_grouped_df = tasks_expanded_df.groupby(["expanded_unit", "status"]).size().reset_index(name="task_count")

fig_bar = px.bar(
    tasks_grouped_df,
    x="expanded_unit",
    y="task_count",
    color="status",
    title="Tasks by Assigned Unit",
    barmode="group",
    text="task_count",
    color_discrete_map={"Completed": "green", "In Progress": "orange", "Not Started": "red"}
).update_layout(
    xaxis_title="Divisi",
    yaxis_title="Jumlah"
)

col2.plotly_chart(fig_bar, use_container_width=True)



# --- FILTER SECTION ---
st.sidebar.header("🔎 Filter Tasks")
status_filter = st.sidebar.multiselect("Filter by Status", options=tasks_df["status"].unique(), default=tasks_df["status"].unique())

distinct_units = sorted(set(tasks_expanded_df["expanded_unit"].unique()))
unit_filter = st.sidebar.multiselect("Filter by Assigned Unit", options=distinct_units, default=distinct_units)

status_order = {"Not Started": 0, "In Progress": 1, "Completed": 2}

# Apply filters
filtered_df = tasks_df[
    (tasks_df["status"].isin(status_filter)) &
    (tasks_df["assigned_unit"].apply(lambda x: any(unit in x for unit in unit_filter)))
]

filtered_df["status_order"] = filtered_df["status"].map(status_order)
filtered_df = filtered_df.sort_values(by=["status_order", "id"]).drop(columns=["status_order"])

import datetime
import plotly.express as px

# Ensure dates are in datetime format and handle missing values
filtered_df["start_date"] = pd.to_datetime(filtered_df["start_date"], errors="coerce")
filtered_df["due_date"] = pd.to_datetime(filtered_df["due_date"], errors="coerce")

# Replace missing start dates with today's date
filtered_df["start_date"].fillna(pd.Timestamp.today(), inplace=True)

# Replace missing due dates with None (so it appears as ongoing)
filtered_df["due_date"] = filtered_df["due_date"].apply(lambda x: x if pd.notna(x) else None)

# --- TASK DETAILS ---
# --- LOAD SUBTASKS ---
SUBTASK_FILE = "subtask.csv"

def load_subtasks():
    if os.path.exists(SUBTASK_FILE):
        return pd.read_csv(SUBTASK_FILE)
    else:
        return pd.DataFrame(columns=["id", "task_id", "sub_task", "start_date", "end_date"])

subtasks_df = load_subtasks()

# Ensure dates are in datetime format
subtasks_df["start_date"] = pd.to_datetime(subtasks_df["start_date"], errors="coerce")
subtasks_df["end_date"] = pd.to_datetime(subtasks_df["end_date"], errors="coerce")

# --- TASK DETAILS MODAL ---
def show_task_details(task):
    modal = Modal("Task Details", key=f"modal_{task['id']}")
    with modal.container():
        st.write(f"**Task Name:** {task['task_name']}")
        st.write(f"**Assigned Unit:** {task['assigned_unit']}")
        st.write(f"**Start Date:** {task['start_date'].strftime('%d/%m/%Y')}")
        st.write(f"**Due Date:** {task['due_date'].strftime('%d/%m/%Y') if pd.notna(task['due_date']) else 'Ongoing'}")

        # ✅ Completed & Pending Activities
        st.write("### ✅ Completed Activities")
        completed_activities = task["completed_activities"]
        st.markdown(completed_activities if completed_activities else "None", unsafe_allow_html=True)

        st.write("### ⏳ Pending Activities")
        pending_activities = task["pending_activities"]
        st.markdown(pending_activities if pending_activities else "None", unsafe_allow_html=True)

        # 📅 Subtask Gantt Chart
        st.write("### 📅 Subtask Timeline")
        task_subtasks = subtasks_df[subtasks_df["task_id"] == task["id"]]

        if not task_subtasks.empty:
            task_subtasks["start_date"] = task_subtasks["start_date"].dt.strftime('%d/%m/%Y')
            task_subtasks["end_date"] = task_subtasks["end_date"].dt.strftime('%d/%m/%Y')

            fig_sub_gantt = px.timeline(
                task_subtasks,
                x_start="start_date",
                x_end="end_date",
                y="sub_task",
                color="sub_task",
                title="Subtask Timelines",
                labels={"sub_task": "Subtask", "start_date": "Start", "end_date": "End"},
            )

            fig_sub_gantt.update_yaxes(categoryorder="total ascending")
            fig_sub_gantt.update_layout(showlegend=False)

            st.plotly_chart(fig_sub_gantt, use_container_width=True)
        else:
            st.write("No subtasks available for this task.")


# --- TASK LIST TABLE ---
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
        col2.write(task["assigned_unit"])
        col3.write(task["start_date"])
        col4.write(task["due_date"])
        col5.write(task["status"])
        
        action_button = col6.button("Details", key=f"btn_{task['id']}")
        if action_button:
            show_task_details(task)

# Render Task Table
render_task_table(filtered_df)

# 📅 Gantt Chart - Task Timeline
st.subheader("📅 Task Timeline")

fig_gantt = px.timeline(
    filtered_df,
    x_start="start_date",
    x_end="due_date",
    y="task_name",
    color="task_name",  # Assign unique colors to each task
    title="Task Timelines",
    labels={"task_name": "Task", "start_date": "Start", "due_date": "Due"},
)

fig_gantt.update_yaxes(categoryorder="total ascending")  # Order tasks chronologically
fig_gantt.update_layout(showlegend=False)  # Hide legend since every task has a unique color

st.plotly_chart(fig_gantt, use_container_width=True)


# --- ADD TASK FORM ---
if st.button("➕ Add Task"):
    with st.form("add_task_form", clear_on_submit=True):
        task_name = st.text_input("Task Name")
        assigned_unit = st.text_input("Assigned Unit (Use ' & ' for multiple units)")
        start_date = st.date_input("Start Date", datetime.date.today())
        due_date = st.date_input("Due Date", datetime.date.today())
        status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"])
        
        if st.form_submit_button("Add Task"):
            new_task = pd.DataFrame([{
                "id": tasks_df["id"].max() + 1 if not tasks_df.empty else 1,
                "task_name": task_name,
                "assigned_unit": assigned_unit,
                "start_date": start_date,
                "due_date": due_date,
                "status": status,
                "completed_activities": "",
                "pending_activities": ""
            }])

            tasks_df = pd.concat([tasks_df, new_task], ignore_index=True)
            save_tasks(tasks_df)
            st.success("Task added successfully!")
            st.experimental_rerun()
