"""
Use pytest-smell as a library to detect smells in test files
"""

import sys
import ast
from pathlib import Path


def analyze_with_pytest_smell_library():
    """
    Analyze test file using pytest-smell as a library
    """
    print("="*70)
    print("PYTEST-SMELL ANALYSIS - Using as Library")
    print("="*70)
    print()
    
    test_file = Path("tests/test_all_11_smells.py")
    
    try:
        # Method 1: Using pytest-smell's detection functions directly
        from pytest_smell.smells import (
            check_assertion_roulette,
            check_conditional_logic,
            check_duplicate_assert,
            check_exception_handling,
            check_redundant_print,
            check_sleepy_test,
            check_unknown_test,
            is_assertion,
            is_print,
            is_sleep
        )
        
        print("✓ pytest-smell imported successfully as library\n")
        
        # Read the test file
        with open(test_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            content = ''.join(lines)
        
        tree = ast.parse(content, filename=str(test_file))
        
        print(f"Analyzing: {test_file}\n")
        print("Smell Detection Results:")
        print("-" * 70)
        
        smells_found = {
            'Assertion Roulette': 0,
            'Conditional Test Logic': 0,
            'Constructor Initialization': 0,
            'Duplicate Assert': 0,
            'Empty Test': 0,
            'Exception Handling': 0,
            'General Fixture': 0,
            'Mystery Guest': 0,
            'Redundant Print': 0,
            'Sleepy Test': 0,
            'Unknown Test': 0
        }
        
        # Traverse the AST to find test functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                
                # Check if it's a test function
                if func_name.startswith('test_'):
                    # 1. Assertion Roulette
                    if check_assertion_roulette(node):
                        smells_found['Assertion Roulette'] += 1
                        print(f"✓ Assertion Roulette: {func_name} (line {node.lineno})")
                    
                    # 2. Conditional Test Logic
                    if check_conditional_logic(node):
                        smells_found['Conditional Test Logic'] += 1
                        print(f"✓ Conditional Test Logic: {func_name} (line {node.lineno})")
                    
                    # 4. Duplicate Assert
                    if check_duplicate_assert(node):
                        smells_found['Duplicate Assert'] += 1
                        print(f"✓ Duplicate Assert: {func_name} (line {node.lineno})")
                    
                    # 5. Empty Test
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        smells_found['Empty Test'] += 1
                        print(f"✓ Empty Test: {func_name} (line {node.lineno})")
                    
                    # 6. Exception Handling
                    if check_exception_handling(node):
                        smells_found['Exception Handling'] += 1
                        print(f"✓ Exception Handling: {func_name} (line {node.lineno})")
                    
                    # 9. Redundant Print
                    if check_redundant_print(node):
                        smells_found['Redundant Print'] += 1
                        print(f"✓ Redundant Print: {func_name} (line {node.lineno})")
                    
                    # 10. Sleepy Test
                    if check_sleepy_test(node):
                        smells_found['Sleepy Test'] += 1
                        print(f"✓ Sleepy Test: {func_name} (line {node.lineno})")
                    
                    # 11. Unknown Test
                    if check_unknown_test(node):
                        smells_found['Unknown Test'] += 1
                        print(f"✓ Unknown Test: {func_name} (line {node.lineno})")
                
                # Check setup methods for Constructor Initialization
                elif func_name in ['setup_method', 'setUp', 'setup_class']:
                    assigns = [n for n in ast.walk(node) if isinstance(n, ast.Assign)]
                    if len(assigns) > 2:
                        smells_found['Constructor Initialization'] += 1
                        smells_found['General Fixture'] += 1
                        print(f"✓ Constructor Initialization: {func_name} (line {node.lineno})")
                        print(f"✓ General Fixture: {func_name} (line {node.lineno})")
        
        # 8. Mystery Guest - check for external dependencies
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute):
                            if isinstance(child.func.value, ast.Name):
                                if child.func.value.id in ['os', 'sys', 'subprocess']:
                                    smells_found['Mystery Guest'] += 1
                                    print(f"✓ Mystery Guest: {node.name} (line {node.lineno})")
                                    break
        
        print("-" * 70)
        print("\nSummary:")
        total_smells = 0
        for smell, count in smells_found.items():
            if count > 0:
                print(f"  {smell:30} : {count}")
                total_smells += count
        
        print(f"\nTotal Smells Detected: {total_smells}/11 smell types")
        print()
        
        return total_smells
        
    except ImportError as e:
        print(f"❌ Cannot import pytest-smell library: {e}")
        print("\nTrying alternative approach using pytest runner...\n")
        
        # Method 2: Run pytest with smell detection plugin
        import subprocess
        
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', 
             '--smell-detect',
             str(test_file),
             '-v', '--tb=no'],
            capture_output=True,
            text=True
        )
        
        print("PYTEST-SMELL OUTPUT (via pytest plugin):")
        print("="*70)
        print(result.stdout)
        
        if result.stderr and "error" in result.stderr.lower():
            print("Errors:")
            print(result.stderr)
        
        return None
    
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None


