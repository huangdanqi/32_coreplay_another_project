#!/usr/bin/env python3
"""
Simple test execution script for diary agent tests.
Provides easy commands for running different test suites.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and return the result."""
    if description:
        print(f"\n{description}")
        print("-" * len(description))
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def main():
    """Main function for test execution."""
    # Change to test directory
    test_dir = Path(__file__).parent
    os.chdir(test_dir)
    
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py <command>")
        print("\nAvailable commands:")
        print("  unit        - Run unit tests")
        print("  integration - Run integration tests")
        print("  performance - Run performance tests")
        print("  acceptance  - Run acceptance tests")
        print("  e2e         - Run end-to-end tests")
        print("  all         - Run all tests")
        print("  quick       - Run quick test subset")
        print("  coverage    - Run tests with coverage report")
        print("  install     - Install test dependencies")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "install":
        success = run_command([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], "Installing test dependencies")
        
        if success:
            print("\n✅ Test dependencies installed successfully!")
        else:
            print("\n❌ Failed to install test dependencies")
            sys.exit(1)
    
    elif command == "unit":
        success = run_command([
            sys.executable, "test_runner.py", "--suite", "unit", "--verbose"
        ], "Running Unit Tests")
    
    elif command == "integration":
        success = run_command([
            sys.executable, "test_runner.py", "--suite", "integration", "--verbose"
        ], "Running Integration Tests")
    
    elif command == "performance":
        success = run_command([
            sys.executable, "test_runner.py", "--suite", "performance", "--verbose"
        ], "Running Performance Tests")
    
    elif command == "acceptance":
        success = run_command([
            sys.executable, "test_runner.py", "--suite", "acceptance", "--verbose"
        ], "Running Acceptance Tests")
    
    elif command == "e2e":
        success = run_command([
            sys.executable, "test_runner.py", "--suite", "e2e", "--verbose"
        ], "Running End-to-End Tests")
    
    elif command == "all":
        success = run_command([
            sys.executable, "test_runner.py", "--suite", "all", "--verbose", "--report", "full_test_report.json"
        ], "Running All Tests")
    
    elif command == "quick":
        # Run a subset of fast tests
        success = run_command([
            sys.executable, "-m", "pytest", "-v", "-m", "not slow", "--tb=short"
        ], "Running Quick Test Subset")
    
    elif command == "coverage":
        success = run_command([
            sys.executable, "-m", "pytest", "--cov=diary_agent", "--cov-report=html", "--cov-report=term-missing", "-v"
        ], "Running Tests with Coverage")
        
        if success:
            print("\n📊 Coverage report generated in htmlcov/index.html")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
    
    if success:
        print(f"\n✅ {command.upper()} tests completed successfully!")
    else:
        print(f"\n❌ {command.upper()} tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()