"""
Examples of using each library individually for test smell detection
"""

# ============================================================================
# Example 1: Using pytest-smell
# ============================================================================
def example_pytest_smell():
    """
    Pytest-smell is a pytest plugin that detects test smells automatically
    
    Installation:
        pip install pytest-smell
    
    Usage:
        pytest --smell-detect tests/ -v
        pytest --smell-detect --smell-report=output.json tests/
    
    Detects:
        - Assertion Roulette
        - Conditional Test Logic
        - Constructor Initialization
        - Default Test
        - Duplicate Assert
        - Empty Test
        - Exception Handling
        - General Fixture
        - Mystery Guest
        - Redundant Print
        - Redundant Assertion
        - Sleepy Test
        - Unknown Test
    """
    import subprocess
    import sys
    
    # Run pytest with smell detection
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', 
         '--smell-detect', 
         'tests/', 
         '-v',
         '--tb=short'],
        capture_output=True,
        text=True
    )
    
    print("Pytest-Smell Output:")
    print(result.stdout)
    return result.stdout


# ============================================================================
# Example 2: Using Radon for complexity metrics
# ============================================================================
def example_radon_complexity(file_path: str):
    """
    Radon computes complexity metrics including cyclomatic complexity,
    maintainability index, and raw metrics
    
    Installation:
        pip install radon
    
    CLI Usage:
        radon cc tests/ -a        # Cyclomatic complexity
        radon mi tests/ -s        # Maintainability index
        radon raw tests/ -s       # Raw metrics
        radon hal tests/          # Halstead metrics
    """
    from radon.complexity import cc_visit, average_complexity
    from radon.metrics import mi_visit, h_visit
    from radon.raw import analyze
    
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    
    print(f"\n{'='*60}")
    print(f"Radon Analysis for: {file_path}")
    print(f"{'='*60}")
    
    # 1. Cyclomatic Complexity
    print("\n1. Cyclomatic Complexity:")
    complexity_results = cc_visit(code)
    for result in complexity_results:
        rank = result.letter  # A=best, F=worst
        print(f"   {result.name}:")
        print(f"     Complexity: {result.complexity} (Rank: {rank})")
        print(f"     Line: {result.lineno}")
        
        # Identify complex tests (smell)
        if result.complexity > 5:
            print(f"     ⚠️  WARNING: High complexity - Complex Test smell")
    
    # Average complexity
    avg = average_complexity(complexity_results)
    print(f"\n   Average Complexity: {avg:.2f}")
    
    # 2. Maintainability Index
    print("\n2. Maintainability Index:")
    mi_score = mi_visit(code, multi=True)
    print(f"   Score: {mi_score:.2f}")
    if mi_score < 50:
        print("   ⚠️  WARNING: Low maintainability (< 50)")
    elif mi_score < 65:
        print("   ⚠️  CAUTION: Moderate maintainability (50-65)")
    else:
        print("   ✓ Good maintainability (> 65)")
    
    # 3. Raw Metrics
    print("\n3. Raw Metrics:")
    raw = analyze(code)
    print(f"   Lines of Code (LOC): {raw.loc}")
    print(f"   Logical LOC (LLOC): {raw.lloc}")
    print(f"   Source LOC (SLOC): {raw.sloc}")
    print(f"   Comments: {raw.comments}")
    print(f"   Multi-line strings: {raw.multi}")
    print(f"   Blank lines: {raw.blank}")
    
    if raw.loc > 100:
        print("   ⚠️  WARNING: Verbose Test File (> 100 lines)")
    
    # 4. Halstead Metrics
    print("\n4. Halstead Metrics:")
    try:
        halstead = h_visit(code)
        if halstead:
            for h in halstead:
                print(f"   {h.name}:")
                print(f"     Volume: {h.volume:.2f}")
                print(f"     Difficulty: {h.difficulty:.2f}")
                print(f"     Effort: {h.effort:.2f}")
    except Exception as e:
        print(f"   Could not compute Halstead metrics: {e}")


