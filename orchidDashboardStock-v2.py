import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.io as pio
from io import BytesIO
from fpdf import FPDF
from datetime import datetime

# Load translation
@st.cache_data
def load_translations(language):
    with open("translations.json", "r", encoding="utf-8") as f:
        translations = json.load(f)
    return translations.get(language, translations["English"])

# Load CSV data
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/your-username/your-repo/main/data/portfolio.csv"  # Replace with your actual GitHub raw link
    df = pd.read_csv("portfolio.csv")
    df["transaction date"] = pd.to_datetime(df["transaction date"])
    df["holding period days"] = (pd.Timestamp.today() - df["transaction date"]).dt.days
    return df

# Translate UI elements
def t(key, lang_dict):
    return lang_dict.get(key, key)

# Sidebar settings
st.sidebar.title("Settings")
language = st.sidebar.selectbox("Select Language", ["English", "Tamil"])
lang_dict = load_translations(language)

# Main dashboard
st.title(t("Stock Portfolio Dashboard", lang_dict))
data = load_data()

# Filter selection options
st.sidebar.subheader(t("Filter Portfolio", lang_dict))
reset_filters = st.sidebar.button(t("Reset Filters", lang_dict))

if "filters_applied" not in st.session_state or reset_filters:
    st.session_state.filters_applied = {
        "family": [],
        "broker": [],
        "sector": [],
        "stock": []
    }

st.session_state.filters_applied["family"] = st.sidebar.multiselect(
    t("Family Member", lang_dict), options=sorted(data["family member name"].unique()), default=st.session_state.filters_applied["family"])

st.session_state.filters_applied["broker"] = st.sidebar.multiselect(
    t("Broker", lang_dict), options=sorted(data["broker name"].unique()), default=st.session_state.filters_applied["broker"])

st.session_state.filters_applied["sector"] = st.sidebar.multiselect(
    t("Sector", lang_dict), options=sorted(data["sector code"].unique()), default=st.session_state.filters_applied["sector"])

st.session_state.filters_applied["stock"] = st.sidebar.multiselect(
    t("Stock Code", lang_dict), options=sorted(data["stock code"].unique()), default=st.session_state.filters_applied["stock"])

# Apply filters
if st.session_state.filters_applied["family"]:
    data = data[data["family member name"].isin(st.session_state.filters_applied["family"])]
if st.session_state.filters_applied["broker"]:
    data = data[data["broker name"].isin(st.session_state.filters_applied["broker"])]
if st.session_state.filters_applied["sector"]:
    data = data[data["sector code"].isin(st.session_state.filters_applied["sector"])]
if st.session_state.filters_applied["stock"]:
    data = data[data["stock code"].isin(st.session_state.filters_applied["stock"])]

# Selection options
sort_options = {
    t("Family Member", lang_dict): "family member name",
    t("Sector", lang_dict): "sector code",
    t("Broker", lang_dict): "broker name",
    t("Stock Code", lang_dict): "stock code"
}

sort_choice = st.selectbox(t("Sort Portfolio By", lang_dict), list(sort_options.keys()))
sort_field = sort_options[sort_choice]

# Sort data
sorted_data = data.sort_values(by=[sort_field])

# Summary section (moved to top)
st.subheader(t("Summary by", lang_dict) + f" {sort_choice}")
summary = sorted_data.groupby(sort_field).agg({
    "invested amount": "sum",
    "current value": "sum"
}).reset_index()

summary["return_raw"] = ((summary["current value"] - summary["invested amount"]) / summary["invested amount"]) * 100
summary["invested amount"] = summary["invested amount"].apply(lambda x: f"₹{x:,.0f}")
summary["current value"] = summary["current value"].apply(lambda x: f"₹{x:,.0f}")
summary["return (%)"] = summary["return_raw"].apply(lambda x: f"{x:.2f}%")
summary = summary.drop(columns="return_raw")

# Add total row
total_row = {sort_field: "Total",
             "invested amount": f"₹{data['invested amount'].sum():,.0f}",
             "current value": f"₹{data['current value'].sum():,.0f}",
             "return (%)": f"{((data['current value'].sum() - data['invested amount'].sum()) / data['invested amount'].sum()) * 100:.2f}%"}
summary = pd.concat([summary, pd.DataFrame([total_row])], ignore_index=True)

summary.index = summary.index + 1
summary.reset_index(inplace=True)
summary.rename(columns={"index": "S.No"}, inplace=True)
st.dataframe(summary)

# Display sorted data with formatting
st.subheader(t("Detailed Portfolio Data", lang_dict))
display_data = sorted_data.copy()
display_data["invested amount"] = display_data["invested amount"].apply(lambda x: f"₹{x:,.0f}")
display_data["current value"] = display_data["current value"].apply(lambda x: f"₹{x:,.0f}")
display_data["return (%)"] = ((sorted_data["current value"] - sorted_data["invested amount"]) / sorted_data["invested amount"]) * 100
display_data["return (%)"] = display_data["return (%)"].apply(lambda x: f"{x:.2f}%")

# Highlight negative returns
def highlight_negative(val):
    try:
        return 'color: red' if float(val.replace('%','')) < 0 else ''
    except:
        return ''

st.dataframe(display_data.style.applymap(highlight_negative, subset=["return (%)"]))

# Pie chart of current value distribution
st.subheader(t("Current Value Distribution", lang_dict))
pie_chart = px.pie(summary, names=sort_field, values="current value", title=t("Current Value Distribution", lang_dict))
st.plotly_chart(pie_chart)

# Bar chart of return percentage
st.subheader(t("Return Percentage by", lang_dict) + f" {sort_choice}")
bar_chart = px.bar(summary, x=sort_field, y="return (%)", title=t("Return Percentage by", lang_dict) + f" {sort_choice}",
                   color="return (%)", color_continuous_scale="Blues")
st.plotly_chart(bar_chart)

# Average beta / correlation metrics
if "portfolio metrics code" in data.columns:
    st.subheader(t("Average Portfolio Metrics", lang_dict))
    avg_metrics = data.groupby(sort_field)["portfolio metrics code"].mean().reset_index()
    avg_metrics.columns = [sort_field, "average metrics"]
    st.dataframe(avg_metrics)

    metrics_bar = px.bar(avg_metrics, x=sort_field, y="average metrics",
                         title=t("Average Portfolio Metrics by", lang_dict) + f" {sort_choice}",
                         color="average metrics", color_continuous_scale="Greens")
    st.plotly_chart(metrics_bar)

# Show full data toggle
if st.checkbox(t("Show Full Data", lang_dict)):
    st.write(data)
