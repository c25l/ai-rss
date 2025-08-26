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
warnings.filterwarnings('ignore')

class ResearchPredictor:
    def __init__(self, model_path="research_mlp_improved.pkl"):
        self.model_data = None
        self.model = None
        self.scaler = None
        self.load_model(model_path)
    
    def load_model(self, model_path):
        """Load the trained model and components"""
        try:
            with open(model_path, 'rb') as f:
                self.model_data = pickle.load(f)
            
            self.model = self.model_data['model']
            self.scaler = self.model_data['scaler']
            
            print(f"✅ Model loaded successfully!")
            print(f"   Architecture: {self.model_data['architecture']}")
            print(f"   Training samples: {self.model_data['training_info']['total_samples']}")
            print(f"   Original acceptance rate: {self.model_data['training_info']['acceptance_rate']:.2%}")
            print()
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
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
            print("❌ Error: Empty text provided")
            return None
        
        print(f"📄 Analyzing text ({len(text)} characters)...")
        print(f"   Preview: {text[:100]}...")
        print()
        
        # Get embedding
        print("🔄 Getting embedding from nomic-embed-text...")
        embedding = self.get_nomic_embedding(text)
        
        if embedding is None:
            print("❌ Could not get embedding. Make sure Ollama is running with nomic-embed-text model.")
            return None
        
        # Normalize using the same scaler from training
        embedding_normalized = self.scaler.transform(embedding.reshape(1, -1))
        
        # Predict
        print("🤖 Running prediction...")
        probability = self.model.predict(embedding_normalized, verbose=0)[0][0]
        
        return probability
    
    def interpret_prediction(self, probability, text):
        """Provide interpretation of the prediction"""
        print("=" * 60)
        print("📊 PREDICTION RESULTS")
        print("=" * 60)
        
        print(f"🎯 Acceptance Probability: {probability:.1%}")
        
        if probability >= 0.8:
            verdict = "🟢 STRONG ACCEPT"
            confidence = "High"
        elif probability >= 0.6:
            verdict = "🟡 LIKELY ACCEPT"
            confidence = "Moderate"
        elif probability >= 0.4:
            verdict = "🟡 UNCERTAIN"
            confidence = "Low"
        elif probability >= 0.2:
            verdict = "🔴 LIKELY REJECT"
            confidence = "Moderate"
        else:
            verdict = "🔴 STRONG REJECT"
            confidence = "High"
        
        print(f"📋 Verdict: {verdict}")
        print(f"🎪 Confidence: {confidence}")
        
        # Additional context
        training_acceptance_rate = self.model_data['training_info']['acceptance_rate']
        if probability > training_acceptance_rate:
            print(f"📈 Above average (training acceptance rate: {training_acceptance_rate:.1%})")
        else:
            print(f"📉 Below average (training acceptance rate: {training_acceptance_rate:.1%})")
        
        # Text stats
        word_count = len(text.split())
        print(f"\n📝 Text Stats:")
        print(f"   Characters: {len(text):,}")
        print(f"   Words: {word_count:,}")
        print(f"   Estimated reading time: {word_count // 200:.1f} minutes")
        
        return probability
    
    def predict_from_file(self, file_path):
        """Predict from a text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            print(f"📂 Loading text from: {file_path}")
            return self.predict(text)
            
        except Exception as e:
            print(f"❌ Error reading file {file_path}: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description="Predict research article acceptance probability")
    parser.add_argument("--model", default="research_mlp_improved.pkl", 
                       help="Path to the trained model file")
    parser.add_argument("--text", type=str, 
                       help="Text to analyze (direct input)")
    parser.add_argument("--file", type=str,
                       help="File containing text to analyze")
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="Interactive mode - paste text and get predictions")
    
    args = parser.parse_args()
    
    # Initialize predictor
    predictor = ResearchPredictor(args.model)
    
    if args.interactive:
        print("🔄 INTERACTIVE MODE")
        print("Paste your research article text and press Enter twice when done.")
        print("Type 'quit' to exit.\n")
        
        while True:
            print("-" * 40)
            print("Paste text (press Enter twice when done):")
            lines = []
            while True:
                line = input()
                if line.lower() == 'quit':
                    print("👋 Goodbye!")
                    return
                if line == "" and lines:
                    break
                lines.append(line)
            
            text = '\n'.join(lines)
            if text.strip():
                prob = predictor.predict(text)
                if prob is not None:
                    predictor.interpret_prediction(prob, text)
                print()
    
    elif args.text:
        prob = predictor.predict(args.text)
        if prob is not None:
            predictor.interpret_prediction(prob, args.text)
    
    elif args.file:
        prob = predictor.predict_from_file(args.file)
        if prob is not None:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
            predictor.interpret_prediction(prob, text)
    
    else:
        print("❌ Please provide text via --text, --file, or use --interactive mode")
        print("Usage examples:")
        print('  python predict_acceptance.py --text "Your research article text here"')
        print('  python predict_acceptance.py --file article.txt')
        print('  python predict_acceptance.py --interactive')

if __name__ == "__main__":
    main()