#!/usr/bin/env python3
"""
Integration test runner for microservices architecture.

This script runs all integration tests and provides detailed reporting
on service interactions and system behavior.
"""

import asyncio
import subprocess
import sys
import time
import httpx
import json
from pathlib import Path
from typing import Dict, List, Optional

# Service URLs
SERVICES = {
    "user": "http://localhost:8001",
    "task": "http://localhost:8002", 
    "notification": "http://localhost:8003"
}


class IntegrationTestRunner:
    """Runner for integration tests with service health checks."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def check_service_health(self, service_name: str, url: str) -> bool:
        """Check if a service is healthy and responding."""
        try:
            response = await self.client.get(f"{url}/health")
            if response.status_code == 200:
                print(f"✓ {service_name.title()} Service is healthy")
                return True
            else:
                print(f"✗ {service_name.title()} Service returned status {response.status_code}")
                return False
        except httpx.RequestError as e:
            print(f"✗ {service_name.title()} Service is not accessible: {e}")
            return False
    
    async def check_all_services(self) -> bool:
        """Check health of all services."""
        print("Checking service health...")
        print("-" * 40)
        
        all_healthy = True
        for service_name, url in SERVICES.items():
            is_healthy = await self.check_service_health(service_name, url)
            if not is_healthy:
                all_healthy = False
        
        print("-" * 40)
        return all_healthy
    
    def run_pytest(self, test_file: Optional[str] = None, verbose: bool = True) -> int:
        """Run pytest with appropriate arguments."""
        cmd = ["python", "-m", "pytest"]
        
        if test_file:
            cmd.append(test_file)
        else:
            cmd.append("tests/integration/")
        
        if verbose:
            cmd.extend(["-v", "-s"])
        
        cmd.extend([
            "--asyncio-mode=auto",
            "--tb=short",
            "--color=yes"
        ])
        
        print(f"Running: {' '.join(cmd)}")
        print("=" * 60)
        
        return subprocess.run(cmd).returncode
    
    async def run_service_connectivity_test(self) -> bool:
        """Test basic connectivity between services."""
        print("Testing service connectivity...")
        
        # Test user service endpoints
        try:
            response = await self.client.get(f"{SERVICES['user']}/docs")
            print(f"✓ User Service API docs accessible")
        except:
            print(f"✗ User Service API docs not accessible")
            return False
        
        # Test task service endpoints  
        try:
            response = await self.client.get(f"{SERVICES['task']}/docs")
            print(f"✓ Task Service API docs accessible")
        except:
            print(f"✗ Task Service API docs not accessible")
            return False
        
        # Test notification service endpoints
        try:
            response = await self.client.get(f"{SERVICES['notification']}/docs")
            print(f"✓ Notification Service API docs accessible")
        except:
            print(f"✗ Notification Service API docs not accessible")
            return False
        
        return True


async def main():
    """Main function to run integration tests."""
    runner = IntegrationTestRunner()
    
    try:
        print("🚀 Starting Integration Test Suite")
        print("=" * 60)
        
        # Check service health
        services_healthy = await runner.check_all_services()
        if not services_healthy:
            print("\n❌ Some services are not healthy. Please start all services before running tests.")
            print("\nTo start services, run: docker-compose up -d")
            return 1
        
        # Test service connectivity
        connectivity_ok = await runner.run_service_connectivity_test()
        if not connectivity_ok:
            print("\n❌ Service connectivity test failed.")
            return 1
        
        print("\n✓ All services are healthy and accessible")
        print("=" * 60)
        
        # Run different test suites
        test_suites = [
            ("Database Integration Tests", "tests/integration/test_database_integration.py"),
            ("End-to-End Auth Flow Tests", "tests/integration/test_end_to_end_auth_flow.py"),
            ("Service Interaction Tests", "tests/integration/test_service_interactions.py")
        ]
        
        overall_success = True
        
        for suite_name, test_file in test_suites:
            print(f"\n🧪 Running {suite_name}")
            print("=" * 60)
            
            result = runner.run_pytest(test_file)
            if result != 0:
                print(f"\n❌ {suite_name} failed")
                overall_success = False
            else:
                print(f"\n✅ {suite_name} passed")
        
        # Run all tests together for final verification
        print(f"\n🔄 Running Complete Integration Test Suite")
        print("=" * 60)
        
        final_result = runner.run_pytest()
        
        if final_result == 0 and overall_success:
            print("\n🎉 All integration tests passed successfully!")
            print("=" * 60)
            print("✓ Database consistency verified")
            print("✓ Authentication flow working")
            print("✓ Service interactions functioning")
            print("✓ Cross-service data flow validated")
            return 0
        else:
            print("\n❌ Some integration tests failed")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
    finally:
        await runner.close()


def run_specific_test(test_name: str):
    """Run a specific test file."""
    runner = IntegrationTestRunner()
    
    test_files = {
        "database": "tests/integration/test_database_integration.py",
        "auth": "tests/integration/test_end_to_end_auth_flow.py", 
        "interactions": "tests/integration/test_service_interactions.py"
    }
    
    if test_name not in test_files:
        print(f"Unknown test: {test_name}")
        print(f"Available tests: {', '.join(test_files.keys())}")
        return 1
    
    return runner.run_pytest(test_files[test_name])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        exit_code = run_specific_test(test_name)
        sys.exit(exit_code)
    else:
        # Run all tests
        exit_code = asyncio.run(main())
        sys.exit(exit_code)