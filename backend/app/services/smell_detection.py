# app/services/smell_detection.py

import subprocess
import ast
from pathlib import Path
from collections import defaultdict


# =====================================================
# MAIN ENTRY POINT
# =====================================================
def detect_smells_for_project(project_path: Path):

    test_files = list(project_path.glob("**/test_*.py")) + \
                 list(project_path.glob("**/*_test.py"))

    if not test_files:
        return {
            "total_files": 0,
            "total_smells": 0,
            "details": []
        }

    results = []
    total_smells = 0

    for file in test_files:
        rel_path = str(file.relative_to(project_path))
        
        # Detect all smells using comprehensive AST analysis
        file_smells = detect_all_smells(file)

        total_smells += len(file_smells)

        results.append({
            "file": rel_path,
            "smells": file_smells,
            "smell_count": len(file_smells)
        })

    return {
        "total_files": len(test_files),
        "total_smells": total_smells,
        "details": results
    }


# =====================================================
# COMPREHENSIVE SMELL DETECTOR (ALL 15 SMELLS)
# =====================================================
def detect_all_smells(test_file: Path):
    """Detect all 15 test smells using AST analysis"""
    
    smells = []

    try:
        source = test_file.read_text(encoding="utf-8")
        tree = ast.parse(source)
        lines = source.splitlines()

        # Track various metrics for smell detection
        class_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        function_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        # Analyze each class
        for class_node in class_nodes:
            smells.extend(analyze_class_smells(class_node, source))
        
        # Analyze each function/method
        for func_node in function_nodes:
            smells.extend(analyze_function_smells(func_node, source, lines))
        
        # Whole-file smells
        smells.extend(detect_module_level_smells(tree, source, lines))

    except Exception as e:
        print(f"Error analyzing {test_file}: {e}")

    return smells


# =====================================================
# CLASS-LEVEL SMELL DETECTION
# =====================================================
def analyze_class_smells(class_node: ast.ClassDef, source: str):
    """Detect smells at the class level"""
    smells = []
    
    test_methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef) 
                    and n.name.startswith('test_')]
    all_methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]
    
    # 1. Constructor Initialization (CI)
    has_init = any(m.name == '__init__' for m in all_methods)
    if has_init:
        smells.append({
            "type": "Constructor Initialization",
            "line": class_node.lineno,
            "message": "__init__ used in test class instead of setup_method/setUp"
        })
    
    # 2. General Fixture (GF) - Complex setup
    setup_methods = [m for m in all_methods if m.name in ['setup_method', 'setUp', 'setup', 'setUpClass']]
    for setup in setup_methods:
        # Count assignments in setup
        assignments = [n for n in ast.walk(setup) if isinstance(n, ast.Assign)]
        if len(assignments) > 5:  # Threshold for "overly complex"
            smells.append({
                "type": "General Fixture",
                "line": setup.lineno,
                "message": f"Complex fixture setup with {len(assignments)} assignments"
            })
    
    # 3. Test Maverick (TM) - Isolated test class
    if len(test_methods) <= 1 and len(test_methods) > 0:
        smells.append({
            "type": "Test Maverick",
            "line": class_node.lineno,
            "message": "Test class with only one test method"
        })
    
    # 4. Lack of Cohesion (LCTC)
    if len(test_methods) > 1:
        attr_usage_per_method = []
        for method in test_methods:
            attrs = set()
            for n in ast.walk(method):
                if isinstance(n, ast.Attribute):
                    if isinstance(n.value, ast.Name) and n.value.id == "self":
                        attrs.add(n.attr)
            attr_usage_per_method.append(attrs)
        
        # Check if methods share attributes
        if attr_usage_per_method:
            common_attrs = set.intersection(*attr_usage_per_method) if len(attr_usage_per_method) > 1 else set()
            if not common_attrs and any(attr_usage_per_method):
                smells.append({
                    "type": "Lack of Cohesion of Test Cases",
                    "line": class_node.lineno,
                    "message": "Test methods do not share common attributes"
                })
    
    return smells


