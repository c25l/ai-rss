#!/usr/bin/env python3
"""
Research Article GLM Analysis with and without Random Projections
Compare GLM performance against MLP and Decision Tree
"""
import psycopg2
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.random_projection import GaussianRandomProjection
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, confusion_matrix
import requests
import pickle
import warnings
warnings.filterwarnings('ignore')

class ResearchGLM:
    def __init__(self):
        self.articles = None
        self.labels = None
        self.embeddings = None
        self.scaler = None
        
        # Models
        self.glm_full = None
        self.glm_projected = None
        self.random_projection = None
        
        # Results storage
        self.results = {}
        
    def connect_db(self):
        return psycopg2.connect("dbname=airss host=localhost")
    
    def pull_data(self):
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
    
    def vectorize_all_articles(self):
        print(f"Vectorizing {len(self.articles)} articles with nomic-embed-text...")
        embeddings = []
        
        for i, article in enumerate(self.articles):
            if i % 100 == 0:
                print(f"  Progress: {i}/{len(self.articles)}")
            
            embedding = self.get_nomic_embedding(article)
            if embedding is not None:
                embeddings.append(embedding)
            else:
                embeddings.append(np.zeros(768))
        
        self.embeddings = np.array(embeddings)
        print(f"Vectorization complete! Shape: {self.embeddings.shape}")
        
        # Standardize features
        self.scaler = StandardScaler()
        self.embeddings = self.scaler.fit_transform(self.embeddings)
        print("Features standardized")
    
    def train_glm_full(self, X_train, y_train, X_test, y_test):
        """Train GLM on full 768-dimensional embeddings"""
        print(f"\n=== Training GLM (Full 768-dim) ===")
        
        # Use L1 regularization for feature selection and L2 for stability
        self.glm_full = LogisticRegression(
            penalty='elasticnet',  # Elastic net combines L1 and L2
            l1_ratio=0.1,  # Mostly L2 with some L1
            C=0.1,  # Strong regularization for high-dim data
            solver='saga',  # Supports elastic net
            max_iter=1000,
            random_state=42,
            class_weight='balanced'  # Handle class imbalance
        )
        
        self.glm_full.fit(X_train, y_train)
        
        # Evaluate
        train_pred_proba = self.glm_full.predict_proba(X_train)[:, 1]
        test_pred_proba = self.glm_full.predict_proba(X_test)[:, 1]
        
        train_pred = self.glm_full.predict(X_train)
        test_pred = self.glm_full.predict(X_test)
        
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        test_auc = roc_auc_score(y_test, test_pred_proba)
        
        print(f"Training Accuracy: {train_acc:.3f}")
        print(f"Test Accuracy: {test_acc:.3f}")
        print(f"Test AUC-ROC: {test_auc:.3f}")
        
        # Store results
        self.results['glm_full'] = {
            'train_acc': train_acc,
            'test_acc': test_acc,
            'test_auc': test_auc,
            'test_pred_proba': test_pred_proba,
            'test_pred': test_pred,
            'model': self.glm_full
        }
        
        print(f"\nClassification Report (GLM Full):")
        print(classification_report(y_test, test_pred, target_names=['Reject', 'Accept']))
        
        return test_acc
    
    def train_glm_projected(self, X_train, y_train, X_test, y_test, n_components=100):
        """Train GLM with random projections for dimensionality reduction"""
        print(f"\n=== Training GLM with Random Projections ({n_components}-dim) ===")
        
        # Apply random projection
        self.random_projection = GaussianRandomProjection(
            n_components=n_components, 
            random_state=42
        )
        
        X_train_proj = self.random_projection.fit_transform(X_train)
        X_test_proj = self.random_projection.transform(X_test)
        
        print(f"Projected from {X_train.shape[1]} to {X_train_proj.shape[1]} dimensions")
        
        # Train GLM on projected data
        self.glm_projected = LogisticRegression(
            penalty='l2',  # L2 regularization
            C=1.0,  # Less aggressive regularization for lower-dim data
            solver='liblinear',
            max_iter=1000,
            random_state=42,
            class_weight='balanced'
        )
        
        self.glm_projected.fit(X_train_proj, y_train)
        
        # Evaluate
        train_pred_proba = self.glm_projected.predict_proba(X_train_proj)[:, 1]
        test_pred_proba = self.glm_projected.predict_proba(X_test_proj)[:, 1]
        
        train_pred = self.glm_projected.predict(X_train_proj)
        test_pred = self.glm_projected.predict(X_test_proj)
        
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        test_auc = roc_auc_score(y_test, test_pred_proba)
        
        print(f"Training Accuracy: {train_acc:.3f}")
        print(f"Test Accuracy: {test_acc:.3f}")
        print(f"Test AUC-ROC: {test_auc:.3f}")
        
        # Store results
        self.results['glm_projected'] = {
            'train_acc': train_acc,
            'test_acc': test_acc,
            'test_auc': test_auc,
            'test_pred_proba': test_pred_proba,
            'test_pred': test_pred,
            'model': self.glm_projected,
            'n_components': n_components
        }
        
        print(f"\nClassification Report (GLM Projected):")
        print(classification_report(y_test, test_pred, target_names=['Reject', 'Accept']))
        
        return test_acc
    
    def analyze_glm_coefficients(self):
        """Analyze GLM coefficients for interpretability"""
        if self.glm_full is None:
            print("No full GLM model trained")
            return
            
        print(f"\n=== GLM Coefficient Analysis ===")
        
        # Get coefficients
        coefs = self.glm_full.coef_[0]  # Shape: (768,)
        intercept = self.glm_full.intercept_[0]
        
        print(f"Intercept (bias): {intercept:.4f}")
        print(f"Number of features: {len(coefs)}")
        
        # Find most important features
        coef_abs = np.abs(coefs)
        top_indices = np.argsort(coef_abs)[-20:][::-1]  # Top 20 features
        
        print(f"\nTop 20 Most Important Features (by |coefficient|):")
        for i, idx in enumerate(top_indices):
            direction = "➕" if coefs[idx] > 0 else "➖"
            print(f"{i+1:2d}. Feature {idx:3d}: {coefs[idx]:+.4f} {direction}")
        
        # Summary statistics
        print(f"\nCoefficient Statistics:")
        print(f"  Mean: {coefs.mean():.6f}")
        print(f"  Std:  {coefs.std():.6f}")
        print(f"  Min:  {coefs.min():.6f}")
        print(f"  Max:  {coefs.max():.6f}")
        print(f"  Non-zero: {np.count_nonzero(coefs)}/{len(coefs)} ({100*np.count_nonzero(coefs)/len(coefs):.1f}%)")
    
    def compare_models(self):
        """Compare GLM models against each other and previous results"""
        print(f"\n" + "="*60)
        print(f"MODEL COMPARISON")
        print(f"="*60)
        
        # Previous results (from our earlier analysis)
        previous_results = {
            'Decision Tree': {'test_acc': 0.801, 'test_auc': None},
            'MLP (Improved)': {'test_acc': 0.742, 'test_auc': 0.814}  # Estimated from misclassification count
        }
        
        # Combine all results
        all_results = {}
        all_results.update(previous_results)
        
        if 'glm_full' in self.results:
            all_results['GLM (Full 768-dim)'] = {
                'test_acc': self.results['glm_full']['test_acc'],
                'test_auc': self.results['glm_full']['test_auc']
            }
        
        if 'glm_projected' in self.results:
            n_comp = self.results['glm_projected']['n_components']
            all_results[f'GLM (Random Proj {n_comp}-dim)'] = {
                'test_acc': self.results['glm_projected']['test_acc'],
                'test_auc': self.results['glm_projected']['test_auc']
            }
        
        # Sort by test accuracy
        sorted_results = sorted(all_results.items(), key=lambda x: x[1]['test_acc'], reverse=True)
        
        print(f"{'Model':<25} {'Test Acc':<10} {'AUC-ROC':<8}")
        print(f"{'-'*25} {'-'*10} {'-'*8}")
        
        for model_name, metrics in sorted_results:
            acc_str = f"{metrics['test_acc']:.3f}"
            auc_str = f"{metrics['test_auc']:.3f}" if metrics['test_auc'] is not None else "N/A"
            print(f"{model_name:<25} {acc_str:<10} {auc_str:<8}")
        
        # Find best model
        best_model = sorted_results[0]
        print(f"\n🏆 Best Model: {best_model[0]} (Accuracy: {best_model[1]['test_acc']:.3f})")
        
        return sorted_results
    
    def save_glm_models(self, filename="research_glm_models.pkl"):
        """Save GLM models and components"""
        model_package = {
            'glm_full': self.glm_full,
            'glm_projected': self.glm_projected,
            'random_projection': self.random_projection,
            'scaler': self.scaler,
            'results': self.results,
            'training_info': {
                'total_samples': len(self.labels),
                'acceptance_rate': self.labels.mean(),
                'embedding_model': 'nomic-embed-text',
                'standardized': True
            }
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(model_package, f)
        print(f"\nGLM models saved: {filename}")
    
    def run_glm_analysis(self):
        print("=== RESEARCH ARTICLE GLM ANALYSIS ===\n")
        
        self.pull_data()
        self.vectorize_all_articles()
        
        # Split data (same split for fair comparison)
        X_train, X_test, y_train, y_test = train_test_split(
            self.embeddings, self.labels, test_size=0.2, random_state=42, stratify=self.labels
        )
        
        print(f"Training set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")
        
        # Train both GLM variants
        self.train_glm_full(X_train, y_train, X_test, y_test)
        self.train_glm_projected(X_train, y_train, X_test, y_test, n_components=100)
        
        # Try different projection dimensions
        for n_comp in [50, 200]:
            print(f"\n--- Testing with {n_comp} components ---")
            rp = GaussianRandomProjection(n_components=n_comp, random_state=42)
            X_train_proj = rp.fit_transform(X_train)
            X_test_proj = rp.transform(X_test)
            
            glm_temp = LogisticRegression(
                penalty='l2', C=1.0, solver='liblinear', 
                max_iter=1000, random_state=42, class_weight='balanced'
            )
            glm_temp.fit(X_train_proj, y_train)
            
            test_acc = accuracy_score(y_test, glm_temp.predict(X_test_proj))
            test_auc = roc_auc_score(y_test, glm_temp.predict_proba(X_test_proj)[:, 1])
            
            print(f"GLM ({n_comp}-dim) - Accuracy: {test_acc:.3f}, AUC: {test_auc:.3f}")
        
        # Analysis and comparison
        self.analyze_glm_coefficients()
        comparison = self.compare_models()
        self.save_glm_models()
        
        return comparison

def main():
    glm = ResearchGLM()
    results = glm.run_glm_analysis()
    return results

if __name__ == "__main__":
    main()