def analyze_with_custom_ast():
    """
    Fallback: Custom AST-based detection similar to pytest-smell
    """
    print("\n" + "="*70)
    print("CUSTOM AST ANALYSIS (pytest-smell patterns)")
    print("="*70)
    print()
    
    test_file = Path("tests/test_all_11_smells.py")
    
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tree = ast.parse(content, filename=str(test_file))
    
    smells = {
        'Assertion Roulette': 0,
        'Conditional Test Logic': 0,
        'Constructor Initialization': 0,
        'Duplicate Assert': 0,
        'Empty Test': 0,
        'Exception Handling': 0,
        'General Fixture': 0,
        'Mystery Guest': 0,
        'Redundant Print': 0,
        'Sleepy Test': 0,
        'Unknown Test': 0
    }
    
    class SmellDetector(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            if node.name.startswith('test_'):
                # Check for empty test
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    smells['Empty Test'] += 1
                    print(f"✓ Empty Test: {node.name} (line {node.lineno})")
                
                # Check for unknown test (short/unclear names)
                if len(node.name) <= 6 or node.name == 'test_x':
                    smells['Unknown Test'] += 1
                    print(f"✓ Unknown Test: {node.name} (line {node.lineno})")
                
                # Count assertions
                assertions = [n for n in ast.walk(node) if isinstance(n, ast.Assert)]
                if len(assertions) > 3:
                    smells['Assertion Roulette'] += 1
                    print(f"✓ Assertion Roulette: {node.name} has {len(assertions)} assertions (line {node.lineno})")
                
                # Check for duplicate asserts
                assert_values = []
                for a in assertions:
                    assert_str = ast.unparse(a.test) if hasattr(ast, 'unparse') else str(a.test)
                    assert_values.append(assert_str)
                if len(assert_values) != len(set(assert_values)):
                    smells['Duplicate Assert'] += 1
                    print(f"✓ Duplicate Assert: {node.name} (line {node.lineno})")
                
                # Check for conditional logic
                has_if = any(isinstance(n, ast.If) for n in ast.walk(node))
                if has_if:
                    smells['Conditional Test Logic'] += 1
                    print(f"✓ Conditional Test Logic: {node.name} (line {node.lineno})")
                
                # Check for try-except
                has_try = any(isinstance(n, ast.Try) for n in ast.walk(node))
                if has_try:
                    smells['Exception Handling'] += 1
                    print(f"✓ Exception Handling: {node.name} (line {node.lineno})")
                
                # Check for print statements
                for n in ast.walk(node):
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                        if n.func.id == 'print':
                            smells['Redundant Print'] += 1
                            print(f"✓ Redundant Print: {node.name} (line {node.lineno})")
                            break
                        elif n.func.id == 'sleep' or (isinstance(n.func, ast.Attribute) 
                                                      and n.func.attr == 'sleep'):
                            smells['Sleepy Test'] += 1
                            print(f"✓ Sleepy Test: {node.name} (line {node.lineno})")
                            break
                
                # Check for os/file operations (Mystery Guest)
                for n in ast.walk(node):
                    if isinstance(n, ast.Call):
                        if isinstance(n.func, ast.Attribute):
                            if (isinstance(n.func.value, ast.Name) and 
                                n.func.value.id == 'os'):
                                smells['Mystery Guest'] += 1
                                print(f"✓ Mystery Guest: {node.name} (line {node.lineno})")
                                break
            
            elif node.name == 'setup_method' or node.name == 'setUp':
                # Check for constructor initialization
                assigns = [n for n in ast.walk(node) if isinstance(n, ast.Assign)]
                if len(assigns) > 3:
                    smells['Constructor Initialization'] += 1
                    smells['General Fixture'] += 1
                    print(f"✓ Constructor Initialization: {node.name} (line {node.lineno})")
                    print(f"✓ General Fixture: {node.name} has {len(assigns)} assignments (line {node.lineno})")
            
            self.generic_visit(node)
    
    detector = SmellDetector()
    detector.visit(tree)
    
    print("\n" + "-"*70)
    print("\nSummary:")
    total = 0
    for smell, count in smells.items():
        if count > 0:
            print(f"  {smell:30} : {count}")
            total += count
    
    print(f"\nTotal Smells Detected: {total}")
    print("="*70)


if __name__ == "__main__":
    # Try to use pytest-smell as library first
    result = analyze_with_pytest_smell_library()
    
    # If library approach fails, use custom AST analysis
    if result is None:
        analyze_with_custom_ast()
