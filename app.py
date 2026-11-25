
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import datetime as dt

from google import genai
from db import (
    create_table,
    add_transaction,
    get_transactions,
    update_transaction,
    delete_transaction
)

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="MONOGRAPH | Expense Tracker",
    page_icon="💰",
    layout="wide"
)

create_table()

# Gemini AI Configuration
client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)


# ==========================================
# BUDGET DATABASE FUNCTIONS
# ==========================================

def create_budget_table():

    conn = sqlite3.connect("expenses.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS monthly_budgets (
            month TEXT PRIMARY KEY,
            amount REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def get_monthly_budget(month):

    conn = sqlite3.connect("expenses.db")

    result = conn.execute(
        "SELECT amount FROM monthly_budgets WHERE month = ?",
        (month,)
    ).fetchone()

    conn.close()

    return result[0] if result else 0.0


def save_monthly_budget(month, amount):

    conn = sqlite3.connect("expenses.db")

    conn.execute("""
        INSERT OR REPLACE INTO monthly_budgets
        (month, amount)
        VALUES (?, ?)
    """, (month, amount))

    conn.commit()
    conn.close()


# ==========================================
# CATEGORY BUDGET DATABASE FUNCTIONS
# ==========================================

def save_category_budget(month, category, amount):

    conn = sqlite3.connect("expenses.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS category_budgets (
            month TEXT,
            category TEXT,
            amount REAL NOT NULL,
            PRIMARY KEY (month, category)
        )
    """)

    conn.execute("""
        INSERT OR REPLACE INTO category_budgets
        (month, category, amount)
        VALUES (?, ?, ?)
    """, (month, category, amount))

    conn.commit()
    conn.close()


def get_category_budgets(month):

    conn = sqlite3.connect("expenses.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS category_budgets (
            month TEXT,
            category TEXT,
            amount REAL NOT NULL,
            PRIMARY KEY (month, category)
        )
    """)

    result = conn.execute("""
        SELECT category, amount
        FROM category_budgets
        WHERE month = ?
    """, (month,)).fetchall()

    conn.close()

    return dict(result)


# Create budget table if it doesn't exist
create_budget_table()


# ==========================================
# EDITORIAL / SWISS DESIGN SYSTEM
# ==========================================


st.markdown("""
<style>

/* =====================================
   MONOGRAPH — EDITORIAL DESIGN SYSTEM
===================================== */

:root {
    --bg: #171715;
    --sidebar: #20201D;
    --card: #24241F;
    --card-hover: #2B2B24;
    --border: #414137;
    --text: #F3EEE3;
    --muted: #A7A396;
    --accent: #C9D68A;
    --accent-soft: #DDE7B2;
    --income: #AFC78C;
    --expense: #D17B57;
    --warning: #D6AE68;
}

/* MAIN BACKGROUND */

.stApp {
    background-color: var(--bg);
    color: var(--text);
}

.main .block-container {
    max-width: 1450px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
}

/* SIDEBAR */

[data-testid="stSidebar"] {
    background-color: var(--sidebar);
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 2rem;
}

[data-testid="stSidebar"] * {
    color: var(--text);
}

/* SIDEBAR NAVIGATION */

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 7px 9px;
    border-radius: 5px;
    transition: background 0.2s ease;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background-color: #303029;
}

[data-testid="stSidebar"] [role="radio"][aria-checked="true"] {
    color: var(--accent) !important;
}

[data-testid="stSidebar"] [role="radio"][aria-checked="true"] svg {
    color: var(--accent) !important;
    fill: var(--accent) !important;
}

/* HEADINGS */

h1, h2, h3 {
    color: var(--text) !important;
    letter-spacing: -1px;
}

h1 {
    font-weight: 800 !important;
}

h2, h3 {
    font-weight: 700 !important;
}

/* EDITORIAL TYPOGRAPHY */

.editorial-eyebrow {
    color: var(--accent);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 3px;
    margin-bottom: 25px;
}

.editorial-title {
    font-size: clamp(45px, 6vw, 65px);
    font-weight: 800;
    line-height: 1;
    letter-spacing: -3px;
    color: var(--text);
}

.editorial-italic {
    font-size: clamp(45px, 6vw, 65px);
    font-family: Georgia, serif;
    font-style: italic;
    color: var(--accent);
    line-height: 1.15;
}

.editorial-subtitle {
    color: var(--muted);
    font-size: 14px;
    margin-top: 15px;
}

/* FINANCIAL CARDS */

.balance-card,
.finance-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 7px;
    transition: border-color 0.2s ease,
                background 0.2s ease;
}

.balance-card:hover,
.finance-card:hover {
    background: var(--card-hover);
    border-color: #666650;
}

.balance-card {
    border-left: 5px solid var(--accent);
    padding: 28px 30px;
    margin-bottom: 15px;
}

.balance-label,
.finance-label {
    color: #B4B0A4;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.8px;
}

.balance-value {
    color: var(--accent);
    font-size: clamp(30px, 4vw, 43px);
    font-weight: 800;
    margin-top: 12px;
}

.balance-description {
    color: var(--muted);
    font-size: 13px;
    margin-top: 8px;
}

.finance-card {
    padding: 23px;
    min-height: 115px;
}

.income-value {
    color: var(--income);
    font-size: 27px;
    font-weight: 700;
    margin-top: 13px;
}

.expense-value {
    color: var(--expense);
    font-size: 27px;
    font-weight: 700;
    margin-top: 13px;
}

/* STREAMLIT METRIC CARDS */

[data-testid="stMetric"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 17px 19px;
}

[data-testid="stMetricLabel"] {
    color: var(--muted);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
}

[data-testid="stMetricValue"] {
    color: var(--text);
    font-weight: 750;
}

/* CHART CONTAINERS */

div[data-testid="stPlotlyChart"] {
    background-color: var(--card);
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 12px;
}

/* BUTTONS */

.stButton button,
.stFormSubmitButton button,
.stDownloadButton button {
    background-color: var(--accent);
    color: var(--bg);
    border: 1px solid var(--accent);
    border-radius: 4px;
    font-weight: 700;
    min-height: 42px;
    transition: all 0.2s ease;
}

.stButton button:hover,
.stFormSubmitButton button:hover,
.stDownloadButton button:hover {
    background-color: var(--accent-soft);
    color: var(--bg);
    border-color: var(--accent-soft);
}

/* INPUTS */

.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stTextArea textarea {
    background-color: var(--card);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 4px;
}

.stSelectbox div[data-baseweb="select"],
.stMultiSelect div[data-baseweb="select"] {
    background-color: var(--card);
    border-color: var(--border);
}

/* PROGRESS BARS */

.stProgress > div > div > div > div {
    background-color: var(--accent);
}

/* ALERTS — MATCH BRAND PALETTE */

[data-testid="stAlert"] {
    background-color: var(--card);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
}

[data-testid="stAlert"][kind="info"] {
    border-left: 4px solid #91AFCB;
}

[data-testid="stAlert"][kind="success"] {
    border-left: 4px solid var(--accent);
}

[data-testid="stAlert"][kind="warning"] {
    border-left: 4px solid var(--warning);
}

[data-testid="stAlert"][kind="error"] {
    border-left: 4px solid var(--expense);
}

/* TABLES */

div[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 7px;
    overflow: hidden;
}

/* DIVIDERS */

hr {
    border-color: var(--border);
}

/* GENERAL TEXT */

p, label, span {
    text-decoration: none;
}

/* RESPONSIVE SPACING */

@media (max-width: 768px) {
    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 1.5rem;
    }

    .editorial-title,
    .editorial-italic {
        font-size: 42px;
        letter-spacing: -2px;
    }

    .balance-card {
        padding: 20px;
    }

    .finance-card {
        padding: 16px;
    }
}

</style>
""", unsafe_allow_html=True)
# ==========================================
# SIDEBAR NAVIGATION
# ==========================================

st.sidebar.title("💰 MONOGRAPH")
st.sidebar.caption("PERSONAL FINANCE MANAGER")

st.sidebar.divider()


page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Add Transaction",
        "Transaction History",
        "Budget Planner",
        "Financial Reports",
        "AI Financial Assistant"
    ]
)



# ==========================================
# LOAD DATABASE
# ==========================================

data = get_transactions()

df = pd.DataFrame(
    data,
    columns=[
        "ID",
        "Type",
        "Amount",
        "Description",
        "Category",
        "Date"
    ]
)

if not df.empty:
    df["Date"] = pd.to_datetime(df["Date"])
    df["Amount"] = pd.to_numeric(df["Amount"])


# ==========================================
# DASHBOARD
# ==========================================


