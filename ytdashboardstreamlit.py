import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

st.set_page_config(page_title="YouTube Analytics Dashboard", page_icon="📊", layout="wide")

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
#header            
st.markdown("# 📊 YouTube Analytics Dashboard")
st.markdown("*Comprehensive analysis of global YouTube channel statistics*")

#sidebar
st.sidebar.header("🔍 Filter Options")
countries = sorted(df['country'].dropna().unique().tolist())
channel_types = sorted(df['channel_type'].dropna().unique().tolist())

selected_countries = st.sidebar.multiselect("Countries", countries, default=[])
selected_types = st.sidebar.multiselect("Channel Types", channel_types, default=[])

#advanced
st.sidebar.subheader("Advanced Filters")
min_subs = st.sidebar.slider("Min Subscribers (M)", 0, int(df['subscribers'].max()/1000000), 0)
min_views = st.sidebar.slider("Min Video Views (B)", 0, int(df['video_views'].max()/1000000000), 0)
earnings_range = st.sidebar.slider(
    "Monthly Earnings Range ($K)", 
    0, int(df['highest_monthly_earnings'].max()/1000), 
    (0, int(df['highest_monthly_earnings'].max()/1000))
)

#apply
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

#kpimetrics
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

#search&compare
st.subheader("🔍 Channel Search & Compare")
col1, col2 = st.columns(2)

with col1:
    search_term = st.text_input("Search for a specific channel:", placeholder="Type channel name...")
    if search_term:
        matches = filtered_df[filtered_df['youtuber'].str.contains(search_term, case=False, na=False)]
        if not matches.empty:
            st.write(f"Found {len(matches)} matches:")
            for _, channel in matches.head(5).iterrows():
                st.write(f"🎬 **{channel['youtuber']}** ({channel['country']}) - {channel['subscribers']/1000000:.1f}M subs")

with col2:
    #channelcompare
    available_channels = filtered_df['youtuber'].dropna().tolist()[:100]  # Limit for performance
    compare_channels = st.multiselect("Compare Channels (max 5):", available_channels, max_selections=5)
    
    if compare_channels:
        comparison_data = filtered_df[filtered_df['youtuber'].isin(compare_channels)]
        metrics_to_compare = ['subscribers', 'video_views', 'uploads', 'avg_monthly_earnings']
        
        fig_compare = px.bar(
            comparison_data.melt(id_vars=['youtuber'], value_vars=metrics_to_compare),
            x='youtuber', y='value', color='variable', barmode='group',
            title="Channel Comparison", facet_col='variable', facet_col_wrap=2
        )
        fig_compare.update_yaxes(matches=None)
        st.plotly_chart(fig_compare, use_container_width=True)

