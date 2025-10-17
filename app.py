import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Import custom modules
from utils.data_fetcher import DataFetcher
from utils.analyzer import SentimentAnalyzer
import config

# Page configuration
st.set_page_config(
    page_title="Strategic Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with light theme
def load_css():
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 700;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin: 1.5rem 0 1rem 0;
        font-weight: 600;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 0.5rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .positive-sentiment { 
        background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
    }
    .negative-sentiment { 
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
    }
    .neutral-sentiment { 
        background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
    }
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 25px;
        font-weight: 600;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        color: white;
    }
    .alert-box {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 5px solid;
    }
    .alert-success {
        background-color: #d4edda;
        border-color: #28a745;
        color: #155724;
    }
    .alert-warning {
        background-color: #fff3cd;
        border-color: #ffc107;
        color: #856404;
    }
    .alert-danger {
        background-color: #f8d7da;
        border-color: #dc3545;
        color: #721c24;
    }
    </style>
    """, unsafe_allow_html=True)

class StrategicIntelligenceDashboard:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.analyzer = SentimentAnalyzer()
        self.df = None
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'api_keys_configured' not in st.session_state:
            st.session_state.api_keys_configured = False
        if 'news_data' not in st.session_state:
            st.session_state.news_data = pd.DataFrame()
        if 'analysis_complete' not in st.session_state:
            st.session_state.analysis_complete = False
    
    def render_api_key_input(self):
        """Render API key input section"""
        st.sidebar.header("🔑 API Configuration")
        
        with st.sidebar.expander("Configure API Keys", expanded=not st.session_state.api_keys_configured):
            st.info("Enter your API keys to fetch real-time data")
            
            newsapi_key = st.text_input(
                "NewsAPI Key",
                type="password",
                placeholder="Enter your NewsAPI key...",
                help="Get your key from https://newsapi.org"
            )
            
            gnews_key = st.text_input(
                "GNews Key", 
                type="password",
                placeholder="Enter your GNews key...",
                help="Get your key from https://gnews.io"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔒 Save API Keys", use_container_width=True):
                    if newsapi_key or gnews_key:
                        success = self.data_fetcher.configure_keys(newsapi_key, gnews_key)
                        if success:
                            st.session_state.api_keys_configured = True
                            st.session_state.newsapi_key = newsapi_key
                            st.session_state.gnews_key = gnews_key
                            st.success("✅ API keys configured successfully!")
                            st.rerun()
                    else:
                        st.error("❌ Please enter at least one API key")
            
            with col2:
                if st.button("🔄 Use Sample Data", use_container_width=True):
                    st.session_state.api_keys_configured = True
                    st.session_state.news_data = self.create_sample_data()
                    st.session_state.analysis_complete = True
                    st.success("✅ Loaded sample data for demonstration!")
                    st.rerun()
    
    def render_data_fetching_section(self):
        """Render data fetching controls"""
        st.sidebar.header("📥 Data Configuration")
        
        # Competitor selection
        selected_competitors = st.sidebar.multiselect(
            "Select Competitors to Analyze",
            options=list(config.COMPETITORS.keys()),
            default=list(config.COMPETITORS.keys())[:3],
            help="Choose which competitors to include in the analysis"
        )
        
        # Articles per query
        articles_per_query = st.sidebar.slider(
            "Articles per Query",
            min_value=5,
            max_value=50,
            value=15,
            help="Number of articles to fetch per search query"
        )
        
        # Date range
        days_back = st.sidebar.slider(
            "Analysis Period (Days)",
            min_value=1,
            max_value=90,
            value=30,
            help="How far back to search for articles"
        )
        
        # Fetch data button
        if st.sidebar.button("🚀 Fetch & Analyze Data", type="primary", use_container_width=True):
            if not selected_competitors:
                st.sidebar.error("❌ Please select at least one competitor")
                return
            
            # Create competitor dictionary
            competitors_to_analyze = {comp: config.COMPETITORS[comp] for comp in selected_competitors}
            
            # Fetch data
            with st.spinner("🔄 Fetching news data from APIs..."):
                fetched_data = self.data_fetcher.fetch_competitor_data(
                    competitors=competitors_to_analyze,
                    articles_per_query=articles_per_query,
                    days_back=days_back
                )
            
            if not fetched_data.empty:
                # Analyze sentiment
                with st.spinner("🧠 Analyzing sentiment and emotions..."):
                    analyzed_data = self.analyzer.analyze_dataframe(fetched_data)
                
                st.session_state.news_data = analyzed_data
                st.session_state.analysis_complete = True
                st.success("✅ Data analysis complete! Check the dashboard below.")
                st.rerun()
            else:
                st.error("❌ No data fetched. Please check your API keys and try again.")
    
    def render_dashboard_controls(self):
        """Render dashboard controls"""
        st.sidebar.header("🎛️ Dashboard Controls")
        
        # Analysis type
        analysis_type = st.sidebar.selectbox(
            "Analysis Focus",
            options=['Overall Dashboard', 'Competitor Comparison', 'Trend Analysis', 'Emotion Analysis', 'Source Analysis'],
            help="Choose what type of analysis to focus on"
        )
        
        # Sentiment filters
        sentiment_filter = st.sidebar.multiselect(
            "Filter by Sentiment",
            options=['Positive', 'Negative', 'Neutral'],
            default=['Positive', 'Negative', 'Neutral'],
            help="Filter articles by sentiment"
        )
        
        # Source filters
        available_sources = []
        if not st.session_state.news_data.empty:
            available_sources = st.session_state.news_data['source'].unique().tolist()
        
        source_filter = st.sidebar.multiselect(
            "Filter by Source",
            options=available_sources,
            default=available_sources,
            help="Filter articles by news source"
        )
        
        return {
            'analysis_type': analysis_type,
            'sentiment_filter': sentiment_filter,
            'source_filter': source_filter
        }
    
    def create_sample_data(self):
        """Create comprehensive sample data for demonstration"""
        sample_data = []
        competitors = list(config.COMPETITORS.keys())
        sources = ['NewsAPI', 'GNews', 'Reuters', 'Bloomberg', 'TechCrunch']
        emotions = ['Joy', 'Fear', 'Anger', 'Surprise', 'Sadness', 'Neutral']
        
        # Create more realistic date distribution
        base_date = datetime.now()
        
        for i in range(200):  # More sample data
            competitor = np.random.choice(competitors)
            sentiment = np.random.choice(['Positive', 'Negative', 'Neutral'], 
                                       p=[0.4, 0.3, 0.3])
            
            # Generate appropriate scores and emotions based on sentiment
            if sentiment == 'Positive':
                score = np.random.uniform(0.1, 0.9)
                emotion = np.random.choice(['Joy', 'Surprise'], p=[0.7, 0.3])
            elif sentiment == 'Negative':
                score = np.random.uniform(-0.9, -0.1)
                emotion = np.random.choice(['Fear', 'Anger', 'Sadness'], p=[0.5, 0.3, 0.2])
            else:
                score = np.random.uniform(-0.1, 0.1)
                emotion = 'Neutral'
            
            # Create more realistic dates
            days_ago = np.random.randint(0, 30)
            hours_ago = np.random.randint(0, 24)
            published_date = base_date - timedelta(days=days_ago, hours=hours_ago)
            
            sample_data.append({
                'competitor': competitor,
                'title': f'{competitor} announces {["breakthrough", "partnership", "earnings", "product"][i % 4]} in {["AI", "semiconductors", "technology", "market"][i % 4]}',
                'text': f'This is a detailed news article about {competitor} and their recent developments in the technology sector. Market analysts are watching closely.',
                'published_at': published_date,
                'source': np.random.choice(sources),
                'sentiment_label': sentiment,
                'sentiment_score': round(score, 3),
                'vader_score': round(score * np.random.uniform(0.8, 1.2), 3),
                'textblob_score': round(score * np.random.uniform(0.8, 1.2), 3),
                'subjectivity': round(np.random.uniform(0.3, 0.9), 3),
                'emotion': emotion,
                'entities': [competitor, np.random.choice(['AI', 'GPU', 'CPU', 'semiconductor']), 'technology'],
                'url': f'https://example.com/article/{i}'
            })
        
        df = pd.DataFrame(sample_data)
        df['published_at'] = pd.to_datetime(df['published_at'])
        return df
    
    def render_kpi_metrics(self, filtered_df):
        """Render KPI metrics at the top"""
        st.markdown("### 📈 Key Performance Indicators")
        
        if filtered_df.empty:
            st.warning("No data available for the selected filters.")
            return
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_articles = len(filtered_df)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Articles</div>
                <div class="metric-value">{total_articles}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            positive_articles = len(filtered_df[filtered_df['sentiment_label'] == 'Positive'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Positive Articles</div>
                <div class="metric-value">{positive_articles}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            negative_articles = len(filtered_df[filtered_df['sentiment_label'] == 'Negative'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Negative Articles</div>
                <div class="metric-value">{negative_articles}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            avg_sentiment = filtered_df['sentiment_score'].mean()
            sentiment_color = "positive-sentiment" if avg_sentiment > 0.1 else "negative-sentiment" if avg_sentiment < -0.1 else "neutral-sentiment"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Avg Sentiment</div>
                <div class="metric-value {sentiment_color}">{avg_sentiment:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            unique_sources = filtered_df['source'].nunique()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">News Sources</div>
                <div class="metric-value">{unique_sources}</div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_sentiment_analysis(self, filtered_df):
        """Render sentiment analysis section"""
        st.markdown('<div class="section-header">📊 Sentiment Analysis</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment distribution pie chart
            sentiment_counts = filtered_df['sentiment_label'].value_counts()
            fig = px.pie(
                values=sentiment_counts.values,
                names=sentiment_counts.index,
                title="Sentiment Distribution",
                color=sentiment_counts.index,
                color_discrete_map={
                    'Positive': '#2ecc71',
                    'Negative': '#e74c3c',
                    'Neutral': '#f39c12'
                }
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Sentiment distribution by competitor
            sentiment_by_competitor = pd.crosstab(
                filtered_df['competitor'], 
                filtered_df['sentiment_label']
            )
            fig = px.bar(
                sentiment_by_competitor,
                title="Sentiment Distribution by Competitor",
                barmode='stack',
                color_discrete_map={
                    'Positive': '#2ecc71',
                    'Negative': '#e74c3c',
                    'Neutral': '#f39c12'
                }
            )
            fig.update_layout(xaxis_title="Competitor", yaxis_title="Number of Articles")
            st.plotly_chart(fig, use_container_width=True)
    
    def render_competitor_comparison(self, filtered_df):
        """Render competitor comparison section"""
        st.markdown('<div class="section-header">🏢 Competitor Comparison</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Average sentiment by competitor
            avg_sentiment = filtered_df.groupby('competitor')['sentiment_score'].mean().sort_values()
            fig = px.bar(
                x=avg_sentiment.values,
                y=avg_sentiment.index,
                orientation='h',
                title="Average Sentiment Score by Competitor",
                color=avg_sentiment.values,
                color_continuous_scale='RdYlGn',
                color_continuous_midpoint=0
            )
            fig.update_layout(xaxis_title="Sentiment Score", yaxis_title="Competitor")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Sentiment score distribution
            fig = px.box(
                filtered_df,
                x='competitor',
                y='sentiment_score',
                title="Sentiment Score Distribution by Competitor",
                color='competitor'
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # Competitor performance matrix
        st.markdown("#### Competitor Performance Matrix")
        competitor_stats = filtered_df.groupby('competitor').agg({
            'sentiment_score': ['mean', 'count'],
            'subjectivity': 'mean'
        }).round(3)
        competitor_stats.columns = ['Avg Sentiment', 'Article Count', 'Avg Subjectivity']
        competitor_stats = competitor_stats.sort_values('Avg Sentiment', ascending=False)
        
        st.dataframe(competitor_stats.style.background_gradient(
            subset=['Avg Sentiment'], cmap='RdYlGn'
        ), use_container_width=True)
    
    def render_trend_analysis(self, filtered_df):
        """Render trend analysis section"""
        st.markdown('<div class="section-header">📈 Trend Analysis</div>', unsafe_allow_html=True)
        
        # Convert to datetime and extract date
        filtered_df['date'] = pd.to_datetime(filtered_df['published_at']).dt.date
        
        # Daily sentiment trend
        daily_sentiment = filtered_df.groupby(['date', 'competitor'])['sentiment_score'].mean().reset_index()
        
        fig = px.line(
            daily_sentiment,
            x='date',
            y='sentiment_score',
            color='competitor',
            title="Daily Sentiment Trend by Competitor",
            markers=True
        )
        fig.update_layout(xaxis_title="Date", yaxis_title="Average Sentiment Score")
        st.plotly_chart(fig, use_container_width=True)
        
        # Additional trend charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Volume trend
            daily_volume = filtered_df.groupby('date').size().reset_index(name='count')
            fig = px.area(
                daily_volume,
                x='date',
                y='count',
                title="Daily Article Volume Trend"
            )
            fig.update_layout(xaxis_title="Date", yaxis_title="Number of Articles")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Sentiment trend with moving average
            sentiment_trend = filtered_df.groupby('date')['sentiment_score'].mean().reset_index()
            sentiment_trend['moving_avg'] = sentiment_trend['sentiment_score'].rolling(window=3).mean()
            
            fig = px.line(
                sentiment_trend,
                x='date',
                y=['sentiment_score', 'moving_avg'],
                title="Overall Sentiment Trend (with 3-day Moving Average)",
                labels={'value': 'Sentiment Score', 'variable': 'Metric'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render_emotion_analysis(self, filtered_df):
        """Render emotion analysis section"""
        st.markdown('<div class="section-header">😊 Emotion Analysis</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Emotion distribution
            emotion_counts = filtered_df['emotion'].value_counts()
            fig = px.pie(
                values=emotion_counts.values,
                names=emotion_counts.index,
                title="Emotion Distribution in Articles"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Emotion by competitor heatmap
            emotion_by_competitor = pd.crosstab(
                filtered_df['competitor'],
                filtered_df['emotion'],
                normalize='index'
            )
            fig = px.imshow(
                emotion_by_competitor,
                title="Emotion Distribution Heatmap by Competitor",
                aspect="auto",
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Emotion-sentiment correlation
        st.markdown("#### Emotion vs Sentiment Analysis")
        emotion_sentiment = filtered_df.groupby('emotion')['sentiment_score'].agg(['mean', 'count']).round(3)
        emotion_sentiment.columns = ['Average Sentiment', 'Number of Articles']
        emotion_sentiment = emotion_sentiment.sort_values('Average Sentiment', ascending=False)
        
        st.dataframe(emotion_sentiment.style.background_gradient(
            subset=['Average Sentiment'], cmap='RdYlGn'
        ), use_container_width=True)
    
    def render_source_analysis(self, filtered_df):
        """Render source analysis section"""
        st.markdown('<div class="section-header">📰 Source Analysis</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Source distribution
            source_counts = filtered_df['source'].value_counts().head(10)
            fig = px.bar(
                x=source_counts.values,
                y=source_counts.index,
                orientation='h',
                title="Top 10 News Sources",
                color=source_counts.values,
                color_continuous_scale='viridis'
            )
            fig.update_layout(xaxis_title="Number of Articles", yaxis_title="Source")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Sentiment by source
            source_sentiment = filtered_df.groupby('source')['sentiment_score'].mean().sort_values().tail(10)
            fig = px.bar(
                x=source_sentiment.values,
                y=source_sentiment.index,
                orientation='h',
                title="Average Sentiment by Source (Top 10)",
                color=source_sentiment.values,
                color_continuous_scale='RdYlGn',
                color_continuous_midpoint=0
            )
            fig.update_layout(xaxis_title="Average Sentiment Score", yaxis_title="Source")
            st.plotly_chart(fig, use_container_width=True)
    
    def render_entity_analysis(self, filtered_df):
        """Render entity analysis section"""
        st.markdown('<div class="section-header">🔍 Key Entities & Topics</div>', unsafe_allow_html=True)
        
        # Extract all entities
        all_entities = []
        for entities in filtered_df['entities']:
            if isinstance(entities, list):
                all_entities.extend(entities)
        
        entity_counts = pd.Series(all_entities).value_counts().head(15)
        
        fig = px.bar(
            x=entity_counts.values,
            y=entity_counts.index,
            orientation='h',
            title="Top 15 Mentioned Entities",
            color=entity_counts.values,
            color_continuous_scale='viridis'
        )
        fig.update_layout(xaxis_title="Frequency", yaxis_title="Entity")
        st.plotly_chart(fig, use_container_width=True)
    
    def render_alert_system(self, filtered_df):
        """Render alert system"""
        st.markdown('<div class="section-header">🚨 Key Alerts & Insights</div>', unsafe_allow_html=True)
        
        if filtered_df.empty:
            st.info("No data available for generating alerts.")
            return
        
        alerts = []
        
        # Check for negative sentiment spikes in last 3 days
        recent_cutoff = datetime.now() - timedelta(days=3)
        recent_data = filtered_df[filtered_df['published_at'] >= recent_cutoff]
        
        if not recent_data.empty:
            negative_spike = recent_data[recent_data['sentiment_label'] == 'Negative']
            if len(negative_spike) > 8:
                alerts.append({
                    'type': 'danger',
                    'message': f"⚠️ High negative sentiment spike: {len(negative_spike)} negative articles in last 3 days",
                    'severity': 'High'
                })
            
            # Check for positive momentum
            positive_spike = recent_data[recent_data['sentiment_label'] == 'Positive']
            if len(positive_spike) > 10:
                alerts.append({
                    'type': 'success',
                    'message': f"📈 Strong positive momentum: {len(positive_spike)} positive articles in last 3 days",
                    'severity': 'Medium'
                })
        
        # Competitor-specific alerts
        for competitor in filtered_df['competitor'].unique():
            comp_data = filtered_df[filtered_df['competitor'] == competitor]
            avg_sentiment = comp_data['sentiment_score'].mean()
            article_count = len(comp_data)
            
            if avg_sentiment < -0.3 and article_count > 5:
                alerts.append({
                    'type': 'warning',
                    'message': f"🔴 {competitor} showing strongly negative sentiment ({avg_sentiment:.2f}) across {article_count} articles",
                    'severity': 'High'
                })
            elif avg_sentiment > 0.4 and article_count > 5:
                alerts.append({
                    'type': 'success',
                    'message': f"🟢 {competitor} showing strongly positive sentiment ({avg_sentiment:.2f}) across {article_count} articles",
                    'severity': 'Medium'
                })
        
        # Display alerts
        if not alerts:
            st.success("🎉 No critical alerts at this time. Market sentiment appears stable.")
        else:
            for alert in alerts:
                if alert['type'] == 'danger':
                    st.markdown(f'<div class="alert-box alert-danger">🚨 {alert["message"]}</div>', unsafe_allow_html=True)
                elif alert['type'] == 'warning':
                    st.markdown(f'<div class="alert-box alert-warning">⚠️ {alert["message"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="alert-box alert-success">✅ {alert["message"]}</div>', unsafe_allow_html=True)
    
    def render_raw_data(self, filtered_df):
        """Render raw data table"""
        st.markdown('<div class="section-header">📋 Article Details</div>', unsafe_allow_html=True)
        
        if filtered_df.empty:
            st.info("No data available to display.")
            return
        
        # Show data table with sentiment coloring
        display_columns = ['competitor', 'title', 'source', 'published_at', 'sentiment_label', 'sentiment_score', 'emotion']
        
        # Create a styled dataframe
        display_df = filtered_df[display_columns].copy()
        display_df['published_at'] = display_df['published_at'].dt.strftime('%Y-%m-%d %H:%M')
        
        # Add download button
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv,
            file_name="strategic_intelligence_data.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # Display the dataframe
        st.dataframe(display_df, use_container_width=True)
    
    def run(self):
        """Main method to run the dashboard"""
        load_css()
        
        # Header
        st.markdown('<h1 class="main-header">🎯 Strategic Intelligence Dashboard</h1>', unsafe_allow_html=True)
        st.markdown("### Real-time Market Intelligence & Sentiment Analysis")
        
        # API Key Input Section
        self.render_api_key_input()
        
        if not st.session_state.api_keys_configured:
            st.info("👆 Please configure your API keys in the sidebar to get started, or use sample data for demonstration.")
            return
        
        # Data Fetching Section
        self.render_data_fetching_section()
        
        if not st.session_state.analysis_complete:
            st.info("🚀 Configure your analysis parameters in the sidebar and click 'Fetch & Analyze Data' to begin.")
            
            # Show sample dashboard preview
            st.markdown("---")
            st.subheader("📊 Dashboard Preview")
            st.info("This is a preview of what your dashboard will look like. Configure API keys and fetch data to see real insights!")
            return
        
        # Dashboard Controls
        filters = self.render_dashboard_controls()
        
        # Filter data based on selections
        filtered_df = st.session_state.news_data.copy()
        
        # Apply sentiment filter
        if filters['sentiment_filter']:
            filtered_df = filtered_df[filtered_df['sentiment_label'].isin(filters['sentiment_filter'])]
        
        # Apply source filter
        if filters['source_filter']:
            filtered_df = filtered_df[filtered_df['source'].isin(filters['source_filter'])]
        
        # Main Dashboard
        if filtered_df.empty:
            st.warning("No data matches the selected filters. Please adjust your filter criteria.")
            return
        
        # Render all components based on analysis type
        analysis_type = filters['analysis_type']
        
        # Always show KPIs and Alerts
        self.render_kpi_metrics(filtered_df)
        self.render_alert_system(filtered_df)
        
        # Show analysis based on selected type
        if analysis_type == 'Overall Dashboard':
            self.render_sentiment_analysis(filtered_df)
            self.render_competitor_comparison(filtered_df)
            self.render_entity_analysis(filtered_df)
            self.render_source_analysis(filtered_df)
        
        elif analysis_type == 'Competitor Comparison':
            self.render_competitor_comparison(filtered_df)
            self.render_sentiment_analysis(filtered_df)
        
        elif analysis_type == 'Trend Analysis':
            self.render_trend_analysis(filtered_df)
            self.render_sentiment_analysis(filtered_df)
        
        elif analysis_type == 'Emotion Analysis':
            self.render_emotion_analysis(filtered_df)
            self.render_sentiment_analysis(filtered_df)
        
        elif analysis_type == 'Source Analysis':
            self.render_source_analysis(filtered_df)
            self.render_entity_analysis(filtered_df)
        
        # Always show raw data at the bottom
        st.markdown("---")
        self.render_raw_data(filtered_df)
        
        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: #666;'>"
            "Strategic Intelligence Dashboard • Built with Streamlit • "
            "Data sources: NewsAPI, GNews"
            "</div>",
            unsafe_allow_html=True
        )

# Run the dashboard
if __name__ == "__main__":
    dashboard = StrategicIntelligenceDashboard()
    dashboard.run()