# ============================================================================
# Example 3: Using Flake8 for code quality
# ============================================================================
def example_flake8(file_path: str):
    """
    Flake8 checks for PEP 8 compliance and common code quality issues
    
    Installation:
        pip install flake8
    
    CLI Usage:
        flake8 tests/
        flake8 tests/ --format=html --htmldir=report
        flake8 tests/ --statistics
    """
    import subprocess
    import sys
    
    print(f"\n{'='*60}")
    print(f"Flake8 Analysis for: {file_path}")
    print(f"{'='*60}\n")
    
    # Run flake8
    result = subprocess.run(
        [sys.executable, '-m', 'flake8', 
         file_path,
         '--show-source',
         '--statistics'],
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print("Issues found:")
        print(result.stdout)
    else:
        print("✓ No issues found")
    
    if result.stderr:
        print(f"Errors: {result.stderr}")
    
    return result.stdout


# ============================================================================
# Example 4: Using JSCPD for duplication detection
# ============================================================================
def example_jscpd(directory: str = "tests"):
    """
    JSCPD detects copy-paste duplications in code
    
    Installation:
        npm install -g jscpd
        
        OR for Python projects:
        pip install jscpd-python (if available)
    
    CLI Usage:
        jscpd tests/
        jscpd tests/ --format json --output report.json
        jscpd tests/ --min-lines 3 --min-tokens 30
    """
    import subprocess
    import json
    
    print(f"\n{'='*60}")
    print(f"JSCPD Duplication Analysis for: {directory}")
    print(f"{'='*60}\n")
    
    try:
        # Run JSCPD with JSON output
        result = subprocess.run(
            ['jscpd', directory, 
             '--format', 'json',
             '--min-lines', '3',
             '--min-tokens', '30',
             '--reporters', 'json,console'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("Console Output:")
        print(result.stdout)
        
        # Parse JSON output if available
        if result.stdout:
            try:
                data = json.loads(result.stdout)
                if 'duplicates' in data:
                    print(f"\nFound {len(data['duplicates'])} duplicate(s):")
                    for dup in data['duplicates'][:5]:  # Show first 5
                        print(f"  - {dup.get('format', 'python')}")
                        print(f"    Lines: {dup.get('lines', 'N/A')}")
                        print(f"    Tokens: {dup.get('tokens', 'N/A')}")
            except json.JSONDecodeError:
                pass
    
    except FileNotFoundError:
        print("❌ JSCPD not found. Install with: npm install -g jscpd")
    except subprocess.TimeoutExpired:
        print("❌ JSCPD timed out")
    except Exception as e:
        print(f"❌ Error running JSCPD: {e}")


# ============================================================================
# Example 5: Using AST for pattern-based detection
# ============================================================================
def example_ast_analysis(file_path: str):
    """
    Python's AST module for custom pattern detection
    
    Built-in to Python - no installation needed
    """
    import ast
    from collections import defaultdict
    
    print(f"\n{'='*60}")
    print(f"AST Analysis for: {file_path}")
    print(f"{'='*60}\n")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    
    tree = ast.parse(code, filename=file_path)
    
    # Collect statistics
    stats = {
        'test_functions': 0,
        'assertions': defaultdict(int),
        'conditionals': [],
        'loops': [],
        'try_except': [],
        'sleeps': [],
        'prints': []
    }
    
    class SmellDetector(ast.NodeVisitor):
        def __init__(self):
            self.current_test = None
        
        def visit_FunctionDef(self, node):
            if node.name.startswith('test_'):
                stats['test_functions'] += 1
                self.current_test = node.name
                
                # Check assertions
                assertion_count = sum(
                    1 for _ in ast.walk(node) 
                    if isinstance(_, ast.Assert)
                )
                stats['assertions'][node.name] = assertion_count
                
                # Check for conditionals
                if any(isinstance(n, ast.If) for n in ast.walk(node)):
                    stats['conditionals'].append(node.name)
                
                # Check for loops
                if any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(node)):
                    stats['loops'].append(node.name)
                
                # Check for try-except
                if any(isinstance(n, ast.Try) for n in ast.walk(node)):
                    stats['try_except'].append(node.name)
            
            self.generic_visit(node)
            self.current_test = None
        
        def visit_Call(self, node):
            if self.current_test:
                # Check for time.sleep
                if isinstance(node.func, ast.Attribute):
                    if (isinstance(node.func.value, ast.Name) and 
                        node.func.value.id == 'time' and 
                        node.func.attr == 'sleep'):
                        stats['sleeps'].append(self.current_test)
                
                # Check for print
                elif isinstance(node.func, ast.Name) and node.func.id == 'print':
                    stats['prints'].append(self.current_test)
            
            self.generic_visit(node)
    
    detector = SmellDetector()
    detector.visit(tree)
    
    # Print results
    print(f"Total test functions: {stats['test_functions']}\n")
    
    print("Assertion counts:")
    for test, count in stats['assertions'].items():
        status = ""
        if count == 0:
            status = " ⚠️  Assertion-Less Test"
        elif count > 3:
            status = " ⚠️  Assertion Roulette"
        print(f"  {test}: {count} assertion(s){status}")
    
    if stats['conditionals']:
        print(f"\n⚠️  Conditional Test Logic in: {', '.join(stats['conditionals'])}")
    
    if stats['loops']:
        print(f"\n⚠️  Loops in tests: {', '.join(stats['loops'])}")
    
    if stats['try_except']:
        print(f"\n⚠️  Try-Except blocks in: {', '.join(stats['try_except'])}")
    
    if stats['sleeps']:
        print(f"\n⚠️  Sleep calls (Sleepy Test): {', '.join(stats['sleeps'])}")
    
    if stats['prints']:
        print(f"\n⚠️  Print statements in: {', '.join(stats['prints'])}")


# ============================================================================
# Example 6: Using ast-grep (if installed)
# ============================================================================
def example_ast_grep(directory: str = "tests"):
    """
    ast-grep is a structural search tool for code
    
    Installation:
        cargo install ast-grep
        OR download from: https://github.com/ast-grep/ast-grep
    
    CLI Usage:
        ast-grep --pattern 'def test_$NAME(): $$$' tests/
        ast-grep scan -c ast-grep-rules.yml tests/
    """
    import subprocess
    
    print(f"\n{'='*60}")
    print(f"ast-grep Analysis for: {directory}")
    print(f"{'='*60}\n")
    
    try:
        # Run ast-grep with rule file
        result = subprocess.run(
            ['ast-grep', 'scan', 
             '-c', 'ast-grep-rules.yml',
             directory],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.stdout:
            print("Results:")
            print(result.stdout)
        else:
            print("✓ No issues found")
        
        if result.stderr and "not found" not in result.stderr.lower():
            print(f"\nWarnings/Errors:\n{result.stderr}")
    
    except FileNotFoundError:
        print("❌ ast-grep not found.")
        print("   Install: cargo install ast-grep")
        print("   Or download from: https://github.com/ast-grep/ast-grep")
    except Exception as e:
        print(f"❌ Error running ast-grep: {e}")


# ============================================================================
# Main: Run all examples
# ============================================================================
def main():
    """Run all examples"""
    import sys
    
    # Example file to analyze
    test_file = "tests/test_arithmetic.py"
    
    print("="*60)
    print("TEST SMELL DETECTION - LIBRARY EXAMPLES")
    print("="*60)
    
    # 1. Pytest-smell
    print("\n" + "="*60)
    print("1. PYTEST-SMELL")
    print("="*60)
    try:
        example_pytest_smell()
    except Exception as e:
        print(f"Error: {e}")
    
    # 2. Radon
    print("\n" + "="*60)
    print("2. RADON")
    print("="*60)
    try:
        example_radon_complexity(test_file)
    except Exception as e:
        print(f"Error: {e}")
    
    # 3. Flake8
    print("\n" + "="*60)
    print("3. FLAKE8")
    print("="*60)
    try:
        example_flake8(test_file)
    except Exception as e:
        print(f"Error: {e}")
    
    # 4. JSCPD
    print("\n" + "="*60)
    print("4. JSCPD")
    print("="*60)
    try:
        example_jscpd("tests")
    except Exception as e:
        print(f"Error: {e}")
    
    # 5. AST
    print("\n" + "="*60)
    print("5. AST (Python Built-in)")
    print("="*60)
    try:
        example_ast_analysis(test_file)
    except Exception as e:
        print(f"Error: {e}")
    
    # 6. ast-grep
    print("\n" + "="*60)
    print("6. AST-GREP")
    print("="*60)
    try:
        example_ast_grep("tests")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
