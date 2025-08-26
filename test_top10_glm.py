#!/usr/bin/env python3
"""
Test GLM with only top 10 most important features
"""
import pickle
import numpy as np
import psycopg2
import requests
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score

def connect_db():
    return psycopg2.connect("dbname=airss host=localhost")

def pull_data():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT article_text, accepted FROM research_reviews ORDER BY created_at DESC")
    rows = cur.fetchall()
    
    articles = [row[0] for row in rows]
    labels = np.array([int(row[1]) for row in rows])
    conn.close()
    
    print(f"Loaded {len(articles)} articles")
    return articles, labels

def get_nomic_embedding(text):
    try:
        response = requests.post("http://localhost:11434/api/embeddings",
                               json={"model": "nomic-embed-text", "prompt": text[:8000]},
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            embedding = result.get("embedding", [])
            if embedding and len(embedding) == 768:
                return np.array(embedding)
        return None
    except:
        return None

def vectorize_articles(articles):
    print(f"Vectorizing {len(articles)} articles...")
    embeddings = []
    
    for i, article in enumerate(articles):
        if i % 100 == 0:
            print(f"  Progress: {i}/{len(articles)}")
        
        embedding = get_nomic_embedding(article)
        if embedding is not None:
            embeddings.append(embedding)
        else:
            embeddings.append(np.zeros(768))
    
    return np.array(embeddings)

def main():
    print("=== Testing GLM with Top 10 Features ===\n")
    
    # Get data
    articles, labels = pull_data()
    embeddings = vectorize_articles(articles)
    
    # Standardize
    scaler = StandardScaler()
    embeddings_scaled = scaler.fit_transform(embeddings)
    
    # Split data (same random state as full model)
    X_train, X_test, y_train, y_test = train_test_split(
        embeddings_scaled, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    # Top 10 feature indices from the full GLM analysis
    top_10_features = [569, 369, 344, 256, 546, 491, 618, 76, 272, 506]
    
    # Extract only top 10 features
    X_train_top10 = X_train[:, top_10_features]
    X_test_top10 = X_test[:, top_10_features]
    
    print(f"Using features: {top_10_features}")
    print(f"Training on {X_train_top10.shape} data")
    print(f"Testing on {X_test_top10.shape} data")
    
    # Train GLM with only top 10 features
    glm_top10 = LogisticRegression(
        penalty='l2',
        C=1.0,  # Less regularization needed with fewer features
        solver='liblinear',
        max_iter=1000,
        random_state=42,
        class_weight='balanced'
    )
    
    glm_top10.fit(X_train_top10, y_train)
    
    # Evaluate
    train_pred = glm_top10.predict(X_train_top10)
    test_pred = glm_top10.predict(X_test_top10)
    
    train_pred_proba = glm_top10.predict_proba(X_train_top10)[:, 1]
    test_pred_proba = glm_top10.predict_proba(X_test_top10)[:, 1]
    
    train_acc = accuracy_score(y_train, train_pred)
    test_acc = accuracy_score(y_test, test_pred)
    test_auc = roc_auc_score(y_test, test_pred_proba)
    
    print(f"\n=== Results ===")
    print(f"Training Accuracy: {train_acc:.3f}")
    print(f"Test Accuracy: {test_acc:.3f}")
    print(f"Test AUC-ROC: {test_auc:.3f}")
    
    print(f"\nClassification Report (Top 10 GLM):")
    print(classification_report(y_test, test_pred, target_names=['Reject', 'Accept']))
    
    # Show coefficients
    print(f"\nTop 10 Feature Coefficients:")
    print(f"Intercept: {glm_top10.intercept_[0]:.4f}")
    for i, (feature_idx, coef) in enumerate(zip(top_10_features, glm_top10.coef_[0])):
        direction = "➕" if coef > 0 else "➖"
        print(f"Feature {feature_idx}: {coef:+.4f} {direction}")
    
    # Compare to full model
    print(f"\n=== Comparison ===")
    print(f"Full GLM (768 features): 72.9% accuracy, 0.797 AUC")
    print(f"Top 10 GLM: {test_acc:.1%} accuracy, {test_auc:.3f} AUC")
    
    accuracy_diff = test_acc - 0.729
    auc_diff = test_auc - 0.797
    print(f"Difference: {accuracy_diff:+.1%} accuracy, {auc_diff:+.3f} AUC")

if __name__ == "__main__":
    main()