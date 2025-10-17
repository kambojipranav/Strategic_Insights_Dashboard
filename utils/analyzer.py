import pandas as pd
import numpy as np
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
from collections import Counter
from datetime import datetime
import streamlit as st

class SentimentAnalyzer:
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()
    
    def clean_text(self, text):
        """Clean text for analysis"""
        if pd.isna(text):
            return ""
        text = str(text)
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\!\?]', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def analyze_sentiment_vader(self, text):
        """Analyze sentiment using VADER"""
        cleaned_text = self.clean_text(text)
        scores = self.vader_analyzer.polarity_scores(cleaned_text)
        
        # Determine sentiment label
        compound = scores['compound']
        if compound >= 0.05:
            sentiment_label = "Positive"
        elif compound <= -0.05:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"
            
        return {
            "sentiment_label": sentiment_label,
            "sentiment_score": compound,
            "positive_score": scores['pos'],
            "negative_score": scores['neg'],
            "neutral_score": scores['neu']
        }
    
    def analyze_sentiment_textblob(self, text):
        """Analyze sentiment using TextBlob"""
        cleaned_text = self.clean_text(text)
        analysis = TextBlob(cleaned_text)
        
        polarity = analysis.sentiment.polarity
        subjectivity = analysis.sentiment.subjectivity
        
        # Determine sentiment label
        if polarity > 0.1:
            sentiment_label = "Positive"
        elif polarity < -0.1:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"
            
        return {
            "sentiment_label_tb": sentiment_label,
            "sentiment_score_tb": polarity,
            "subjectivity": subjectivity
        }
    
    def extract_entities(self, text):
        """Extract key entities using simple pattern matching"""
        cleaned_text = self.clean_text(text)
        
        # Common tech companies and products
        entities = []
        tech_keywords = [
            'NVIDIA', 'AMD', 'Intel', 'TSMC', 'Qualcomm', 'Apple', 'Google',
            'Microsoft', 'Amazon', 'Meta', 'Tesla', 'AI', 'GPU', 'CPU',
            'semiconductor', 'chip', 'processor', 'earnings', 'stock', 'market',
            'technology', 'innovation', 'research', 'development', 'investment'
        ]
        
        for keyword in tech_keywords:
            if keyword.lower() in cleaned_text.lower():
                entities.append(keyword)
        
        return list(set(entities))  # Remove duplicates
    
    def analyze_emotion(self, text):
        """Basic emotion detection based on keywords"""
        cleaned_text = self.clean_text(text).lower()
        
        emotion_keywords = {
            'Joy': ['growth', 'profit', 'success', 'win', 'gain', 'positive', 'bullish', 'optimistic', 'achievement', 'breakthrough'],
            'Fear': ['drop', 'fall', 'loss', 'risk', 'concern', 'worry', 'bearish', 'pessimistic', 'uncertainty', 'volatility'],
            'Anger': ['sue', 'lawsuit', 'fight', 'conflict', 'dispute', 'angry', 'frustrated', 'controversy', 'allegation'],
            'Surprise': ['unexpected', 'surprise', 'shock', 'sudden', 'unanticipated', 'announcement', 'release', 'launch'],
            'Sadness': ['decline', 'loss', 'miss', 'disappoint', 'cut', 'reduce', 'layoff', 'downturn', 'recession']
        }
        
        emotion_scores = {emotion: 0 for emotion in emotion_keywords.keys()}
        
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in cleaned_text:
                    emotion_scores[emotion] += 1
        
        # Get dominant emotion
        if sum(emotion_scores.values()) == 0:
            dominant_emotion = "Neutral"
        else:
            dominant_emotion = max(emotion_scores, key=emotion_scores.get)
            
        return dominant_emotion
    
    def comprehensive_analysis(self, text):
        """Perform comprehensive sentiment analysis"""
        vader_result = self.analyze_sentiment_vader(text)
        textblob_result = self.analyze_sentiment_textblob(text)
        entities = self.extract_entities(text)
        emotion = self.analyze_emotion(text)
        
        # Combine results - weighted average
        combined_score = (vader_result['sentiment_score'] * 0.6 + 
                         textblob_result['sentiment_score_tb'] * 0.4)
        
        # Final sentiment determination
        if combined_score >= 0.1:
            final_sentiment = "Positive"
        elif combined_score <= -0.1:
            final_sentiment = "Negative"
        else:
            final_sentiment = "Neutral"
        
        return {
            "sentiment_label": final_sentiment,
            "sentiment_score": round(combined_score, 3),
            "vader_score": round(vader_result['sentiment_score'], 3),
            "textblob_score": round(textblob_result['sentiment_score_tb'], 3),
            "subjectivity": round(textblob_result['subjectivity'], 3),
            "emotion": emotion,
            "entities": entities,
            "analysis_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def analyze_dataframe(self, df, text_column='text'):
        """Analyze sentiment for entire dataframe"""
        if df.empty:
            return df
            
        st.info("🧠 Starting comprehensive sentiment analysis...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        analysis_results = []
        total_rows = len(df)
        
        for idx, row in df.iterrows():
            if pd.isna(row[text_column]):
                analysis_results.append({
                    "sentiment_label": "Unknown",
                    "sentiment_score": 0.0,
                    "vader_score": 0.0,
                    "textblob_score": 0.0,
                    "subjectivity": 0.0,
                    "emotion": "Neutral",
                    "entities": [],
                    "analysis_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            else:
                analysis = self.comprehensive_analysis(row[text_column])
                analysis_results.append(analysis)
            
            # Update progress
            progress = (idx + 1) / total_rows
            progress_bar.progress(progress)
            status_text.text(f"Analyzing article {idx + 1}/{total_rows}...")
        
        progress_bar.empty()
        status_text.empty()
        
        # Convert to DataFrame and combine with original
        analysis_df = pd.DataFrame(analysis_results)
        final_df = pd.concat([df.reset_index(drop=True), analysis_df], axis=1)
        
        st.success("✅ Sentiment analysis complete!")
        return final_df