# =====================================================
# FUNCTION-LEVEL SMELL DETECTION
# =====================================================
def analyze_function_smells(func_node: ast.FunctionDef, source: str, lines: list):
    """Detect smells at the function level"""
    smells = []
    
    # Only analyze test functions
    if not func_node.name.startswith('test_'):
        return smells
    
    # Get function body nodes
    body_nodes = func_node.body
    
    # 1. Empty Test (ET)
    if len(body_nodes) == 1 and isinstance(body_nodes[0], ast.Pass):
        smells.append({
            "type": "Empty Test",
            "line": func_node.lineno,
            "message": "Test contains only 'pass' statement"
        })
        return smells  # No need to check further
    
    if len(body_nodes) == 0:
        smells.append({
            "type": "Empty Test",
            "line": func_node.lineno,
            "message": "Test has no body"
        })
        return smells
    
    # Collect all nodes in function
    all_nodes = list(ast.walk(func_node))
    
    # 2. Assertion Roulette (AR) - Multiple assertions without messages
    assertions = [n for n in all_nodes if isinstance(n, ast.Assert)]
    if len(assertions) > 3:
        assertions_without_msg = [a for a in assertions if a.msg is None]
        if len(assertions_without_msg) > 3:
            smells.append({
                "type": "Assertion Roulette",
                "line": func_node.lineno,
                "message": f"{len(assertions_without_msg)} assertions without messages"
            })
    
    # 3. Redundant Assertion (RA) - assert True
    for node in assertions:
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            smells.append({
                "type": "Redundant Assertion",
                "line": node.lineno,
                "message": "assert True detected"
            })
    
    # 4. Suboptimal Assert (SA) - Boolean comparison
    for node in assertions:
        if isinstance(node.test, ast.Compare):
            for comp in node.test.comparators:
                if isinstance(comp, ast.Constant) and comp.value in [True, False]:
                    smells.append({
                        "type": "Suboptimal Assert",
                        "line": node.lineno,
                        "message": "Comparing with True/False instead of direct assertion"
                    })
    
    # 5. Conditional Test Logic (CTL) - if/else/for/while
    has_if = any(isinstance(n, ast.If) for n in all_nodes)
    has_for = any(isinstance(n, (ast.For, ast.While)) for n in all_nodes)
    if has_if:
        if_node = next(n for n in all_nodes if isinstance(n, ast.If))
        smells.append({
            "type": "Conditional Test Logic",
            "line": if_node.lineno,
            "message": "Test contains conditional logic (if/else)"
        })
    if has_for:
        for_node = next(n for n in all_nodes if isinstance(n, (ast.For, ast.While)))
        smells.append({
            "type": "Conditional Test Logic",
            "line": for_node.lineno,
            "message": "Test contains loop logic"
        })
    
    # 6. Exception Handling (EH) - try/except
    try_nodes = [n for n in all_nodes if isinstance(n, ast.Try)]
    for try_node in try_nodes:
        # Check for generic exception handling
        for handler in try_node.handlers:
            if handler.type is None or (isinstance(handler.type, ast.Name) and handler.type.id == "Exception"):
                smells.append({
                    "type": "Exception Handling",
                    "line": try_node.lineno,
                    "message": "Generic exception handling in test"
                })
    
    # 7. Sleepy Test (ST) - time.sleep()
    for node in all_nodes:
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'sleep':
                smells.append({
                    "type": "Sleepy Test",
                    "line": node.lineno,
                    "message": "Test uses time.sleep()"
                })
    
    # 8. Redundant Print (RP) - print statements
    print_calls = []
    for node in all_nodes:
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'print':
                print_calls.append(node.lineno)
    if print_calls:
        smells.append({
            "type": "Redundant Print",
            "line": print_calls[0],
            "message": f"Test contains {len(print_calls)} print statement(s)"
        })
    
    # 9. Magic Number Test (MNT) - Hardcoded numbers in assertions
    magic_numbers = detect_magic_numbers(func_node)
    if magic_numbers:
        smells.append({
            "type": "Magic Number Test",
            "line": magic_numbers[0],
            "message": f"Test uses magic numbers without explanation"
        })
    
    # 10. Mystery Guest (MG) - External dependencies
    mystery_guest = detect_mystery_guest(func_node)
    if mystery_guest:
        smells.append({
            "type": "Mystery Guest",
            "line": mystery_guest[0],
            "message": mystery_guest[1]
        })
    
    # 11. Duplicate Assert (DA) - Same assertion repeated
    duplicate_asserts = detect_duplicate_assertions(assertions)
    if duplicate_asserts:
        smells.append({
            "type": "Duplicate Assert",
            "line": duplicate_asserts[0],
            "message": "Duplicate assertion found"
        })
    
    # 12. Resource Optimism (RO) - File operations without error handling
    resource_ops = detect_resource_optimism(func_node)
    if resource_ops:
        smells.append({
            "type": "Resource Optimism",
            "line": resource_ops,
            "message": "File/resource operation without proper error handling"
        })
    
    # 13. Verbose Test - Very long test (> 30 lines or too many statements)
    func_length = (func_node.end_lineno or func_node.lineno) - func_node.lineno
    if func_length > 30:
        smells.append({
            "type": "Verbose Test",
            "line": func_node.lineno,
            "message": f"Test is too long ({func_length} lines)"
        })
    
    # 14. Unknown Test - Test with unclear purpose (no assertions)
    if len(assertions) == 0 and len(body_nodes) > 1:
        smells.append({
            "type": "Unknown Test",
            "line": func_node.lineno,
            "message": "Test has no assertions"
        })
    
    return smells


