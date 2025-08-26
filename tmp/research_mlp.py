#!/usr/bin/env python3
"""
Research Article MLP Analysis with nomic-embed-text embeddings
"""
import psycopg2
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
import requests
import pickle
import json
import os

class ResearchMLP:
    def __init__(self):
        self.articles = None
        self.labels = None
        self.embeddings = None
        self.model = None
        
    def connect_db(self):
        """Connect to PostgreSQL"""
        return psycopg2.connect("dbname=airss host=localhost")
    
    def pull_data(self):
        """Pull research articles and labels"""
        conn = self.connect_db()
        cur = conn.cursor()
        
        cur.execute("SELECT article_text, accepted FROM research_reviews ORDER BY created_at DESC")
        rows = cur.fetchall()
        
        self.articles = [row[0] for row in rows]
        self.labels = np.array([int(row[1]) for row in rows])
        
        conn.close()
        
        print(f"Loaded {len(self.articles)} articles")
        print(f"Acceptance rate: {self.labels.mean():.2%}")
        
    def get_nomic_embedding(self, text):
        """Get embedding from nomic-embed-text via Ollama"""
        try:
            response = requests.post("http://localhost:11434/api/embeddings",
                                   json={"model": "nomic-embed-text", "prompt": text[:8000]},
                                   timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get("embedding", [])
                if embedding and len(embedding) == 768:  # nomic should be 768-dim
                    return np.array(embedding)
            
            print(f"Warning: Failed to get embedding, status: {response.status_code}")
            return None
            
        except Exception as e:
            print(f"Embedding error: {e}")
            return None
    
    def vectorize_all_articles(self):
        """Vectorize all articles with nomic-embed-text"""
        if self.articles is None:
            print("No articles loaded. Run pull_data() first.")
            return False
        
        print(f"Vectorizing {len(self.articles)} articles with nomic-embed-text...")
        embeddings = []
        failed_indices = []
        
        for i, article in enumerate(self.articles):
            if i % 50 == 0:
                print(f"  Progress: {i}/{len(self.articles)}")
            
            embedding = self.get_nomic_embedding(article)
            if embedding is not None:
                embeddings.append(embedding)
            else:
                embeddings.append(np.zeros(768))  # fallback to zeros
                failed_indices.append(i)
        
        self.embeddings = np.array(embeddings)
        
        print(f"Vectorization complete!")
        print(f"  Shape: {self.embeddings.shape}")
        print(f"  Failed embeddings (using zeros): {len(failed_indices)}")
        
        return True
    
    def build_mlp(self):
        """Build MLP architecture"""
        model = Sequential([
            Dense(256, activation='relu', input_shape=(768,)),
            Dropout(0.2),
            Dense(64, activation='relu'),
            Dropout(0.2),
            Dense(1, activation='sigmoid')
        ])
        
        # Handle class imbalance with class weights
        pos_weight = (len(self.labels) - np.sum(self.labels)) / np.sum(self.labels)
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        return pos_weight
    
    def train_model(self):
        """Train the MLP model"""
        if self.embeddings is None or self.labels is None:
            print("No data loaded. Run vectorize_all_articles() first.")
            return False
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            self.embeddings, self.labels, test_size=0.2, random_state=42, stratify=self.labels
        )
        
        print(f"Training set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")
        
        # Build model
        pos_weight = self.build_mlp()
        print(f"Class weights - Positive class weight: {pos_weight:.2f}")
        
        # Calculate class weights for training
        class_weight = {0: 1.0, 1: pos_weight}
        
        # Early stopping
        early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        
        # Train
        print("\nTraining MLP...")
        history = self.model.fit(
            X_train, y_train,
            validation_split=0.2,
            epochs=100,
            batch_size=32,
            class_weight=class_weight,
            callbacks=[early_stop],
            verbose=1
        )
        
        # Evaluate
        print("\n=== EVALUATION ===")
        
        # Predictions
        train_pred_proba = self.model.predict(X_train).flatten()
        test_pred_proba = self.model.predict(X_test).flatten()
        
        train_pred = (train_pred_proba > 0.5).astype(int)
        test_pred = (test_pred_proba > 0.5).astype(int)
        
        # Metrics
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        test_auc = roc_auc_score(y_test, test_pred_proba)
        
        print(f"Training Accuracy: {train_acc:.3f}")
        print(f"Test Accuracy: {test_acc:.3f}")
        print(f"Test AUC-ROC: {test_auc:.3f}")
        
        print(f"\nTest Set Classification Report:")
        print(classification_report(y_test, test_pred, target_names=['Reject', 'Accept']))
        
        # Show some probability examples
        print(f"\nSample Predictions (Probability of Acceptance):")
        indices = np.random.choice(len(y_test), 10, replace=False)
        for i in indices:
            prob = test_pred_proba[i]
            actual = 'Accept' if y_test.iloc[i] else 'Reject'
            print(f"  Actual: {actual:6s} | Predicted Prob: {prob:.3f}")
        
        return history, (X_test, y_test, test_pred_proba)
    
    def save_model(self, base_path="research_mlp"):
        """Save model in multiple formats"""
        if self.model is None:
            print("No model to save. Train first.")
            return
        
        # Save Keras model (.h5)
        h5_path = f"{base_path}.h5"
        self.model.save(h5_path)
        print(f"Saved Keras model: {h5_path}")
        
        # Save model + metadata as pickle
        model_data = {
            'model': self.model,
            'architecture': {
                'input_dim': 768,
                'hidden_layers': [256, 64],
                'output_dim': 1,
                'activation': 'relu',
                'final_activation': 'sigmoid'
            },
            'training_info': {
                'total_samples': len(self.labels),
                'acceptance_rate': self.labels.mean(),
                'embedding_model': 'nomic-embed-text'
            }
        }
        
        pkl_path = f"{base_path}.pkl"
        with open(pkl_path, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"Saved model + metadata: {pkl_path}")
    
    def run_full_analysis(self):
        """Run complete MLP analysis"""
        print("=== Research Article MLP Analysis ===\n")
        
        self.pull_data()
        if not self.vectorize_all_articles():
            return False
        
        history, eval_data = self.train_model()
        self.save_model()
        
        print("\nAnalysis complete! Models saved.")
        return True

def main():
    mlp = ResearchMLP()
    mlp.run_full_analysis()

if __name__ == "__main__":
    main()