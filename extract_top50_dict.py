#!/usr/bin/env python3
"""
Extract top 50 feature locations and coefficients as dictionary
"""
import pickle
import numpy as np

def extract_top50_coefficients():
    """Extract top 50 features and their coefficients from the saved GLM model"""
    with open('research_glm_models.pkl', 'rb') as f:
        model_package = pickle.load(f)
    
    glm_full = model_package['glm_full']
    coefs = glm_full.coef_[0]  # Shape: (768,)
    
    # Get top 50 features by absolute coefficient value
    coef_abs = np.abs(coefs)
    top_50_indices = np.argsort(coef_abs)[-50:][::-1]  # Top 50 features
    
    # Create dictionary with locations as keys and coefficients as values
    top50_dict = {}
    for idx in top_50_indices:
        top50_dict[int(idx)] = float(coefs[idx])
    
    return top50_dict

if __name__ == "__main__":
    coeffs = extract_top50_coefficients()
    print("Top 50 GLM coefficients:")
    print(coeffs)