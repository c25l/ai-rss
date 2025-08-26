#!/usr/bin/env python3
"""
Check results of the improved MLP model
"""
import pickle
import numpy as np

def check_model_results():
    # Load the saved model
    try:
        with open('research_mlp_improved.pkl', 'rb') as f:
            model_data = pickle.load(f)
        
        print("=== IMPROVED MLP MODEL RESULTS ===\n")
        
        # Print model info
        print("Model Architecture:", model_data.get('architecture', 'Unknown'))
        print("Training Info:")
        training_info = model_data.get('training_info', {})
        for key, value in training_info.items():
            if key == 'acceptance_rate':
                print(f"  {key}: {value:.2%}")
            else:
                print(f"  {key}: {value}")
        
        # Check if we have misclassified analysis
        misclassified = model_data.get('misclassified_analysis')
        if misclassified:
            print(f"\n=== MISCLASSIFICATION ANALYSIS ===")
            print(f"Total misclassified articles: {len(misclassified['true_labels'])}")
            
            # Count false positives and negatives
            false_positives = sum(1 for i, true_label in enumerate(misclassified['true_labels']) if true_label == 0)
            false_negatives = sum(1 for i, true_label in enumerate(misclassified['true_labels']) if true_label == 1)
            
            print(f"False Positives (wrongly accepted): {false_positives}")
            print(f"False Negatives (wrongly rejected): {false_negatives}")
            
            # Show some examples
            print(f"\n=== SAMPLE MISCLASSIFIED ARTICLES ===")
            for i in range(min(3, len(misclassified['articles']))):
                true_label = "Accept" if misclassified['true_labels'][i] else "Reject"
                pred_prob = misclassified['predicted_probs'][i]
                article_preview = misclassified['articles'][i][:150] + "..."
                
                print(f"\nExample {i+1}:")
                print(f"  True Label: {true_label}")
                print(f"  Predicted Probability: {pred_prob:.3f}")
                print(f"  Article Preview: {article_preview}")
                print("-" * 60)
        
        print(f"\nModel successfully loaded and analyzed!")
        return True
        
    except Exception as e:
        print(f"Error loading model: {e}")
        return False

if __name__ == "__main__":
    check_model_results()