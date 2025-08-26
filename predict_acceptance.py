#!/usr/bin/env python3
"""
Research Article Acceptance Predictor
Uses the trained MLP model to predict acceptance probability for new text input
"""
import pickle
import numpy as np
import requests
import sys
import argparse
import warnings

class ResearchPredictor:
    def __init__(self, model_path="research_mlp_improved.pkl"):
        self.model_data = None
        self.model = None
        self.scaler = None
        self.load_model(model_path)
        print("loaded model")
    
    def load_model(self, model_path):
        """Load the trained model and components"""
        try:
            with open(model_path, 'rb') as f:
                self.model_data = pickle.load(f)
            
            self.model = self.model_data['model']
            self.scaler = self.model_data['scaler']

        except Exception as e:
            sys.exit(1)
    
    def get_nomic_embedding(self, text):
        """Get embedding from nomic-embed-text via Ollama"""
        try:
            response = requests.post("http://localhost:11434/api/embeddings",
                                   json={"model": "nomic-embed-text", "prompt": text[:8000]},
                                   timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get("embedding", [])
                if embedding and len(embedding) == 768:
                    return np.array(embedding)
            
            print(f"⚠️  Warning: Failed to get embedding from Ollama (status: {response.status_code})")
            return None
            
        except Exception as e:
            print(f"⚠️  Warning: Ollama connection error: {e}")
            return None
    
    def predict(self, text):
        """Predict acceptance probability for given text"""
        if not text.strip():
            return -1
        
        embedding = self.get_nomic_embedding(text)
        
        if embedding is None:
            return -1
        # Normalize using the same scaler from training
        embedding_normalized = self.scaler.transform(embedding.reshape(1, -1))
        
        # Predict
        print("🤖 Running prediction...")
        probability = self.model.predict(embedding_normalized, verbose=0)[0][0]
        
        return probability
    
