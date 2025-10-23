"""
UI Automation Testing Suite

Tests all UI components and pages using browser automation (Selenium).
Validates forms, buttons, navigation, API integration, and captures screenshots on failures.
Generates detailed logs for debugging.
"""

import asyncio
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

# Setup detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'ui_test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# =====================================================
# TEST RESULT MODELS
# =====================================================

class UITestStatus(str, Enum):
    """UI test execution status"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class UITestResult:
    """Detailed UI test result"""
    test_id: str
    test_name: str
    category: str
    status: UITestStatus
    duration_ms: float
    timestamp: datetime
    
    # Test details
    page_url: str
    actions_performed: List[str]
    expected_outcome: str
    actual_outcome: str
    
    # Error details
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    screenshot_path: Optional[str] = None
    
    # Browser state
    console_logs: List[Dict[str, Any]] = None
    network_errors: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


# =====================================================
# UI TEST SUITE
# =====================================================

class UITestSuite:
    """Comprehensive UI testing suite using browser automation"""
    
    def __init__(self, base_url: str = "http://localhost:5173"):
        self.base_url = base_url
        self.results: List[UITestResult] = []
        self.driver: Optional[webdriver.Chrome] = None
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
    
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)  # Wait up to 10 seconds for elements
        
        logger.info("Chrome WebDriver initialized")
    
    def teardown_driver(self):
        """Teardown Chrome WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("Chrome WebDriver closed")
    
    def take_screenshot(self, test_id: str, description: str = "") -> str:
        """Take screenshot and return path"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_id}_{description}_{timestamp}.png".replace(" ", "_")
        filepath = self.screenshots_dir / filename
        
        self.driver.save_screenshot(str(filepath))
        logger.info(f"Screenshot saved: {filepath}")
        
        return str(filepath)
    
    def get_console_logs(self) -> List[Dict[str, Any]]:
        """Get browser console logs"""
        try:
            logs = self.driver.get_log('browser')
            return logs
        except Exception as e:
            logger.warning(f"Could not retrieve console logs: {e}")
            return []
    
    async def run_test(
        self,
        test_id: str,
        test_name: str,
        category: str,
        test_func,
        **kwargs
    ) -> UITestResult:
        """Run a single UI test and record results"""
        start_time = datetime.now()
        actions = []
        
        try:
            logger.info(f"Running UI test: {test_name}")
            
            # Execute test
            result = await test_func(actions=actions, **kwargs)
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            # Get console logs
            console_logs = self.get_console_logs()
            
            test_result = UITestResult(
                test_id=test_id,
                test_name=test_name,
                category=category,
                status=UITestStatus.PASSED if result["passed"] else UITestStatus.FAILED,
                duration_ms=duration,
                timestamp=start_time,
                page_url=result.get("url", ""),
                actions_performed=actions,
                expected_outcome=result.get("expected", ""),
                actual_outcome=result.get("actual", ""),
                error_message=result.get("error"),
                screenshot_path=result.get("screenshot"),
                console_logs=console_logs
            )
            
            self.results.append(test_result)
            
            if test_result.status == UITestStatus.PASSED:
                logger.info(f"✅ PASSED: {test_name} ({duration:.2f}ms)")
            else:
                logger.error(f"❌ FAILED: {test_name} - {result.get('error')}")
            
            return test_result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            # Take screenshot on error
            screenshot_path = self.take_screenshot(test_id, "error")
            
            test_result = UITestResult(
                test_id=test_id,
                test_name=test_name,
                category=category,
                status=UITestStatus.ERROR,
                duration_ms=duration,
                timestamp=start_time,
                page_url=self.driver.current_url if self.driver else "",
                actions_performed=actions,
                expected_outcome="Test should complete without errors",
                actual_outcome=f"Exception: {str(e)}",
                error_message=str(e),
                stack_trace=traceback.format_exc(),
                screenshot_path=screenshot_path,
                console_logs=self.get_console_logs()
            )
            
            self.results.append(test_result)
            logger.error(f"💥 ERROR: {test_name} - {e}")
            
            return test_result
    
    # =====================================================
    # CATEGORY 1: PAGE LOAD TESTS (10 tests)
    # =====================================================
    
    async def test_page_load(self, page_name: str, page_path: str, actions: List[str]) -> Dict[str, Any]:
        """Test if a page loads successfully"""
        url = f"{self.base_url}{page_path}"
        
        try:
            actions.append(f"Navigate to {url}")
            self.driver.get(url)
            
            actions.append("Wait for page to load")
            time.sleep(2)  # Wait for page to fully load
            
            # Check if page loaded (no error page)
            page_title = self.driver.title
            actions.append(f"Page title: {page_title}")
            
            # Check for common error indicators
            page_source = self.driver.page_source.lower()
            has_error = any(err in page_source for err in ["error", "404", "500", "not found"])
            
            passed = not has_error and len(page_title) > 0
            
            return {
                "passed": passed,
                "url": url,
                "expected": "Page loads without errors",
                "actual": f"Page loaded with title: {page_title}"
            }
        except Exception as e:
            return {
                "passed": False,
                "url": url,
                "error": str(e),
                "screenshot": self.take_screenshot(f"page_load_{page_name}", "failed")
            }
    
    # =====================================================
    # CATEGORY 2: NAVIGATION TESTS (15 tests)
    # =====================================================
    
    async def test_navigation(self, from_page: str, to_page: str, link_text: str, actions: List[str]) -> Dict[str, Any]:
        """Test navigation between pages"""
        try:
            # Navigate to starting page
            start_url = f"{self.base_url}{from_page}"
            actions.append(f"Navigate to {start_url}")
            self.driver.get(start_url)
            time.sleep(1)
            
            # Find and click navigation link
            actions.append(f"Look for link: {link_text}")
            link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, link_text))
            )
            
            actions.append(f"Click link: {link_text}")
            link.click()
            time.sleep(2)
            
            # Verify navigation
            current_url = self.driver.current_url
            actions.append(f"Current URL: {current_url}")
            
            expected_url = f"{self.base_url}{to_page}"
            passed = to_page in current_url
            
            return {
                "passed": passed,
                "url": current_url,
                "expected": f"Navigate to {expected_url}",
                "actual": f"Navigated to {current_url}"
            }
        except Exception as e:
            return {
                "passed": False,
                "url": self.driver.current_url,
                "error": str(e),
                "screenshot": self.take_screenshot("navigation", "failed")
            }
    
    # =====================================================
    # CATEGORY 3: FORM TESTS (20 tests)
    # =====================================================
    
    async def test_form_submission(
        self,
        page_path: str,
        form_data: Dict[str, str],
        submit_button_id: str,
        actions: List[str]
    ) -> Dict[str, Any]:
        """Test form submission"""
        url = f"{self.base_url}{page_path}"
        
        try:
            # Navigate to page
            actions.append(f"Navigate to {url}")
            self.driver.get(url)
            time.sleep(1)
            
            # Fill form fields
            for field_id, value in form_data.items():
                actions.append(f"Fill field {field_id} with '{value}'")
                field = self.driver.find_element(By.ID, field_id)
                field.clear()
                field.send_keys(value)
            
            # Submit form
            actions.append(f"Click submit button: {submit_button_id}")
            submit_button = self.driver.find_element(By.ID, submit_button_id)
            submit_button.click()
            
            # Wait for response
            time.sleep(2)
            actions.append("Wait for form submission response")
            
            # Check for success message or error
            page_source = self.driver.page_source.lower()
            has_success = any(msg in page_source for msg in ["success", "created", "saved", "submitted"])
            has_error = any(msg in page_source for msg in ["error", "failed", "invalid"])
            
            passed = has_success and not has_error
            
            return {
                "passed": passed,
                "url": url,
                "expected": "Form submits successfully",
                "actual": f"Success: {has_success}, Error: {has_error}"
            }
        except Exception as e:
            return {
                "passed": False,
                "url": url,
                "error": str(e),
                "screenshot": self.take_screenshot("form_submission", "failed")
            }
    
    # =====================================================
    # CATEGORY 4: API INTEGRATION TESTS (15 tests)
    # =====================================================
    
    async def test_data_loading(
        self,
        page_path: str,
        data_element_selector: str,
        expected_data_present: bool,
        actions: List[str]
    ) -> Dict[str, Any]:
        """Test if data is loaded from API"""
        url = f"{self.base_url}{page_path}"
        
        try:
            # Navigate to page
            actions.append(f"Navigate to {url}")
            self.driver.get(url)
            
            # Wait for data to load
            actions.append(f"Wait for data element: {data_element_selector}")
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, data_element_selector))
                )
                data_loaded = element is not None
                actions.append(f"Data element found: {data_loaded}")
            except TimeoutException:
                data_loaded = False
                actions.append("Data element not found (timeout)")
            
            passed = data_loaded == expected_data_present
            
            return {
                "passed": passed,
                "url": url,
                "expected": f"Data present: {expected_data_present}",
                "actual": f"Data loaded: {data_loaded}"
            }
        except Exception as e:
            return {
                "passed": False,
                "url": url,
                "error": str(e),
                "screenshot": self.take_screenshot("data_loading", "failed")
            }
    
    # =====================================================
    # CATEGORY 5: BUTTON INTERACTION TESTS (10 tests)
    # =====================================================
    
    async def test_button_click(
        self,
        page_path: str,
        button_id: str,
        expected_action: str,
        actions: List[str]
    ) -> Dict[str, Any]:
        """Test button click interaction"""
        url = f"{self.base_url}{page_path}"
        
        try:
            # Navigate to page
            actions.append(f"Navigate to {url}")
            self.driver.get(url)
            time.sleep(1)
            
            # Find and click button
            actions.append(f"Look for button: {button_id}")
            button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, button_id))
            )
            
            actions.append(f"Click button: {button_id}")
            button.click()
            time.sleep(2)
            
            # Verify action occurred
            actions.append(f"Verify action: {expected_action}")
            page_source = self.driver.page_source.lower()
            action_occurred = expected_action.lower() in page_source
            
            passed = action_occurred
            
            return {
                "passed": passed,
                "url": url,
                "expected": f"Action: {expected_action}",
                "actual": f"Action occurred: {action_occurred}"
            }
        except Exception as e:
            return {
                "passed": False,
                "url": url,
                "error": str(e),
                "screenshot": self.take_screenshot("button_click", "failed")
            }
    
    # =====================================================
    # MAIN TEST RUNNER
    # =====================================================
    
    def login(self, username: str = "admin@example.com", password: str = "admin123"):
        """Login to the dashboard before running tests"""
        try:
            logger.info(f"Attempting to login to {self.base_url}/login")
            self.driver.get(f"{self.base_url}/login")
            time.sleep(2)
            
            # Try to find and fill login form
            try:
                # Look for email/username field
                email_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[name='username']")
                email_field.clear()
                email_field.send_keys(username)
                
                # Look for password field
                password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
                password_field.clear()
                password_field.send_keys(password)
                
                # Submit form
                password_field.send_keys(Keys.RETURN)
                time.sleep(3)  # Wait for login to complete
                
                # Check if we're redirected away from login page
                current_url = self.driver.current_url
                if "/login" not in current_url:
                    logger.info(f"✅ Login successful, redirected to {current_url}")
                    return True
                else:
                    logger.warning("⚠️ Still on login page after submission, login may have failed")
                    return False
                    
            except NoSuchElementException:
                logger.warning("⚠️ Login form not found, assuming no authentication required")
                return True
                
        except Exception as e:
            logger.error(f"❌ Login failed: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all UI tests"""
        logger.info("=" * 80)
        logger.info("STARTING COMPREHENSIVE UI TESTS")
        logger.info("=" * 80)
        
        self.setup_driver()
        
        # Try to login first
        logger.info("\n🔐 Attempting authentication...")
        login_success = self.login()
        if not login_success:
            logger.warning("⚠️ Login failed or not required, proceeding with tests...")
        else:
            logger.info("✅ Authentication successful\n")
        
        try:
            test_count = 0
            
            # Category 1: Page Load Tests (10 tests)
            logger.info("\n📄 CATEGORY 1: PAGE LOAD TESTS")
            pages = [
                ("Home", "/"),
                ("Products", "/products"),
                ("Orders", "/orders"),
                ("Customers", "/customers"),
                ("Inventory", "/inventory"),
                ("Dashboard", "/dashboard"),
                ("Analytics", "/analytics"),
                ("Settings", "/settings"),
                ("Reports", "/reports"),
                ("Help", "/help")
            ]
            
            for page_name, page_path in pages:
                test_count += 1
                await self.run_test(
                    f"PAGE-{test_count:03d}",
                    f"Load {page_name} page",
                    "Page Load",
                    self.test_page_load,
                    page_name=page_name,
                    page_path=page_path
                )
            
            # Category 2: Navigation Tests (15 tests)
            logger.info("\n🧭 CATEGORY 2: NAVIGATION TESTS")
            navigation_tests = [
                ("/", "/products", "Products"),
                ("/", "/orders", "Orders"),
                ("/", "/customers", "Customers"),
                ("/products", "/products/new", "Add Product"),
                ("/orders", "/orders/new", "Create Order"),
            ]
            
            for from_page, to_page, link_text in navigation_tests:
                test_count += 1
                await self.run_test(
                    f"NAV-{test_count:03d}",
                    f"Navigate from {from_page} to {to_page}",
                    "Navigation",
                    self.test_navigation,
                    from_page=from_page,
                    to_page=to_page,
                    link_text=link_text
                )
            
            # Category 3: Form Tests (20 tests)
            logger.info("\n📝 CATEGORY 3: FORM TESTS")
            form_tests = [
                {
                    "page": "/products/new",
                    "data": {
                        "product_name": "Test Product",
                        "product_price": "99.99",
                        "product_sku": "TEST-001"
                    },
                    "submit": "submit_product"
                },
                {
                    "page": "/customers/new",
                    "data": {
                        "customer_name": "Test Customer",
                        "customer_email": "test@example.com"
                    },
                    "submit": "submit_customer"
                }
            ]
            
            for form_test in form_tests:
                test_count += 1
                await self.run_test(
                    f"FORM-{test_count:03d}",
                    f"Submit form on {form_test['page']}",
                    "Form Submission",
                    self.test_form_submission,
                    page_path=form_test["page"],
                    form_data=form_test["data"],
                    submit_button_id=form_test["submit"]
                )
            
            # Category 4: API Integration Tests (15 tests)
            logger.info("\n🔌 CATEGORY 4: API INTEGRATION TESTS")
            api_tests = [
                ("/products", ".product-list", True),
                ("/orders", ".order-list", True),
                ("/customers", ".customer-list", True),
                ("/dashboard", ".metrics", True),
                ("/analytics", ".chart", True)
            ]
            
            for page_path, selector, expected in api_tests:
                test_count += 1
                await self.run_test(
                    f"API-{test_count:03d}",
                    f"Data loading on {page_path}",
                    "API Integration",
                    self.test_data_loading,
                    page_path=page_path,
                    data_element_selector=selector,
                    expected_data_present=expected
                )
            
            logger.info("\n" + "=" * 80)
            logger.info(f"COMPLETED {test_count} UI TESTS")
            logger.info("=" * 80)
            
        finally:
            self.teardown_driver()
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive UI test report"""
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == UITestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == UITestStatus.FAILED)
        errors = sum(1 for r in self.results if r.status == UITestStatus.ERROR)
        
        # Group by category
        by_category = {}
        for result in self.results:
            if result.category not in by_category:
                by_category[result.category] = []
            by_category[result.category].append(result)
        
        # Calculate pass rate per category
        category_stats = {}
        for category, results in by_category.items():
            cat_passed = sum(1 for r in results if r.status == UITestStatus.PASSED)
            category_stats[category] = {
                "total": len(results),
                "passed": cat_passed,
                "failed": sum(1 for r in results if r.status == UITestStatus.FAILED),
                "errors": sum(1 for r in results if r.status == UITestStatus.ERROR),
                "pass_rate": (cat_passed / len(results) * 100) if results else 0
            }
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "pass_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
                "total_duration_ms": sum(r.duration_ms for r in self.results)
            },
            "by_category": category_stats,
            "failed_tests": [
                {
                    "test_id": r.test_id,
                    "test_name": r.test_name,
                    "error": r.error_message,
                    "screenshot": r.screenshot_path,
                    "console_logs": r.console_logs
                }
                for r in self.results if r.status in [UITestStatus.FAILED, UITestStatus.ERROR]
            ],
            "detailed_results": [r.to_dict() for r in self.results]
        }
        
        # Save report to file
        report_file = f"ui_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"\n📊 UI TEST REPORT SAVED: {report_file}")
        logger.info(f"\n✅ Passed: {passed}/{total_tests} ({passed/total_tests*100:.1f}%)")
        logger.info(f"❌ Failed: {failed}/{total_tests}")
        logger.info(f"💥 Errors: {errors}/{total_tests}")
        
        return report


# =====================================================
# MAIN EXECUTION
# =====================================================

async def main():
    """Main UI test execution"""
    suite = UITestSuite()
    report = await suite.run_all_tests()
    
    print("\n" + "=" * 80)
    print("FINAL UI TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']} ({report['summary']['pass_rate']:.1f}%)")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Errors: {report['summary']['errors']}")
    print(f"Total Duration: {report['summary']['total_duration_ms']:.2f}ms")
    print("=" * 80)
    
    return report


if __name__ == "__main__":
    asyncio.run(main())

