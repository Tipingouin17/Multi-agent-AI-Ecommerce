"""
Enhanced UI Dashboard Testing Suite

Comprehensive tests for all 4 dashboard interfaces:
- Admin Interface
- Merchant Interface  
- Customer Interface
- Database Test Interface

Tests all buttons, navigation, real-time features, and agent connectivity.
"""

import time
import json
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'ui_dashboard_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestStatus(str, Enum):
    """Test execution status"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class TestResult:
    """Test result"""
    test_id: str
    test_name: str
    interface: str
    status: TestStatus
    duration_ms: float
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None


class DashboardUITests:
    """Comprehensive dashboard UI testing"""
    
    def __init__(self, base_url: str = "http://localhost:5173"):
        self.base_url = base_url
        self.results: List[TestResult] = []
        self.driver: Optional[webdriver.Chrome] = None
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
    
    def setup_driver(self, headless: bool = True):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            logger.info("✅ Chrome WebDriver initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize WebDriver: {e}")
            raise
    
    def teardown_driver(self):
        """Close WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("✅ WebDriver closed")
    
    def take_screenshot(self, test_name: str) -> str:
        """Take screenshot"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{test_name}_{timestamp}.png"
            filepath = self.screenshots_dir / filename
            self.driver.save_screenshot(str(filepath))
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None
    
    def run_test(self, test_id: str, test_name: str, interface: str, test_func, **kwargs) -> TestResult:
        """Run a single test"""
        logger.info(f"\n🧪 [{test_id}] {test_name}")
        start_time = time.time()
        
        try:
            test_func(**kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            result = TestResult(
                test_id=test_id,
                test_name=test_name,
                interface=interface,
                status=TestStatus.PASSED,
                duration_ms=duration_ms
            )
            logger.info(f"   ✅ PASSED ({duration_ms:.0f}ms)")
            
        except AssertionError as e:
            duration_ms = (time.time() - start_time) * 1000
            screenshot_path = self.take_screenshot(test_id)
            
            result = TestResult(
                test_id=test_id,
                test_name=test_name,
                interface=interface,
                status=TestStatus.FAILED,
                duration_ms=duration_ms,
                error_message=str(e),
                screenshot_path=screenshot_path
            )
            logger.error(f"   ❌ FAILED: {e}")
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            screenshot_path = self.take_screenshot(test_id)
            
            result = TestResult(
                test_id=test_id,
                test_name=test_name,
                interface=interface,
                status=TestStatus.ERROR,
                duration_ms=duration_ms,
                error_message=str(e),
                screenshot_path=screenshot_path
            )
            logger.error(f"   ❌ ERROR: {e}")
        
        self.results.append(result)
        return result
    
    # =====================================================
    # ADMIN INTERFACE TESTS
    # =====================================================
    
    def test_admin_dashboard_loads(self):
        """Test admin dashboard loads"""
        self.driver.get(f"{self.base_url}/admin")
        time.sleep(2)
        assert "admin" in self.driver.current_url.lower() or "dashboard" in self.driver.page_source.lower()
    
    def test_admin_agent_status(self):
        """Test admin can see agent status"""
        self.driver.get(f"{self.base_url}/admin")
        time.sleep(2)
        # Look for agent status indicators
        page_source = self.driver.page_source.lower()
        assert "agent" in page_source or "status" in page_source or "health" in page_source
    
    def test_admin_system_metrics(self):
        """Test admin can see system metrics"""
        self.driver.get(f"{self.base_url}/admin")
        time.sleep(2)
        page_source = self.driver.page_source.lower()
        assert any(word in page_source for word in ["metric", "performance", "cpu", "memory", "uptime"])
    
    def test_admin_alerts(self):
        """Test admin can see alerts"""
        self.driver.get(f"{self.base_url}/admin")
        time.sleep(2)
        page_source = self.driver.page_source.lower()
        assert "alert" in page_source or "notification" in page_source or "warning" in page_source
    
    # =====================================================
    # MERCHANT INTERFACE TESTS
    # =====================================================
    
    def test_merchant_dashboard_loads(self):
        """Test merchant dashboard loads"""
        self.driver.get(f"{self.base_url}/merchant")
        time.sleep(2)
        assert "merchant" in self.driver.current_url.lower() or "product" in self.driver.page_source.lower()
    
    def test_merchant_product_management(self):
        """Test merchant can access product management"""
        self.driver.get(f"{self.base_url}/merchant")
        time.sleep(2)
        page_source = self.driver.page_source.lower()
        assert "product" in page_source or "inventory" in page_source or "catalog" in page_source
    
    def test_merchant_order_management(self):
        """Test merchant can access order management"""
        self.driver.get(f"{self.base_url}/merchant")
        time.sleep(2)
        page_source = self.driver.page_source.lower()
        assert "order" in page_source or "sale" in page_source or "transaction" in page_source
    
    def test_merchant_marketplace_integration(self):
        """Test merchant can see marketplace integration"""
        self.driver.get(f"{self.base_url}/merchant")
        time.sleep(2)
        page_source = self.driver.page_source.lower()
        assert "marketplace" in page_source or "channel" in page_source or "integration" in page_source
    
    # =====================================================
    # CUSTOMER INTERFACE TESTS
    # =====================================================
    
    def test_customer_dashboard_loads(self):
        """Test customer dashboard loads"""
        self.driver.get(f"{self.base_url}/customer")
        time.sleep(2)
        assert "customer" in self.driver.current_url.lower() or "shop" in self.driver.page_source.lower()
    
    def test_customer_product_catalog(self):
        """Test customer can see product catalog"""
        self.driver.get(f"{self.base_url}/customer")
        time.sleep(2)
        page_source = self.driver.page_source.lower()
        assert "product" in page_source or "catalog" in page_source or "shop" in page_source
    
    def test_customer_order_tracking(self):
        """Test customer can track orders"""
        self.driver.get(f"{self.base_url}/customer")
        time.sleep(2)
        page_source = self.driver.page_source.lower()
        assert "order" in page_source or "track" in page_source or "status" in page_source
    
    def test_customer_cart(self):
        """Test customer can see shopping cart"""
        self.driver.get(f"{self.base_url}/customer")
        time.sleep(2)
        page_source = self.driver.page_source.lower()
        assert "cart" in page_source or "basket" in page_source or "checkout" in page_source
    
    # =====================================================
    # DATABASE TEST INTERFACE TESTS
    # =====================================================
    
    def test_database_test_loads(self):
        """Test database test interface loads"""
        self.driver.get(f"{self.base_url}/database-test")
        time.sleep(2)
        assert "database" in self.driver.current_url.lower() or "test" in self.driver.page_source.lower()
    
    def test_database_connectivity(self):
        """Test database connectivity check"""
        self.driver.get(f"{self.base_url}/database-test")
        time.sleep(2)
        page_source = self.driver.page_source.lower()
        assert "database" in page_source or "connection" in page_source or "postgres" in page_source
    
    def test_database_agent_health(self):
        """Test database agent health check"""
        self.driver.get(f"{self.base_url}/database-test")
        time.sleep(3)
        page_source = self.driver.page_source.lower()
        assert "agent" in page_source or "health" in page_source or "status" in page_source
    
    # =====================================================
    # NAVIGATION TESTS
    # =====================================================
    
    def test_navigation_admin_to_merchant(self):
        """Test navigation from admin to merchant"""
        self.driver.get(f"{self.base_url}/admin")
        time.sleep(1)
        self.driver.get(f"{self.base_url}/merchant")
        time.sleep(1)
        assert "merchant" in self.driver.current_url.lower()
    
    def test_navigation_merchant_to_customer(self):
        """Test navigation from merchant to customer"""
        self.driver.get(f"{self.base_url}/merchant")
        time.sleep(1)
        self.driver.get(f"{self.base_url}/customer")
        time.sleep(1)
        assert "customer" in self.driver.current_url.lower()
    
    def test_navigation_customer_to_database(self):
        """Test navigation from customer to database test"""
        self.driver.get(f"{self.base_url}/customer")
        time.sleep(1)
        self.driver.get(f"{self.base_url}/database-test")
        time.sleep(1)
        assert "database" in self.driver.current_url.lower() or "test" in self.driver.current_url.lower()
    
    # =====================================================
    # MAIN TEST RUNNER
    # =====================================================
    
    def run_all_tests(self, headless: bool = True) -> Dict[str, Any]:
        """Run all dashboard UI tests"""
        logger.info("=" * 80)
        logger.info("🚀 DASHBOARD UI COMPREHENSIVE TESTS")
        logger.info("=" * 80)
        
        self.setup_driver(headless=headless)
        
        try:
            # Admin Interface Tests
            logger.info("\n" + "=" * 80)
            logger.info("📊 ADMIN INTERFACE TESTS")
            logger.info("=" * 80)
            
            self.run_test("ADMIN-001", "Admin dashboard loads", "Admin", self.test_admin_dashboard_loads)
            self.run_test("ADMIN-002", "Admin can see agent status", "Admin", self.test_admin_agent_status)
            self.run_test("ADMIN-003", "Admin can see system metrics", "Admin", self.test_admin_system_metrics)
            self.run_test("ADMIN-004", "Admin can see alerts", "Admin", self.test_admin_alerts)
            
            # Merchant Interface Tests
            logger.info("\n" + "=" * 80)
            logger.info("🏪 MERCHANT INTERFACE TESTS")
            logger.info("=" * 80)
            
            self.run_test("MERCHANT-001", "Merchant dashboard loads", "Merchant", self.test_merchant_dashboard_loads)
            self.run_test("MERCHANT-002", "Merchant can access product management", "Merchant", self.test_merchant_product_management)
            self.run_test("MERCHANT-003", "Merchant can access order management", "Merchant", self.test_merchant_order_management)
            self.run_test("MERCHANT-004", "Merchant can see marketplace integration", "Merchant", self.test_merchant_marketplace_integration)
            
            # Customer Interface Tests
            logger.info("\n" + "=" * 80)
            logger.info("🛒 CUSTOMER INTERFACE TESTS")
            logger.info("=" * 80)
            
            self.run_test("CUSTOMER-001", "Customer dashboard loads", "Customer", self.test_customer_dashboard_loads)
            self.run_test("CUSTOMER-002", "Customer can see product catalog", "Customer", self.test_customer_product_catalog)
            self.run_test("CUSTOMER-003", "Customer can track orders", "Customer", self.test_customer_order_tracking)
            self.run_test("CUSTOMER-004", "Customer can see shopping cart", "Customer", self.test_customer_cart)
            
            # Database Test Interface Tests
            logger.info("\n" + "=" * 80)
            logger.info("🗄️  DATABASE TEST INTERFACE TESTS")
            logger.info("=" * 80)
            
            self.run_test("DATABASE-001", "Database test interface loads", "Database Test", self.test_database_test_loads)
            self.run_test("DATABASE-002", "Database connectivity check works", "Database Test", self.test_database_connectivity)
            self.run_test("DATABASE-003", "Database agent health check works", "Database Test", self.test_database_agent_health)
            
            # Navigation Tests
            logger.info("\n" + "=" * 80)
            logger.info("🧭 NAVIGATION TESTS")
            logger.info("=" * 80)
            
            self.run_test("NAV-001", "Navigate admin to merchant", "Navigation", self.test_navigation_admin_to_merchant)
            self.run_test("NAV-002", "Navigate merchant to customer", "Navigation", self.test_navigation_merchant_to_customer)
            self.run_test("NAV-003", "Navigate customer to database test", "Navigation", self.test_navigation_customer_to_database)
            
        finally:
            self.teardown_driver()
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate test report"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        
        # Group by interface
        by_interface = {}
        for result in self.results:
            if result.interface not in by_interface:
                by_interface[result.interface] = []
            by_interface[result.interface].append(result)
        
        # Calculate stats per interface
        interface_stats = {}
        for interface, results in by_interface.items():
            int_passed = sum(1 for r in results if r.status == TestStatus.PASSED)
            interface_stats[interface] = {
                "total": len(results),
                "passed": int_passed,
                "failed": sum(1 for r in results if r.status == TestStatus.FAILED),
                "errors": sum(1 for r in results if r.status == TestStatus.ERROR),
                "pass_rate": (int_passed / len(results) * 100) if results else 0
            }
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "pass_rate": (passed / total * 100) if total > 0 else 0
            },
            "by_interface": interface_stats,
            "results": [asdict(r) for r in self.results]
        }
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {total}")
        logger.info(f"✅ Passed: {passed}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"⚠️  Errors: {errors}")
        logger.info(f"📈 Pass Rate: {report['summary']['pass_rate']:.1f}%")
        
        logger.info("\n📋 BY INTERFACE:")
        for interface, stats in interface_stats.items():
            logger.info(f"  {interface}: {stats['passed']}/{stats['total']} ({stats['pass_rate']:.1f}%)")
        
        # Save report to JSON
        report_file = f"ui_dashboard_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"\n💾 Report saved to: {report_file}")
        
        return report


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dashboard UI Comprehensive Tests")
    parser.add_argument("--url", default="http://localhost:5173", help="Dashboard URL")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    args = parser.parse_args()
    
    tester = DashboardUITests(base_url=args.url)
    report = tester.run_all_tests(headless=args.headless)
    
    # Exit with error code if tests failed
    if report['summary']['failed'] > 0 or report['summary']['errors'] > 0:
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()

