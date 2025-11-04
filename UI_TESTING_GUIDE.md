# Comprehensive UI Testing Guide

**Author:** Manus AI
**Date:** November 04, 2025

## 1. Overview

This document provides a comprehensive guide to the new UI automation testing suite for the multi-agent e-commerce platform's dashboard. The testing suite is designed to be robust, easy to run, and thorough, ensuring that all critical user interfaces and functionalities are working as expected.

The tests are built using **Python** and **Selenium WebDriver**, and they cover all four main interfaces of the dashboard:

- **Admin Interface**: Monitors agent health, system metrics, and alerts.
- **Merchant Interface**: Manages products, orders, and marketplace integrations.
- **Customer Interface**: Provides the customer-facing shopping experience.
- **Database Test Interface**: Verifies database connectivity and agent health checks.

## 2. Prerequisites

Before running the UI tests, ensure the following prerequisites are met:

1.  **Python 3.8+**: The test scripts are written in Python. You can download it from [python.org](https://python.org).
2.  **Google Chrome**: The tests run on the Chrome browser.
3.  **ChromeDriver**: The Selenium WebDriver requires ChromeDriver to interact with the Chrome browser. It must be installed and available in your system's `PATH`.
    - You can download ChromeDriver from the [official site](https://chromedriver.chromium.org/downloads).
    - Alternatively, for easier management, you can install it using a package manager:
        - **Windows (with Chocolatey)**: `choco install chromedriver`
        - **macOS (with Homebrew)**: `brew install chromedriver`
        - **Debian/Ubuntu**: `sudo apt-get install chromium-chromedriver`
4.  **Running Dashboard**: The dashboard must be running and accessible at `http://localhost:5173`. You can start it using `start_dashboard.bat` (Windows) or `./start_dashboard.sh` (Linux/macOS).

## 3. How to Run Tests

There are two primary ways to run the UI tests: as a standalone script or as part of the master launch process.

### 3.1. Standalone Test Execution

We have created dedicated scripts for both Windows and Linux/macOS to simplify the test execution process. These scripts automatically handle dependency checks and environment setup.

#### On Windows

Use the `run_ui_tests.bat` batch script:

```batch
run_ui_tests.bat
```

The script will:
1.  Verify that Python is installed.
2.  Check if the dashboard is running.
3.  Install the `selenium` package if it's missing.
4.  Verify that `chromedriver` is in the system's PATH.
5.  Execute the comprehensive test suite in **headless mode** (no browser window will appear).

#### On Linux/macOS

Use the `run_ui_tests.sh` shell script:

```bash
./run_ui_tests.sh
```

Make sure the script is executable first:
```bash
chmod +x run_ui_tests.sh
```

The script performs the same checks as the Windows version and runs the tests in headless mode.

### 3.2. Integrated with Master Launch Script

The UI tests are now integrated into the `master_launch.bat` and `master_launch.sh` scripts. After the dashboard has successfully started, you will be prompted to run the UI tests.

```text
================================================================================
UI TESTING (OPTIONAL)
================================================================================

Would you like to run comprehensive UI tests for the dashboard?
This will test all 4 interfaces (Admin, Merchant, Customer, Database Test)

Run UI tests? (y/N):
```

Enter `y` and press Enter to execute the tests. The master script will call the appropriate test runner (`run_ui_tests.bat` or `run_ui_tests.sh`) and display the results.

## 4. Test Structure

The core logic for the UI tests resides in the following file:

- `testing/ui_dashboard_comprehensive_tests.py`

This script is organized into several categories of tests, each targeting a specific aspect of the dashboard.

| Test ID        | Interface       | Test Name                                  | Description                                                 |
| :------------- | :-------------- | :----------------------------------------- | :---------------------------------------------------------- |
| **ADMIN**      | **Admin**       |                                            | **Tests for the administrative dashboard**                  |
| `ADMIN-001`    | Admin           | Admin dashboard loads                      | Verifies that the admin interface page loads correctly.     |
| `ADMIN-002`    | Admin           | Admin can see agent status                 | Checks for elements related to agent health and status.     |
| `ADMIN-003`    | Admin           | Admin can see system metrics               | Looks for CPU, memory, or other performance metrics.        |
| `ADMIN-004`    | Admin           | Admin can see alerts                       | Checks for a notification or alerts section.                |
| **MERCHANT**   | **Merchant**    |                                            | **Tests for the merchant-facing interface**                 |
| `MERCHANT-001` | Merchant        | Merchant dashboard loads                   | Verifies that the merchant interface page loads correctly.  |
| `MERCHANT-002` | Merchant        | Merchant can access product management     | Checks for product or inventory management sections.        |
| `MERCHANT-003` | Merchant        | Merchant can access order management       | Checks for order or sales management sections.              |
| `MERCHANT-004` | Merchant        | Merchant can see marketplace integration   | Looks for marketplace or channel integration settings.      |
| **CUSTOMER**   | **Customer**    |                                            | **Tests for the customer-facing shopping experience**       |
| `CUSTOMER-001` | Customer        | Customer dashboard loads                   | Verifies that the customer interface page loads correctly.  |
| `CUSTOMER-002` | Customer        | Customer can see product catalog           | Checks that the product catalog is visible.                 |
| `CUSTOMER-003` | Customer        | Customer can track orders                  | Looks for an order tracking or order status feature.        |
| `CUSTOMER-004` | Customer        | Customer can see shopping cart             | Checks for the presence of a shopping cart or basket.       |
| **DATABASE**   | **Database Test** |                                            | **Tests for the database and connectivity test page**       |
| `DATABASE-001` | Database Test   | Database test interface loads              | Verifies that the database test page loads correctly.       |
| `DATABASE-002` | Database Test   | Database connectivity check works          | Checks for elements indicating database connection status.  |
| `DATABASE-003` | Database Test   | Database agent health check works          | Checks for elements related to agent health status.         |
| **NAV**        | **Navigation**  |                                            | **Tests for navigating between different interfaces**       |
| `NAV-001`      | Navigation      | Navigate admin to merchant                 | Ensures seamless navigation between the two interfaces.     |
| `NAV-002`      | Navigation      | Navigate merchant to customer              | Ensures seamless navigation between the two interfaces.     |
| `NAV-003`      | Navigation      | Navigate customer to database test         | Ensures seamless navigation between the two interfaces.     |

## 5. Reports and Artifacts

After each test run, the following artifacts are generated to help you analyze the results:

### 5.1. JSON Test Report

A detailed report in JSON format is generated and saved in the project's root directory. The filename includes a timestamp, for example:

- `ui_dashboard_test_report_20251104_143000.json`

This report contains:
- A summary of the test run (total tests, pass/fail counts, pass rate).
- A breakdown of results by interface.
- A detailed list of all test results, including duration and error messages for failed tests.

### 5.2. Log File

A log file is created in the project's root directory with a timestamp, for example:

- `ui_dashboard_test_20251104_143000.log`

This file contains the detailed output of the test run, including which tests were run and their status.

### 5.3. Screenshots on Failure

If a test fails or encounters an error, a screenshot of the browser window is automatically taken and saved to the `screenshots/` directory. The filename corresponds to the `test_id` and includes a timestamp, making it easy to identify the context of the failure.

- `screenshots/ADMIN-002_20251104_143105.png`

This feature is invaluable for debugging UI issues quickly.

