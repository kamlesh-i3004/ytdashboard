
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv(r"C:\Users\Kamlesh\Documents\Code aur Masti\hexintern\Global YouTube Statistics.csv", encoding='latin1')
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    numeric_cols = [
        "subscribers", "video_views", "uploads", "video_views_rank", "country_rank",
        "channel_type_rank", "subscribers_for_last_30_days", "video_views_for_the_last_30_days",
        "lowest_monthly_earnings", "highest_monthly_earnings", "lowest_yearly_earnings",
        "highest_yearly_earnings"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("Filter Options")
countries = df['country'].dropna().unique().tolist()
channel_types = df['channel_type'].dropna().unique().tolist()

selected_country = st.sidebar.selectbox("Country", ["All"] + countries)
selected_type = st.sidebar.selectbox("Channel Type", ["All"] + channel_types)
min_subs = st.sidebar.slider("Min Subscribers", 0, int(df['subscribers'].max()), 0)

# Apply filters
filtered_df = df.copy()
if selected_country != "All":
    filtered_df = filtered_df[filtered_df['country'] == selected_country]
if selected_type != "All":
    filtered_df = filtered_df[filtered_df['channel_type'] == selected_type]
filtered_df = filtered_df[filtered_df['subscribers'] >= min_subs]

# Title
st.title("📊 YouTube Channel Dashboard")

# KPI Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Channels", len(filtered_df))
col2.metric("Average Subscribers", f"{int(filtered_df['subscribers'].mean()):,}")
col3.metric("Avg. Monthly Earnings", f"${int(filtered_df['highest_monthly_earnings'].mean()):,}")

# Charts
st.subheader("Top 10 Channels by Subscribers")
top10 = filtered_df.sort_values(by='subscribers', ascending=False).head(10)
fig = px.bar(top10, x='youtuber', y='subscribers', color='country', title='Top 10 Channels')
st.plotly_chart(fig, use_container_width=True)

st.subheader("Monthly vs Yearly Earnings Distribution")
earnings = filtered_df[['lowest_monthly_earnings', 'highest_monthly_earnings', 'lowest_yearly_earnings', 'highest_yearly_earnings']]
st.line_chart(earnings)

st.subheader("Correlation Heatmap")
corr = filtered_df.select_dtypes(include=np.number).corr()
fig2 = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='blues')
st.plotly_chart(fig2, use_container_width=True)

# Data preview
st.subheader("📄 Filtered Data Preview")
st.dataframe(filtered_df.head(20))
