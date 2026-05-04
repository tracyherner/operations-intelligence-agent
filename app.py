import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------------
st.set_page_config(
    page_title="Operations Intelligence Agent",
    page_icon="🧠",
    layout="wide"
)

# ---------------------------------------------------------
# CUSTOM STYLING
# ---------------------------------------------------------
st.markdown("""
<style>
.stApp { background-color: #f7f6ef; }
h1, h2, h3 { color: #115740; }

input[type="text"] {
    background-color: white !important;
    border: 2px solid #B9975B !important;
    border-radius: 12px !important;
    padding: 14px !important;
    color: #333 !important;
}

.main-card {
    background-color: white;
    padding: 24px;
    border-radius: 16px;
    border-top: 5px solid #B9975B;
    box-shadow: 0 3px 12px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

section[data-testid="stSidebar"] {
    background-color: #115740 !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] label {
    color: white !important;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
section[data-testid="stSidebar"] div[data-baseweb="input"] > div {
    border: 2px solid #B9975B !important;
    border-radius: 10px !important;
    background-color: white !important;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] span,
section[data-testid="stSidebar"] input {
    color: #333 !important;
}
/* Fix radio button text specifically */
section[data-testid="stSidebar"] div[role="radiogroup"] label p {
    color: white !important;
}

/* Make selected radio stand out */
section[data-testid="stSidebar"] input[type="radio"]:checked + div p {
    font-weight: 600;
    color: #B9975B !important;
}
/* Toggle + checkbox labels */
section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label p,
section[data-testid="stSidebar"] div[data-testid="stToggle"] label p {
    color: white !important;
}
            
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
employees = pd.read_csv("data/employees.csv")
availability = pd.read_csv("data/availability.csv")
tours = pd.read_csv("data/tours.csv")
events = pd.read_csv("data/events.csv")

# ---------------------------------------------------------
# SIDEBAR: MODE + SCENARIO SIMULATOR
# ---------------------------------------------------------
st.sidebar.header("Scenario Simulator")

mode_toggle = st.sidebar.toggle("✨ Agent Mode (ON = Auto, OFF = Scenario)", value=True)

if mode_toggle:
    mode = "✨ Agent (Auto)"
else:
    mode = "🧪 Scenario Planning"

selected_date = st.sidebar.selectbox(
    "Select Date",
    sorted(events["date"].unique())
)

# These are always needed
budget = st.sidebar.number_input("Labor Budget", 0, 2000, 600, 50)
shift_hours = st.sidebar.number_input("Shift Length", 1, 12, 6)

if mode == "🧪 Scenario Planning":
    st.sidebar.markdown("### Manual Forecast Overrides")

    expected_demand = st.sidebar.selectbox("Expected Demand", ["Low", "Normal", "High"])
    day_type = st.sidebar.selectbox("Day Type", ["Weekday", "Weekend", "Event Day"])
    weather_impact = st.sidebar.selectbox("Weather", ["Poor", "Normal", "Great"])
    tour_volume = st.sidebar.selectbox("Tour Volume", ["Low", "Normal", "High"])
    community_events = st.sidebar.selectbox("Community Events", ["None", "Small", "Large"])
    winery_events = st.sidebar.selectbox("Winery Events", ["None", "Small", "Large"])
    hotel_occupancy = st.sidebar.selectbox("Hotel Occupancy", ["Low", "Normal", "High"])

else:
    # Default assumptions when the system is running automatically
    expected_demand = "Normal"
    day_type = "Weekday"
    weather_impact = "Normal"
    tour_volume = "Normal"
    community_events = "None"
    winery_events = "None"
    hotel_occupancy = "Normal"

# ---------------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------------
def forecast_staffing_needs():
    """Forecast how many employees are needed by department."""
    plan = {
        "Retail": 2,
        "Tasting Room": 3,
        "Tours": 2,
        "Food Service": 1
    }

    if expected_demand == "High":
        plan["Retail"] += 1
        plan["Tasting Room"] += 1

    if day_type == "Weekend":
        plan["Tasting Room"] += 2

    if day_type == "Event Day":
        plan["Retail"] += 1
        plan["Tasting Room"] += 1
        plan["Food Service"] += 1

    if weather_impact == "Great":
        plan["Tasting Room"] += 1
        plan["Tours"] += 1

    if tour_volume == "High":
        plan["Tours"] += 1

    if community_events == "Large":
        plan["Retail"] += 1
        plan["Tasting Room"] += 1

    if winery_events == "Large":
        plan["Tasting Room"] += 1
        plan["Food Service"] += 1

    if hotel_occupancy == "High":
        plan["Tours"] += 1
        plan["Tasting Room"] += 1

    today_events = get_today_events(events, selected_date)

    for _, event in today_events.iterrows():
        impacted_department = event["department_impact"]

        if impacted_department in plan:
            plan[impacted_department] += 1

    return plan


def generate_schedule(plan):
    """Assign employees while avoiding double-booking and respecting certifications."""
    schedule = {}
    used = set()

    for dept, needed in plan.items():
        assigned = []

        for _, row in employees.iterrows():
            if len(assigned) < needed and row["name"] not in used:

                if dept == "Food Service" and row["servsafe_cert"] == "Yes":
                    assigned.append(row)
                    used.add(row["name"])

                elif dept != "Food Service" and row["abc_cert"] == "Yes":
                    assigned.append(row)
                    used.add(row["name"])

        schedule[dept] = assigned

    return schedule


def calculate_cost(schedule):
    """Estimate payroll using a simplified demo rate."""
    default_rate = 8
    return sum(len(staff) * shift_hours * default_rate for staff in schedule.values())


def show_staffing_plan(schedule, plan):
    """Display staffing plan by department."""
    for dept, staff in schedule.items():
        st.markdown(f"### {dept}")
        st.write(f"Required staff: **{plan[dept]}**")

        if staff:
            for person in staff:
                st.write(f"- {person['name']}")

        if len(staff) < plan[dept]:
            st.error(f"⚠️ Understaffed by {plan[dept] - len(staff)}")


def get_today_events(events_df, selected_date):
    """Filter scheduled events for the selected date."""
    return events_df[events_df["date"] == selected_date]


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.markdown("""
<div style="background:#115740;padding:16px 24px;border-radius:12px;color:white;">
<h2 style="margin-bottom:2px;color:white;">Operations Intelligence Agent</h2>
<h4 style="margin-top:0;color:#B9975B;">Agentic AI for Managerial Decision-Making</h4>
<p>Real-time insights for staffing, compliance, budgeting, and risk.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------
# SEARCH BAR
# ---------------------------------------------------------
query = st.text_input(
    "",
    placeholder="Ask: who is missing certifications? | staff this weekend | show summary"
)

if not query:
    st.info("Try: who is missing certifications? | staff this weekend | show summary")

# ---------------------------------------------------------
# SHARED CALCULATIONS
# ---------------------------------------------------------
staffing_plan_today = forecast_staffing_needs()
schedule_today = generate_schedule(staffing_plan_today)
cost_today = calculate_cost(schedule_today)

needed_today = sum(staffing_plan_today.values())
assigned_today = sum(len(staff) for staff in schedule_today.values())
shortage_today = needed_today - assigned_today
today_events = get_today_events(events, selected_date)

# ---------------------------------------------------------
# TABS
# ---------------------------------------------------------
tab_today, tab_agent, tab_dashboard, tab_data = st.tabs([
    "📊 Today",
    "🧠 Agent",
    "📈 Dashboard",
    "📂 Data"
])

# ---------------------------------------------------------
# TAB 1: TODAY
# ---------------------------------------------------------
with tab_today:
    st.markdown("## What's Happening Today?")
    if mode == "🤖 Agent (Auto)":
        st.success("Running in Agent Mode: staffing is based on scheduled events and system logic.")
    else:
        st.warning("Scenario Mode: manual inputs are overriding the automatic forecast.")

    if not today_events.empty:
        st.markdown("### 📅 Scheduled Events")
        for _, event in today_events.iterrows():
            st.write(
                f"• {event['event_name']} ({event['event_type']}) — "
                f"{event['expected_guests']} guests"
            )
    else:
        st.write("No scheduled events.")

    total_event_guests = today_events["expected_guests"].sum() if not today_events.empty else 0
    event_count = len(today_events)

    risk_level = "Low"
    risk_reason = "No major scheduled demand drivers."

    if total_event_guests >= 200 or event_count >= 3:
        risk_level = "High"
        risk_reason = "Multiple events or high expected guest volume may increase staffing pressure."
    elif total_event_guests >= 75 or event_count >= 1:
        risk_level = "Moderate"
        risk_reason = "Scheduled events may increase demand in one or more departments."

    st.markdown(
        f"""
        <div class="main-card">
            <h3>Today’s Operational Risk: {risk_level}</h3>
            <p>{risk_reason}</p>
            <p><strong>Total Event Guests:</strong> {total_event_guests}</p>
            <p><strong>Scheduled Events:</strong> {event_count}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    today1, today2, today3, today4 = st.columns(4)

    with today1:
        st.markdown(
            f"""<div class="main-card"><h3>Staff Needed</h3><h1>{needed_today}</h1></div>""",
            unsafe_allow_html=True
        )

    with today2:
        st.markdown(
            f"""<div class="main-card"><h3>Assigned</h3><h1>{assigned_today}</h1></div>""",
            unsafe_allow_html=True
        )

    with today3:
        st.markdown(
            f"""<div class="main-card"><h3>Shortage</h3><h1>{shortage_today}</h1></div>""",
            unsafe_allow_html=True
        )

    with today4:
        st.markdown(
            f"""<div class="main-card"><h3>Labor Cost</h3><h1>${cost_today}</h1></div>""",
            unsafe_allow_html=True
        )

    st.markdown(
        f"""
        <div class="main-card">
            <h3>Forecast Inputs Used</h3>
            <p><strong>Selected Date:</strong> {selected_date}</p>
            <p><strong>Expected Demand:</strong> {expected_demand}</p>
            <p><strong>Day Type:</strong> {day_type}</p>
            <p><strong>Weather:</strong> {weather_impact}</p>
            <p><strong>Tour Volume:</strong> {tour_volume}</p>
            <p><strong>Community Events:</strong> {community_events}</p>
            <p><strong>Winery Events:</strong> {winery_events}</p>
            <p><strong>Hotel Occupancy:</strong> {hotel_occupancy}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------------------------------------------------
# TAB 2: AGENT
# ---------------------------------------------------------
with tab_agent:
    st.markdown("## Agent Response")

    if query:
        query = query.lower()

        staffing_plan = staffing_plan_today
        schedule = schedule_today
        cost = cost_today

        if "cert" in query or "missing" in query:
            st.subheader("Certification Gaps")

            found_gap = False

            for _, row in employees.iterrows():
                issues = []

                if row["abc_cert"] == "No":
                    issues.append("ABC")
                if row["servsafe_cert"] == "No":
                    issues.append("ServSafe")

                if issues:
                    found_gap = True
                    st.write(f"- {row['name']} needs: {', '.join(issues)}")

            if not found_gap:
                st.success("No certification gaps found.")

        elif "staff" in query or "schedule" in query:
            st.subheader("Staffing Plan")
            show_staffing_plan(schedule, staffing_plan)

        elif "budget" in query or "cost" in query:
            st.subheader("Budget Analysis")
            st.write(f"Estimated Cost: **${cost}**")
            st.write(f"Budget: **${budget}**")

            if cost > budget:
                st.error(f"Over budget by ${cost - budget}")
            else:
                st.success("Within budget")

        elif "summary" in query or "overview" in query:
            st.subheader("Manager Summary")

            critical = []
            moderate = []

            for _, row in employees.iterrows():
                if row["abc_cert"] == "No":
                    critical.append(f"{row['name']} missing ABC certification")
                if row["servsafe_cert"] == "No":
                    moderate.append(f"{row['name']} missing ServSafe certification")

            for dept, staff in schedule.items():
                if len(staff) < staffing_plan[dept]:
                    critical.append(
                        f"{dept} understaffed by {staffing_plan[dept] - len(staff)}"
                    )

            st.write(f"Estimated Cost: **${cost}**")
            st.write(f"Budget: **${budget}**")

            if not today_events.empty:
                st.write(
                    f"Today's demand is influenced by {len(today_events)} scheduled event(s) "
                    f"with approximately {today_events['expected_guests'].sum()} expected guests."
                )

            if critical:
                st.error("Critical Issues")
                for item in critical:
                    st.write(f"- {item}")

            if moderate:
                st.warning("Moderate Issues")
                for item in moderate:
                    st.write(f"- {item}")

            st.subheader("One Priority / One Action")

            if critical:
                st.error(f"Priority: {critical[0]}")
                st.write("Action: Address this issue before lower-priority staffing changes.")
            elif cost > budget:
                st.error("Priority: Labor cost is over budget")
                st.write("Action: Review staffing assignments and reduce coverage only where service risk is low.")
            elif moderate:
                st.warning(f"Priority: {moderate[0]}")
                st.write("Action: Schedule training or cross-training.")
            else:
                st.success("Priority: Operations appear stable")
                st.write("Action: Maintain current plan and monitor demand.")

        else:
            st.write("Try asking about staffing, certifications, budget, or summary.")
    else:
        st.info("Ask a question in the search bar above to generate an agent response.")

# ---------------------------------------------------------
# TAB 3: DASHBOARD
# ---------------------------------------------------------
with tab_dashboard:
    st.markdown("## Operations Overview")

    total_employees = len(employees)
    abc_count = (employees["abc_cert"] == "Yes").sum()
    servsafe_count = (employees["servsafe_cert"] == "Yes").sum()

    card1, card2, card3 = st.columns(3)

    with card1:
        st.markdown(
            f"""<div class="main-card"><h3>Total Employees</h3><h1>{total_employees}</h1></div>""",
            unsafe_allow_html=True
        )

    with card2:
        st.markdown(
            f"""<div class="main-card"><h3>ABC Certified</h3><h1>{abc_count}</h1></div>""",
            unsafe_allow_html=True
        )

    with card3:
        st.markdown(
            f"""<div class="main-card"><h3>ServSafe Certified</h3><h1>{servsafe_count}</h1></div>""",
            unsafe_allow_html=True
        )

# ---------------------------------------------------------
# TAB 4: DATA
# ---------------------------------------------------------
with tab_data:
    st.markdown("## Data Tables")

    with st.expander("View Workforce Data"):
        st.dataframe(employees, use_container_width=True)

    with st.expander("View Availability Data"):
        st.dataframe(availability, use_container_width=True)

    with st.expander("View Tours Data"):
        st.dataframe(tours, use_container_width=True)

    with st.expander("View Events Data"):
        st.dataframe(events, use_container_width=True)