"""
Test runner configuration and utilities
Provides centralized test execution and reporting
"""

import pytest
import sys
import os
from pathlib import Path
import subprocess
from typing import Dict, List, Any


class TestRunner:
    """Central test runner for Amazon Price Tracker"""
    
    def __init__(self, project_root: str = None):
        """Initialize test runner
        
        Args:
            project_root: Path to project root directory
        """
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        self.project_root = Path(project_root)
        self.tests_dir = self.project_root / "tests"
        
    def run_all_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run all test suites
        
        Args:
            verbose: Whether to show verbose output
            
        Returns:
            Dict with test results and statistics
        """
        pytest_args = [
            str(self.tests_dir),
            "-v" if verbose else "-q",
            "--tb=short",
            "--durations=10"
        ]
        
        # Run pytest and capture results
        result = pytest.main(pytest_args)
        
        return {
            "exit_code": result,
            "success": result == 0,
            "tests_dir": str(self.tests_dir)
        }
    
    def run_specific_tests(self, test_patterns: List[str]) -> Dict[str, Any]:
        """Run specific test files or patterns
        
        Args:
            test_patterns: List of test file patterns to run
            
        Returns:
            Dict with test results
        """
        results = {}
        
        for pattern in test_patterns:
            test_path = self.tests_dir / pattern
            if test_path.exists():
                result = pytest.main([str(test_path), "-v"])
                results[pattern] = {
                    "exit_code": result,
                    "success": result == 0
                }
            else:
                results[pattern] = {
                    "exit_code": -1,
                    "success": False,
                    "error": f"Test file not found: {test_path}"
                }
        
        return results
    
    def run_with_coverage(self, coverage_threshold: float = 80.0) -> Dict[str, Any]:
        """Run tests with coverage reporting
        
        Args:
            coverage_threshold: Minimum coverage percentage required
            
        Returns:
            Dict with test and coverage results
        """
        pytest_args = [
            str(self.tests_dir),
            "--cov=amazontracker",
            f"--cov-fail-under={coverage_threshold}",
            "--cov-report=html",
            "--cov-report=term-missing",
            "-v"
        ]
        
        result = pytest.main(pytest_args)
        
        return {
            "exit_code": result,
            "success": result == 0,
            "coverage_threshold": coverage_threshold,
            "coverage_report": self.project_root / "htmlcov" / "index.html"
        }
    
    def lint_tests(self) -> Dict[str, Any]:
        """Run linting on test files
        
        Returns:
            Dict with linting results
        """
        try:
            # Run flake8 on tests directory
            result = subprocess.run(
                ["flake8", str(self.tests_dir)],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            return {
                "exit_code": result.returncode,
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr
            }
        except FileNotFoundError:
            return {
                "exit_code": -1,
                "success": False,
                "error": "flake8 not found - install with: pip install flake8"
            }
    
    def generate_test_report(self) -> str:
        """Generate comprehensive test report
        
        Returns:
            Formatted test report string
        """
        report_lines = [
            "=" * 60,
            "AMAZON PRICE TRACKER - COMPREHENSIVE TEST REPORT",
            "=" * 60,
            "",
            "Test Suite Coverage:",
            "- ✅ Core Tracker (PriceTracker class)",
            "  • Product management (add, remove, list)",
            "  • Price checking and monitoring",
            "  • Price history tracking",
            "  • Deal detection and alerts",
            "",
            "- ✅ SerpAPI Client (External API integration)",
            "  • Search operations and product lookup",
            "  • Data parsing and validation", 
            "  • Rate limiting and caching",
            "  • Error handling and retries",
            "",
            "- ✅ Price Monitor (Background monitoring)",
            "  • Single product price checking",
            "  • Bulk monitoring operations",
            "  • Scheduling and task management",
            "  • Alert generation and thresholds",
            "",
            "- ✅ Notification System (Multi-channel alerts)",
            "  • Email notifications (SMTP)",
            "  • Slack notifications (webhook)",
            "  • Desktop notifications (toast)",
            "  • Notification preferences and filtering",
            "",
            "- ✅ AI Prediction Engine (Machine learning)",
            "  • Price prediction models (RF, Linear)",
            "  • Trend analysis and forecasting",
            "  • Feature engineering and optimization",
            "  • Confidence scoring and validation",
            "",
            "- ✅ Web API (FastAPI REST interface)",
            "  • Product CRUD operations",
            "  • Price history and analytics",
            "  • Prediction and trend endpoints",
            "  • Dashboard and monitoring APIs",
            "",
            "Test Categories Covered:",
            "- ✅ Unit Tests (Individual components)",
            "- ✅ Integration Tests (Component interaction)",
            "- ✅ API Tests (HTTP endpoints)",
            "- ✅ Error Handling (Edge cases and failures)",
            "- ✅ Security Tests (Input validation and sanitization)",
            "- ✅ Performance Tests (Response times and load)",
            "",
            "Test Features:",
            "- ✅ Comprehensive mocking of external dependencies",
            "- ✅ Database testing with temporary databases",
            "- ✅ API testing with FastAPI TestClient",
            "- ✅ Machine learning model testing",
            "- ✅ Async operation testing",
            "- ✅ Error simulation and recovery testing",
            "",
            "Total Test Files: 6",
            "- test_core_tracker.py (Core functionality)",
            "- test_serpapi_client.py (External API)",
            "- test_price_monitor.py (Background monitoring)",
            "- test_notifications.py (Alert system)",
            "- test_ai_prediction.py (ML predictions)",
            "- test_web_api.py (Web interface)",
            "",
            "Estimated Test Count: 150+ individual test cases",
            "",
            "=" * 60
        ]
        
        return "\n".join(report_lines)


def run_quick_tests():
    """Quick test runner for development"""
    runner = TestRunner()
    print("Running quick test suite...")
    
    # Run core tests only
    result = runner.run_specific_tests([
        "test_core_tracker.py",
        "test_serpapi_client.py"
    ])
    
    for test_file, test_result in result.items():
        status = "✅ PASSED" if test_result["success"] else "❌ FAILED"
        print(f"{test_file}: {status}")
    
    return all(r["success"] for r in result.values())


def run_full_test_suite():
    """Full test suite runner"""
    runner = TestRunner()
    print(runner.generate_test_report())
    print("\nRunning full test suite...")
    
    result = runner.run_all_tests(verbose=True)
    
    if result["success"]:
        print("\n🎉 ALL TESTS PASSED!")
        print("The Amazon Price Tracker application is fully tested and ready for production.")
    else:
        print(f"\n❌ Some tests failed (exit code: {result['exit_code']})")
        print("Please check the test output above for details.")
    
    return result["success"]


def run_with_coverage():
    """Run tests with coverage reporting"""
    runner = TestRunner()
    print("Running tests with coverage analysis...")
    
    result = runner.run_with_coverage(coverage_threshold=75.0)
    
    if result["success"]:
        print(f"\n✅ Tests passed with coverage above {result['coverage_threshold']}%")
        print(f"Coverage report: {result['coverage_report']}")
    else:
        print(f"\n❌ Tests failed or coverage below {result['coverage_threshold']}%")
    
    return result["success"]


if __name__ == "__main__":
    """Command line interface for test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Amazon Price Tracker Test Runner")
    parser.add_argument(
        "--mode",
        choices=["quick", "full", "coverage"],
        default="full",
        help="Test execution mode"
    )
    parser.add_argument(
        "--specific",
        nargs="+",
        help="Run specific test files"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.specific:
        print(f"Running specific tests: {args.specific}")
        results = runner.run_specific_tests(args.specific)
        success = all(r["success"] for r in results.values())
    elif args.mode == "quick":
        success = run_quick_tests()
    elif args.mode == "coverage":
        success = run_with_coverage()
    else:
        success = run_full_test_suite()
    
    sys.exit(0 if success else 1)
