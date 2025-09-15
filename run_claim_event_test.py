#!/usr/bin/env python3
"""
Test runner for Claim Event function testing.

This script provides an easy way to run the Claim Event function tests
and generate a comprehensive test report.
"""

import sys
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

def setup_test_environment():
    """Setup the test environment."""
    print("🔧 Setting up test environment...")
    
    # Add the project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Check if required dependencies are available
    try:
        import pytest
        print("✅ pytest is available")
    except ImportError:
        print("❌ pytest not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest"], check=True)
    
    # Check if diary_agent module is available
    try:
        from diary_agent.utils.data_models import EventData
        print("✅ diary_agent module is available")
    except ImportError as e:
        print(f"❌ diary_agent module not found: {e}")
        print("Please ensure you're running this from the project root directory")
        return False
    
    return True

def run_claim_event_tests():
    """Run the Claim Event function tests."""
    print("\n🧪 Running Claim Event function tests...")
    
    # Test file path
    test_file = "test_claim_event_function.py"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file {test_file} not found!")
        return False
    
    # Run pytest with verbose output
    cmd = [
        sys.executable, "-m", "pytest",
        test_file,
        "-v",
        "--tb=short",
        "--capture=no"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("\n" + "="*60)
        print("TEST RESULTS")
        print("="*60)
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("ERRORS:")
            print(result.stderr)
        
        print(f"\nExit code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ All Claim Event tests passed!")
        else:
            print("❌ Some Claim Event tests failed!")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_specific_claim_event_test():
    """Run a specific test to demonstrate the Claim Event function."""
    print("\n🎯 Running specific Claim Event demonstration...")
    
    try:
        # Import necessary components
        from diary_agent.utils.data_models import EventData, DiaryEntry, EmotionalTag
        from datetime import datetime
        
        # Create a sample claim event
        event_data = EventData(
            event_id="demo_claim_001",
            event_type="adoption_event",
            event_name="toy_claimed",
            timestamp=datetime.now(),
            user_id=123,
            context_data={
                "device_id": "demo_toy_001",
                "binding_method": "mobile_app",
                "device_type": "smart_toy",
                "device_name": "演示机器人"
            },
            metadata={
                "owner_info": {
                    "name": "演示用户",
                    "nickname": "小主人",
                    "personality": "lively"
                },
                "claim_method": "app_binding"
            }
        )
        
        print("✅ Created sample claim event data:")
        print(f"   Event ID: {event_data.event_id}")
        print(f"   Event Name: {event_data.event_name}")
        print(f"   User ID: {event_data.user_id}")
        print(f"   Device ID: {event_data.context_data['device_id']}")
        print(f"   Owner Name: {event_data.metadata['owner_info']['name']}")
        
        # Test event validation
        assert event_data.event_name == "toy_claimed"
        assert event_data.event_type == "adoption_event"
        assert "device_id" in event_data.context_data
        assert "owner_info" in event_data.metadata
        
        print("✅ Event data validation passed!")
        
        # Test event mapper integration
        from diary_agent.utils.event_mapper import EventMapper
        event_mapper = EventMapper()
        
        assert event_mapper.is_claimed_event("toy_claimed")
        assert "toy_claimed" in event_mapper.get_claimed_events()
        
        print("✅ Event mapper integration passed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in demonstration: {e}")
        return False

def generate_test_report():
    """Generate a test report."""
    report = {
        "test_name": "Claim Event Function Test",
        "timestamp": datetime.now().isoformat(),
        "specification": {
            "trigger_condition": "Each time a device is bound",
            "content_requirement": "Owner's personal information"
        },
        "test_coverage": [
            "Device binding simulation",
            "Event generation and routing", 
            "Adoption agent processing",
            "Diary entry generation with owner info",
            "Integration with adopted_function.py",
            "Error handling and fallback mechanisms"
        ],
        "status": "completed"
    }
    
    report_file = "claim_event_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Test report generated: {report_file}")

def main():
    """Main test runner function."""
    print("🚀 Claim Event Function Test Runner")
    print("="*50)
    
    # Setup environment
    if not setup_test_environment():
        print("❌ Failed to setup test environment")
        return 1
    
    # Run specific demonstration
    if not run_specific_claim_event_test():
        print("❌ Failed to run demonstration")
        return 1
    
    # Run full test suite
    if not run_claim_event_tests():
        print("❌ Failed to run full test suite")
        return 1
    
    # Generate report
    generate_test_report()
    
    print("\n🎉 Claim Event function testing completed successfully!")
    print("\nSummary:")
    print("- ✅ Device binding trigger condition verified")
    print("- ✅ Owner's personal information requirement verified") 
    print("- ✅ Event processing workflow tested")
    print("- ✅ Error handling mechanisms tested")
    print("- ✅ Integration with adopted_function.py verified")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
