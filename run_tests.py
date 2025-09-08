#!/usr/bin/env python3
"""
Test runner script for AAS Middleware.
Runs both unit tests and integration tests.
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"\n❌ Command not found: {cmd[0]}")
        print("Please ensure pytest is installed: pip install pytest pytest-asyncio")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run AAS Middleware tests")
    parser.add_argument(
        "--unit", 
        action="store_true", 
        help="Run unit tests only"
    )
    parser.add_argument(
        "--integration", 
        action="store_true", 
        help="Run integration tests only"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Run all tests (default)"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Run with coverage reporting"
    )
    
    args = parser.parse_args()
    
    # Default to running all tests if no specific type specified
    if not any([args.unit, args.integration, args.all]):
        args.all = True
    
    # Build pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        pytest_cmd.append("-v")
    
    if args.coverage:
        pytest_cmd.extend(["--cov=aas_middleware", "--cov-report=html", "--cov-report=term"])
    
    # Add test discovery
    pytest_cmd.extend(["--tb=short", "--strict-markers"])
    
    success = True
    
    # Run unit tests
    if args.unit or args.all:
        unit_cmd = pytest_cmd + ["tests/test_connectors.py", "tests/test_basic.py"]
        success &= run_command(unit_cmd, "Unit Tests")
    
    # Run integration tests
    if args.integration or args.all:
        integration_cmd = pytest_cmd + ["tests/test_integration.py"]
        success &= run_command(integration_cmd, "Integration Tests")
    
    # Summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