if page == "Dashboard":

    # ==========================================
    # MONOGRAPH DASHBOARD HEADER
    # ==========================================

    st.markdown("""
    <div style="padding: 15px 0 30px 0;
border-bottom: 1px solid #414137;
margin-bottom: 30px;">

<div class="editorial-eyebrow">
MONOGRAPH / PERSONAL FINANCE / 2026
</div>

<div class="editorial-title">Know where</div>
 <div class="editorial-italic">it goes.</div>

<div class="editorial-subtitle">
            Your money, your decisions. A clearer perspective
            on your financial life.
</div>
</div>
    """, unsafe_allow_html=True)

    # ==========================================
    # FINANCIAL CALCULATIONS
    # ==========================================

    if not df.empty:
        income = df[df["Type"] == "Income"]["Amount"].sum()
        expenses = df[df["Type"] == "Expense"]["Amount"].sum()
        transaction_count = len(df)
    else:
        income = 0
        expenses = 0
        transaction_count = 0

    balance = income - expenses

    savings_rate = (
        (balance / income) * 100 if income > 0 else 0
    )

    # ==========================================
    # FINANCIAL OVERVIEW
    # ==========================================

    st.markdown("""
    <div class="editorial-eyebrow">
        FINANCIAL OVERVIEW / 01
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown("**AVAILABLE BALANCE**")
        st.markdown(
            f"<h3 style='color:{'#C9D68A' if balance >= 0 else '#D17B57'};'>"
            f"₹{balance:,.0f}</h3>",
            unsafe_allow_html=True
        )

    with c2:
        st.markdown("**TOTAL INCOME**")
        st.markdown(
            f"<h3 style='color:#AFC78C;'>₹{income:,.0f}</h3>",
            unsafe_allow_html=True
        )

    with c3:
        st.markdown("**TOTAL EXPENSES**")
        st.markdown(
            f"<h3 style='color:#D17B57;'>₹{expenses:,.0f}</h3>",
            unsafe_allow_html=True
        )

    with c4:
        st.markdown("**SAVINGS RATE**")
        st.markdown(
            f"<h3 style='color:#C9D68A;'>{savings_rate:.1f}%</h3>",
            unsafe_allow_html=True
        )

    st.divider()

    
    # ==========================================
    # ANALYTICS / CHARTS
    # ==========================================

    st.markdown("""
    <div class="editorial-eyebrow">
        FINANCIAL ANALYTICS / 02
    </div>
    """, unsafe_allow_html=True)

    if not df.empty:

        expense_df = df[df["Type"] == "Expense"].copy()

        chart1, chart2 = st.columns(2, gap="large")

        # ======================================
        # CATEGORY DONUT CHART
        # ======================================

        with chart1:

            st.subheader("Spending Distribution")

            if not expense_df.empty:

                category_data = (
                    expense_df.groupby("Category")["Amount"]
                    .sum()
                    .reset_index()
                    .sort_values("Amount", ascending=False)
                )

                fig = px.pie(
                    category_data,
                    names="Category",
                    values="Amount",
                    hole=0.65,
                    color_discrete_sequence=[
                        "#C9D68A",
                        "#D17B57",
                        "#E6BD73",
                        "#8F9B80",
                        "#A99DB9",
                        "#C4BCAF"
                    ]
                )

                fig.update_traces(
                    textposition="inside",
                    textinfo="percent",
                    textfont=dict(size=11, color="#171715"),
                    marker=dict(
                        line=dict(color="#24241F", width=3)
                    ),
                    hole=0.65,
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Amount: ₹%{value:,.0f}<br>"
                        "Share: %{percent}"
                        "<extra></extra>"
                    )
                )

                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(
                        color="#F3EEE3",
                        size=11
                    ),
                    height=390,
                    autosize=True,
                    margin=dict(
                        t=15,
                        b=75,
                        l=10,
                        r=10
                    ),
                    legend=dict(
                        title="",
                        orientation="h",
                        yanchor="top",
                        y=-0.12,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=10),
                        bgcolor="rgba(0,0,0,0)"
                    )
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    config={"displayModeBar": False}
                )

            else:

                st.info(
                    "Add expenses to see your spending distribution."
                )

        # ======================================
        # MONTHLY CASH FLOW CHART
        # ======================================

        with chart2:

            st.subheader("Monthly Cash Flow")

            monthly_df = df.copy()

            monthly_df["Month"] = (
                monthly_df["Date"].dt.strftime("%Y-%m")
            )

            monthly_data = monthly_df.pivot_table(
                index="Month",
                columns="Type",
                values="Amount",
                aggfunc="sum",
                fill_value=0
            ).reset_index()

            for col in ["Income", "Expense"]:
                if col not in monthly_data.columns:
                    monthly_data[col] = 0

            monthly_data = monthly_data.sort_values("Month")

            monthly_data["Month Label"] = pd.to_datetime(
                monthly_data["Month"],
                format="%Y-%m"
            ).dt.strftime("%b %Y")

            fig2 = px.bar(
                monthly_data,
                x="Month Label",
                y=["Income", "Expense"],
                barmode="group",
                color_discrete_map={
                    "Income": "#C9D68A",
                    "Expense": "#D17B57"
                },
                labels={
                    "value": "Amount (₹)",
                    "variable": "Transaction Type",
                    "Month Label": "Month"
                },
                hover_data={
                    "Month Label": False
                }
            )

            fig2.update_traces(
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "%{fullData.name}: ₹%{y:,.0f}"
                    "<extra></extra>"
                )
            )

            fig2.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(
                    color="#F3EEE3",
                    size=11
                ),
                height=390,
                autosize=True,
                margin=dict(
                    t=55,
                    b=55,
                    l=55,
                    r=15
                ),
                legend=dict(
                    title="",
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=11),
                    bgcolor="rgba(0,0,0,0)"
                ),
                xaxis_title="",
                yaxis_title="Amount (₹)",
                bargap=0.3,
                bargroupgap=0.12
            )

            fig2.update_xaxes(
                tickangle=-15,
                showgrid=False,
                automargin=True
            )

            fig2.update_yaxes(
                gridcolor="#414137",
                zeroline=False,
                tickprefix="₹",
                tickformat=",.0f",
                automargin=True
            )

            st.plotly_chart(
                fig2,
                use_container_width=True,
                config={"displayModeBar": False}
            )

        st.divider()

        # ==========================================
        # SPENDING INSIGHTS
        # ==========================================

        st.markdown("""
        <div class="editorial-eyebrow">
            SPENDING INSIGHTS / 03
        </div>
        """, unsafe_allow_html=True)

        if not expense_df.empty:

            category_totals = (
                expense_df.groupby("Category")["Amount"].sum()
            )

            highest_category = category_totals.idxmax()
            highest_amount = category_totals.max()

            average_expense = expense_df["Amount"].mean()
            expense_count = len(expense_df)

            i1, i2, i3 = st.columns(3)

            with i1:
                st.markdown("**TOP SPENDING CATEGORY**")
                st.markdown(
                    f"<h3 style='color:#C9D68A;'>{highest_category}</h3>",
                    unsafe_allow_html=True
                )
                st.caption(f"₹{highest_amount:,.2f} spent")

            with i2:
                st.markdown("**AVERAGE EXPENSE**")
                st.markdown(
                    f"<h3 style='color:#F3EEE3;'>₹{average_expense:,.0f}</h3>",
                    unsafe_allow_html=True
                )
                st.caption(f"Across {expense_count} transactions")

            with i3:
                st.markdown("**TOTAL TRANSACTIONS**")
                st.markdown(
                    f"<h3 style='color:#C9D68A;'>{transaction_count}</h3>",
                    unsafe_allow_html=True
                )
                st.caption("Income and expenses combined")

            st.markdown("### Your Spending Observation")

            st.markdown(
                f"""
                <div style="
                    background:#24241F;
                    border:1px solid #414137;
                    border-left:4px solid #C9D68A;
                    border-radius:6px;
                    padding:18px 20px;
                    color:#F3EEE3;">
                    Your highest spending category is
                    <strong style="color:#C9D68A;">
                    {highest_category}
                    </strong>,
                    accounting for
                    <strong>₹{highest_amount:,.2f}</strong>
                    in recorded expenses.
                </div>
                """,
                unsafe_allow_html=True
            )

        else:
            st.info("Add expenses to generate spending insights.")

        st.divider()


        # ==========================================
        # RECENT TRANSACTIONS
        # ==========================================

        st.markdown("""
        <div class="editorial-eyebrow">
            RECENT ACTIVITY / 04
        </div>
        """, unsafe_allow_html=True)

        st.subheader("Latest Transactions")

        recent = (
            df.sort_values("Date", ascending=False)
            .head(5)
            .copy()
        )

        recent["Date"] = recent["Date"].dt.strftime("%d %b %Y")

        recent_display = recent.drop(columns=["ID"])

        # Style transaction types
        def style_transaction_type(value):
            if value == "Income":
                return (
                    "color: #C9D68A; "
                    "font-weight: 700; "
                    "background-color: #292D20;"
                )
            elif value == "Expense":
                return (
                    "color: #D17B57; "
                    "font-weight: 700; "
                    "background-color: #30241F;"
                )
            return ""

        # Apply premium table styling
        styled_recent = (
            recent_display.style
            .map(
                style_transaction_type,
                subset=["Type"]
            )
            .format({
                "Amount": "₹{:,.0f}"
            })
            .set_table_styles([
                {
                    "selector": "th",
                    "props": [
                        ("background-color", "#292923"),
                        ("color", "#C9D68A"),
                        ("font-weight", "700"),
                        ("font-size", "12px"),
                        ("text-transform", "uppercase"),
                        ("letter-spacing", "1px"),
                        ("padding", "14px"),
                        ("border-bottom", "1px solid #45443B")
                    ]
                },
                {
                    "selector": "td",
                    "props": [
                        ("background-color", "#1D1D1A"),
                        ("color", "#F3EEE3"),
                        ("font-size", "13px"),
                        ("padding", "14px"),
                        ("border-bottom", "1px solid #38382F")
                    ]
                },
                {
                    "selector": "table",
                    "props": [
                        ("border-collapse", "collapse"),
                        ("width", "100%"),
                        ("border", "1px solid #414137"),
                        ("border-radius", "8px")
                    ]
                }
            ])
        )

        st.dataframe(
            styled_recent,
            use_container_width=True,
            hide_index=True,
            height=260
        )

        st.caption(
            f"Showing the latest {len(recent)} transactions."
        )


    else:

        st.markdown("""
        <div style="
            background:#24241F;
            border:1px solid #414137;
            border-radius:8px;
            padding:30px;
            text-align:center;">
            <div style="color:#C9D68A;
                        font-size:12px;
                        letter-spacing:2px;
                        font-weight:700;">
                YOUR FINANCIAL JOURNEY STARTS HERE
            </div>
            <h2 style="color:#F3EEE3;">
                No transactions yet.
            </h2>
            <p style="color:#A7A396;">
                Add your first transaction to unlock your financial dashboard.
            </p>
        </div>
        """, unsafe_allow_html=True)


#
elif page == "Add Transaction":

    # ==========================================
    # ADD TRANSACTION / PAGE DESIGN
    # ==========================================

    st.markdown("""
<style>
div[data-testid="stForm"] {
        background: #20201D;
        border: 1px solid #414137;
        border-radius: 10px;
        padding: 25px;
}

div[data-testid="stForm"] label {
    color: #D8D2C5;
    font-size: 13px;
    font-weight: 600;
}

div[data-testid="stForm"] input {
    background-color: #292923;
    color: #F3EEE3;
}

div[data-testid="stForm"] button[kind="primary"] {
    background-color: #C9D68A;
    color: #171715;
    border: none;
    font-weight: 800;
    letter-spacing: 1px;
    min-height: 48px;
}

div[data-testid="stForm"] button[kind="primary"]:hover {
    background-color: #D9E5A0;
    color: #171715;
}
</style>
""", unsafe_allow_html=True)

    # EDITORIAL HEADER

    st.markdown("""
    <div style="
        padding: 15px 0 30px 0;
        border-bottom: 1px solid #45443B;
        margin-bottom: 30px;
    ">
    <div class="editorial-eyebrow">
        MONOGRAPH / NEW ENTRY / 2026
    </div>

    <div class="editorial-title">
        Make every
    </div>

    <div class="editorial-italic">
        rupee count.
    </div>

    <div class="editorial-subtitle">
        Record your financial activity.
        Stay aware of where your money moves.
    </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.4, 0.85], gap="large")

    # ==========================================
    # TRANSACTION FORM
    # ==========================================

    with col1:

        st.markdown("""
        <div class="editorial-eyebrow">
            TRANSACTION DETAILS / 01
        </div>
        """, unsafe_allow_html=True)

        with st.form("transaction_form"):

            st.markdown(
                "### Enter transaction details"
            )

            transaction_type = st.selectbox(
                "Transaction Type",
                ["Expense", "Income"]
            )

            amount = st.number_input(
                "Amount (₹)",
                min_value=1.0,
                step=100.0
            )

            description = st.text_input(
                "Description",
                placeholder="Example: Groceries, Salary"
            )

            category = st.selectbox(
                "Category",
                [
                    "Food",
                    "Transport",
                    "Shopping",
                    "Entertainment",
                    "Bills",
                    "Health",
                    "Education",
                    "Salary",
                    "Other"
                ]
            )

            date = st.date_input(
                "Transaction Date"
            )

            st.markdown("<br>", unsafe_allow_html=True)

            submitted = st.form_submit_button(
                "SAVE TRANSACTION  →",
                use_container_width=True,
                type="primary"
            )

            if submitted:

                if description.strip():

                    add_transaction(
                        transaction_type,
                        amount,
                        description,
                        category,
                        date
                    )

                    st.success(
                        "Transaction saved successfully!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Please enter a description."
                    )

    # ==========================================
    # INFORMATION PANEL
    # ==========================================

    with col2:

        st.markdown("""
<div style="
background: #24241F;
border: 1px solid #414137;
border-top: 4px solid #C9D68A;
border-radius: 8px;
padding: 25px;
">

<div style="
    color: #C9D68A;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
">
    A SMALL REMINDER / 02
</div>

<div style="
    color: #F3EEE3;
    font-size: 29px;
    font-weight: 800;
    line-height: 1.2;
    margin-top: 25px;
">
    Know your numbers.
</div>

<div style="
    color: #A7A396;
    font-size: 14px;
    line-height: 1.9;
    margin-top: 18px;
">
    Every transaction tells a story about
    your financial habits. Recording your
    income and expenses helps you understand
    that story.
</div>

<hr style="
    border-color: #414137;
    margin: 28px 0;
">

<div style="margin-bottom: 24px;">
<div style="
    color: #C9D68A;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
">
    01 / RECORD
</div>
<div style="
    color: #A7A396;
    font-size: 13px;
    margin-top: 7px;
    line-height: 1.7;
">
    Enter the amount and description
    of your transaction.
</div>
</div>

<div style="margin-bottom: 24px;">
    <div style="
        color: #C9D68A;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1px;
    ">
        02 / CLASSIFY
    </div>
    <div style="
        color: #A7A396;
        font-size: 13px;
        margin-top: 7px;
        line-height: 1.7;
    ">
        Choose the correct transaction
        category.
    </div>
</div>

<div>
    <div style="
        color: #C9D68A;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1px;
    ">
        03 / TRACK
    </div>
    <div style="
        color: #A7A396;
        font-size: 13px;
        margin-top: 7px;
        line-height: 1.7;
    ">
        Review your financial activity
        through your dashboard and reports.
    </div>
</div>

<hr style="
    border-color: #414137;
    margin: 28px 0 18px 0;
">

<div style="
    color: #C9D68A;
    font-family: Georgia, serif;
    font-size: 20px;
    font-style: italic;
">
    Small entries. Clearer decisions.
</div>

</div>
""", unsafe_allow_html=True)



