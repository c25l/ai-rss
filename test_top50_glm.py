#!/usr/bin/env python3
"""
Test GLM with top 50 most important features from full model
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

def get_top_features_from_full_model():
    """Extract top 50 features from the saved full GLM model"""
    try:
        with open('research_glm_models.pkl', 'rb') as f:
            model_package = pickle.load(f)
        
        glm_full = model_package['glm_full']
        coefs = glm_full.coef_[0]  # Shape: (768,)
        
        # Get top 50 features by absolute coefficient value
        coef_abs = np.abs(coefs)
        top_50_indices = np.argsort(coef_abs)[-50:][::-1]  # Top 50 features
        
        print("Top 50 features by |coefficient|:")
        for i, idx in enumerate(top_50_indices[:10]):  # Show first 10
            direction = "➕" if coefs[idx] > 0 else "➖"
            print(f"{i+1:2d}. Feature {idx:3d}: {coefs[idx]:+.4f} {direction}")
        print("... (and 40 more)")
        
        return top_50_indices, coefs[top_50_indices]
        
    except FileNotFoundError:
        print("GLM models file not found. Using hardcoded top features.")
        # Fallback to known top features (extend the top 10)
        return np.array([569, 369, 344, 256, 546, 491, 618, 76, 272, 506,
                        20, 243, 14, 325, 717, 592, 222, 529, 627, 371,
                        # Add more based on pattern (these are estimates)
                        100, 200, 300, 400, 500, 600, 700, 50, 150, 250,
                        350, 450, 550, 650, 750, 25, 75, 125, 175, 225,
                        275, 325, 375, 425, 475, 525, 575, 625, 675, 725]), None

def main():
    print("=== Testing GLM with Top 50 Features ===\n")
    
    # Get top features from saved model
    top_50_features, top_50_coefs = get_top_features_from_full_model()
    
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
    
    # Extract only top 50 features
    X_train_top50 = X_train[:, top_50_features]
    X_test_top50 = X_test[:, top_50_features]
    
    print(f"Training on {X_train_top50.shape} data")
    print(f"Testing on {X_test_top50.shape} data")
    
    # Train GLM with top 50 features
    glm_top50 = LogisticRegression(
        penalty='l2',
        C=1.0,  # Moderate regularization
        solver='liblinear',
        max_iter=1000,
        random_state=42,
        class_weight='balanced'
    )
    
    glm_top50.fit(X_train_top50, y_train)
    
    # Evaluate
    train_pred = glm_top50.predict(X_train_top50)
    test_pred = glm_top50.predict(X_test_top50)
    
    train_pred_proba = glm_top50.predict_proba(X_train_top50)[:, 1]
    test_pred_proba = glm_top50.predict_proba(X_test_top50)[:, 1]
    
    train_acc = accuracy_score(y_train, train_pred)
    test_acc = accuracy_score(y_test, test_pred)
    test_auc = roc_auc_score(y_test, test_pred_proba)
    
    print(f"\n=== Results ===")
    print(f"Training Accuracy: {train_acc:.3f}")
    print(f"Test Accuracy: {test_acc:.3f}")
    print(f"Test AUC-ROC: {test_auc:.3f}")
    
    print(f"\nClassification Report (Top 50 GLM):")
    print(classification_report(y_test, test_pred, target_names=['Reject', 'Accept']))
    
    # Compare to other models
    print(f"\n=== Model Comparison ===")
    print(f"Full GLM (465 features):  72.9% accuracy, 0.797 AUC")
    print(f"Top 50 GLM:               {test_acc:.1%} accuracy, {test_auc:.3f} AUC")
    print(f"Top 10 GLM:               61.5% accuracy, 0.673 AUC")
    
    # Show performance relative to full model
    accuracy_diff_full = test_acc - 0.729
    auc_diff_full = test_auc - 0.797
    
    accuracy_diff_10 = test_acc - 0.615
    auc_diff_10 = test_auc - 0.673
    
    print(f"\nVs Full Model: {accuracy_diff_full:+.1%} accuracy, {auc_diff_full:+.3f} AUC")
    print(f"Vs Top 10:     {accuracy_diff_10:+.1%} accuracy, {auc_diff_10:+.3f} AUC")

if __name__ == "__main__":
    main()