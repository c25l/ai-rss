#!/usr/bin/env python3
import traceback
import numpy as np
from collections import defaultdict

def simple_test():
    """Test basic numpy operations that might cause the error"""
    try:
        # Test simple array comparisons
        arr = np.array([1, 2, 3])
        print("Testing array comparisons...")
        
        # This would cause the error:
        # if arr: print("This will fail")
        
        # Proper ways:
        if arr.any(): print("arr.any() works")
        if len(arr) > 0: print("len(arr) > 0 works")
        
        # Test list comparison
        lst = [1, 2, 3]
        if lst: print("list comparison works")
        
        print("Basic tests passed")
        return True
        
    except Exception as e:
        print(f"Error in simple test: {e}")
        traceback.print_exc()
        return False

def test_clustering_logic():
    """Test the specific clustering logic that might be failing"""
    try:
        print("Testing clustering logic...")
        
        # Create sample embeddings
        embeddings = np.random.rand(10, 100)
        print(f"Created embeddings shape: {embeddings.shape}")
        
        # Test the problematic line
        has_keywords = False
        for v in embeddings:
            if np.sum(v) > 0:
                has_keywords = True
                break
        print(f"Has keywords check: {has_keywords}")
        
        # Test another potential issue
        clusters_for_best_score = None
        if clusters_for_best_score is not None:
            print("None check works")
        else:
            print("None check works (else branch)")
            
        return True
        
    except Exception as e:
        print(f"Error in clustering test: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Running debug tests...")
    simple_test()
    test_clustering_logic()
    print("Debug tests complete")