#randchannel
st.subheader("🎲 Random Channel Spotlight")
if st.button("Discover Random Channel"):
    random_channel = filtered_df.sample(1).iloc[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        ### 🎬 {random_channel['youtuber']}
        **Country:** {random_channel['country']}  
        **Type:** {random_channel['channel_type']}
        """)
    
    with col2:
        st.metric("Subscribers", f"{random_channel['subscribers']/1000000:.1f}M")
        st.metric("Total Views", f"{random_channel['video_views']/1000000000:.1f}B")
        
    with col3:
        st.metric("Videos Uploaded", f"{int(random_channel['uploads'])}")
        if pd.notna(random_channel['avg_monthly_earnings']):
            st.metric("Est. Monthly Earnings", f"${random_channel['avg_monthly_earnings']:,.0f}")

#maindash
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🌍 Geographic Analysis", "💰 Financial Insights", "📈 Performance Metrics", "🏆 Leaderboards"])

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
    
    #worldmap
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
    
    #correlationmatrix
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
with tab5:
    st.subheader("🏆 YouTube Leaderboards")
    
    #leaderboard
    leaderboard_type = st.selectbox(
        "Choose Leaderboard:", 
        ["👑 Most Subscribers", "👀 Most Views", "📹 Most Videos", "💰 Highest Earners", 
         "🔥 Best Engagement", "⚡ Most Efficient", "🌟 Hidden Gems"]
    )
    
    if leaderboard_type == "👑 Most Subscribers":
        top_channels = filtered_df.nlargest(20, 'subscribers')
        display_cols = ['youtuber', 'country', 'subscribers', 'channel_type']
        
    elif leaderboard_type == "👀 Most Views":
        top_channels = filtered_df.nlargest(20, 'video_views')
        display_cols = ['youtuber', 'country', 'video_views', 'channel_type']
        
    elif leaderboard_type == "📹 Most Videos":
        top_channels = filtered_df.nlargest(20, 'uploads')
        display_cols = ['youtuber', 'country', 'uploads', 'channel_type']
        
    elif leaderboard_type == "💰 Highest Earners":
        top_channels = filtered_df.nlargest(20, 'avg_monthly_earnings')
        display_cols = ['youtuber', 'country', 'avg_monthly_earnings', 'channel_type']
        
    elif leaderboard_type == "🔥 Best Engagement":
        top_channels = filtered_df.nlargest(20, 'engagement_rate')
        display_cols = ['youtuber', 'country', 'engagement_rate', 'channel_type']
        
    elif leaderboard_type == "⚡ Most Efficient":
        top_channels = filtered_df.nlargest(20, 'views_per_video')
        display_cols = ['youtuber', 'country', 'views_per_video', 'channel_type']
        
    else:
        #highenglowsubs
        gems = filtered_df[
            (filtered_df['engagement_rate'] > filtered_df['engagement_rate'].quantile(0.6)) &
            (filtered_df['subscribers'] < filtered_df['subscribers'].quantile(0.4))
        ].nlargest(20, 'engagement_rate')
        top_channels = gems
        display_cols = ['youtuber', 'country', 'engagement_rate', 'subscribers', 'channel_type']
    
    #rankleaderboard
    if not top_channels.empty:
        leaderboard_display = top_channels[display_cols].reset_index(drop=True)
        leaderboard_display.index += 1 
        leaderboard_display.index.name = 'Rank'
        
        for col in leaderboard_display.columns:
            if col == 'subscribers' or col == 'video_views':
                leaderboard_display[col] = leaderboard_display[col].apply(lambda x: f"{x/1000000:.1f}M" if pd.notna(x) else "N/A")
            elif col == 'avg_monthly_earnings':
                leaderboard_display[col] = leaderboard_display[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
            elif col == 'views_per_video':
                leaderboard_display[col] = leaderboard_display[col].apply(lambda x: f"{x/1000000:.1f}M" if pd.notna(x) else "N/A")
            elif col == 'engagement_rate':
                leaderboard_display[col] = leaderboard_display[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
        
        st.dataframe(leaderboard_display, use_container_width=True)
        
        #top3
        st.subheader("🥇 Top 3 Spotlight")
        cols = st.columns(3)
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (idx, channel) in enumerate(top_channels.head(3).iterrows()):
            with cols[i]:
                st.markdown(f"""
                <div style="background: linear-gradient(45deg, #FFD700, #FFA500); padding: 15px; border-radius: 10px; text-align: center; color: white; margin: 10px 0;">
                    <h3>{medals[i]} #{i+1}</h3>
                    <h4>{channel['youtuber']}</h4>
                    <p>{channel['country']} • {channel['channel_type']}</p>
                </div>
                """, unsafe_allow_html=True)

#funfact
st.subheader("🎯 Fun Facts & Quick Stats")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 🌍 Global Reach
    """)
    unique_countries = filtered_df['country'].nunique()
    st.info(f"📍 Channels from **{unique_countries}** different countries!")
    
    most_common_country = filtered_df['country'].value_counts().index[0]
    country_count = filtered_df['country'].value_counts().iloc[0]
    st.info(f"🏆 **{most_common_country}** leads with **{country_count}** channels!")

with col2:
    st.markdown("""
    ### 💰 Money Talks
    """)
    total_monthly_earnings = filtered_df['avg_monthly_earnings'].sum()
    st.success(f"💸 Combined monthly earnings: **${total_monthly_earnings/1000000:.1f}M**")
    
    median_earnings = filtered_df['avg_monthly_earnings'].median()
    st.info(f"📊 Median monthly earnings: **${median_earnings:,.0f}**")

with col3:
    st.markdown("""
    ### 📺 Content Stats
    """)
    total_videos = filtered_df['uploads'].sum()
    st.info(f"🎬 Total videos uploaded: **{total_videos:,.0f}**")
    
    avg_videos_per_channel = filtered_df['uploads'].mean()
    st.info(f"📹 Average videos per channel: **{avg_videos_per_channel:.0f}**")

#quiz
st.subheader("🎮 YouTube Trivia Challenge")

if st.button("🎲 Generate Random Trivia Question"):
    quiz_type = np.random.choice(['highest', 'country', 'type', 'compare'])
    
    if quiz_type == 'highest':
        top_channel = filtered_df.nlargest(1, 'subscribers').iloc[0]
        st.warning(f"❓ **Which channel has the most subscribers in your filtered data?**")
        if st.button("Show Answer 👀"):
            st.success(f"🎉 **{top_channel['youtuber']}** with {top_channel['subscribers']/1000000:.1f}M subscribers!")
    
    elif quiz_type == 'country':
        random_country = filtered_df['country'].dropna().sample(1).iloc[0]
        country_channels = filtered_df[filtered_df['country'] == random_country]
        st.warning(f"❓ **How many channels are from {random_country}?**")
        if st.button("Show Answer 👀"):
            st.success(f"🎉 There are **{len(country_channels)}** channels from {random_country}!")
    
    elif quiz_type == 'type':
        most_common_type = filtered_df['channel_type'].value_counts().index[0]
        type_count = filtered_df['channel_type'].value_counts().iloc[0]
        st.warning(f"❓ **What's the most common channel type?**")
        if st.button("Show Answer 👀"):
            st.success(f"🎉 **{most_common_type}** with **{type_count}** channels!")
    
    else:  # compare
        two_channels = filtered_df.sample(2)
        ch1, ch2 = two_channels.iloc[0], two_channels.iloc[1]
        st.warning(f"❓ **Who has more subscribers: {ch1['youtuber']} or {ch2['youtuber']}?**")
        if st.button("Show Answer 👀"):
            winner = ch1 if ch1['subscribers'] > ch2['subscribers'] else ch2
            st.success(f"🎉 **{winner['youtuber']}** wins with {winner['subscribers']/1000000:.1f}M subscribers!")

