#!/usr/bin/env python3
"""
Comprehensive coverage report generator for microservices task management system.

This script combines coverage reports from all services and generates a unified
coverage report with detailed analysis and recommendations.
"""

import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from datetime import datetime


class CoverageReportGenerator:
    """Generates comprehensive coverage reports from multiple services."""
    
    def __init__(self, output_dir: str = "coverage-reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.services = {
            'user-service': {
                'type': 'python',
                'coverage_file': 'user-service/coverage.xml',
                'html_dir': 'user-service/coverage-html'
            },
            'task-service': {
                'type': 'python',
                'coverage_file': 'task-service/coverage.xml',
                'html_dir': 'task-service/coverage-html'
            },
            'notification-service': {
                'type': 'python',
                'coverage_file': 'notification-service/coverage.xml',
                'html_dir': 'notification-service/coverage-html'
            },
            'frontend': {
                'type': 'javascript',
                'coverage_file': 'frontend/coverage/coverage-final.json',
                'html_dir': 'frontend/coverage'
            }
        }
        self.coverage_data = {}
    
    def parse_python_coverage(self, coverage_file: str) -> Dict[str, Any]:
        """Parse Python coverage XML file."""
        try:
            tree = ET.parse(coverage_file)
            root = tree.getroot()
            
            # Extract overall coverage metrics
            coverage_data = {
                'line_rate': float(root.get('line-rate', 0)) * 100,
                'branch_rate': float(root.get('branch-rate', 0)) * 100,
                'lines_covered': int(root.get('lines-covered', 0)),
                'lines_valid': int(root.get('lines-valid', 0)),
                'branches_covered': int(root.get('branches-covered', 0)),
                'branches_valid': int(root.get('branches-valid', 0)),
                'packages': []
            }
            
            # Extract package-level coverage
            for package in root.findall('.//package'):
                package_data = {
                    'name': package.get('name'),
                    'line_rate': float(package.get('line-rate', 0)) * 100,
                    'branch_rate': float(package.get('branch-rate', 0)) * 100,
                    'classes': []
                }
                
                # Extract class-level coverage
                for class_elem in package.findall('.//class'):
                    class_data = {
                        'name': class_elem.get('name'),
                        'filename': class_elem.get('filename'),
                        'line_rate': float(class_elem.get('line-rate', 0)) * 100,
                        'branch_rate': float(class_elem.get('branch-rate', 0)) * 100
                    }
                    package_data['classes'].append(class_data)
                
                coverage_data['packages'].append(package_data)
            
            return coverage_data
            
        except Exception as e:
            print(f"Error parsing Python coverage file {coverage_file}: {e}")
            return {
                'line_rate': 0,
                'branch_rate': 0,
                'lines_covered': 0,
                'lines_valid': 0,
                'branches_covered': 0,
                'branches_valid': 0,
                'packages': []
            }
    
    def parse_javascript_coverage(self, coverage_file: str) -> Dict[str, Any]:
        """Parse JavaScript coverage JSON file."""
        try:
            with open(coverage_file, 'r') as f:
                coverage_json = json.load(f)
            
            total_statements = 0
            covered_statements = 0
            total_branches = 0
            covered_branches = 0
            total_functions = 0
            covered_functions = 0
            total_lines = 0
            covered_lines = 0
            
            files = []
            
            for filename, file_data in coverage_json.items():
                if filename.startswith('node_modules/'):
                    continue
                
                # Statement coverage
                statements = file_data.get('s', {})
                total_statements += len(statements)
                covered_statements += sum(1 for count in statements.values() if count > 0)
                
                # Branch coverage
                branches = file_data.get('b', {})
                for branch_data in branches.values():
                    total_branches += len(branch_data)
                    covered_branches += sum(1 for count in branch_data if count > 0)
                
                # Function coverage
                functions = file_data.get('f', {})
                total_functions += len(functions)
                covered_functions += sum(1 for count in functions.values() if count > 0)
                
                # Line coverage
                lines = file_data.get('statementMap', {})
                total_lines += len(lines)
                covered_lines += sum(1 for line_num in lines.keys() 
                                   if statements.get(line_num, 0) > 0)
                
                files.append({
                    'name': filename,
                    'statements': {
                        'total': len(statements),
                        'covered': sum(1 for count in statements.values() if count > 0),
                        'pct': (sum(1 for count in statements.values() if count > 0) / len(statements) * 100) if statements else 0
                    },
                    'branches': {
                        'total': sum(len(branch_data) for branch_data in branches.values()),
                        'covered': sum(sum(1 for count in branch_data if count > 0) for branch_data in branches.values()),
                        'pct': 0  # Calculate percentage
                    },
                    'functions': {
                        'total': len(functions),
                        'covered': sum(1 for count in functions.values() if count > 0),
                        'pct': (sum(1 for count in functions.values() if count > 0) / len(functions) * 100) if functions else 0
                    }
                })
            
            return {
                'line_rate': (covered_lines / total_lines * 100) if total_lines > 0 else 0,
                'branch_rate': (covered_branches / total_branches * 100) if total_branches > 0 else 0,
                'function_rate': (covered_functions / total_functions * 100) if total_functions > 0 else 0,
                'statement_rate': (covered_statements / total_statements * 100) if total_statements > 0 else 0,
                'lines_covered': covered_lines,
                'lines_valid': total_lines,
                'branches_covered': covered_branches,
                'branches_valid': total_branches,
                'functions_covered': covered_functions,
                'functions_valid': total_functions,
                'statements_covered': covered_statements,
                'statements_valid': total_statements,
                'files': files
            }
            
        except Exception as e:
            print(f"Error parsing JavaScript coverage file {coverage_file}: {e}")
            return {
                'line_rate': 0,
                'branch_rate': 0,
                'function_rate': 0,
                'statement_rate': 0,
                'lines_covered': 0,
                'lines_valid': 0,
                'branches_covered': 0,
                'branches_valid': 0,
                'functions_covered': 0,
                'functions_valid': 0,
                'statements_covered': 0,
                'statements_valid': 0,
                'files': []
            }
    
    def collect_coverage_data(self):
        """Collect coverage data from all services."""
        for service_name, service_config in self.services.items():
            coverage_file = service_config['coverage_file']
            
            if not os.path.exists(coverage_file):
                print(f"Warning: Coverage file not found for {service_name}: {coverage_file}")
                self.coverage_data[service_name] = {
                    'line_rate': 0,
                    'branch_rate': 0,
                    'error': f"Coverage file not found: {coverage_file}"
                }
                continue
            
            if service_config['type'] == 'python':
                self.coverage_data[service_name] = self.parse_python_coverage(coverage_file)
            elif service_config['type'] == 'javascript':
                self.coverage_data[service_name] = self.parse_javascript_coverage(coverage_file)
            
            self.coverage_data[service_name]['service_type'] = service_config['type']
    
    def calculate_overall_coverage(self) -> Dict[str, float]:
        """Calculate overall coverage across all services."""
        total_lines = 0
        covered_lines = 0
        total_branches = 0
        covered_branches = 0
        
        for service_name, data in self.coverage_data.items():
            if 'error' in data:
                continue
            
            total_lines += data.get('lines_valid', 0)
            covered_lines += data.get('lines_covered', 0)
            total_branches += data.get('branches_valid', 0)
            covered_branches += data.get('branches_covered', 0)
        
        return {
            'line_rate': (covered_lines / total_lines * 100) if total_lines > 0 else 0,
            'branch_rate': (covered_branches / total_branches * 100) if total_branches > 0 else 0,
            'total_lines': total_lines,
            'covered_lines': covered_lines,
            'total_branches': total_branches,
            'covered_branches': covered_branches
        }
    
    def generate_html_report(self):
        """Generate comprehensive HTML coverage report."""
        overall_coverage = self.calculate_overall_coverage()
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Microservices Task Management - Coverage Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .overall-stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; margin-bottom: 5px; }}
        .stat-label {{ color: #666; }}
        .service-section {{ margin-bottom: 30px; }}
        .service-header {{ background-color: #007bff; color: white; padding: 15px; border-radius: 8px 8px 0 0; }}
        .service-content {{ border: 1px solid #ddd; border-top: none; padding: 20px; border-radius: 0 0 8px 8px; }}
        .coverage-bar {{ width: 100%; height: 20px; background-color: #e9ecef; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
        .coverage-fill {{ height: 100%; transition: width 0.3s ease; }}
        .coverage-excellent {{ background-color: #28a745; }}
        .coverage-good {{ background-color: #ffc107; }}
        .coverage-poor {{ background-color: #dc3545; }}
        .timestamp {{ text-align: center; color: #666; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; }}
        .error {{ color: #dc3545; font-style: italic; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Microservices Task Management System</h1>
            <h2>Test Coverage Report</h2>
        </div>
        
        <div class="overall-stats">
            <div class="stat-card">
                <div class="stat-value" style="color: {'#28a745' if overall_coverage['line_rate'] >= 80 else '#ffc107' if overall_coverage['line_rate'] >= 60 else '#dc3545'}">{overall_coverage['line_rate']:.1f}%</div>
                <div class="stat-label">Overall Line Coverage</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: {'#28a745' if overall_coverage['branch_rate'] >= 80 else '#ffc107' if overall_coverage['branch_rate'] >= 60 else '#dc3545'}">{overall_coverage['branch_rate']:.1f}%</div>
                <div class="stat-label">Overall Branch Coverage</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{overall_coverage['covered_lines']}</div>
                <div class="stat-label">Lines Covered</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{overall_coverage['total_lines']}</div>
                <div class="stat-label">Total Lines</div>
            </div>
        </div>
"""
        
        # Add service-specific sections
        for service_name, data in self.coverage_data.items():
            if 'error' in data:
                html_content += f"""
        <div class="service-section">
            <div class="service-header">
                <h3>{service_name.replace('-', ' ').title()}</h3>
            </div>
            <div class="service-content">
                <p class="error">Error: {data['error']}</p>
            </div>
        </div>
"""
                continue
            
            line_rate = data.get('line_rate', 0)
            branch_rate = data.get('branch_rate', 0)
            
            coverage_class = 'coverage-excellent' if line_rate >= 80 else 'coverage-good' if line_rate >= 60 else 'coverage-poor'
            
            html_content += f"""
        <div class="service-section">
            <div class="service-header">
                <h3>{service_name.replace('-', ' ').title()}</h3>
            </div>
            <div class="service-content">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <h4>Line Coverage: {line_rate:.1f}%</h4>
                        <div class="coverage-bar">
                            <div class="coverage-fill {coverage_class}" style="width: {line_rate}%"></div>
                        </div>
                        <p>{data.get('lines_covered', 0)} of {data.get('lines_valid', 0)} lines covered</p>
                    </div>
                    <div>
                        <h4>Branch Coverage: {branch_rate:.1f}%</h4>
                        <div class="coverage-bar">
                            <div class="coverage-fill {coverage_class}" style="width: {branch_rate}%"></div>
                        </div>
                        <p>{data.get('branches_covered', 0)} of {data.get('branches_valid', 0)} branches covered</p>
                    </div>
                </div>
            </div>
        </div>
"""
        
        html_content += f"""
        <div class="timestamp">
            <p>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Write HTML report
        html_file = self.output_dir / "combined-coverage-report.html"
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        print(f"HTML coverage report generated: {html_file}")
    
    def generate_json_report(self):
        """Generate JSON coverage report for CI/CD integration."""
        overall_coverage = self.calculate_overall_coverage()
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'overall_coverage': overall_coverage,
            'services': self.coverage_data,
            'summary': {
                'total_services': len(self.services),
                'services_with_coverage': len([s for s in self.coverage_data.values() if 'error' not in s]),
                'services_with_errors': len([s for s in self.coverage_data.values() if 'error' in s]),
                'meets_threshold': overall_coverage['line_rate'] >= 80
            }
        }
        
        json_file = self.output_dir / "combined-coverage-report.json"
        with open(json_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"JSON coverage report generated: {json_file}")
        return report_data
    
    def generate_reports(self):
        """Generate all coverage reports."""
        print("Collecting coverage data from all services...")
        self.collect_coverage_data()
        
        print("Generating HTML coverage report...")
        self.generate_html_report()
        
        print("Generating JSON coverage report...")
        json_data = self.generate_json_report()
        
        # Print summary
        overall_coverage = self.calculate_overall_coverage()
        print(f"\n=== Coverage Summary ===")
        print(f"Overall Line Coverage: {overall_coverage['line_rate']:.1f}%")
        print(f"Overall Branch Coverage: {overall_coverage['branch_rate']:.1f}%")
        print(f"Total Lines: {overall_coverage['total_lines']}")
        print(f"Covered Lines: {overall_coverage['covered_lines']}")
        
        for service_name, data in self.coverage_data.items():
            if 'error' in data:
                print(f"{service_name}: ERROR - {data['error']}")
            else:
                print(f"{service_name}: {data.get('line_rate', 0):.1f}% line coverage")
        
        return json_data


def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive coverage reports')
    parser.add_argument('--output-dir', default='coverage-reports', 
                       help='Output directory for coverage reports')
    parser.add_argument('--threshold', type=float, default=80.0,
                       help='Coverage threshold for pass/fail')
    
    args = parser.parse_args()
    
    generator = CoverageReportGenerator(args.output_dir)
    report_data = generator.generate_reports()
    
    # Exit with error code if coverage is below threshold
    overall_coverage = report_data['overall_coverage']['line_rate']
    if overall_coverage < args.threshold:
        print(f"\nCoverage {overall_coverage:.1f}% is below threshold {args.threshold}%")
        exit(1)
    else:
        print(f"\nCoverage {overall_coverage:.1f}% meets threshold {args.threshold}%")
        exit(0)


if __name__ == '__main__':
    main()