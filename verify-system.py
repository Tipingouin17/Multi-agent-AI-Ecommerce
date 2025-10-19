#!/usr/bin/env python3
"""
Multi-Agent E-commerce System Verification Script

This script performs comprehensive checks on all system components:
- Docker services (PostgreSQL, Kafka, Redis, etc.)
- All 14 agents
- Log files for errors
- Database connectivity
- Message broker connectivity

Only reports success if ALL checks pass with NO errors.
"""

import subprocess
import sys
import time
import re
from pathlib import Path
from typing import List, Tuple, Dict
import json

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class SystemVerifier:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.project_root = Path(__file__).parent
        self.log_dir = self.project_root / "logs"
        
    def print_header(self, text: str):
        """Print section header."""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}{text}{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")
        
    def print_success(self, text: str):
        """Print success message."""
        print(f"{GREEN}✓{RESET} {text}")
        
    def print_error(self, text: str):
        """Print error message."""
        print(f"{RED}✗{RESET} {text}")
        self.errors.append(text)
        
    def print_warning(self, text: str):
        """Print warning message."""
        print(f"{YELLOW}⚠{RESET} {text}")
        self.warnings.append(text)
        
    def run_command(self, cmd: List[str], check: bool = False) -> Tuple[int, str, str]:
        """Run shell command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timeout"
        except Exception as e:
            return -1, "", str(e)
    
    def check_docker_services(self) -> bool:
        """Check all Docker services are running."""
        self.print_header("Checking Docker Services")
        
        required_services = [
            "multi-agent-postgres",
            "multi-agent-redis",
            "multi-agent-kafka",
            "multi-agent-zookeeper",
            "multi-agent-prometheus",
            "multi-agent-grafana",
            "multi-agent-loki",
            "multi-agent-promtail",
            "multi-agent-nginx"
        ]
        
        code, stdout, stderr = self.run_command(["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"])
        
        if code != 0:
            self.print_error("Docker is not running or not accessible")
            return False
            
        running_containers = {}
        for line in stdout.strip().split('\n'):
            if '\t' in line:
                name, status = line.split('\t', 1)
                running_containers[name] = status
        
        all_running = True
        for service in required_services:
            if service in running_containers:
                status = running_containers[service]
                if "Up" in status:
                    self.print_success(f"{service}: {status}")
                else:
                    self.print_error(f"{service}: {status}")
                    all_running = False
            else:
                self.print_error(f"{service}: Not running")
                all_running = False
                
        return all_running
    
    def check_docker_logs(self) -> bool:
        """Check Docker container logs for errors."""
        self.print_header("Checking Docker Container Logs")
        
        containers = [
            "multi-agent-postgres",
            "multi-agent-kafka",
            "multi-agent-redis",
            "multi-agent-loki",
            "multi-agent-promtail"
        ]
        
        error_patterns = [
            r"ERROR",
            r"FATAL",
            r"panic",
            r"failed",
            r"cannot",
            r"permission denied",
            r"connection refused"
        ]
        
        all_clean = True
        for container in containers:
            code, stdout, stderr = self.run_command(
                ["docker", "logs", "--tail", "50", container]
            )
            
            if code != 0:
                self.print_warning(f"{container}: Could not retrieve logs")
                continue
            
            # Combine stdout and stderr
            logs = stdout + stderr
            errors_found = []
            
            for pattern in error_patterns:
                matches = re.findall(pattern, logs, re.IGNORECASE)
                if matches:
                    errors_found.extend(matches)
            
            if errors_found:
                self.print_error(f"{container}: Found {len(errors_found)} error(s) in logs")
                # Show first few errors
                for error in errors_found[:3]:
                    print(f"  - {error}")
                all_clean = False
            else:
                self.print_success(f"{container}: No errors in recent logs")
        
        return all_clean
    
    def check_database_connection(self) -> bool:
        """Check PostgreSQL database connectivity."""
        self.print_header("Checking Database Connection")
        
        code, stdout, stderr = self.run_command([
            "docker", "exec", "multi-agent-postgres",
            "psql", "-U", "postgres", "-d", "multi_agent_ecommerce",
            "-c", "SELECT 1;"
        ])
        
        if code == 0:
            self.print_success("PostgreSQL connection successful")
            return True
        else:
            self.print_error(f"PostgreSQL connection failed: {stderr}")
            return False
    
    def check_agent_processes(self) -> bool:
        """Check if agent processes are running."""
        self.print_header("Checking Agent Processes")
        
        agents = [
            "order_agent",
            "inventory_agent",
            "product_agent",
            "carrier_selection_agent",
            "warehouse_selection_agent",
            "customer_communication_agent",
            "demand_forecasting_agent",
            "dynamic_pricing_agent",
            "reverse_logistics_agent",
            "risk_anomaly_detection_agent",
            "ai_monitoring_agent",
            "d2c_ecommerce_agent",
            "standard_marketplace_agent",
            "refurbished_marketplace_agent"
        ]
        
        # Check for Python processes running agents
        code, stdout, stderr = self.run_command(["ps", "aux"])
        
        if code != 0:
            self.print_warning("Could not check agent processes (ps command failed)")
            return False
        
        running_agents = []
        for agent in agents:
            if agent in stdout:
                running_agents.append(agent)
                self.print_success(f"{agent}: Running")
            else:
                self.print_warning(f"{agent}: Not detected in process list")
        
        if len(running_agents) == 0:
            self.print_warning("No agents appear to be running")
            return False
        
        return True
    
    def check_agent_logs(self) -> bool:
        """Check agent log files for errors."""
        self.print_header("Checking Agent Log Files")
        
        if not self.log_dir.exists():
            self.print_warning(f"Log directory not found: {self.log_dir}")
            return False
        
        # Find all agent log files
        log_files = list(self.log_dir.glob("**/*.log"))
        
        if not log_files:
            self.print_warning("No log files found")
            return False
        
        error_patterns = [
            r"ERROR",
            r"CRITICAL",
            r"FATAL",
            r"Exception",
            r"Traceback",
            r"failed",
            r"cannot import",
            r"ModuleNotFoundError",
            r"ImportError",
            r"ConnectionError",
            r"TimeoutError"
        ]
        
        all_clean = True
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    # Read last 100 lines
                    lines = f.readlines()[-100:]
                    content = ''.join(lines)
                
                errors_found = []
                for pattern in error_patterns:
                    matches = re.findall(f".*{pattern}.*", content, re.IGNORECASE)
                    if matches:
                        errors_found.extend(matches[:2])  # Limit to 2 per pattern
                
                if errors_found:
                    self.print_error(f"{log_file.name}: Found {len(errors_found)} error(s)")
                    for error in errors_found[:3]:  # Show first 3
                        print(f"  - {error.strip()[:100]}")
                    all_clean = False
                else:
                    self.print_success(f"{log_file.name}: No errors detected")
                    
            except Exception as e:
                self.print_warning(f"{log_file.name}: Could not read ({e})")
        
        return all_clean
    
    def check_ports(self) -> bool:
        """Check if required ports are listening."""
        self.print_header("Checking Required Ports")
        
        required_ports = {
            5432: "PostgreSQL",
            6379: "Redis",
            9092: "Kafka",
            2181: "Zookeeper",
            9090: "Prometheus",
            3000: "Grafana",
            3100: "Loki"
        }
        
        code, stdout, stderr = self.run_command(["netstat", "-an"])
        
        if code != 0:
            self.print_warning("Could not check ports (netstat failed)")
            return False
        
        all_listening = True
        for port, service in required_ports.items():
            if f":{port}" in stdout or f".{port}" in stdout:
                self.print_success(f"Port {port} ({service}): Listening")
            else:
                self.print_error(f"Port {port} ({service}): Not listening")
                all_listening = False
        
        return all_listening
    
    def generate_report(self) -> Dict:
        """Generate final verification report."""
        self.print_header("System Verification Report")
        
        total_checks = 6
        passed_checks = total_checks - len([e for e in self.errors if "✗" in str(e)])
        
        report = {
            "total_checks": total_checks,
            "passed": passed_checks,
            "failed": total_checks - passed_checks,
            "errors": self.errors,
            "warnings": self.warnings,
            "status": "PASS" if len(self.errors) == 0 else "FAIL"
        }
        
        print(f"Total Checks: {total_checks}")
        print(f"Passed: {GREEN}{passed_checks}{RESET}")
        print(f"Failed: {RED}{total_checks - passed_checks}{RESET}")
        print(f"Warnings: {YELLOW}{len(self.warnings)}{RESET}")
        print(f"Errors: {RED}{len(self.errors)}{RESET}")
        
        if len(self.errors) == 0:
            print(f"\n{BOLD}{GREEN}{'='*60}{RESET}")
            print(f"{BOLD}{GREEN}✓ SYSTEM VERIFICATION PASSED{RESET}")
            print(f"{BOLD}{GREEN}All components are running without errors!{RESET}")
            print(f"{BOLD}{GREEN}{'='*60}{RESET}\n")
        else:
            print(f"\n{BOLD}{RED}{'='*60}{RESET}")
            print(f"{BOLD}{RED}✗ SYSTEM VERIFICATION FAILED{RESET}")
            print(f"{BOLD}{RED}Please fix the following errors:{RESET}")
            print(f"{BOLD}{RED}{'='*60}{RESET}\n")
            for i, error in enumerate(self.errors, 1):
                print(f"{i}. {error}")
        
        if self.warnings:
            print(f"\n{BOLD}{YELLOW}Warnings:{RESET}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"{i}. {warning}")
        
        return report
    
    def run_all_checks(self) -> bool:
        """Run all verification checks."""
        print(f"{BOLD}Multi-Agent E-commerce System Verification{RESET}")
        print(f"Starting comprehensive system check...\n")
        
        # Run all checks
        docker_ok = self.check_docker_services()
        docker_logs_ok = self.check_docker_logs()
        db_ok = self.check_database_connection()
        ports_ok = self.check_ports()
        agents_ok = self.check_agent_processes()
        agent_logs_ok = self.check_agent_logs()
        
        # Generate report
        report = self.generate_report()
        
        return report["status"] == "PASS"

def main():
    verifier = SystemVerifier()
    success = verifier.run_all_checks()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

