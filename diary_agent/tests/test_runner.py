"""
Test runner for comprehensive diary agent testing.
Provides utilities for running different test suites and generating reports.
"""

import pytest
import sys
import os
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess


class TestRunner:
    """Comprehensive test runner for diary agent system."""
    
    def __init__(self, test_dir: str = None):
        """Initialize test runner."""
        self.test_dir = test_dir or os.path.dirname(__file__)
        self.results = {}
        
    def run_unit_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run all unit tests."""
        print("Running Unit Tests...")
        
        unit_test_files = [
            "test_base_agent.py",
            "test_condition_checker.py", 
            "test_event_router.py",
            "test_llm_manager.py",
            "test_sub_agent_manager.py",
            "test_config_manager.py",
            "test_diary_entry_generator.py",
            "test_database_integration.py",
            "test_weather_agent.py",
            "test_trending_agent.py",
            "test_holiday_agent.py",
            "test_friends_agent.py",
            "test_same_frequency_agent.py",
            "test_adoption_agent.py",
            "test_interactive_agent.py",
            "test_dairy_agent_controller.py",
            "test_error_handling.py"
        ]
        
        return self._run_test_suite("unit", unit_test_files, verbose)
    
    def run_integration_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run integration tests."""
        print("Running Integration Tests...")
        
        integration_test_files = [
            "test_integration_workflow.py"
        ]
        
        return self._run_test_suite("integration", integration_test_files, verbose)
    
    def run_performance_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run performance tests."""
        print("Running Performance Tests...")
        
        performance_test_files = [
            "test_performance.py"
        ]
        
        return self._run_test_suite("performance", performance_test_files, verbose)
    
    def run_acceptance_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run acceptance tests."""
        print("Running Acceptance Tests...")
        
        acceptance_test_files = [
            "test_acceptance.py"
        ]
        
        return self._run_test_suite("acceptance", acceptance_test_files, verbose)
    
    def run_end_to_end_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run end-to-end tests."""
        print("Running End-to-End Tests...")
        
        e2e_test_files = [
            "test_end_to_end.py"
        ]
        
        return self._run_test_suite("end_to_end", e2e_test_files, verbose)
    
    def run_all_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run all test suites."""
        print("Running Complete Test Suite...")
        
        start_time = time.time()
        
        # Run all test suites
        results = {
            "unit": self.run_unit_tests(verbose),
            "integration": self.run_integration_tests(verbose),
            "performance": self.run_performance_tests(verbose),
            "acceptance": self.run_acceptance_tests(verbose),
            "end_to_end": self.run_end_to_end_tests(verbose)
        }
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generate summary
        summary = self._generate_summary(results, total_time)
        results["summary"] = summary
        
        return results
    
    def _run_test_suite(self, suite_name: str, test_files: List[str], verbose: bool) -> Dict[str, Any]:
        """Run a specific test suite."""
        start_time = time.time()
        
        # Filter existing test files
        existing_files = []
        for test_file in test_files:
            test_path = os.path.join(self.test_dir, test_file)
            if os.path.exists(test_path):
                existing_files.append(test_path)
            elif verbose:
                print(f"Warning: Test file not found: {test_file}")
        
        if not existing_files:
            return {
                "status": "skipped",
                "reason": "No test files found",
                "duration": 0,
                "tests_run": 0,
                "failures": 0,
                "errors": 0
            }
        
        # Run pytest on the test files
        pytest_args = [
            "-v" if verbose else "-q",
            "--tb=short",
            "--disable-warnings"
        ] + existing_files
        
        try:
            # Capture pytest output
            result = pytest.main(pytest_args)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse pytest result
            status = "passed" if result == 0 else "failed"
            
            return {
                "status": status,
                "duration": duration,
                "pytest_exit_code": result,
                "files_tested": len(existing_files),
                "test_files": [os.path.basename(f) for f in existing_files]
            }
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                "status": "error",
                "duration": duration,
                "error": str(e),
                "files_tested": len(existing_files)
            }
    
    def _generate_summary(self, results: Dict[str, Any], total_time: float) -> Dict[str, Any]:
        """Generate test summary."""
        summary = {
            "total_duration": total_time,
            "timestamp": datetime.now().isoformat(),
            "suites": {}
        }
        
        total_files = 0
        passed_suites = 0
        failed_suites = 0
        
        for suite_name, suite_result in results.items():
            if suite_name == "summary":
                continue
                
            suite_summary = {
                "status": suite_result.get("status", "unknown"),
                "duration": suite_result.get("duration", 0),
                "files_tested": suite_result.get("files_tested", 0)
            }
            
            summary["suites"][suite_name] = suite_summary
            total_files += suite_result.get("files_tested", 0)
            
            if suite_result.get("status") == "passed":
                passed_suites += 1
            elif suite_result.get("status") in ["failed", "error"]:
                failed_suites += 1
        
        summary["totals"] = {
            "suites_run": len(results) - 1,  # Exclude summary
            "suites_passed": passed_suites,
            "suites_failed": failed_suites,
            "total_files_tested": total_files
        }
        
        return summary
    
    def generate_report(self, results: Dict[str, Any], output_file: str = None) -> str:
        """Generate detailed test report."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_report_{timestamp}.json"
        
        # Add metadata
        report = {
            "test_run_metadata": {
                "timestamp": datetime.now().isoformat(),
                "python_version": sys.version,
                "test_directory": self.test_dir,
                "report_generated": datetime.now().isoformat()
            },
            "results": results
        }
        
        # Write report
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def print_summary(self, results: Dict[str, Any]):
        """Print test summary to console."""
        if "summary" not in results:
            print("No summary available")
            return
        
        summary = results["summary"]
        
        print("\n" + "="*60)
        print("DIARY AGENT TEST SUMMARY")
        print("="*60)
        
        print(f"Total Duration: {summary['total_duration']:.2f} seconds")
        print(f"Timestamp: {summary['timestamp']}")
        
        print(f"\nSuite Results:")
        for suite_name, suite_info in summary["suites"].items():
            status_icon = "✓" if suite_info["status"] == "passed" else "✗"
            print(f"  {status_icon} {suite_name.upper()}: {suite_info['status']} "
                  f"({suite_info['files_tested']} files, {suite_info['duration']:.2f}s)")
        
        totals = summary["totals"]
        print(f"\nOverall Results:")
        print(f"  Suites Run: {totals['suites_run']}")
        print(f"  Suites Passed: {totals['suites_passed']}")
        print(f"  Suites Failed: {totals['suites_failed']}")
        print(f"  Total Files Tested: {totals['total_files_tested']}")
        
        success_rate = (totals['suites_passed'] / totals['suites_run']) * 100 if totals['suites_run'] > 0 else 0
        print(f"  Success Rate: {success_rate:.1f}%")
        
        print("="*60)


def main():
    """Main function for running tests from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Diary Agent Test Runner")
    parser.add_argument("--suite", choices=["unit", "integration", "performance", "acceptance", "e2e", "all"],
                       default="all", help="Test suite to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--report", "-r", help="Generate report file")
    parser.add_argument("--test-dir", help="Test directory path")
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner(args.test_dir)
    
    # Run specified test suite
    if args.suite == "unit":
        results = {"unit": runner.run_unit_tests(args.verbose)}
    elif args.suite == "integration":
        results = {"integration": runner.run_integration_tests(args.verbose)}
    elif args.suite == "performance":
        results = {"performance": runner.run_performance_tests(args.verbose)}
    elif args.suite == "acceptance":
        results = {"acceptance": runner.run_acceptance_tests(args.verbose)}
    elif args.suite == "e2e":
        results = {"end_to_end": runner.run_end_to_end_tests(args.verbose)}
    else:  # all
        results = runner.run_all_tests(args.verbose)
    
    # Print summary
    if "summary" in results:
        runner.print_summary(results)
    
    # Generate report if requested
    if args.report:
        report_file = runner.generate_report(results, args.report)
        print(f"\nDetailed report saved to: {report_file}")
    
    # Exit with appropriate code
    if "summary" in results:
        totals = results["summary"]["totals"]
        exit_code = 0 if totals["suites_failed"] == 0 else 1
    else:
        # Single suite run
        suite_result = list(results.values())[0]
        exit_code = 0 if suite_result.get("status") == "passed" else 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()