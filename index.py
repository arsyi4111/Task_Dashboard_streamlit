import streamlit as st
import pandas as pd
import psycopg2
import datetime
import os
import plotly.express as px
from streamlit_modal import Modal
import base64
from datetime import date

st.set_page_config(page_title="Team Activity Dashboard", layout="wide")

# Database connection settings
DB_HOST = st.secrets["DB_HOST"]
DB_NAME = st.secrets["DB_NAME"]
DB_USER = st.secrets["DB_USER"]
DB_PASS = st.secrets["DB_PASS"]

def connect_db():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )



# Function to encode image to Base64
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Get Base64 version of the background image
bg_image_base64 = get_base64_image("element/pospay_bg.webp")

# Apply background using CSS
st.markdown(f"""
    <style>
    body {{
        background-image: url("data:image/webp;base64,{bg_image_base64}");
        background-size: 50%;
        background-position: center top;  /* Align the image */
        background-repeat: no-repeat;
        background-attachment: fixed;
        opacity: 0.9;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- STYLING ---
st.markdown(
    """
    <style>
        .header-box {
            background-color: #1c2d5a;  /* Main brand blue */
            padding: 20px;
            border-radius: 12px;
            color: white;
            text-align: center;
            font-size: 30px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .corner-accent::before {
            content: "";
            position: fixed;
            top: 0;
            right: 0;
            width: 100px;
            height: 100px;
            background-color: #1c2d5a; /* Brand blue */
            clip-path: polygon(100% 0, 0 0, 100% 100%);
        }
        .subheader-box {
            background-color: #ef4123; /* Accent vivid red */
            padding: 10px;
            border-radius: 8px;
            color: white;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .metric-box {
            background-color: #f9f9f9;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 10px;
        }
        .metric-box h3 {
            margin: 0;
            font-size: 20px;
            color: #1c2d5a; /* Brand blue */
        }
        .metric-box p {
            margin: 0;
            font-size: 16px;
            color: #ef4123; /* Accent */
        }
        .alert-box {
            background-color: #fdeaea;  /* Light red background */
            color: #dc2626;             /* Standard alert red */
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 10px;
            border: 1px solid #dc2626;
        }
    </style>
    <div class='corner-accent'></div>
    <div class='header-box'>📌 Team Activity Dashboard</div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    /* Global font */
    html, body, [class*="css"]  {
        font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', sans-serif;
        color: #1c2d5a;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        font-weight: 600;
        color: #1c2d5a;
    }

    /* Primary buttons */
    .stButton button {
        background-color: #1c2d5a;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6em 1.2em;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #142046;
    }

    /* Accent highlights (brand red #ef4123) */
    .st-emotion-cache-1v0mbdj p, .accent-text {
        color: #ef4123 !important;
        font-weight: 600;
    }

    /* Warning or error messages */
    .stAlert {
        border-left: 6px solid red !important;
        border-radius: 6px;
    }

    /* Metric boxes */
    [data-testid="stMetric"] {
        background-color: #f9fafc;
        border: 1px solid #e5e7eb;
        border-left: 5px solid #1c2d5a;
        padding: 1em;
        border-radius: 12px;
        margin: 0.5em 0;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1c2d5a;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] p {
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# --- COUNTDOWN TO EOM & EOY ---
today = datetime.date.today()
end_of_month = datetime.date(today.year, today.month + 1, 1) - datetime.timedelta(days=1) if today.month < 12 else datetime.date(today.year, 12, 31)
end_of_year = datetime.date(today.year, 12, 31)

days_to_eom = (end_of_month - today).days
days_to_eoy = (end_of_year - today).days

col1, col2 = st.columns(2)
col1.markdown(f"<div class='metric-box'><h3>Days to End of Month</h3><p>{days_to_eom}</p></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='metric-box'><h3>Days to End of Year</h3><p>{days_to_eoy}</p></div>", unsafe_allow_html=True)

def load_tasks():
    try:
        # Try DB connection first
        conn = connect_db()
        query = "SELECT * FROM tasks;"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.warning(f"⚠️ Using fallback CSV because DB connection failed: {e}")
        # Load local CSV instead
        return pd.read_csv("task.csv")

def load_csv():
    return pd.read_csv("task.csv")

tasks_df = load_tasks()

# Ensure dates are in datetime format
tasks_df["start_date"] = pd.to_datetime(tasks_df["start_date"], errors="coerce",dayfirst=True).dt.date
tasks_df["due_date"] = pd.to_datetime(tasks_df["due_date"], errors="coerce",dayfirst=True).dt.date

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
st.markdown("<div class='subheader-box'>📊 Task Overview</div>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

# Task status count
status_counts = tasks_df["status"].value_counts()
total_tasks = len(tasks_df)
completed = status_counts.get("Completed", 0)
in_progress = status_counts.get("In Progress", 0)
not_started = status_counts.get("Not Started", 0)

col1.markdown(f"<div class='metric-box'><h3>📌 Total Tasks</h3><p>{total_tasks}</p></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='metric-box'><h3>✅ Completed</h3><p>{completed}</p></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='metric-box'><h3>⚙️ In Progress</h3><p>{in_progress}</p></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='metric-box'><h3>🚧 Not Started</h3><p>{not_started}</p></div>", unsafe_allow_html=True)

# --- GRAPHS ---
st.markdown("<div class='subheader-box'>📈 Task Statistics</div>", unsafe_allow_html=True)
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

# --- ALERT SECTION ---
today = datetime.date.today()
one_week_from_now = today + datetime.timedelta(days=7)

# Count tasks close to deadline
close_to_deadline_df = tasks_df[
    (pd.to_datetime(tasks_df["due_date"], dayfirst=True).dt.date >= today) & 
    (pd.to_datetime(tasks_df["due_date"], dayfirst=True).dt.date <= one_week_from_now) & 
    (tasks_df["status"].isin(["Not Started", "In Progress"]))
]
close_to_deadline = close_to_deadline_df.shape[0]

# Count overdue tasks
overdue_tasks_df = tasks_df[
    (pd.to_datetime(tasks_df["due_date"], dayfirst=True).dt.date < today) & 
    (tasks_df["status"] != "Completed")
]
overdue_tasks = overdue_tasks_df.shape[0]

# Count unconfirmed tasks
unconfirmed_tasks_df = tasks_df[
    (tasks_df["assigned_unit"].isna() | tasks_df["due_date"].isna()) & 
    (tasks_df["status"] != "Completed")
]
unconfirmed_tasks = unconfirmed_tasks_df.shape[0]

# Generate alert message
close_to_deadline_tasks = "<br>".join([f"{row['task_name']} ({row['assigned_unit']}) ({row['status']}) ({row['due_date']})" for _, row in close_to_deadline_df.iterrows()])
overdue_tasks_list = "<br>".join([f"{row['task_name']} ({row['assigned_unit']})" for _, row in overdue_tasks_df.iterrows()])
unconfirmed_tasks_list = "<br>".join([f"{row['task_name']} ({row['assigned_unit']})" for _, row in unconfirmed_tasks_df.iterrows()])

st.markdown(f"""
    <div class='alert-box'>
        <strong>⚠️ Alert:</strong><br>
        <strong>Tasks close to deadline:</strong> {close_to_deadline}<br>
        {close_to_deadline_tasks if close_to_deadline_tasks else "None"}<br><br>
        <strong>Overdue tasks:</strong> {overdue_tasks}<br>
        {overdue_tasks_list if overdue_tasks_list else "None"}<br><br>
        <strong>Unconfirmed tasks (Please add Assigned Unit and Due Date):</strong> {unconfirmed_tasks}<br>
        {unconfirmed_tasks_list if unconfirmed_tasks_list else "None"}
    </div>
""", unsafe_allow_html=True)

# --- FILTER SECTION ---
st.sidebar.header("🔎 Filter Tasks")

# Search bar for task name
search_query = st.sidebar.text_input("Search Task Name", "")

# Multiselect for unit filter
distinct_units = sorted(set(tasks_expanded_df["expanded_unit"].unique()))
unit_filter = st.sidebar.multiselect("Filter by Assigned Unit", options=distinct_units, default=distinct_units)

# Multiselect for status filter
status_filter = st.sidebar.multiselect("Filter by Status", options=tasks_df["status"].unique(), default=tasks_df["status"].unique())

# Apply filters
filtered_df = tasks_df[
    (tasks_df["status"].isin(status_filter)) & 
    (tasks_df["assigned_unit"].apply(lambda x: any(unit in x for unit in unit_filter))) & 
    (tasks_df["task_name"].str.contains(search_query, case=False, na=False))  # Case-insensitive search
]

import datetime
import plotly.express as px

# Ensure dates are in datetime format and handle missing values
filtered_df["start_date"] = pd.to_datetime(filtered_df["start_date"], errors="coerce",dayfirst=True)
filtered_df["due_date"] = pd.to_datetime(filtered_df["due_date"], errors="coerce",dayfirst=True)

# Replace missing start dates with today's date
filtered_df["start_date"].fillna(pd.Timestamp(year=2025, month=2, day=1), inplace=True)

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
subtasks_df["start_date"] = pd.to_datetime(subtasks_df["start_date"], errors="coerce",dayfirst=True)
subtasks_df["end_date"] = pd.to_datetime(subtasks_df["end_date"], errors="coerce",dayfirst=True)

# --- TASK DETAILS MODAL ---
def show_task_details(task):
    modal = Modal("Task Details", key=f"modal_{task['id']}")
    with modal.container():
        st.write(f"**Task Name:** {task['task_name']}")
        st.write(f"**Assigned Unit:** {task['assigned_unit']}")
        st.write(f"**Start Date:** {task['start_date'].strftime('%d/%m/%Y')}")
        st.write(f"**Due Date:** {task['due_date'].strftime('%d/%m/%Y') if pd.notna(task['due_date']) else 'TBC'}")
        st.write(f"**Tindak Lanjut:** {task['follow_up']}")

        st.write("### ✅ Completed Activities")
        st.markdown(task["completed_activities"] if task["completed_activities"] else "None", unsafe_allow_html=True)

        st.write("### ⏳ Pending Activities")
        st.markdown(task["pending_activities"] if task["pending_activities"] else "None", unsafe_allow_html=True)

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

def update_task_in_db(task_id, new_task_name, new_assigned_unit, new_start_date, new_due_date, new_status, new_follow_up, new_completed_activities, new_pending_activities):
    query = """
    UPDATE tasks 
    SET task_name = %s, assigned_unit = %s, start_date = %s, due_date = %s, status = %s, follow_up = %s, completed_activities = %s, pending_activities = %s
    WHERE id = %s
    """
    values = (new_task_name, new_assigned_unit, new_start_date, new_due_date, new_status, new_follow_up, new_completed_activities, new_pending_activities, task_id)

    print("🔍 SQL Query:", query)
    print("🔍 Values:", values)  # Debugging output

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Task updated successfully!")
        return True  # Indicate success
    except Exception as e:
        print("❌ Error updating task:", e)
        return False  # Indicate failure

def execute_db_query(query, values=()):
    conn = connect_db()  # Update with your actual DB path
    cursor = conn.cursor()
    cursor.execute(query, values)
    conn.commit()
    conn.close()    

import io

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Tasks")
    return output.getvalue()

import streamlit as st
import pandas as pd
from datetime import date

def render_task_table(filtered_df):
    # CSS untuk style border di setiap cell
    st.markdown("""
        <style>
        .task-header, .task-cell {
            border: 1px solid #ccc;
            padding: 6px;
            text-align: left;
            vertical-align: middle;
        }
        .task-header {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='subheader-box'>📋 Task List</div>", unsafe_allow_html=True)

    # 📥 Download + Sorting
    colA, colB, colC = st.columns([1, 1, 1])
    with colA:
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(label="📥 Download CSV", data=csv_data, file_name="tasks.csv", mime="text/csv")

    with colC:
        sort_option = st.selectbox("Sort by", ["Task Name", "Assigned Unit", "Due Date", "Status"], index=2)

    # Apply Sorting
    if sort_option == "Task Name":
        filtered_df = filtered_df.sort_values(by="task_name", ascending=True)
    elif sort_option == "Assigned Unit":
        filtered_df = filtered_df.sort_values(by="assigned_unit", ascending=True)
    elif sort_option == "Due Date":
        filtered_df = filtered_df.sort_values(by="due_date", ascending=True, na_position="last")
    elif sort_option == "Status":
        status_order = {"Not Started": 0, "In Progress": 1, "Completed": 2}
        filtered_df = filtered_df.sort_values(by="status", key=lambda x: x.map(status_order))

    # === HEADER ===
    col0, col1, col2, col3, col4, col5, col6 = st.columns([0.4, 3, 2, 2, 2, 1, 1])
    col0.markdown("<div class='task-header'>No</div>", unsafe_allow_html=True)
    col1.markdown("<div class='task-header'>Task Name</div>", unsafe_allow_html=True)
    col2.markdown("<div class='task-header'>Assigned Unit</div>", unsafe_allow_html=True)
    col3.markdown("<div class='task-header'>Due Date</div>", unsafe_allow_html=True)
    col4.markdown("<div class='task-header'>Status</div>", unsafe_allow_html=True)
    col5.markdown("<div class='task-header'>Details</div>", unsafe_allow_html=True)
    col6.markdown("<div class='task-header'>Edit</div>", unsafe_allow_html=True)

    # === ROWS ===
    for i, (_, task) in enumerate(filtered_df.iterrows(), start=1):
        col0, col1, col2, col3, col4, col5, col6 = st.columns([0.4, 3, 2, 2, 2, 1, 1])

        # No
        col0.markdown(f"<div class='task-cell'>{i}</div>", unsafe_allow_html=True)

        # Task Name
        col1.markdown(f"<div class='task-cell'>{task['task_name']}</div>", unsafe_allow_html=True)
        # Assigned Unit
        col2.markdown(f"<div class='task-cell'>{task['assigned_unit']}</div>", unsafe_allow_html=True)

        # Due Date
        due_date = pd.to_datetime(task["due_date"], dayfirst=True).strftime('%d %B %Y') if pd.notna(task["due_date"]) else "TBC"
        col3.markdown(f"<div class='task-cell'>{due_date}</div>", unsafe_allow_html=True)

        # Status (berwarna)
        status_color = {"Completed": "green", "In Progress": "orange", "Not Started": "red"}.get(task["status"], "black")
        col4.markdown(f"<div class='task-cell' style='color:{status_color}'>{task['status']}</div>", unsafe_allow_html=True)

        # Tombol interaktif tetap Streamlit
        details_button = col5.button("Details", key=f"details_{task['id']}")
        if details_button:
            show_task_details(task)

        edit_button = col6.button("✏️ Edit", key=f"edit_{task['id']}")
        if edit_button:
            st.session_state[f"edit_mode_{task['id']}"] = True

        # Mode edit (sama seperti sebelumnya)...
        if st.session_state.get(f"edit_mode_{task['id']}", False):
            with st.form(f"edit_form_{task['id']}", clear_on_submit=True):
                # form isiannya tetap sama seperti sebelumnya
                new_task_name = st.text_input("Task Name", value=task["task_name"])
                assigned_units = ["Fund Distribution", "Payment", "Fronting", "MCFS", "Resya",
                                  "Marketing", "DGPS", "Product Management", "not assigned"]

                assigned_units_list = task["assigned_unit"].split(" & ") if task["assigned_unit"] else []
                new_assigned_unit = st.multiselect("Assigned Unit", assigned_units, default=assigned_units_list)
                new_assigned_unit_str = " & ".join(new_assigned_unit)

                default_start_date = pd.to_datetime(task["start_date"]).date() if pd.notna(task["start_date"]) else date.today()
                default_due_date = pd.to_datetime(task["due_date"]).date() if pd.notna(task["due_date"]) else date.today()
                new_start_date = st.date_input("Start Date", value=default_start_date)
                new_due_date = st.date_input("Due Date", value=default_due_date)

                new_status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"],
                                          index=["Not Started", "In Progress", "Completed"].index(task["status"]))
                new_follow_up = st.text_area("Tindak Lanjut", value=task["follow_up"])

                new_completed_activities = st.text_area("✅ Completed Activities", value=task.get("completed_activities", ""))
                new_pending_activities = st.text_area("⏳ Pending Activities", value=task.get("pending_activities", ""))

                colA, colB, colC = st.columns([1, 1, 1])
                with colA:
                    submitted = st.form_submit_button("Save Changes")
                with colC:
                    cancel = st.form_submit_button("Cancel")

            if submitted:
                update_task_in_db(
                    task["id"], new_task_name, new_assigned_unit_str, new_start_date,
                    new_due_date, new_status, new_follow_up, new_completed_activities, new_pending_activities
                )
                st.success("✅ Task updated successfully!")
                st.session_state[f"edit_mode_{task['id']}"] = False
                st.rerun()

            if cancel:
                st.session_state[f"edit_mode_{task['id']}"] = False
                st.rerun()


# Render Task Table
render_task_table(filtered_df)


from datetime import datetime

# 📅 Gantt Chart - Task Timeline
st.markdown("<div class='subheader-box'>📅 Task Timeline</div>", unsafe_allow_html=True)

# Sort the filtered_df by due date before creating the Gantt chart
filtered_df = filtered_df.sort_values(by=["due_date", "id"], ascending=[False, True])

fig_gantt = px.timeline(
    filtered_df,
    x_start="start_date",
    x_end="due_date",
    y="task_name",
    color="task_name",  # Assign unique colors to each task
    title="Task Timelines",
    labels={"task_name": "Task", "start_date": "Start", "due_date": "Due"},
)

# Make the Y-axis scrollable if too many tasks
fig_gantt.update_layout(
    showlegend=False,
    xaxis=dict(tickfont=dict(size=10)),
    margin=dict(l=10, r=10, t=30, b=30),
    yaxis=dict(side="left", automargin=True),  # Adjust left margin dynamically
)

fig_gantt.update_yaxes(categoryorder="total descending")  # Order tasks chronologically
fig_gantt.update_layout(showlegend=False)  # Hide legend since every task has a unique color

# Add a vertical line for today's date
today = datetime.today().strftime('%Y-%m-%d')  # Get today's date
fig_gantt.add_vline(x=today, line_width=2, line_dash="dash", line_color="red")  # Red dashed line

st.plotly_chart(fig_gantt, use_container_width=True)

import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
def add_task_to_db(task_id, task_name, assigned_unit, start_date, due_date, status, follow_up, completed_activities, pending_activities):
    query = """
    INSERT INTO tasks (id, task_name, assigned_unit, start_date, due_date, status, follow_up, completed_activities, pending_activities)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    values = (task_id, task_name, assigned_unit, start_date, due_date, status, follow_up, completed_activities, pending_activities)
    
    # Debugging logs before execution
    logging.debug(f"Executing Query: {query}")
    logging.debug(f"Query Values: {values}")
    
    execute_db_query(query, values)

# Store state of the form
if "show_form" not in st.session_state:
    st.session_state.show_form = False

# Toggle form visibility
if st.button("➕ Add Task"):
    st.session_state.show_form = True  # Keep form visible

# Only show the form when needed
if st.session_state.show_form:
    with st.form("add_task_form", clear_on_submit=True):
        task_name = st.text_input("Task Name")
        assigned_units = st.multiselect("Assigned Unit", ["Fund Distribution", "Payment", "Fronting", "MCFS", "Resya", "Marketing", "DGPS", "Product Management","not assigned"])
        assigned_unit_str = " & ".join(assigned_units)  # Join selected units with '&'
        start_date = st.date_input("Start Date", date.today())
        due_date = st.date_input("Due Date", date.today())
        status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"])
        follow_up = st.text_area("Tindak Lanjut")
        completed_activities = st.text_area("✅ Completed Activities")
        pending_activities = st.text_area("⏳ Pending Activities")
        
        colA, colB, colC = st.columns([1, 1, 1])
        with colA:
            submitted = st.form_submit_button("Add Task")
        with colC:
            cancel = st.form_submit_button("Cancel")
        
    if submitted:
        if not task_name.strip():
            st.error("⚠ Task Name is required!")
        elif not assigned_units:
            st.error("⚠ Assigned Unit is required!")
        else:
            new_task_id = int(tasks_df["id"].max() + 1) if not tasks_df.empty else 1

            new_task = pd.DataFrame([{
                "id": new_task_id,
                "task_name": task_name,
                "assigned_unit": assigned_unit_str,
                "start_date": start_date,
                "due_date": due_date,
                "status": status,
                "follow_up": follow_up,
                "completed_activities": completed_activities,
                "pending_activities": pending_activities
            }])

            # Update database
            add_task_to_db(new_task_id, task_name, assigned_unit_str, start_date, due_date, status, follow_up, completed_activities, pending_activities)
            st.success("✅ Task added successfully!")
            st.session_state.show_form = False
            st.rerun()
        
        if cancel:
            st.session_state.show_form = False
            st.rerun()