# ==========================================
# TRANSACTION HISTORY
# ==========================================

elif page == "Transaction History":

    # ======================================
    # PAGE HEADER
    # ======================================

    st.markdown("""
<div style="
    padding: 15px 0 30px 0;
    border-bottom: 1px solid #45443B;
    margin-bottom: 30px;
">
<div class="editorial-eyebrow">
    MONOGRAPH / RECORDS / 2026
</div>

<div class="editorial-title">
    Every rupee,
</div>

<div class="editorial-italic">
    accounted for.
</div>

<div class="editorial-subtitle">
    A complete record of your financial activity.
</div>
</div>
""", unsafe_allow_html=True)

    if not df.empty:

        # ======================================
        # FILTERS
        # ======================================

        st.markdown("""
        <div class="editorial-eyebrow">
            FILTER YOUR RECORDS / 01
        </div>
        """, unsafe_allow_html=True)

        filter1, filter2 = st.columns(2, gap="large")

        with filter1:

            selected_type = st.selectbox(
                "Transaction Type",
                ["All", "Income", "Expense"]
            )

        with filter2:

            categories = ["All"] + sorted(
                df["Category"].dropna().unique().tolist()
            )

            selected_category = st.selectbox(
                "Category",
                categories
            )

        # APPLY FILTERS

        filtered_df = df.copy()

        if selected_type != "All":

            filtered_df = filtered_df[
                filtered_df["Type"] == selected_type
            ]

        if selected_category != "All":

            filtered_df = filtered_df[
                filtered_df["Category"] == selected_category
            ]

        # ======================================
        # FILTERED SUMMARY
        # ======================================

        st.markdown("""
        <div class="editorial-eyebrow">
            RECORD SUMMARY / 02
        </div>
        """, unsafe_allow_html=True)

        total_records = len(filtered_df)

        total_income = filtered_df[
            filtered_df["Type"] == "Income"
        ]["Amount"].sum()

        total_expenses = filtered_df[
            filtered_df["Type"] == "Expense"
        ]["Amount"].sum()

        summary1, summary2, summary3 = st.columns(3)

        with summary1:
            st.metric(
                "TOTAL RECORDS",
                total_records
            )

        with summary2:
            st.metric(
                "TOTAL INCOME",
                f"₹{total_income:,.2f}"
            )

        with summary3:
            st.metric(
                "TOTAL EXPENSES",
                f"₹{total_expenses:,.2f}"
            )

        st.divider()

        # ======================================
        # ALL TRANSACTIONS
        # ======================================

        st.markdown("""
        <div class="editorial-eyebrow">
            ALL TRANSACTIONS / 03
        </div>
        """, unsafe_allow_html=True)

        st.subheader("Your Financial Records")

        if not filtered_df.empty:

            # Sort records by date
            sorted_df = filtered_df.sort_values(
                "Date",
                ascending=False
            ).copy()

            # Preserve original values for CSV
            export_df = sorted_df.drop(
                columns=["ID"]
            ).copy()

            csv_data = export_df.to_csv(
                index=False
            ).encode("utf-8")

            # Export button
            st.download_button(
                label="↓  DOWNLOAD TRANSACTIONS (CSV)",
                data=csv_data,
                file_name="monograph_transactions.csv",
                mime="text/csv",
                use_container_width=True
            )

            # Prepare display table
            display_df = export_df.copy()

            display_df["Date"] = pd.to_datetime(
                display_df["Date"]
            ).dt.strftime("%d %b %Y")

            # Colour-code transaction types
            def style_transaction_type(value):

                if value == "Income":
                    return (
                        "color: #C9D68A;"
                        "font-weight: 700;"
                        "background-color: #292D20;"
                    )

                elif value == "Expense":
                    return (
                        "color: #D17B57;"
                        "font-weight: 700;"
                        "background-color: #30241F;"
                    )

                return ""

            styled_table = (
                display_df.style
                .map(
                    style_transaction_type,
                    subset=["Type"]
                )
                .format({
                    "Amount": "₹{:,.2f}"
                })
                .set_table_styles([
                    {
                        "selector": "th",
                        "props": [
                            ("background-color", "#292923"),
                            ("color", "#C9D68A"),
                            ("font-weight", "700"),
                            ("font-size", "12px"),
                            ("letter-spacing", "1px"),
                            ("padding", "15px"),
                            ("border-bottom", "1px solid #45443B")
                        ]
                    },
                    {
                        "selector": "td",
                        "props": [
                            ("background-color", "#1D1D1A"),
                            ("color", "#F3EEE3"),
                            ("font-size", "13px"),
                            ("padding", "14px"),
                            ("border-bottom", "1px solid #38382F")
                        ]
                    },
                    {
                        "selector": "table",
                        "props": [
                            ("width", "100%"),
                            ("border-collapse", "collapse"),
                            ("border", "1px solid #414137")
                        ]
                    }
                ])
            )

            st.dataframe(
                styled_table,
                use_container_width=True,
                hide_index=True,
                height=420
            )

            st.caption(
                f"Showing {total_records} transaction(s)."
            )

            # ======================================
            # TRANSACTION MANAGEMENT
            # ======================================

            st.divider()

            st.markdown("""
            <div class="editorial-eyebrow">
                RECORD MANAGEMENT / 04
            </div>
            """, unsafe_allow_html=True)

            st.subheader("Manage Transactions")

            transaction_options = {}

            for _, row in filtered_df.iterrows():

                label = (
                    f"#{int(row['ID'])}  |  "
                    f"{row['Description']}  |  "
                    f"₹{row['Amount']:,.2f}"
                )

                transaction_options[label] = int(row["ID"])

            selected_label = st.selectbox(
                "Choose a transaction to manage",
                list(transaction_options.keys())
            )

            selected_id = transaction_options[selected_label]

            selected_transaction = filtered_df[
                filtered_df["ID"] == selected_id
            ].iloc[0]

            # ======================================
            # EDIT TRANSACTION
            # ======================================

            with st.expander("✏️  EDIT TRANSACTION"):

                st.caption(
                    "Modify the details of your selected transaction."
                )

                with st.form("edit_transaction_form"):

                    edit_col1, edit_col2 = st.columns(2)

                    with edit_col1:

                        edit_type = st.selectbox(
                            "Transaction Type",
                            ["Expense", "Income"],
                            index=["Expense", "Income"].index(
                                str(selected_transaction["Type"])
                            )
                        )

                        edit_amount = st.number_input(
                            "Amount (₹)",
                            min_value=1.0,
                            value=float(
                                selected_transaction["Amount"]
                            ),
                            step=100.0
                        )

                        edit_description = st.text_input(
                            "Description",
                            value=str(
                                selected_transaction["Description"]
                            )
                        )

                    with edit_col2:

                        edit_categories = sorted(
                            df["Category"]
                            .dropna()
                            .astype(str)
                            .unique()
                            .tolist()
                        )

                        current_category = str(
                            selected_transaction["Category"]
                        )

                        if current_category not in edit_categories:
                            edit_categories.append(current_category)

                        edit_category = st.selectbox(
                            "Category",
                            edit_categories,
                            index=edit_categories.index(
                                current_category
                            )
                        )

                        edit_date = st.date_input(
                            "Transaction Date",
                            value=pd.to_datetime(
                                selected_transaction["Date"]
                            ).date()
                        )

                    update_button = st.form_submit_button(
                        "SAVE CHANGES  →",
                        use_container_width=True
                    )

                    if update_button:

                        if edit_description.strip():

                            update_transaction(
                                selected_id,
                                edit_type,
                                edit_amount,
                                edit_description,
                                edit_category,
                                edit_date
                            )

                            st.success(
                                "Transaction updated successfully!"
                            )

                            st.rerun()

                        else:

                            st.error(
                                "Description cannot be empty."
                            )

            # ======================================
            # DELETE TRANSACTION
            # ======================================

            with st.expander("🗑️  DELETE TRANSACTION"):

                st.caption(
                    "Permanently remove the selected transaction."
                )

                st.warning(
                    f"Selected: {selected_transaction['Description']} "
                    f"— ₹{selected_transaction['Amount']:,.2f}"
                )

                with st.form("delete_transaction_form"):

                    confirm_delete = st.checkbox(
                        "I confirm that I want to permanently delete this transaction."
                    )

                    delete_button = st.form_submit_button(
                        "DELETE TRANSACTION",
                        use_container_width=True
                    )

                    if delete_button:

                        if confirm_delete:

                            delete_transaction(selected_id)

                            st.success(
                                "Transaction deleted successfully!"
                            )

                            st.rerun()

                        else:

                            st.error(
                                "Please confirm before deleting."
                            )

        else:

            st.info(
                "No transactions match your selected filters."
            )

    else:

        st.markdown("""
        <div style="
            background: #24241F;
            border: 1px solid #414137;
            border-radius: 8px;
            padding: 30px;
            text-align: center;
        ">
            <div style="
                color: #C9D68A;
                font-size: 12px;
                letter-spacing: 2px;
                font-weight: 700;
            ">
                YOUR RECORDS / EMPTY
            </div>

            <h2 style="color: #F3EEE3;">
                No transactions found.
            </h2>

            <p style="color: #A7A396;">
                Add your first transaction to begin tracking your finances.
            </p>
        </div>
        """, unsafe_allow_html=True)


