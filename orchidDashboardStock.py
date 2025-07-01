import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.io as pio
from io import BytesIO
from fpdf import FPDF

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
    return pd.read_csv(url)

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

# Sort and display
sorted_data = data.sort_values(by=[sort_field])
st.dataframe(sorted_data)

# Summary section
st.subheader(t("Summary by", lang_dict) + f" {sort_choice}")
summary = sorted_data.groupby(sort_field).agg({
    "quantity": "sum",
    "invested amount": "sum",
    "current value": "sum",
    "holding period days": "mean"
}).reset_index()

summary["return (%)"] = ((summary["current value"] - summary["invested amount"]) / summary["invested amount"]) * 100
st.dataframe(summary)

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
