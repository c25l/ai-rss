#!/usr/bin/env python3
"""
Improved Research Article MLP - Push for higher accuracy
"""
import psycopg2
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, confusion_matrix
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.regularizers import l2
import requests
import pickle
import warnings
warnings.filterwarnings('ignore')

class ImprovedResearchMLP:
    def __init__(self):
        self.articles = None
        self.labels = None
        self.embeddings = None
        self.scaler = None
        self.model = None
        self.misclassified_data = None
        
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
        
    def build_improved_mlp(self):
        """Build deeper, more robust MLP"""
        model = Sequential([
            # First hidden layer - larger to capture complexity
            Dense(512, activation='relu', input_shape=(768,), kernel_regularizer=l2(0.01)),
            BatchNormalization(),
            Dropout(0.4),
            
            # Second hidden layer
            Dense(256, activation='relu', kernel_regularizer=l2(0.01)),
            BatchNormalization(),
            Dropout(0.4),
            
            # Third hidden layer
            Dense(128, activation='relu', kernel_regularizer=l2(0.01)),
            BatchNormalization(),
            Dropout(0.3),
            
            # Fourth hidden layer - smaller for final feature extraction
            Dense(64, activation='relu', kernel_regularizer=l2(0.01)),
            BatchNormalization(),
            Dropout(0.2),
            
            # Output layer
            Dense(1, activation='sigmoid')
        ])
        
        # Use Adam with lower learning rate for stability
        optimizer = Adam(learning_rate=0.0005, beta_1=0.9, beta_2=0.999)
        
        model.compile(
            optimizer=optimizer,
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        return model
    
    def train_with_cv(self):
        """Train with cross-validation and advanced techniques"""
        X_train, X_test, y_train, y_test = train_test_split(
            self.embeddings, self.labels, test_size=0.2, random_state=42, stratify=self.labels
        )
        
        print(f"Training set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")
        
        # Build model
        self.build_improved_mlp()
        
        # Class weights for imbalance
        pos_weight = (len(self.labels) - np.sum(self.labels)) / np.sum(self.labels)
        class_weight = {0: 1.0, 1: pos_weight}
        print(f"Class weights: {class_weight}")
        
        # Advanced callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True, verbose=1),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=1e-6, verbose=1)
        ]
        
        # Train with more epochs and patience
        print("\nTraining improved MLP...")
        history = self.model.fit(
            X_train, y_train,
            validation_split=0.25,  # Use more validation data
            epochs=200,  # More epochs
            batch_size=16,  # Smaller batch size for better gradients
            class_weight=class_weight,
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate
        print("\n=== IMPROVED MLP RESULTS ===")
        
        train_pred_proba = self.model.predict(X_train, verbose=0).flatten()
        test_pred_proba = self.model.predict(X_test, verbose=0).flatten()
        
        train_pred = (train_pred_proba > 0.5).astype(int)
        test_pred = (test_pred_proba > 0.5).astype(int)
        
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        test_auc = roc_auc_score(y_test, test_pred_proba)
        
        print(f"Training Accuracy: {train_acc:.3f}")
        print(f"Test Accuracy: {test_acc:.3f}")
        print(f"Test AUC-ROC: {test_auc:.3f}")
        
        print(f"\nDetailed Classification Report:")
        print(classification_report(y_test, test_pred, target_names=['Reject', 'Accept']))
        
        print(f"\nConfusion Matrix:")
        cm = confusion_matrix(y_test, test_pred)
        print(cm)
        
        # Store misclassified data for analysis
        misclassified_indices = np.where(y_test != test_pred)[0]
        X_test_orig_indices = np.arange(len(self.labels))[len(X_train):]  # Get original indices
        
        self.misclassified_data = {
            'indices': X_test_orig_indices[misclassified_indices],
            'articles': [self.articles[X_test_orig_indices[i]] for i in misclassified_indices],
            'true_labels': y_test[misclassified_indices],
            'predicted_probs': test_pred_proba[misclassified_indices],
            'predicted_labels': test_pred[misclassified_indices]
        }
        
        print(f"\nMisclassified: {len(misclassified_indices)} out of {len(y_test)} test samples")
        
        return history, test_acc
    
    def analyze_misclassified(self):
        """Analyze patterns in misclassified articles"""
        if self.misclassified_data is None:
            print("No misclassified data available")
            return
        
        print(f"\n=== MISCLASSIFIED ARTICLES ANALYSIS ===")
        
        false_positives = []  # Predicted Accept, Actually Reject
        false_negatives = []  # Predicted Reject, Actually Accept
        
        for i in range(len(self.misclassified_data['true_labels'])):
            true_label = self.misclassified_data['true_labels'][i]
            pred_prob = self.misclassified_data['predicted_probs'][i]
            article = self.misclassified_data['articles'][i]
            
            if true_label == 0:  # Actually rejected but predicted accepted
                false_positives.append({
                    'article': article,
                    'prob': pred_prob,
                    'length': len(article),
                    'words': len(article.split())
                })
            else:  # Actually accepted but predicted rejected
                false_negatives.append({
                    'article': article,
                    'prob': pred_prob,
                    'length': len(article),
                    'words': len(article.split())
                })
        
        print(f"False Positives (wrongly accepted): {len(false_positives)}")
        print(f"False Negatives (wrongly rejected): {len(false_negatives)}")
        
        if false_positives:
            print(f"\n--- FALSE POSITIVES (Top 3 by confidence) ---")
            fp_sorted = sorted(false_positives, key=lambda x: x['prob'], reverse=True)
            for i, fp in enumerate(fp_sorted[:3]):
                print(f"\n{i+1}. Confidence: {fp['prob']:.3f}")
                print(f"   Length: {fp['length']} chars, {fp['words']} words")
                print(f"   Content: {fp['article'][:200]}...")
        
        if false_negatives:
            print(f"\n--- FALSE NEGATIVES (Top 3 by confidence) ---")
            fn_sorted = sorted(false_negatives, key=lambda x: x['prob'])
            for i, fn in enumerate(fn_sorted[:3]):
                print(f"\n{i+1}. Confidence: {fn['prob']:.3f}")
                print(f"   Length: {fn['length']} chars, {fn['words']} words")
                print(f"   Content: {fn['article'][:200]}...")
        
        # Statistical analysis
        if false_positives:
            fp_lengths = [fp['length'] for fp in false_positives]
            fp_words = [fp['words'] for fp in false_positives]
            print(f"\nFalse Positives Stats:")
            print(f"  Avg length: {np.mean(fp_lengths):.0f} chars")
            print(f"  Avg words: {np.mean(fp_words):.0f}")
        
        if false_negatives:
            fn_lengths = [fn['length'] for fn in false_negatives]
            fn_words = [fn['words'] for fn in false_negatives]
            print(f"\nFalse Negatives Stats:")
            print(f"  Avg length: {np.mean(fn_lengths):.0f} chars")
            print(f"  Avg words: {np.mean(fn_words):.0f}")
    
    def save_model(self, filename="research_mlp_improved.pkl"):
        """Save model and all components"""
        model_package = {
            'model': self.model,
            'scaler': self.scaler,
            'architecture': 'Improved MLP: 768→512→256→128→64→1',
            'training_info': {
                'total_samples': len(self.labels),
                'acceptance_rate': self.labels.mean(),
                'embedding_model': 'nomic-embed-text',
                'standardized': True
            },
            'misclassified_analysis': self.misclassified_data
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(model_package, f)
        print(f"Model saved: {filename}")
    
    def run_improved_analysis(self):
        print("=== IMPROVED RESEARCH ARTICLE MLP ===\n")
        
        self.pull_data()
        self.vectorize_all_articles()
        history, test_acc = self.train_with_cv()
        
        print(f"\n=== FINAL RESULTS ===")
        print(f"Best Test Accuracy: {test_acc:.3f}")
        
        self.analyze_misclassified()
        self.save_model()
        
        print(f"\nImproved analysis complete!")
        return test_acc

def main():
    mlp = ImprovedResearchMLP()
    accuracy = mlp.run_improved_analysis()
    return accuracy

if __name__ == "__main__":
    main()