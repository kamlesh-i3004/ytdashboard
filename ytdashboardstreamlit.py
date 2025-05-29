import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# Page config
st.set_page_config(page_title="YouTube Analytics Dashboard", page_icon="📊", layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("Global YouTube Statistics.csv", encoding='latin1')
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    
    numeric_cols = [
        'video_views', 'uploads', 'subscribers', 
        'video_views_for_the_last_30_days', 'lowest_monthly_earnings',
        'highest_monthly_earnings', 'lowest_yearly_earnings',
        'highest_yearly_earnings'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Add calculated fields
    df['avg_monthly_earnings'] = (df['lowest_monthly_earnings'] + df['highest_monthly_earnings']) / 2
    df['avg_yearly_earnings'] = (df['lowest_yearly_earnings'] + df['highest_yearly_earnings']) / 2
    df['views_per_video'] = df['video_views'] / df['uploads']
    df['engagement_rate'] = df['video_views_for_the_last_30_days'] / df['video_views'] * 100
    
    return df

df = load_data()

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stMetric > label {
        font-size: 16px !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 📊 YouTube Analytics Dashboard")
st.markdown("*Comprehensive analysis of global YouTube channel statistics*")

# Sidebar filters
st.sidebar.header("🔍 Filter Options")
countries = sorted(df['country'].dropna().unique().tolist())
channel_types = sorted(df['channel_type'].dropna().unique().tolist())

selected_countries = st.sidebar.multiselect("Countries", countries, default=[])
selected_types = st.sidebar.multiselect("Channel Types", channel_types, default=[])

# Advanced filters
st.sidebar.subheader("Advanced Filters")
min_subs = st.sidebar.slider("Min Subscribers (M)", 0, int(df['subscribers'].max()/1000000), 0)
min_views = st.sidebar.slider("Min Video Views (B)", 0, int(df['video_views'].max()/1000000000), 0)
earnings_range = st.sidebar.slider(
    "Monthly Earnings Range ($K)", 
    0, int(df['highest_monthly_earnings'].max()/1000), 
    (0, int(df['highest_monthly_earnings'].max()/1000))
)

# Apply filters
filtered_df = df.copy()
if selected_countries:
    filtered_df = filtered_df[filtered_df['country'].isin(selected_countries)]
if selected_types:
    filtered_df = filtered_df[filtered_df['channel_type'].isin(selected_types)]

filtered_df = filtered_df[
    (filtered_df['subscribers'] >= min_subs * 1000000) &
    (filtered_df['video_views'] >= min_views * 1000000000) &
    (filtered_df['highest_monthly_earnings'] >= earnings_range[0] * 1000) &
    (filtered_df['highest_monthly_earnings'] <= earnings_range[1] * 1000)
]

# KPI Metrics - Enhanced
st.subheader("📈 Key Performance Indicators")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total Channels", 
        f"{len(filtered_df):,}",
        delta=f"{len(filtered_df) - len(df)} from total"
    )

with col2:
    avg_subs = filtered_df['subscribers'].mean()
    st.metric(
        "Avg Subscribers", 
        f"{avg_subs/1000000:.1f}M",
        delta=f"{(avg_subs - df['subscribers'].mean())/1000000:.1f}M"
    )

with col3:
    avg_earnings = filtered_df['avg_monthly_earnings'].mean()
    st.metric(
        "Avg Monthly Earnings", 
        f"${avg_earnings/1000:.0f}K",
        delta=f"${(avg_earnings - df['avg_monthly_earnings'].mean())/1000:.0f}K"
    )

with col4:
    avg_views = filtered_df['video_views'].mean()
    st.metric(
        "Avg Total Views", 
        f"{avg_views/1000000000:.1f}B",
        delta=f"{(avg_views - df['video_views'].mean())/1000000000:.1f}B"
    )

with col5:
    avg_engagement = filtered_df['engagement_rate'].mean()
    st.metric(
        "Avg Engagement Rate", 
        f"{avg_engagement:.1f}%",
        delta=f"{avg_engagement - df['engagement_rate'].mean():.1f}%"
    )

# Main Dashboard
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🌍 Geographic Analysis", "💰 Financial Insights", "📈 Performance Metrics"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 15 Channels by Subscribers")
        top15 = filtered_df.nlargest(15, 'subscribers')
        fig1 = px.bar(
            top15, 
            x='subscribers', 
            y='youtuber', 
            color='channel_type',
            title='Top 15 Channels by Subscribers',
            orientation='h',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig1.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("Channel Type Distribution")
        type_dist = filtered_df['channel_type'].value_counts()
        fig2 = px.pie(
            values=type_dist.values, 
            names=type_dist.index,
            title='Distribution of Channel Types',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        st.subheader("Subscribers vs Video Views")
        fig3 = px.scatter(
            filtered_df.sample(min(500, len(filtered_df))), 
            x='subscribers', 
            y='video_views',
            color='channel_type',
            size='uploads',
            hover_data=['youtuber', 'country'],
            title='Subscribers vs Total Video Views',
            log_x=True, log_y=True
        )
        st.plotly_chart(fig3, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Channels by Country")
        country_stats = filtered_df.groupby('country').agg({
            'youtuber': 'count',
            'subscribers': 'mean',
            'avg_monthly_earnings': 'mean'
        }).round(0)
        country_stats.columns = ['Channel Count', 'Avg Subscribers', 'Avg Monthly Earnings']
        country_stats = country_stats.sort_values('Channel Count', ascending=False).head(15)
        
        fig4 = px.bar(
            country_stats.reset_index(), 
            x='country', 
            y='Channel Count',
            title='Top 15 Countries by Channel Count',
            color='Channel Count',
            color_continuous_scale='viridis'
        )
        fig4.update_xaxes(tickangle=45)
        st.plotly_chart(fig4, use_container_width=True)
    
    with col2:
        st.subheader("Average Subscribers by Country")
        fig5 = px.bar(
            country_stats.reset_index().head(10), 
            x='country', 
            y='Avg Subscribers',
            title='Top 10 Countries by Average Subscribers',
            color='Avg Subscribers',
            color_continuous_scale='plasma'
        )
        fig5.update_xaxes(tickangle=45)
        st.plotly_chart(fig5, use_container_width=True)
    
    # World map (if you have country codes)
    st.subheader("Global Distribution")
    st.info("💡 Tip: Add country codes to your dataset to enable world map visualization!")

with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Earnings Distribution")
        fig6 = px.histogram(
            filtered_df[filtered_df['avg_monthly_earnings'] > 0], 
            x='avg_monthly_earnings',
            nbins=50,
            title='Distribution of Monthly Earnings',
            color_discrete_sequence=['#FF6B6B']
        )
        fig6.update_xaxes(title="Monthly Earnings ($)")
        st.plotly_chart(fig6, use_container_width=True)
    
    with col2:
        st.subheader("Earnings by Channel Type")
        earnings_by_type = filtered_df.groupby('channel_type')['avg_monthly_earnings'].mean().sort_values(ascending=False)
        fig7 = px.bar(
            x=earnings_by_type.index,
            y=earnings_by_type.values,
            title='Average Monthly Earnings by Channel Type',
            color=earnings_by_type.values,
            color_continuous_scale='blues'
        )
        fig7.update_xaxes(tickangle=45)
        st.plotly_chart(fig7, use_container_width=True)
    
    st.subheader("Top Earners")
    top_earners = filtered_df.nlargest(10, 'avg_monthly_earnings')[
        ['youtuber', 'country', 'channel_type', 'subscribers', 'avg_monthly_earnings']
    ]
    top_earners['avg_monthly_earnings'] = top_earners['avg_monthly_earnings'].apply(lambda x: f"${x:,.0f}")
    top_earners['subscribers'] = top_earners['subscribers'].apply(lambda x: f"{x/1000000:.1f}M")
    st.dataframe(top_earners, use_container_width=True)

with tab4:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Views Per Video Analysis")
        fig8 = px.scatter(
            filtered_df.sample(min(300, len(filtered_df))), 
            x='uploads', 
            y='views_per_video',
            color='channel_type',
            size='subscribers',
            hover_data=['youtuber'],
            title='Upload Count vs Views Per Video',
            log_y=True
        )
        st.plotly_chart(fig8, use_container_width=True)
    
    with col2:
        st.subheader("Engagement Rate Distribution")
        fig9 = px.box(
            filtered_df[filtered_df['engagement_rate'].notna()], 
            x='channel_type', 
            y='engagement_rate',
            title='Engagement Rate by Channel Type'
        )
        fig9.update_xaxes(tickangle=45)
        st.plotly_chart(fig9, use_container_width=True)
    
    # Correlation Matrix
    st.subheader("Performance Correlation Matrix")
    corr_cols = ['subscribers', 'video_views', 'uploads', 'views_per_video', 
                 'engagement_rate', 'avg_monthly_earnings']
    corr_data = filtered_df[corr_cols].corr()
    
    fig10 = px.imshow(
        corr_data, 
        text_auto=True, 
        aspect="auto", 
        color_continuous_scale='RdBu',
        title="Correlation Between Key Metrics"
    )
    st.plotly_chart(fig10, use_container_width=True)

# Advanced Analytics Section
st.subheader("🔍 Advanced Analytics")

col1, col2 = st.columns(2)

with col1:
    st.write("**Performance Insights:**")
    
    # Top performers by efficiency
    efficiency_metric = filtered_df['video_views'] / filtered_df['uploads']
    top_efficient = filtered_df.loc[efficiency_metric.nlargest(5).index]
    
    st.write("Most efficient channels (views per upload):")
    for _, row in top_efficient.iterrows():
        st.write(f"• **{row['youtuber']}**: {efficiency_metric[row.name]/1000000:.1f}M views/video")

with col2:
    st.write("**Growth Potential:**")
    
    # High engagement, lower subscribers (growth potential)
    potential = filtered_df[
        (filtered_df['engagement_rate'] > filtered_df['engagement_rate'].quantile(0.7)) &
        (filtered_df['subscribers'] < filtered_df['subscribers'].quantile(0.5))
    ].nlargest(5, 'engagement_rate')
    
    st.write("High engagement, growth potential:")
    for _, row in potential.iterrows():
        st.write(f"• **{row['youtuber']}**: {row['engagement_rate']:.1f}% engagement")

# Data Export
st.subheader("📤 Data Export")
col1, col2, col3 = st.columns(3)

with col1:
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download Filtered Data (CSV)",
        data=csv,
        file_name=f"youtube_data_filtered_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

with col2:
    summary_stats = filtered_df.describe()
    summary_csv = summary_stats.to_csv()
    st.download_button(
        label="Download Summary Stats (CSV)",
        data=summary_csv,
        file_name=f"youtube_summary_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# Raw Data Preview
with st.expander("📄 View Filtered Dataset"):
    st.dataframe(
        filtered_df.head(100), 
        use_container_width=True,
        height=400
    )

# Footer
st.markdown("---")
st.markdown("*Dashboard created with Streamlit • Data insights for YouTube channel analysis*")
