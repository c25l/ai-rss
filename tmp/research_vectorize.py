#!/usr/bin/env python3
"""
Simple Research Article Analysis - Pull, Vectorize, Train Decision Tree
"""
import psycopg2
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import requests
import json

def connect_db():
    """Connect to PostgreSQL"""
    return psycopg2.connect("dbname=airss host=localhost")

def pull_data():
    """Pull research articles and labels"""
    conn = connect_db()
    cur = conn.cursor()
    
    # Check table structure
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'research_reviews'")
    columns = [row[0] for row in cur.fetchall()]
    print(f"DB columns: {columns}")
    
    # Get data
    cur.execute("SELECT article_text, accepted FROM research_reviews ORDER BY created_at DESC")
    rows = cur.fetchall()
    
    articles = [row[0] for row in rows]
    labels = [row[1] for row in rows]
    
    conn.close()
    
    print(f"Loaded {len(articles)} articles")
    print(f"Acceptance rate: {sum(labels)/len(labels):.2%}")
    
    return articles, labels

def vectorize_text(text):
    """Simple text vectorization using basic features"""
    text_lower = text.lower()
    
    features = []
    
    # Basic stats
    features.append(len(text))
    features.append(len(text.split()))
    features.append(len([s for s in text.split('.') if s.strip()]))
    features.append(text.count('?'))
    features.append(text.count('!'))
    
    # Research keywords
    keywords = [
        'machine learning', 'neural', 'model', 'algorithm', 'data',
        'experiment', 'results', 'performance', 'accuracy', 'training',
        'transformer', 'embedding', 'attention', 'language', 'deep',
        'learning', 'network', 'optimization', 'loss', 'gradient',
        'parameter', 'function', 'statistical', 'probability', 'method',
        'approach', 'technique', 'framework', 'architecture', 'system'
    ]
    
    for kw in keywords:
        features.append(text_lower.count(kw))
    
    # Math/science indicators
    math_terms = ['equation', 'theorem', 'proof', 'formula', 'mathematical', 
                  'numerical', 'computational', 'analysis', 'evaluation', 'metric']
    
    for term in math_terms:
        features.append(text_lower.count(term))
    
    # Quality indicators
    quality_terms = ['novel', 'significant', 'important', 'contribution', 
                    'improvement', 'state-of-the-art', 'benchmark', 'baseline']
    
    for term in quality_terms:
        features.append(text_lower.count(term))
    
    return np.array(features)

def vectorize_with_ollama(text):
    """Try to vectorize with Ollama, fallback to simple features"""
    try:
        # Try embeddings endpoint
        response = requests.post("http://localhost:11434/api/embeddings",
                               json={"model": "qwen3:8b", "prompt": text[:1000]},
                               timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            embedding = result.get("embedding", [])
            if embedding:
                return np.array(embedding)
    except:
        pass
    
    # Fallback to simple features
    return vectorize_text(text)

def main():
    print("=== Research Article Decision Tree Analysis ===\n")
    
    # Pull data
    print("1. Pulling data from database...")
    articles, labels = pull_data()
    
    # Vectorize first few with Ollama to test
    print(f"\n2. Vectorizing {len(articles)} articles...")
    vectors = []
    
    for i, article in enumerate(articles):
        if i % 100 == 0:
            print(f"   Processing {i}/{len(articles)}")
        
        # Try Ollama for first 50, then use simple features for speed
        if i < 50:
            vector = vectorize_with_ollama(article)
        else:
            vector = vectorize_text(article)
        vectors.append(vector)
    
    # Make all vectors same length
    max_len = max(len(v) for v in vectors)
    X = np.array([np.pad(v, (0, max(0, max_len - len(v))), 'constant')[:max_len] for v in vectors])
    y = np.array(labels)
    
    print(f"   Vector shape: {X.shape}")
    
    # Train decision tree
    print("\n3. Training decision tree...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    model = DecisionTreeClassifier(max_depth=10, min_samples_split=10, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    
    print(f"\n=== RESULTS ===")
    print(f"Training Accuracy: {accuracy_score(y_train, train_pred):.3f}")
    print(f"Test Accuracy: {accuracy_score(y_test, test_pred):.3f}")
    print(f"\nTest Set Classification Report:")
    print(classification_report(y_test, test_pred, target_names=['Reject', 'Accept']))
    
    # Feature importance
    importances = model.feature_importances_
    top_indices = np.argsort(importances)[-10:][::-1]
    print(f"\nTop 10 Most Important Features:")
    for i, idx in enumerate(top_indices):
        print(f"{i+1:2d}. Feature {idx:3d}: {importances[idx]:.4f}")
    
    print(f"\nDataset Summary:")
    print(f"  Total articles: {len(articles)}")
    print(f"  Accepted: {sum(labels)} ({sum(labels)/len(labels):.1%})")
    print(f"  Rejected: {len(labels)-sum(labels)} ({(len(labels)-sum(labels))/len(labels):.1%})")

if __name__ == "__main__":
    main()