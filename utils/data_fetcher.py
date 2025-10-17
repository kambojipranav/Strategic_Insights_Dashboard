import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import json
import streamlit as st

class DataFetcher:
    def __init__(self):
        self.newsapi_key = None
        self.gnews_key = None
        
    def configure_keys(self, newsapi_key, gnews_key):
        """Configure API keys"""
        self.newsapi_key = newsapi_key
        self.gnews_key = gnews_key
        
        # Validate keys by making a test call
        if newsapi_key:
            test_result = self.test_newsapi_key()
            if not test_result:
                st.error("❌ Invalid NewsAPI key. Please check your key.")
                return False
        
        if gnews_key:
            test_result = self.test_gnews_key()
            if not test_result:
                st.error("❌ Invalid GNews key. Please check your key.")
                return False
                
        return True
    
    def test_newsapi_key(self):
        """Test NewsAPI key validity"""
        try:
            url = f"https://newsapi.org/v2/top-headlines?country=us&pageSize=1&apiKey={self.newsapi_key}"
            response = requests.get(url)
            return response.status_code == 200
        except:
            return False
    
    def test_gnews_key(self):
        """Test GNews key validity"""
        try:
            url = f"https://gnews.io/api/v4/top-headlines?token={self.gnews_key}&lang=en&max=1"
            response = requests.get(url)
            return response.status_code == 200
        except:
            return False
    
    def get_newsapi_articles(self, query, page_size=20, days_back=7):
        """Fetch articles from NewsAPI"""
        if not self.newsapi_key:
            st.warning("⚠️ NewsAPI key not configured")
            return pd.DataFrame()
            
        data = []
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&sortBy=publishedAt&apiKey={self.newsapi_key}&pageSize={page_size}&language=en"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                articles = response.json().get("articles", [])
                for article in articles:
                    data.append({
                        "source": "NewsAPI",
                        "query": query,
                        "title": article.get('title', ''),
                        "description": article.get('description', ''),
                        "content": article.get('content', ''),
                        "url": article.get('url', ''),
                        "published_at": article.get('publishedAt', ''),
                        "source_name": article.get('source', {}).get('name', ''),
                        "text": f"{article.get('title', '')}. {article.get('description', '') or ''}",
                        "image_url": article.get('urlToImage', '')
                    })
                st.success(f"✅ NewsAPI: Found {len(articles)} articles for '{query}'")
            else:
                st.error(f"❌ NewsAPI Error: {response.status_code} - {response.json().get('message', 'Unknown error')}")
        except Exception as e:
            st.error(f"❌ Error fetching from NewsAPI: {e}")
            
        return pd.DataFrame(data)
    
    def get_gnews_articles(self, query, max_results=20, days_back=7):
        """Fetch articles from GNews"""
        if not self.gnews_key:
            st.warning("⚠️ GNews key not configured")
            return pd.DataFrame()
            
        data = []
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        url = f"https://gnews.io/api/v4/search?q={query}&from={from_date}&token={self.gnews_key}&max={max_results}&lang=en"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                articles = response.json().get("articles", [])
                for article in articles:
                    data.append({
                        "source": "GNews",
                        "query": query,
                        "title": article.get('title', ''),
                        "description": article.get('description', ''),
                        "content": article.get('content', ''),
                        "url": article.get('url', ''),
                        "published_at": article.get('publishedAt', ''),
                        "source_name": article.get('source', {}).get('name', ''),
                        "text": f"{article.get('title', '')}. {article.get('description', '') or ''}",
                        "image_url": article.get('image', '')
                    })
                st.success(f"✅ GNews: Found {len(articles)} articles for '{query}'")
            else:
                error_msg = response.json().get('errors', ['Unknown error'])[0] if response.json().get('errors') else 'Unknown error'
                st.error(f"❌ GNews Error: {response.status_code} - {error_msg}")
        except Exception as e:
            st.error(f"❌ Error fetching from GNews: {e}")
            
        return pd.DataFrame(data)
    
    def fetch_competitor_data(self, competitors, articles_per_query=10, days_back=7):
        """Fetch data for multiple competitors"""
        all_data = []
        
        # Check if any API keys are configured
        if not self.newsapi_key and not self.gnews_key:
            st.error("❌ Please configure at least one API key to fetch data")
            return pd.DataFrame()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_queries = sum(len(queries) for queries in competitors.values())
        current_query = 0
        
        for competitor, queries in competitors.items():
            for query in queries:
                current_query += 1
                progress = current_query / total_queries
                progress_bar.progress(progress)
                status_text.text(f"Fetching data for {competitor}: '{query}'...")
                
                # Fetch from NewsAPI if key is available
                newsapi_df = pd.DataFrame()
                if self.newsapi_key:
                    newsapi_df = self.get_newsapi_articles(
                        query, page_size=articles_per_query, days_back=days_back
                    )
                
                # Fetch from GNews if key is available
                gnews_df = pd.DataFrame()
                if self.gnews_key:
                    gnews_df = self.get_gnews_articles(
                        query, max_results=articles_per_query, days_back=days_back
                    )
                
                # Add competitor tag
                if not newsapi_df.empty:
                    newsapi_df['competitor'] = competitor
                if not gnews_df.empty:
                    gnews_df['competitor'] = competitor
                
                # Combine
                combined = pd.concat([newsapi_df, gnews_df], ignore_index=True)
                if not combined.empty:
                    all_data.append(combined)
                
                # Rate limiting
                time.sleep(1)
        
        progress_bar.empty()
        status_text.empty()
        
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            final_df.dropna(subset=['text'], inplace=True)
            if not final_df.empty:
                final_df['published_at'] = pd.to_datetime(final_df['published_at'])
                final_df.reset_index(drop=True, inplace=True)
                st.success(f"🎉 Successfully fetched {len(final_df)} articles!")
            return final_df
        else:
            st.warning("⚠️ No articles found with the current configuration")
            return pd.DataFrame()