#insights
st.subheader("📋 Data Quality Check")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Missing Data Overview")
    missing_data = filtered_df.isnull().sum()
    missing_data = missing_data[missing_data > 0].sort_values(ascending=False)
    
    if not missing_data.empty:
        fig_missing = px.bar(
            x=missing_data.values, 
            y=missing_data.index,
            orientation='h',
            title="Missing Values by Column",
            color=missing_data.values,
            color_continuous_scale='reds'
        )
        st.plotly_chart(fig_missing, use_container_width=True)
    else:
        st.success("✅ No missing data in filtered dataset!")

with col2:
    st.markdown("### Data Ranges")
    
    #dataranges
    st.write("**Subscriber Range:**")
    st.write(f"Min: {filtered_df['subscribers'].min()/1000:.0f}K | Max: {filtered_df['subscribers'].max()/1000000:.0f}M")
    
    st.write("**Upload Count Range:**")
    st.write(f"Min: {filtered_df['uploads'].min():.0f} | Max: {filtered_df['uploads'].max():.0f}")
    
    if filtered_df['avg_monthly_earnings'].notna().any():
        st.write("**Monthly Earnings Range:**")
        min_earn = filtered_df['avg_monthly_earnings'].min()
        max_earn = filtered_df['avg_monthly_earnings'].max()
        st.write(f"Min: ${min_earn:,.0f} | Max: ${max_earn:,.0f}")

#categorychannel
st.subheader("🎭 Channel Categories Deep Dive")

category_stats = filtered_df.groupby('channel_type').agg({
    'youtuber': 'count',
    'subscribers': ['mean', 'median', 'max'],
    'avg_monthly_earnings': ['mean', 'median'],
    'uploads': 'mean'
}).round(2)

category_stats.columns = ['Count', 'Avg Subscribers', 'Median Subscribers', 'Max Subscribers', 
                         'Avg Earnings', 'Median Earnings', 'Avg Videos']

#formatnumber
category_stats['Avg Subscribers'] = category_stats['Avg Subscribers'].apply(lambda x: f"{x/1000000:.1f}M")
category_stats['Median Subscribers'] = category_stats['Median Subscribers'].apply(lambda x: f"{x/1000000:.1f}M")
category_stats['Max Subscribers'] = category_stats['Max Subscribers'].apply(lambda x: f"{x/1000000:.1f}M")
category_stats['Avg Earnings'] = category_stats['Avg Earnings'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
category_stats['Median Earnings'] = category_stats['Median Earnings'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")

st.dataframe(category_stats, use_container_width=True)

#extraanalysis
st.subheader("🔍 Advanced Analytics")

col1, col2 = st.columns(2)

with col1:
    st.write("**Performance Insights:**")
    
    #topperformer
    efficiency_metric = filtered_df['video_views'] / filtered_df['uploads']
    top_efficient = filtered_df.loc[efficiency_metric.nlargest(5).index]
    
    st.write("Most efficient channels (views per upload):")
    for _, row in top_efficient.iterrows():
        st.write(f"• **{row['youtuber']}**: {efficiency_metric[row.name]/1000000:.1f}M views/video")

with col2:
    st.write("**Growth Potential:**")
    
    #highenglowsubs
    potential = filtered_df[
        (filtered_df['engagement_rate'] > filtered_df['engagement_rate'].quantile(0.7)) &
        (filtered_df['subscribers'] < filtered_df['subscribers'].quantile(0.5))
    ].nlargest(5, 'engagement_rate')
    
    st.write("High engagement, growth potential:")
    for _, row in potential.iterrows():
        st.write(f"• **{row['youtuber']}**: {row['engagement_rate']:.1f}% engagement")

#exportdata
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

#rawrpeview
with st.expander("📄 View Filtered Dataset"):
    st.dataframe(
        filtered_df.head(100), 
        use_container_width=True,
        height=400
    )

#footer
st.markdown("---")
st.markdown("*Dashboard created with Streamlit • Data insights for YouTube channel analysis*")
