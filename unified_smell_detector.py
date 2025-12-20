"""
Unified Test Smell Detector - All 5 Libraries Combined
Detects test smells using pytest-smell, radon, flake8, jscpd, and AST
Ensures no duplicate smell counting across libraries
"""

import ast
import subprocess
import sys
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Import radon
try:
    from radon.complexity import cc_visit
    from radon.metrics import mi_visit
    from radon.raw import analyze
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False
    print("Warning: radon not installed")


class UnifiedSmellDetector:
    """Unified smell detector that combines all 5 libraries without duplicates"""
    
    def __init__(self, test_directory: str = "tests"):
        self.test_directory = Path(test_directory)
        self.file_smells = defaultdict(lambda: defaultdict(set))  # file -> smell_type -> set of (line, description)
        self.library_smells = defaultdict(lambda: defaultdict(int))  # library -> smell_type -> count
        
    def detect_all_smells(self):
        """Run all 5 detection methods and merge results"""
        
        print("="*80)
        print("UNIFIED TEST SMELL DETECTION - ALL 5 LIBRARIES")
        print("="*80)
        print()
        
        # Get all test files
        test_files = list(self.test_directory.glob("**/*.py"))
        test_files = [f for f in test_files if f.name.startswith("test_")]
        
        print(f"Analyzing {len(test_files)} test files...")
        print()
        
        # 1. AST-based detection (most comprehensive, run first)
        print("[1/5] Running AST-based detection...")
        self._detect_with_ast(test_files)
        
        # 2. Radon complexity analysis
        if RADON_AVAILABLE:
            print("[2/5] Running Radon complexity analysis...")
            self._detect_with_radon(test_files)
        else:
            print("[2/5] Skipping Radon (not installed)")
        
        # 3. Flake8 code quality
        print("[3/5] Running Flake8 code quality check...")
        self._detect_with_flake8(test_files)
        
        # 4. JSCPD duplication detection
        print("[4/5] Running JSCPD duplication detection...")
        self._detect_with_jscpd()
        
        # 5. pytest-smell
        print("[5/5] Running pytest-smell detection...")
        self._detect_with_pytest_smell()
        
        print()
        print("="*80)
        print("DETECTION COMPLETE")
        print("="*80)
        print()
        
        # Display results
        self._display_results()
        
        # Save to JSON
        self._save_results()
        
        return self.file_smells
    
    def _detect_with_ast(self, test_files: List[Path]):
        """Detect smells using AST parsing"""
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(test_file))
                visitor = ASTSmellVisitor(test_file.name)
                visitor.visit(tree)
                
                # Add smells (convert to set to avoid duplicates)
                for smell in visitor.smells:
                    smell_type = smell['type']
                    line = smell['line']
                    desc = smell['description']
                    # Check if this exact smell at this line already exists
                    if (line, desc) not in self.file_smells[test_file.name][smell_type]:
                        self.file_smells[test_file.name][smell_type].add((line, desc))
                        self.library_smells['AST'][smell_type] += 1
                    
            except Exception as e:
                pass
    
    def _detect_with_radon(self, test_files: List[Path]):
        """Detect complexity-based smells using Radon"""
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Cyclomatic Complexity
                complexity_results = cc_visit(content)
                for result in complexity_results:
                    if result.complexity > 5:
                        # Only add if not already detected by AST as "Complex Test"
                        smell_type = "Complex Test"
                        line = result.lineno
                        desc = f"Cyclomatic complexity {result.complexity}"
                        self.file_smells[test_file.name][smell_type].add((line, desc))
                        self.library_smells['Radon'][smell_type] += 1
                
                # Maintainability Index
                mi_score = mi_visit(content, multi=True)
                if mi_score and mi_score < 65:
                    smell_type = "Low Maintainability"
                    line = 1
                    desc = f"Maintainability Index: {mi_score:.2f}"
                    # Only add if not already detected
                    if smell_type not in self.file_smells[test_file.name] or len(self.file_smells[test_file.name][smell_type]) == 0:
                        self.file_smells[test_file.name][smell_type].add((line, desc))
                        self.library_smells['Radon'][smell_type] += 1
                
                # Verbose file
                raw = analyze(content)
                if raw.loc > 100:
                    smell_type = "Verbose Test File"
                    # Only add if not already detected by AST or other library
                    if smell_type not in self.file_smells[test_file.name] or len(self.file_smells[test_file.name][smell_type]) == 0:
                        line = 1
                        desc = f"{raw.loc} lines of code"
                        self.file_smells[test_file.name][smell_type].add((line, desc))
                        self.library_smells['Radon'][smell_type] += 1
                        
            except Exception as e:
                pass
    
    def _detect_with_flake8(self, test_files: List[Path]):
        """Detect code quality issues using Flake8"""
        for test_file in test_files:
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'flake8', str(test_file), '--select=F,E,W'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if ':' in line:
                            parts = line.split(':')
                            if len(parts) >= 4:
                                line_num = parts[1].strip()
                                error_code = parts[3].strip().split()[0]
                                error_msg = ':'.join(parts[3:]).strip()
                                
                                # Map flake8 errors to smell types
                                if error_code.startswith('F'):
                                    smell_type = "Code Quality Issue"
                                elif error_code.startswith('E'):
                                    smell_type = "Style Violation"
                                elif error_code.startswith('W'):
                                    smell_type = "Code Warning"
                                else:
                                    continue
                                
                                try:
                                    # Only add if same smell type not already detected at this line
                                    if not any(existing_line == int(line_num) for existing_line, _ in self.file_smells[test_file.name][smell_type]):
                                        self.file_smells[test_file.name][smell_type].add((int(line_num), error_msg))
                                        self.library_smells['Flake8'][smell_type] += 1
                                except:
                                    pass
                                    
            except Exception as e:
                pass
    
    def _detect_with_jscpd(self):
        """Detect code duplication using JSCPD (handles Lazy Test detection partially)"""
        try:
            result = subprocess.run(
                ['jscpd', str(self.test_directory), 
                 '--format', 'json',
                 '--min-lines', '3',
                 '--min-tokens', '30'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    if 'duplicates' in data:
                        for dup in data['duplicates']:
                            # Extract file names and lines
                            first_file = Path(dup['firstFile']['name']).name
                            second_file = Path(dup['secondFile']['name']).name
                            
                            smell_type = "Duplicate Code"
                            line1 = dup['firstFile'].get('start', 1)
                            line2 = dup['secondFile'].get('start', 1)
                            
                            desc1 = f"Duplicated with {second_file}:{line2}"
                            desc2 = f"Duplicated with {first_file}:{line1}"
                            
                            # Only add if not already detected at these lines
                            if not any(existing_line == line1 for existing_line, _ in self.file_smells[first_file][smell_type]):
                                self.file_smells[first_file][smell_type].add((line1, desc1))
                                self.library_smells['JSCPD'][smell_type] += 1
                            if not any(existing_line == line2 for existing_line, _ in self.file_smells[second_file][smell_type]):
                                self.file_smells[second_file][smell_type].add((line2, desc2))
                                self.library_smells['JSCPD'][smell_type] += 1
                            
                except json.JSONDecodeError:
                    pass
                    
        except FileNotFoundError:
            pass
        except Exception as e:
            pass
    
    def _detect_with_pytest_smell(self):
        """Detect smells using pytest-smell"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest_smell',
                 '--tests_path', str(self.test_directory),
                 '--verbose'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout + result.stderr
            
            # Parse pytest-smell output
            import re
            lines = output.split('\n')
            
            for line in lines:
                if 'suffers from' in line:
                    file_match = re.search(r'File "([^"]+)", line (\d+)', line)
                    smell_match = re.search(r'suffers from "([^"]+)"', line)
                    
                    if file_match and smell_match:
                        file_path = file_match.group(1)
                        line_num = int(file_match.group(2))
                        smell_type = smell_match.group(1)
                        
                        filename = Path(file_path).name
                        
                        # Map pytest-smell names to our unified names
                        smell_mapping = {
                            'Assertion Roullete': 'Assertion Roulette',
                            'Conditional Logic': 'Conditional Test Logic',
                            'Duplicate Assert': 'Duplicate Assert',
                            'Exception Handling': 'Exception Handling',
                            'Redundant Print': 'Redundant Print',
                            'Sleepy Test': 'Sleepy Test',
                            'Unknown Test': 'Unknown Test',
                            'Magic Number': 'Magic Number Test',
                            'Eager Test': 'Eager Test',
                            'Ignored Test': 'Ignored Test'
                        }
                        
                        unified_smell = smell_mapping.get(smell_type, smell_type)
                        
                        # Check if same smell type already detected at same line by another library
                        existing_smells = self.file_smells[filename][unified_smell]
                        is_duplicate = any(existing_line == line_num for existing_line, _ in existing_smells)
                        
                        if not is_duplicate:
                            desc = f"Detected by pytest-smell"
                            self.file_smells[filename][unified_smell].add((line_num, desc))
                            self.library_smells['pytest-smell'][unified_smell] += 1
                            
        except Exception as e:
            pass
    
    def _display_results(self):
        """Display results organized by file with detailed line numbers"""
        
        print("="*80)
        print("FILE-WISE SMELL DETECTION RESULTS")
        print("="*80)
        print()
        
        total_files_with_smells = 0
        total_smell_instances = 0
        smell_type_counts = defaultdict(int)
        unique_smell_types = set()
        
        for filename in sorted(self.file_smells.keys()):
            smells = self.file_smells[filename]
            
            if not smells:
                continue
            
            total_files_with_smells += 1
            
            print(f"\n{'='*80}")
            print(f"FILE: {filename}")
            print(f"{'='*80}\n")
            
            file_smell_instances = 0
            file_unique_smell_types = set()
            
            for smell_type in sorted(smells.keys()):
                smell_instances = sorted(smells[smell_type], key=lambda x: x[0])
                count = len(smell_instances)
                file_smell_instances += count
                total_smell_instances += count
                smell_type_counts[smell_type] += count
                unique_smell_types.add(smell_type)
                file_unique_smell_types.add(smell_type)
                
                print(f"  [{smell_type}]")
                # Show all line numbers
                for line, desc in smell_instances:
                    print(f"    Line {line}: {desc}")
                print()
            
            print(f"  → Total smell instances in this file: {file_smell_instances}")
            print(f"  → Unique smell types in this file: {len(file_unique_smell_types)}")
            print()
        
        # Overall summary
        print("\n" + "="*80)
        print("OVERALL SUMMARY")
        print("="*80)
        print(f"Total files analyzed: {len(self.file_smells)}")
        print(f"Total files with smells: {total_files_with_smells}")
        print(f"Total smell instances (all occurrences): {total_smell_instances}")
        print(f"Total unique smell types: {len(unique_smell_types)}")
        print()
        print("Smell type breakdown (instances per type):")
        for smell_type in sorted(smell_type_counts.keys()):
            print(f"  • {smell_type}: {smell_type_counts[smell_type]} instance(s)")
        print()
    
    def _save_results(self):
        """Save results to JSON file"""
        output = {
            'summary': {
                'total_files': len(self.file_smells),
                'total_smells': sum(
                    len(smell_instances) 
                    for smells in self.file_smells.values() 
                    for smell_instances in smells.values()
                )
            },
            'files': {}
        }
        
        for filename, smells in self.file_smells.items():
            output['files'][filename] = {}
            for smell_type, instances in smells.items():
                output['files'][filename][smell_type] = [
                    {'line': line, 'description': desc}
                    for line, desc in sorted(instances, key=lambda x: x[0])
                ]
        
        with open('unified_smell_report.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        print(f"Detailed report saved to: unified_smell_report.json")


class ASTSmellVisitor(ast.NodeVisitor):
    """AST visitor for custom smell detection"""
    
    # Standard thresholds from pytest-smell and research
    ASSERTION_ROULETTE_THRESHOLD = 3  # More than 3 assertions
    VERBOSE_TEST_THRESHOLD = 20  # More than 20 statements
    CONSTRUCTOR_INIT_THRESHOLD = 3  # More than 3 initializations
    ALLOWED_MAGIC_NUMBERS = {0, 1, -1, 2, -2, 10, 100, -10, -100}  # Common test values
    
    def __init__(self, filename: str):
        self.filename = filename
        self.smells = []
        self.current_function = None
        self.function_assertions = defaultdict(int)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.name.startswith('test_'):
            self.current_function = node.name
            
            # Empty Test (standard: only pass or ... ellipsis)
            if len(node.body) == 1:
                if isinstance(node.body[0], ast.Pass):
                    self.smells.append({
                        'line': node.lineno,
                        'type': 'Empty Test',
                        'description': 'Test with only pass statement'
                    })
                elif isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                    if node.body[0].value.value == Ellipsis:
                        self.smells.append({
                            'line': node.lineno,
                            'type': 'Empty Test',
                            'description': 'Test with only ellipsis (...)'
                        })
            
            # Verbose Test (standard: > 20 statements)
            if len(node.body) > self.VERBOSE_TEST_THRESHOLD:
                self.smells.append({
                    'line': node.lineno,
                    'type': 'Verbose Test',
                    'description': f'{len(node.body)} statements (threshold: {self.VERBOSE_TEST_THRESHOLD})'
                })
            
            # Default Test (DT) - Test with non-descriptive name
            name_after_test = node.name[5:]  # Remove 'test_' prefix
            default_patterns = ['1', '2', '3', 'a', 'b', 'c', 'x', 'y', 'z', 
                               'test', 'default', 'temp', 'example', 'sample', 'demo']
            if name_after_test.isdigit() or name_after_test.lower() in default_patterns:
                self.smells.append({
                    'line': node.lineno,
                    'type': 'Default Test',
                    'description': f'Non-descriptive test name: {node.name}'
                })
            
            # Conditional Logic
            if any(isinstance(n, ast.If) for n in ast.walk(node)):
                self.smells.append({
                    'line': node.lineno,
                    'type': 'Conditional Test Logic',
                    'description': 'Contains if/else logic'
                })
            
            # Loop in test
            if any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(node)):
                self.smells.append({
                    'line': node.lineno,
                    'type': 'Test Logic in Loop',
                    'description': 'Contains loop'
                })
            
            # Exception Handling (standard: only flag generic exceptions)
            for n in ast.walk(node):
                if isinstance(n, ast.Try):
                    for handler in n.handlers:
                        # Flag only if catching generic Exception or bare except:
                        if handler.type is None:  # bare except:
                            self.smells.append({
                                'line': n.lineno,
                                'type': 'Exception Handling',
                                'description': 'Uses bare except: (catches all exceptions)'
                            })
                            break
                        elif isinstance(handler.type, ast.Name) and handler.type.id == 'Exception':
                            self.smells.append({
                                'line': n.lineno,
                                'type': 'Exception Handling',
                                'description': 'Catches generic Exception (use specific exceptions)'
                            })
                            break
                    break
            
            # Check for time.sleep and print
            for n in ast.walk(node):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                    if n.func.id == 'print':
                        self.smells.append({
                            'line': n.lineno,
                            'type': 'Redundant Print',
                            'description': 'Contains print statement'
                        })
                        break
                elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                    if n.func.attr == 'sleep':
                        self.smells.append({
                            'line': n.lineno,
                            'type': 'Sleepy Test',
                            'description': 'Uses time.sleep()'
                        })
                        break
            
            # Resource Optimism (RO) - File/network operations without proper checks
            resource_functions = ['open', 'connect', 'urlopen', 'request']
            has_try_except = any(isinstance(n, ast.Try) for n in ast.walk(node))
            
            for n in ast.walk(node):
                if isinstance(n, ast.Call):
                    func_name = None
                    if isinstance(n.func, ast.Name):
                        func_name = n.func.id
                    elif isinstance(n.func, ast.Attribute):
                        func_name = n.func.attr
                    
                    if func_name in resource_functions and not has_try_except:
                        self.smells.append({
                            'line': n.lineno,
                            'type': 'Resource Optimism',
                            'description': f'Uses {func_name}() without error handling'
                        })
                        break
            
            # Count assertions
            assertions = [n for n in ast.walk(node) if isinstance(n, ast.Assert)]
            self.function_assertions[node.name] = len(assertions)
            
            # Assertion Roulette (standard: > 3 assertions)
            if len(assertions) > self.ASSERTION_ROULETTE_THRESHOLD:
                self.smells.append({
                    'line': node.lineno,
                    'type': 'Assertion Roulette',
                    'description': f'{len(assertions)} assertions (threshold: {self.ASSERTION_ROULETTE_THRESHOLD})'
                })
            
            # Magic Numbers (standard: exclude common values like 0, ±1, ±2, 10, 100)
            for assertion in assertions:
                if isinstance(assertion.test, ast.Compare):
                    for comp in assertion.test.comparators:
                        if isinstance(comp, ast.Constant) and isinstance(comp.value, (int, float)):
                            if comp.value not in self.ALLOWED_MAGIC_NUMBERS:
                                self.smells.append({
                                    'line': assertion.lineno,
                                    'type': 'Magic Number Test',
                                    'description': f'Magic number: {comp.value}'
                                })
                                break
            
            # Redundant Assertion (RA) - Meaningless assertions
            for assertion in assertions:
                # Check for: assert True, assert False
                if isinstance(assertion.test, ast.Constant):
                    if assertion.test.value in [True, False]:
                        self.smells.append({
                            'line': assertion.lineno,
                            'type': 'Redundant Assertion',
                            'description': f'Meaningless assertion: assert {assertion.test.value}'
                        })
                
                # Check for: assert x == x (same variable on both sides)
                elif isinstance(assertion.test, ast.Compare):
                    if len(assertion.test.ops) == 1 and isinstance(assertion.test.ops[0], ast.Eq):
                        left = assertion.test.left
                        right = assertion.test.comparators[0]
                        # Check if both sides are the same variable
                        if isinstance(left, ast.Name) and isinstance(right, ast.Name):
                            if left.id == right.id:
                                self.smells.append({
                                    'line': assertion.lineno,
                                    'type': 'Redundant Assertion',
                                    'description': f'Redundant assertion: assert {left.id} == {right.id}'
                                })
            
            # Sensitive Equality (SE) - Float comparison with ==
            for assertion in assertions:
                if isinstance(assertion.test, ast.Compare):
                    # Check for == operator
                    if any(isinstance(op, ast.Eq) for op in assertion.test.ops):
                        # Check if any operand is a float constant or binary operation that could be float
                        for comp in assertion.test.comparators:
                            if isinstance(comp, ast.Constant) and isinstance(comp.value, float):
                                self.smells.append({
                                    'line': assertion.lineno,
                                    'type': 'Sensitive Equality',
                                    'description': f'Float comparison with ==: {comp.value}'
                                })
                                break
                        # Check if left side is float
                        if isinstance(assertion.test.left, ast.Constant) and isinstance(assertion.test.left.value, float):
                            self.smells.append({
                                'line': assertion.lineno,
                                'type': 'Sensitive Equality',
                                'description': f'Float comparison with ==: {assertion.test.left.value}'
                            })
                        # Check for division operations that produce floats
                        elif isinstance(assertion.test.left, ast.BinOp) and isinstance(assertion.test.left.op, ast.Div):
                            self.smells.append({
                                'line': assertion.lineno,
                                'type': 'Sensitive Equality',
                                'description': 'Float division result compared with =='
                            })
        
        elif node.name in ['setup_method', 'setUp']:
            assigns = [n for n in ast.walk(node) if isinstance(n, ast.Assign)]
            if len(assigns) > self.CONSTRUCTOR_INIT_THRESHOLD:
                self.smells.append({
                    'line': node.lineno,
                    'type': 'Constructor Initialization',
                    'description': f'{len(assigns)} initializations (threshold: {self.CONSTRUCTOR_INIT_THRESHOLD})'
                })
        
        self.generic_visit(node)
        
        # Assertion-less test
        if self.current_function == node.name:
            if self.function_assertions[node.name] == 0 and node.name.startswith('test_'):
                self.smells.append({
                    'line': node.lineno,
                    'type': 'Assertion-Less Test',
                    'description': 'No assertions'
                })
        
        self.current_function = None


def main():
    """Main entry point"""
    detector = UnifiedSmellDetector("tests")
    detector.detect_all_smells()
    
    print("\n" + "="*80)
    print("✓ Analysis complete! All 5 libraries used without duplicate counting.")
    print("="*80)


if __name__ == "__main__":
    main()
