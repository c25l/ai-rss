#!/usr/bin/env python3
"""
Research Article Vectorization and Decision Tree Analysis
Pulls research articles from PostgreSQL, vectorizes with Ollama, trains decision tree to predict acceptance
"""
import psycopg2
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import requests
import json
import sys
import os

class ResearchAnalyzer:
    def __init__(self):
        self.articles_df = None
        self.vectors = None
        self.labels = None
        self.model = None
        
    def connect_to_db(self):
        """Connect to PostgreSQL database"""
        try:
            dsn = "dbname=airss host=localhost"
            conn = psycopg2.connect(dsn)
            return conn
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    
    def pull_research_data(self):
        """Pull all records from research_reviews table"""
        conn = self.connect_to_db()
        if not conn:
            return False
            
        try:
            # First check what columns exist
            cur = conn.cursor()
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'research_reviews'")
            columns = [row[0] for row in cur.fetchall()]
            print(f"Available columns in research_reviews: {columns}")
            
            query = """
                SELECT article_text, accepted, created_at 
                FROM research_reviews 
                ORDER BY created_at DESC
            """
            self.articles_df = pd.read_sql(query, conn)
            conn.close()
            
            print(f"Pulled {len(self.articles_df)} research articles from database")
            print(f"Acceptance rate: {self.articles_df['accepted'].mean():.2%}")
            return True
            
        except Exception as e:
            print(f"Error pulling data: {e}")
            if conn:
                conn.close()
            return False
    
    def vectorize_with_ollama(self, text, model="qwen3:8b"):
        """Vectorize text using local Ollama API"""
        try:
            # Use embeddings endpoint if available
            payload = {
                "model": model,
                "prompt": text
            }
            
            # Try embeddings endpoint first
            response = requests.post("http://localhost:11434/api/embeddings", 
                                   json={"model": model, "prompt": text},
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return np.array(result.get("embedding", []))
            
            # Fallback to generate endpoint for basic vectorization
            response = requests.post("http://localhost:11434/api/generate",
                                   json={
                                       "model": model,
                                       "prompt": f"Convert this text to numerical features. Extract key semantic features as numbers: {text[:1000]}",
                                       "stream": False,
                                       "options": {"temperature": 0}
                                   },
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                # Extract numbers from response as simple vectorization fallback
                import re
                numbers = re.findall(r'-?\d+\.?\d*', result.get("response", ""))
                if numbers:
                    return np.array([float(x) for x in numbers[:100]])  # Limit to 100 features
                else:
                    # Use simple text features as last resort
                    return self.simple_text_features(text)
            
            return self.simple_text_features(text)
            
        except Exception as e:
            print(f"Ollama vectorization error: {e}")
            return self.simple_text_features(text)
    
    def simple_text_features(self, text):
        """Simple text features as fallback"""
        features = []
        text_lower = text.lower()
        
        # Basic text statistics
        features.append(len(text))
        features.append(len(text.split()))
        features.append(len(text.split('.')) - 1)  # sentences
        features.append(text.count('?'))
        features.append(text.count('!'))
        
        # Key research terms
        research_terms = ['machine learning', 'neural', 'model', 'algorithm', 'data', 
                         'experiment', 'results', 'performance', 'accuracy', 'training',
                         'transformer', 'embedding', 'llm', 'language model', 'attention']
        
        for term in research_terms:
            features.append(text_lower.count(term))
        
        # Mathematical indicators
        math_indicators = ['equation', 'theorem', 'proof', 'statistical', 'probability',
                          'optimization', 'gradient', 'loss', 'function', 'parameter']
        
        for indicator in math_indicators:
            features.append(text_lower.count(indicator))
        
        return np.array(features[:50])  # Limit to 50 features
    
    def vectorize_all_articles(self):
        """Vectorize all articles using Ollama"""
        if self.articles_df is None:
            print("No articles loaded. Run pull_research_data() first.")
            return False
        
        print("Vectorizing articles with Ollama...")
        vectors = []
        
        for i, text in enumerate(self.articles_df['article_text']):
            if i % 10 == 0:
                print(f"Processed {i}/{len(self.articles_df)} articles")
            
            vector = self.vectorize_with_ollama(text)
            vectors.append(vector)
        
        # Ensure all vectors have the same length
        max_len = max(len(v) for v in vectors)
        padded_vectors = []
        
        for v in vectors:
            if len(v) < max_len:
                padded = np.pad(v, (0, max_len - len(v)), mode='constant')
            else:
                padded = v[:max_len]
            padded_vectors.append(padded)
        
        self.vectors = np.array(padded_vectors)
        self.labels = self.articles_df['accepted'].values
        
        print(f"Vectorization complete. Shape: {self.vectors.shape}")
        return True
    
    def train_decision_tree(self):
        """Train decision tree to predict acceptance"""
        if self.vectors is None or self.labels is None:
            print("No vectorized data. Run vectorize_all_articles() first.")
            return False
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            self.vectors, self.labels, test_size=0.2, random_state=42, 
            stratify=self.labels if len(np.unique(self.labels)) > 1 else None
        )
        
        # Train decision tree
        self.model = DecisionTreeClassifier(
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)
        
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        
        print(f"\n=== Decision Tree Results ===")
        print(f"Training Accuracy: {train_acc:.3f}")
        print(f"Test Accuracy: {test_acc:.3f}")
        print(f"\nClassification Report (Test Set):")
        print(classification_report(y_test, test_pred))
        print(f"\nConfusion Matrix (Test Set):")
        print(confusion_matrix(y_test, test_pred))
        
        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            top_features = np.argsort(importances)[-10:][::-1]
            print(f"\nTop 10 Most Important Features:")
            for i, feat_idx in enumerate(top_features):
                print(f"{i+1:2d}. Feature {feat_idx:3d}: {importances[feat_idx]:.4f}")
        
        return True
    
    def run_full_analysis(self):
        """Run complete analysis pipeline"""
        print("Starting Research Article Analysis...")
        
        if not self.pull_research_data():
            return False
            
        if not self.vectorize_all_articles():
            return False
            
        if not self.train_decision_tree():
            return False
        
        print("\nAnalysis complete!")
        return True

def main():
    analyzer = ResearchAnalyzer()
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main()