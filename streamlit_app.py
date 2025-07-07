import pandas as pd
import streamlit as st
from io import StringIO
import pytz
from datetime import datetime

# --- Config ---
CSV_FILE = "attendance_log.csv"
st.set_page_config(page_title="Zoom Attendance Dashboard", layout="wide")

# Load and clean data
columns = [
    "event_type", "name", "email", "join_time", "leave_time",
    "meeting_id", "topic", "timestamp"
]

try:
    df = pd.read_csv(CSV_FILE, names=columns)

    # Convert to datetime with UTC timezone
    df["join_time"] = pd.to_datetime(df["join_time"], utc=True, errors="coerce")
    df["leave_time"] = pd.to_datetime(df["leave_time"], utc=True, errors="coerce")

    # Convert to IST
    ist = pytz.timezone("Asia/Kolkata")
    df["join_time"] = df["join_time"].dt.tz_convert(ist)
    df["leave_time"] = df["leave_time"].dt.tz_convert(ist)

    # Combine join/leave by participant and meeting
    combined_df = df.pivot_table(
        index=["email", "name", "meeting_id", "topic"],
        values=["join_time", "leave_time"],
        aggfunc="first"
    ).reset_index()

    # Compute duration in minutes
    combined_df["duration_minutes"] = (
        (combined_df["leave_time"] - combined_df["join_time"]).dt.total_seconds() / 60
    ).round(1)

    # Format for display
    combined_df["Join Time"] = combined_df["join_time"].dt.strftime("%d %b %Y, %I:%M %p")
    combined_df["Leave Time"] = combined_df["leave_time"].dt.strftime("%d %b %Y, %I:%M %p")
    combined_df["date_only"] = combined_df["join_time"].dt.date

    # Sidebar Filters
    st.sidebar.title("🔍 Filters")

    # Participant filter
    unique_participants = ["All"] + sorted(combined_df["name"].dropna().unique().tolist())
    selected_participant = st.sidebar.selectbox("👤 Participant", unique_participants)

    # Topic filter
    unique_topics = ["All"] + sorted(combined_df["topic"].dropna().unique().tolist())
    selected_topic = st.sidebar.selectbox("🧾 Topic", unique_topics)

    # Date range filter
    min_date = combined_df["date_only"].min()
    max_date = combined_df["date_only"].max()
    start_date, end_date = st.sidebar.date_input("📅 Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

    # Refresh button
    if st.sidebar.button("🔄 Refresh"):
        st.rerun()

    # Apply filters
    filtered_df = combined_df.copy()
    if selected_participant != "All":
        filtered_df = filtered_df[filtered_df["name"] == selected_participant]
    if selected_topic != "All":
        filtered_df = filtered_df[filtered_df["topic"] == selected_topic]
    filtered_df = filtered_df[
        (filtered_df["date_only"] >= start_date) & (filtered_df["date_only"] <= end_date)
    ]

    # --- Main ---
    st.title("📊 Zoom Attendance Dashboard")

    # Download button
    csv_buffer = StringIO()
    export_cols = ["name", "email", "meeting_id", "topic", "Join Time", "Leave Time", "duration_minutes"]
    filtered_df[export_cols].to_csv(csv_buffer, index=False)
    st.download_button(
        label="⬇️ Download CSV",
        data=csv_buffer.getvalue(),
        file_name="filtered_attendance.csv",
        mime="text/csv",
    )

    # Display grouped by Meeting ID and Topic
    for (meeting_id, topic), group in filtered_df.groupby(["meeting_id", "topic"]):
        st.markdown(f"""
            <h3 style='margin-top: 40px;'>📝 Meeting ID: <code>{meeting_id}</code> — <b>{topic}</b></h3>
        """, unsafe_allow_html=True)

        display_df = group[["name", "email", "Join Time", "Leave Time", "duration_minutes"]].rename(columns={
            "name": "Name",
            "email": "Email",
            "duration_minutes": "Duration (mins)"
        })

        st.dataframe(display_df.style.set_properties(**{
            'font-size': '16px',
            'text-align': 'left'
        }))

except Exception as e:
    st.error(f"⚠️ Error loading data: {e}")