# ==========================================
# BUDGET PLANNER
# ==========================================

elif page == "Budget Planner":

    st.markdown("""
    <div style="padding: 15px 0 25px 0;">
        <div style="color: #C9D68A; font-size: 11px;
                    font-weight: 700; letter-spacing: 3px;">
            MONOGRAPH / FINANCIAL PLANNING / 2026
        </div>
        <h1 style="font-size: 48px; margin-top: 15px;">
            Plan your spending.
        </h1>
        <p style="color: #A7A396;">
            Set limits. Track expenses. Stay in control.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Select month
    current_month = pd.Timestamp.today().strftime("%Y-%m")

    available_months = [
        date.strftime("%Y-%m")
        for date in pd.date_range(
            end=pd.Timestamp.today().replace(day=1),
            periods=12,
            freq="MS"
        )[::-1]
    ]

    selected_month = st.selectbox(
        "Select Budget Month",
        available_months,
        index=0,
        format_func=lambda x: pd.to_datetime(x).strftime("%B %Y")
    )

    # Get saved budget
    saved_budget = get_monthly_budget(selected_month)

    # Set monthly budget
    st.subheader("01 / Set Your Monthly Budget")

    with st.form("budget_form"):

        budget_amount = st.number_input(
            "Monthly Spending Limit (₹)",
            min_value=0.0,
            value=float(saved_budget),
            step=500.0
        )

        budget_submitted = st.form_submit_button(
            "Save Monthly Budget",
            use_container_width=True
        )

        if budget_submitted:

            if budget_amount > 0:

                save_monthly_budget(
                    selected_month,
                    budget_amount
                )

                st.success("Monthly budget saved successfully!")
                st.rerun()

            else:
                st.error("Please enter a budget greater than zero.")

    st.divider()

    # Calculate monthly expenses
    if not df.empty:

        monthly_expenses = df[
            (df["Type"] == "Expense") &
            (df["Date"].dt.strftime("%Y-%m") == selected_month)
        ]["Amount"].sum()

    else:
        monthly_expenses = 0

    remaining_budget = saved_budget - monthly_expenses

    # Display budget statistics
    st.subheader("02 / Your Budget Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Monthly Budget",
        f"₹{saved_budget:,.2f}"
    )

    col2.metric(
        "Amount Spent",
        f"₹{monthly_expenses:,.2f}"
    )

    col3.metric(
        "Remaining Budget",
        f"₹{remaining_budget:,.2f}",
        delta=f"₹{remaining_budget:,.2f}",
        delta_color="normal"
    )

    st.divider()

    # Budget progress
    st.subheader("03 / Spending Progress")

    if saved_budget > 0:

        spending_percentage = (
            monthly_expenses / saved_budget
        ) * 100

        progress = min(spending_percentage / 100, 1.0)

        st.progress(progress)

        st.markdown(
            f"""
            <div style="display:flex;
                        justify-content:space-between;
                        color:#C9D68A;
                        font-size:14px;
                        margin-top:8px;">
                <span>Budget Utilization</span>
                <strong>{spending_percentage:.1f}%</strong>
            </div>
            """,
            unsafe_allow_html=True
        )

        if spending_percentage >= 100:

            st.error(
                "Budget exceeded! You have spent more than your monthly limit."
            )

        elif spending_percentage >= 80:

            st.warning(
                "You have used 80% or more of your monthly budget. Watch your spending!"
            )

        else:

            st.success(
                "Your spending is within the planned budget. Keep it up!"
            )

    else:

        st.info(
            "Set a monthly budget above to start tracking your spending progress."
        )

    st.divider()

    # Category-wise budget spending
    st.subheader("04 / Where Is Your Money Going?")

    if not df.empty:

        monthly_expense_df = df[
            (df["Type"] == "Expense") &
            (df["Date"].dt.strftime("%Y-%m") == selected_month)
        ]

        if not monthly_expense_df.empty:

            category_budget_data = (
                monthly_expense_df.groupby("Category")["Amount"]
                .sum()
                .reset_index()
            )

            fig_budget = px.bar(
                category_budget_data,
                x="Category",
                y="Amount",
                title="Monthly Spending by Category"
            )

            fig_budget.update_layout(
                paper_bgcolor="#22221E",
                plot_bgcolor="#22221E",
                font_color="#F3EEE3",
                title_font_color="#C9D68A"
            )

            st.plotly_chart(
                fig_budget,
                use_container_width=True
            )

        else:

            st.info("No expenses recorded for this month.")

    else:

        st.info("Add transactions to see your spending breakdown.")

    
    st.divider()

    # ==========================================
    # CATEGORY-WISE BUDGET PLANNER
    # ==========================================

    st.subheader("05 / Individual Category Budgets")

    budget_categories = [
        "Food",
        "Transport",
        "Shopping",
        "Entertainment",
        "Bills",
        "Health",
        "Education",
        "Salary",
        "Other"
    ]

    category_budgets = get_category_budgets(selected_month)

    with st.form("category_budget_form"):

        selected_budget_category = st.selectbox(
            "Choose Category",
            budget_categories
        )

        category_amount = st.number_input(
            "Category Spending Limit (₹)",
            min_value=0.0,
            value=float(
                category_budgets.get(
                    selected_budget_category, 0.0
                )
            ),
            step=100.0
        )

        category_submitted = st.form_submit_button(
            "Save Category Budget",
            use_container_width=True
        )

        if category_submitted:

            if category_amount > 0:

                save_category_budget(
                    selected_month,
                    selected_budget_category,
                    category_amount
                )

                st.success("Category budget saved!")
                st.rerun()

            else:
                st.error("Enter an amount greater than zero.")

    st.divider()

    st.subheader("06 / Category Spending Overview")

    if category_budgets:

        for category, limit in category_budgets.items():

            category_spent = 0.0

            if not df.empty:

                category_spent = df[
                    (df["Type"] == "Expense") &
                    (df["Category"] == category) &
                    (df["Date"].dt.strftime("%Y-%m") == selected_month)
                ]["Amount"].sum()

            percentage = (category_spent / limit) * 100

            st.markdown(f"**{category}**")

            st.progress(
                min(percentage / 100, 1.0)
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Spent",
                f"₹{category_spent:,.0f}"
            )

            col2.metric(
                "Budget",
                f"₹{limit:,.0f}"
            )

            col3.metric(
                "Used",
                f"{percentage:.1f}%"
            )

            if percentage >= 100:
                st.error(f"{category} budget exceeded!")

            elif percentage >= 80:
                st.warning(f"{category} budget almost used!")

            else:
                st.success(f"{category} spending is under control.")

            st.divider()

    else:

        st.info(
            "No category budgets set yet. "
            "Create your first category budget above."
        )



# ==========================================
# FINANCIAL REPORTS & ANALYTICS
# ==========================================

elif page == "Financial Reports":

    # ======================================
    # PAGE HEADER
    # ======================================

    st.markdown("""
<div style="
    padding: 15px 0 30px 0;
    border-bottom: 1px solid #45443B;
    margin-bottom: 30px;
">
<div class="editorial-eyebrow">
    MONOGRAPH / ANALYTICS / 2026
</div>

<div class="editorial-title">
    Financial
</div>

<div class="editorial-italic">
    intelligence.
</div>

<div class="editorial-subtitle">
    Understand your financial patterns.
    Make more informed decisions.
</div>
</div>
""", unsafe_allow_html=True)

    if not df.empty:

        # ======================================
        # PREPARE FINANCIAL DATA
        # ======================================

        income_df = df[df["Type"] == "Income"].copy()
        expense_df = df[df["Type"] == "Expense"].copy()

        total_income = income_df["Amount"].sum()
        total_expenses = expense_df["Amount"].sum()

        net_savings = total_income - total_expenses

        savings_rate = (
            (net_savings / total_income) * 100
            if total_income > 0 else 0
        )

        income_spent = (
            (total_expenses / total_income) * 100
            if total_income > 0 else 0
        )

        # ======================================
        # 01 / FINANCIAL SUMMARY
        # ======================================

        st.markdown("""
<div class="editorial-eyebrow">
    FINANCIAL OVERVIEW / 01
</div>
""", unsafe_allow_html=True)

        st.subheader("Your Financial Position")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "TOTAL INCOME",
                f"₹{total_income:,.0f}"
            )

        with c2:
            st.metric(
                "TOTAL EXPENSES",
                f"₹{total_expenses:,.0f}"
            )

        with c3:
            st.metric(
                "NET SAVINGS",
                f"₹{net_savings:,.0f}"
            )

        with c4:
            st.metric(
                "SAVINGS RATE",
                f"{savings_rate:.1f}%"
            )

        st.divider()

        # ======================================
        # 02 / SAVINGS PERFORMANCE
        # ======================================

        st.markdown("""
<div class="editorial-eyebrow">
    SAVINGS PERFORMANCE / 02
</div>
""", unsafe_allow_html=True)

        performance1, performance2 = st.columns([1.2, 1])

        with performance1:

            st.subheader("Your Savings Rate")

            st.markdown(f"""
<div style="
    background: #24241F;
    border: 1px solid #414137;
    border-radius: 8px;
    padding: 22px;
">
<div style="
    color: #A7A396;
    font-size: 12px;
    letter-spacing: 1px;
">
    CURRENT SAVINGS RATE
</div>

<div style="
    color: #C9D68A;
    font-size: 42px;
    font-weight: 800;
    margin-top: 8px;
">
    {savings_rate:.1f}%
</div>

<div style="
    color: #A7A396;
    font-size: 13px;
    margin-top: 5px;
">
    Of your recorded income retained as savings
</div>
</div>
""", unsafe_allow_html=True)

            st.progress(
                max(0.0, min(1.0, savings_rate / 100))
            )

        with performance2:

            st.subheader("Income Utilisation")

            st.markdown(f"""
<div style="
    background: #24241F;
    border: 1px solid #414137;
    border-radius: 8px;
    padding: 22px;
">
<div style="
    color: #A7A396;
    font-size: 12px;
    letter-spacing: 1px;
">
    INCOME SPENT
</div>

<div style="
    color: #D17B57;
    font-size: 42px;
    font-weight: 800;
    margin-top: 8px;
">
    {income_spent:.1f}%
</div>

<div style="
    color: #A7A396;
    font-size: 13px;
    margin-top: 5px;
">
    Of your recorded income used for expenses
</div>
</div>
""", unsafe_allow_html=True)

        if savings_rate >= 30:

            st.success(
                "Excellent! Your savings rate is strong."
            )

        elif savings_rate >= 10:

            st.info(
                "You are saving money. Try to improve your savings rate."
            )

        else:

            st.warning(
                "Your savings rate is low. Review your spending."
            )

        st.divider()

        # ======================================
        # 03 / MONTHLY COMPARISON
        # ======================================

        st.markdown("""
<div class="editorial-eyebrow">
    CASH FLOW ANALYSIS / 03
</div>
""", unsafe_allow_html=True)

        st.subheader("Monthly Income vs Expenses")

        monthly_df = df.copy()

        monthly_df["Month"] = (
            monthly_df["Date"].dt.strftime("%Y-%m")
        )

        monthly_data = monthly_df.pivot_table(
            index="Month",
            columns="Type",
            values="Amount",
            aggfunc="sum",
            fill_value=0
        ).reset_index()

        for col in ["Income", "Expense"]:
            if col not in monthly_data.columns:
                monthly_data[col] = 0

        monthly_data = monthly_data.sort_values("Month")

        monthly_data["Month Label"] = pd.to_datetime(
            monthly_data["Month"],
            format="%Y-%m"
        ).dt.strftime("%b %Y")

        fig = px.bar(
            monthly_data,
            x="Month Label",
            y=["Income", "Expense"],
            barmode="group",
            color_discrete_map={
                "Income": "#C9D68A",
                "Expense": "#D17B57"
            },
            labels={
                "value": "Amount (₹)",
                "variable": "Transaction Type",
                "Month Label": "Month"
            }
        )

        fig.update_traces(
            hovertemplate=(
                "<b>%{x}</b><br>"
                "%{fullData.name}: ₹%{y:,.2f}"
                "<extra></extra>"
            )
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                color="#F3EEE3",
                size=11
            ),
            height=390,
            margin=dict(
                t=55,
                b=55,
                l=55,
                r=15
            ),
            legend=dict(
                title="",
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(0,0,0,0)"
            ),
            xaxis_title="",
            yaxis_title="Amount (₹)",
            bargap=0.3
        )

        fig.update_xaxes(
            showgrid=False,
            tickangle=-15,
            automargin=True
        )

        fig.update_yaxes(
            gridcolor="#414137",
            zeroline=False,
            tickprefix="₹",
            tickformat=",.0f"
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False}
        )

        st.divider()

        # ======================================
        # 04 / CATEGORY ANALYSIS
        # ======================================

        st.markdown("""
<div class="editorial-eyebrow">
    SPENDING BREAKDOWN / 04
</div>
""", unsafe_allow_html=True)

        st.subheader("Where Your Money Goes")

        if not expense_df.empty:

            category_data = (
                expense_df.groupby("Category")["Amount"]
                .sum()
                .reset_index()
                .sort_values("Amount", ascending=False)
            )

            category_col1, category_col2 = st.columns(
                [1.2, 1]
            )

            with category_col1:

                fig2 = px.pie(
                    category_data,
                    names="Category",
                    values="Amount",
                    hole=0.65,
                    color_discrete_sequence=[
                        "#C9D68A",
                        "#D17B57",
                        "#E6BD73",
                        "#8F9B80",
                        "#A99DB9",
                        "#C4BCAF"
                    ]
                )

                fig2.update_traces(
                    textposition="inside",
                    textinfo="percent",
                    marker=dict(
                        line=dict(
                            color="#24241F",
                            width=3
                        )
                    ),
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Spent: ₹%{value:,.2f}<br>"
                        "Share: %{percent}"
                        "<extra></extra>"
                    )
                )

                fig2.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#F3EEE3",
                    height=380,
                    margin=dict(
                        t=15,
                        b=75,
                        l=10,
                        r=10
                    ),
                    legend=dict(
                        title="",
                        orientation="h",
                        yanchor="top",
                        y=-0.12,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=10),
                        bgcolor="rgba(0,0,0,0)"
                    )
                )

                st.plotly_chart(
                    fig2,
                    use_container_width=True,
                    config={"displayModeBar": False}
                )

            with category_col2:

                st.markdown("""
<div class="editorial-eyebrow">
    CATEGORY BREAKDOWN
</div>
""", unsafe_allow_html=True)

                for _, row in category_data.iterrows():

                    category_name = str(row["Category"])
                    category_amount = float(row["Amount"])

                    category_percentage = (
                        category_amount / total_expenses * 100
                        if total_expenses > 0 else 0
                    )

                    st.markdown(f"""
<div style="
    background: #24241F;
    border: 1px solid #414137;
    border-radius: 6px;
    padding: 13px 15px;
    margin-bottom: 10px;
">
<div style="
    display: flex;
    justify-content: space-between;
    gap: 10px;
">
<span style="
    color: #F3EEE3;
    font-size: 13px;
    font-weight: 600;
">
    {category_name}
</span>

<span style="
    color: #C9D68A;
    font-size: 13px;
    font-weight: 700;
">
    ₹{category_amount:,.0f}
</span>
</div>

<div style="
    color: #A7A396;
    font-size: 11px;
    margin-top: 7px;
">
    {category_percentage:.1f}% of total expenses
</div>
</div>
""", unsafe_allow_html=True)

            highest_category = category_data.loc[
                category_data["Amount"].idxmax()
            ]

            st.info(
                f"Your highest spending category is "
                f"{highest_category['Category']} "
                f"(₹{highest_category['Amount']:,.2f})."
            )

        else:

            st.info("No expense records available yet.")

        st.divider()

        # ======================================
        # 05 / MONTHLY FINANCIAL RECORDS
        # ======================================

        st.markdown("""
<div class="editorial-eyebrow">
    FINANCIAL ARCHIVE / 05
</div>
""", unsafe_allow_html=True)

        st.subheader("Monthly Financial Records")

        monthly_data["Net Savings"] = (
            monthly_data["Income"] - monthly_data["Expense"]
        )

        monthly_data["Month"] = monthly_data["Month Label"]

        report_table = monthly_data[
            [
                "Month",
                "Income",
                "Expense",
                "Net Savings"
            ]
        ].copy()

        report_table = report_table.rename(
            columns={
                "Income": "Income (₹)",
                "Expense": "Expenses (₹)",
                "Net Savings": "Net Savings (₹)"
            }
        )

        styled_report = (
            report_table.style
            .format({
                "Income (₹)": "₹{:,.2f}",
                "Expenses (₹)": "₹{:,.2f}",
                "Net Savings (₹)": "₹{:,.2f}"
            })
            .set_table_styles([
                {
                    "selector": "th",
                    "props": [
                        ("background-color", "#292923"),
                        ("color", "#C9D68A"),
                        ("font-weight", "700"),
                        ("font-size", "12px"),
                        ("padding", "14px"),
                        ("border-bottom", "1px solid #45443B")
                    ]
                },
                {
                    "selector": "td",
                    "props": [
                        ("background-color", "#1D1D1A"),
                        ("color", "#F3EEE3"),
                        ("font-size", "13px"),
                        ("padding", "14px"),
                        ("border-bottom", "1px solid #38382F")
                    ]
                },
                {
                    "selector": "table",
                    "props": [
                        ("width", "100%"),
                        ("border-collapse", "collapse"),
                        ("border", "1px solid #414137")
                    ]
                }
            ])
        )

        st.dataframe(
            styled_report,
            use_container_width=True,
            hide_index=True,
            height=260
        )

        st.divider()

        # ======================================
        # 06 / EXPORT REPORTS
        # ======================================

        st.markdown("""
        <div class="editorial-eyebrow">
            DOCUMENT EXPORT / 06
        </div>
        """, unsafe_allow_html=True)

        st.subheader("Export Financial Reports")

        export_col1, export_col2 = st.columns(2)

        # CSV EXPORT

        with export_col1:

            st.markdown("""
<div style="
    background: #24241F;
    border: 1px solid #414137;
    border-radius: 8px;
    padding: 20px;
">
<div style="
    color: #C9D68A;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
">
    SPREADSHEET / CSV
</div>

<div style="
    color: #F3EEE3;
    font-size: 20px;
    font-weight: 700;
    margin-top: 10px;
">
    Monthly Data
</div>

<div style="
    color: #A7A396;
    font-size: 13px;
    margin-top: 6px;
">
    Export your monthly financial records.
</div>
</div>
""", unsafe_allow_html=True)

            report_csv = report_table.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                label="↓ DOWNLOAD CSV REPORT",
                data=report_csv,
                file_name="monograph_financial_report.csv",
                mime="text/csv",
                use_container_width=True
            )

        # ======================================
        # PDF REPORT GENERATOR
        # ======================================

        with export_col2:

            st.markdown("""
<div style="
    background: #24241F;
    border: 1px solid #414137;
    border-radius: 8px;
    padding: 20px;
">
<div style="
    color: #D17B57;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
">
    DOCUMENT / PDF
</div>

<div style="
    color: #F3EEE3;
    font-size: 20px;
    font-weight: 700;
    margin-top: 10px;
">
    Financial Statement
</div>

<div style="
    color: #A7A396;
    font-size: 13px;
    margin-top: 6px;
">
    Download a formatted financial report.
</div>
</div>
""", unsafe_allow_html=True)

            def generate_pdf_report():

                buffer = BytesIO()

                document = SimpleDocTemplate(
                    buffer,
                    pagesize=A4,
                    rightMargin=40,
                    leftMargin=40,
                    topMargin=40,
                    bottomMargin=40
                )

                styles = getSampleStyleSheet()
                elements = []

                elements.append(Paragraph(
                    "MONOGRAPH — FINANCIAL REPORT",
                    styles["Title"]
                ))

                elements.append(Spacer(1, 12))

                elements.append(Paragraph(
                    f"Generated on: {pd.Timestamp.today().strftime('%d %B %Y')}",
                    styles["Normal"]
                ))

                elements.append(Spacer(1, 20))

                # Financial summary

                elements.append(Paragraph(
                    "01 / Financial Summary",
                    styles["Heading2"]
                ))

                summary_data = [
                    ["Financial Metric", "Amount"],
                    ["Total Income", f"INR {total_income:,.2f}"],
                    ["Total Expenses", f"INR {total_expenses:,.2f}"],
                    ["Net Savings", f"INR {net_savings:,.2f}"],
                    ["Savings Rate", f"{savings_rate:.1f}%"]
                ]

                summary_table = Table(
                    summary_data,
                    colWidths=[250, 200]
                )

                summary_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#272721")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F3EEE3")),
                    ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#171715")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("PADDING", (0, 0), (-1, -1), 9)
                ]))

                elements.append(summary_table)
                elements.append(Spacer(1, 25))

                # Category breakdown

                elements.append(Paragraph(
                    "02 / Expense Category Breakdown",
                    styles["Heading2"]
                ))

                category_pdf_data = [
                    ["Category", "Total Spent"]
                ]

                if not expense_df.empty:

                    pdf_categories = (
                        expense_df.groupby("Category")["Amount"]
                        .sum()
                        .sort_values(ascending=False)
                    )

                    for category_name, amount in pdf_categories.items():

                        category_pdf_data.append([
                            str(category_name),
                            f"INR {amount:,.2f}"
                        ])

                else:

                    category_pdf_data.append([
                        "No expenses recorded",
                        "INR 0.00"
                    ])

                category_table = Table(
                    category_pdf_data,
                    colWidths=[250, 200]
                )

                category_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#272721")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("PADDING", (0, 0), (-1, -1), 9)
                ]))

                elements.append(category_table)
                elements.append(Spacer(1, 25))

                # Monthly records

                elements.append(Paragraph(
                    "03 / Monthly Financial Records",
                    styles["Heading2"]
                ))

                monthly_pdf_data = [
                    ["Month", "Income", "Expenses", "Net Savings"]
                ]

                for _, row in monthly_data.iterrows():

                    monthly_pdf_data.append([
                        str(row["Month"]),
                        f"{row['Income']:,.2f}",
                        f"{row['Expense']:,.2f}",
                        f"{row['Net Savings']:,.2f}"
                    ])

                monthly_table = Table(
                    monthly_pdf_data,
                    repeatRows=1
                )

                monthly_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#272721")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("PADDING", (0, 0), (-1, -1), 7)
                ]))

                elements.append(monthly_table)

                document.build(elements)

                buffer.seek(0)

                return buffer.getvalue()

            pdf_data = generate_pdf_report()

            st.download_button(
                label="↓ DOWNLOAD PDF REPORT",
                data=pdf_data,
                file_name="MONOGRAPH_Financial_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    else:

        st.markdown("""
<div style="
background: #24241F;
border: 1px solid #414137;
border-radius: 8px;
padding: 30px;
text-align: center;
">
<div style="
    color: #C9D68A;
    font-size: 12px;
    letter-spacing: 2px;
    font-weight: 700;
">
    FINANCIAL ANALYTICS / EMPTY
</div>

<h2 style="color: #F3EEE3;">
    Your reports are waiting.
</h2>

<p style="color: #A7A396;">
    Add transactions to generate your financial reports.
</p>
</div>
""", unsafe_allow_html=True)


# ==========================================
# MONOGRAPH AI FINANCIAL ASSISTANT
# ==========================================

elif page == "AI Financial Assistant":

    st.markdown("""
    <div style="padding: 15px 0 30px 0;
border-bottom: 1px solid #45443B;
margin-bottom: 30px;">

<div style="color: #C9D68A; font-size: 11px;
font-weight: 700; letter-spacing: 3px;">
MONOGRAPH / INTELLIGENCE / AI
</div>

<h1 style="font-size: 48px; margin-top: 15px;">
Your financial intelligence.
</h1>

<p style="color: #A7A396;">
Understand your habits. Discover opportunities.
Make smarter financial decisions.
</p>
</div>
""", unsafe_allow_html=True)

    if not df.empty:

        # Financial calculations
        income_df = df[df["Type"] == "Income"].copy()
        expense_df = df[df["Type"] == "Expense"].copy()

        total_income = income_df["Amount"].sum()
        total_expenses = expense_df["Amount"].sum()
        balance = total_income - total_expenses

        savings_rate = (
            balance / total_income * 100
            if total_income > 0 else 0
        )

        # Financial Health Score
        if total_income > 0:

            savings_score = max(
                0, min(40, savings_rate * 0.8)
            )

            spending_score = max(
                0,
                30 * (1 - min(total_expenses / total_income, 1))
            )

            consistency_score = 15 if len(df) >= 5 else 5

            budget_score = 15 if balance > 0 else 0

            health_score = round(
                savings_score +
                spending_score +
                consistency_score +
                budget_score
            )

        else:
            health_score = 0

        health_score = min(health_score, 100)

        # 01 Financial Health
        st.subheader("01 / Financial Health Score")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Financial Health",
            f"{health_score}/100"
        )

        col2.metric(
            "Savings Rate",
            f"{savings_rate:.1f}%"
        )

        col3.metric(
            "Net Balance",
            f"₹{balance:,.2f}"
        )

        st.progress(health_score / 100)

        st.caption(
            "This is an experimental spending-health indicator, "
            "not a credit score or professional financial assessment."
        )

        st.divider()

        # 02 Spending Behaviour
        st.subheader("02 / Spending Behaviour")

        if not expense_df.empty:

            category_analysis = (
                expense_df.groupby("Category")["Amount"]
                .sum()
                .sort_values(ascending=False)
            )

            highest_category = category_analysis.index[0]
            highest_amount = category_analysis.iloc[0]

            category_percentage = (
                highest_amount / total_expenses * 100
            )

            col1, col2 = st.columns(2)

            col1.metric(
                "Highest Spending Category",
                highest_category
            )

            col2.metric(
                "Share of Expenses",
                f"{category_percentage:.1f}%"
            )

            st.markdown("**Your spending distribution**")

            for category, amount in category_analysis.items():

                percentage = amount / total_expenses

                st.write(
                    f"{category} — ₹{amount:,.2f}"
                )

                st.progress(float(percentage))

        else:

            st.info("Add expenses to analyse your spending behaviour.")

        st.divider()

        
        st.subheader("Unusual Expense Detection")

        if not expense_df.empty:
            anomalies = []

            for category in expense_df["Category"].dropna().unique():
                category_data = expense_df[
                    expense_df["Category"] == category
                ].copy()

                if len(category_data) >= 3:
                    median_amount = category_data["Amount"].median()
                    threshold = median_amount * 2

                    unusual_transactions = category_data[
                        (category_data["Amount"] > threshold) &
                        ((category_data["Amount"] - median_amount) > 500)
                    ]

                    for _, transaction in unusual_transactions.iterrows():
                        anomalies.append({
                            "Date": transaction["Date"].strftime("%d %b %Y"),
                            "Category": category,
                            "Description": transaction["Description"],
                            "Amount": transaction["Amount"],
                            "Normal Median": median_amount
                        })

            if anomalies:
                anomaly_df = pd.DataFrame(anomalies)

                st.warning(
                    f"Detected {len(anomalies)} potentially unusual transactions."
                )

                st.dataframe(
                    anomaly_df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.success(
                    "No unusually high expenses detected in your current data."
                )

            st.caption(
                "Detection compares each transaction with the median spending "
                "in its category. These are potential anomalies, not confirmed fraud."
            )
        else:
            st.info("Add expenses to start detecting unusual spending.")


    

        # 04 Personalized Recommendations
        st.subheader("04 / Smart Saving Recommendations")

        recommendations = []

        if total_income <= 0:

            recommendations.append(
                "Record your income to enable a more complete "
                "financial analysis."
            )

        else:

            if savings_rate < 10:

                recommendations.append(
                    "Your savings rate is below 10%. "
                    "Try setting aside a fixed amount immediately "
                    "after receiving income."
                )

            elif savings_rate >= 30:

                recommendations.append(
                    "Your savings rate is strong. "
                    "Continue maintaining this savings habit."
                )

            else:

                recommendations.append(
                    "You are saving a portion of your income. "
                    "Consider gradually increasing that amount."
                )

            if not expense_df.empty:

                if category_percentage >= 40:

                    recommendations.append(
                        f"{highest_category} accounts for "
                        f"{category_percentage:.1f}% of your expenses. "
                        "Review whether this spending can be reduced."
                    )

                if balance < 0:

                    recommendations.append(
                        "Your recorded expenses exceed your income. "
                        "Review non-essential spending and your budget."
                    )

                if len(expense_df) >= 5:

                    recommendations.append(
                        "Review your transaction history regularly "
                        "to identify recurring expenses and "
                        "potential savings."
                    )

        for i, recommendation in enumerate(recommendations, 1):

            st.markdown(
                f"""
                <div style="
                    background:#272721;
                    border:1px solid #45443B;
                    border-left:4px solid #C9D68A;
                    padding:18px;
                    margin-bottom:12px;
                    border-radius:4px;
                    color:#F3EEE3;
                ">
                    <span style="color:#C9D68A;
                                 font-size:12px;
                                 font-weight:700;">
                        RECOMMENDATION {i:02d}
                    </span>
                    <p style="margin-bottom:0;">
                        {recommendation}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.divider()

        # 05 Monthly Spending Overview
        st.subheader("05 / Monthly Spending Overview")

        expense_df["Month"] = (
            expense_df["Date"].dt.strftime("%Y-%m")
        )

        monthly_expenses = (
            expense_df.groupby("Month")["Amount"]
            .sum()
            .reset_index()
            .sort_values("Month")
        )

        if not monthly_expenses.empty:

            fig_ai = px.line(
                monthly_expenses,
                x="Month",
                y="Amount",
                markers=True,
                title="Your Monthly Spending Trend"
            )

            fig_ai.update_layout(
                paper_bgcolor="#22221E",
                plot_bgcolor="#22221E",
                font_color="#F3EEE3"
            )

            st.plotly_chart(
                fig_ai,
                use_container_width=True
            )

    else:

        st.info(
            "Your financial intelligence report will appear "
            "after you add some transactions."
        )

        st.caption(
            "Start by recording your income and expenses."
        )


    st.divider()
    st.subheader("🔮 Predictive Expense Forecast")

    expense_df = df[df["Type"] == "Expense"].copy()

    if not expense_df.empty:
        monthly_expenses = (
            expense_df.groupby(expense_df["Date"].dt.to_period("M"))["Amount"]
            .sum()
            .sort_index()
        )

        if len(monthly_expenses) >= 2:
            recent_months = monthly_expenses.tail(3)
            predicted_expense = recent_months.mean()

            st.metric(
                "Estimated Spending Next Month",
                f"₹{predicted_expense:,.2f}"
            )

            st.caption(
                "This estimate uses the average of your last three available months."
            )

            forecast_df = pd.DataFrame({
                "Month": ["Previous Month", "Predicted Next Month"],
                "Amount": [
                    float(monthly_expenses.iloc[-1]),
                    float(predicted_expense)
                ]
            })

            forecast_chart = px.bar(
                forecast_df,
                x="Month",
                y="Amount",
                title="Actual vs Predicted Expenses",
                text_auto=".2f"
            )

            st.plotly_chart(forecast_chart, use_container_width=True)

        else:
            st.info(
                "Add expenses across at least two different months to generate a forecast."
            )
    else:
        st.info("Add some expenses first to generate a forecast.")


    st.divider()
    st.subheader("📈 Monthly Financial Health Trends")

    if not df.empty:
        df["Month"] = df["Date"].dt.to_period("M").astype(str)

        monthly_summary = df.pivot_table(
            index="Month",
            columns="Type",
            values="Amount",
            aggfunc="sum",
            fill_value=0
        ).reset_index()

        for col in ["Income", "Expense"]:
            if col not in monthly_summary.columns:
                monthly_summary[col] = 0

        monthly_summary["Savings"] = (
            monthly_summary["Income"] - monthly_summary["Expense"]
        )

        monthly_summary["Savings Rate"] = monthly_summary.apply(
            lambda row: (
                row["Savings"] / row["Income"] * 100
                if row["Income"] > 0 else 0
            ),
            axis=1
        )

        st.dataframe(monthly_summary, use_container_width=True)

        health_chart = px.line(
            monthly_summary,
            x="Month",
            y=["Income", "Expense", "Savings"],
            markers=True,
            title="Monthly Financial Performance"
        )

        st.plotly_chart(health_chart, use_container_width=True)
    else:
        st.info("Add transactions to view financial health trends.")

    
    st.divider()
    st.subheader("MONOGRAPH AI — Financial Chat Assistant")

    st.write(
        "Ask questions about your spending, savings, budgets "
        "and financial habits."
    )

    # Prepare financial context
    total_income_ai = df[df["Type"] == "Income"]["Amount"].sum()
    total_expense_ai = df[df["Type"] == "Expense"]["Amount"].sum()

    category_summary_ai = (
        df[df["Type"] == "Expense"]
        .groupby("Category")["Amount"]
        .sum()
        .to_dict()
    )

    financial_context = f"""
    You are MONOGRAPH AI, a personal finance assistant.

    Analyse the following financial data and answer the user's
    questions using this information.

    Total Income: ₹{total_income_ai:,.2f}
    Total Expenses: ₹{total_expense_ai:,.2f}
    Remaining Balance: ₹{total_income_ai - total_expense_ai:,.2f}

    Expenses by Category:
    {category_summary_ai}

    Give practical, clear and personalized financial suggestions.
    Do not invent financial information.
    If the available data is insufficient, explain that.
    Do not present yourself as a certified financial advisor.
    """

    # Maintain conversation history
    if "monograph_chat" not in st.session_state:
        st.session_state.monograph_chat = []

    # Display previous messages
    for message in st.session_state.monograph_chat:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    user_question = st.chat_input(
        "Ask MONOGRAPH AI anything about your finances..."
    )

    if user_question:
        st.session_state.monograph_chat.append({
            "role": "user",
            "content": user_question
        })

        with st.chat_message("user"):
            st.markdown(user_question)

        conversation = ""

        for message in st.session_state.monograph_chat:
            conversation += (
                f'\n{message["role"].upper()}: '
                f'{message["content"]}'
            )

        prompt = f"""
        {financial_context}

        Conversation:
        {conversation}

        Respond to the latest user question.
        """

        with st.chat_message("assistant"):
            with st.spinner("MONOGRAPH AI is analysing your finances..."):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.5-flash-lite",
                        contents=prompt
                    )

                    ai_answer = response.text

                    if not ai_answer:
                        ai_answer = "I couldn't generate a response. Please try again."

                    st.markdown(ai_answer)

                    st.session_state.monograph_chat.append({
                        "role": "assistant",
                        "content": ai_answer
                    })

                except Exception as e:
                    st.error(f"Gemini connection error: {e}")


