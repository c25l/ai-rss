#!/usr/bin/env python3
"""
Test script to verify morning and evening editions work correctly
"""
import daily_workflow
import datetime

def test_morning_edition():
    """Test morning edition generation"""
    print("=" * 60)
    print("Testing MORNING EDITION")
    print("=" * 60)
    try:
        daily_workflow.main(edition="morning")
        print("✓ Morning edition completed successfully")
    except Exception as e:
        print(f"✗ Morning edition failed: {e}")

def test_evening_edition():
    """Test evening edition generation"""
    print("\n" + "=" * 60)
    print("Testing EVENING EDITION")
    print("=" * 60)
    try:
        daily_workflow.main(edition="evening")
        print("✓ Evening edition completed successfully")
    except Exception as e:
        print(f"✗ Evening edition failed: {e}")

def test_auto_detection():
    """Test automatic edition detection"""
    print("\n" + "=" * 60)
    print("Testing AUTO DETECTION")
    print("=" * 60)
    edition = daily_workflow.determine_edition()
    current_hour = datetime.datetime.now().hour
    print(f"Current hour: {current_hour}")
    print(f"Detected edition: {edition}")
    if current_hour < 12:
        assert edition == "morning", "Should detect morning edition before noon"
    else:
        assert edition == "evening", "Should detect evening edition after noon"
    print("✓ Auto detection working correctly")

if __name__ == "__main__":
    # Run tests
    #test_auto_detection()

    # Uncomment to test actual email generation
    # WARNING: These will send actual emails!
    test_morning_edition()
    # test_evening_edition()

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("To test email generation, uncomment the test calls in this file")
    print("=" * 60)