# =====================================================
# HELPER FUNCTIONS FOR SPECIFIC SMELL DETECTION
# =====================================================
def detect_magic_numbers(func_node):
    """Detect magic numbers in assertions"""
    magic_lines = []
    for node in ast.walk(func_node):
        if isinstance(node, ast.Assert) and isinstance(node.test, ast.Compare):
            for comp in node.test.comparators:
                if isinstance(comp, ast.Constant) and isinstance(comp.value, (int, float)):
                    if abs(comp.value) > 1 and comp.value not in [0, 1, -1]:
                        magic_lines.append(node.lineno)
    return magic_lines


def detect_mystery_guest(func_node):
    """Detect external dependencies (file system, environment, network)"""
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            # Check for os/file operations
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id in ['os', 'sys', 'environ']:
                        return (node.lineno, f"Uses external dependency: {node.func.value.id}")
                    if node.func.attr in ['open', 'read', 'write']:
                        return (node.lineno, "Accesses file system")
            # Check for open() calls
            if isinstance(node.func, ast.Name) and node.func.id == 'open':
                return (node.lineno, "File system access")
    return None


def detect_duplicate_assertions(assertions):
    """Detect duplicate assertion patterns"""
    assertion_texts = []
    seen = {}
    
    for assertion in assertions:
        # Convert assertion to string representation
        try:
            text = ast.unparse(assertion.test)
            if text in seen:
                return [assertion.lineno]
            seen[text] = assertion.lineno
        except:
            pass
    
    return []


def detect_resource_optimism(func_node):
    """Detect file/resource operations without try-except"""
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'open':
                # Check if it's inside a try-except
                parent = func_node
                in_try = False
                for n in ast.walk(parent):
                    if isinstance(n, ast.Try):
                        for stmt in ast.walk(n):
                            if stmt == node:
                                in_try = True
                
                if not in_try:
                    return node.lineno
    
    return None


def detect_module_level_smells(tree, source, lines):
    """Detect smells at module level"""
    smells = []
    
    # Lazy Test - Check for duplicate test functions
    func_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) 
                  and node.name.startswith('test_')]
    
    func_bodies = {}
    for func in func_nodes:
        try:
            body_str = ast.unparse(func)
            if body_str in func_bodies:
                smells.append({
                    "type": "Lazy Test",
                    "line": func.lineno,
                    "message": f"Duplicate test logic (similar to line {func_bodies[body_str]})"
                })
            else:
                func_bodies[body_str] = func.lineno
        except:
            pass
    
    return smells
