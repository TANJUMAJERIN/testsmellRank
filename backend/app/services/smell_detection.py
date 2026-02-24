

"""
AST-based detection for exactly the 15 test smells analyzed in:
"Prioritizing Test Smells: An Empirical Evaluation of Quality Metrics
and Developer Perceptions" (ICSME 2025)

The 15 smells:
  CTL  - Conditional Test Logic
  AR   - Assertion Roulette
  DA   - Duplicate Assert
  MNT  - Magic Number Test
  OS   - Obscure In-Line Setup
  RA   - Redundant Assertion
  EH   - Exception Handling
  CI   - Constructor Initialization
  SA   - Suboptimal Assert
  TM   - Test Maverick
  RP   - Redundant Print
  GF   - General Fixture
  ST   - Sleepy Test
  ET   - Empty Test
  LCTC - Lack of Cohesion of Test Cases
"""

import ast
from pathlib import Path
from .git_metrics import analyze_project_with_git


# =====================================================
# MAIN ENTRY POINT
# =====================================================

def detect_smells_for_project(
    project_path: Path,
    include_git_metrics: bool = True,
    cp_weight: float = 0.5,
):
    """
    Detect all 15 paper-defined test smells across a project's test files.
    Optionally computes CP/FP/PS metrics from git history.

    cp_weight: weight for CP in PS formula (default 0.5 = equal weighting).
    """
    test_files = (
        list(project_path.glob("**/test_*.py")) +
        list(project_path.glob("**/*_test.py"))
    )

    if not test_files:
        return {
            "total_files": 0,
            "total_smells": 0,
            "details": [],
            "git_metrics": None,
        }

    results = []
    total_smells = 0
    all_smell_instances = []

    for file in test_files:
        rel_path = str(file.relative_to(project_path))

        file_smells = detect_all_smells(file)
        total_smells += len(file_smells)

        for smell in file_smells:
            instance = smell.copy()
            instance['file'] = rel_path
            all_smell_instances.append(instance)

        results.append({
            "file":        rel_path,
            "smells":      file_smells,
            "smell_count": len(file_smells),
        })

    # Git-based metrics (CP / FP / PS)
    git_analysis = None
    if include_git_metrics:
        if all_smell_instances:
            try:
                git_analysis = analyze_project_with_git(project_path, all_smell_instances, cp_weight)
            except Exception as exc:
                print(f"Git metrics calculation failed: {exc}")
                git_analysis = {
                    "error": (
                        "Git metrics could not be computed. "
                        f"Reason: {exc}"
                    ),
                    "metrics": {},
                }
        else:
            # No smells detected — check whether a git repo even exists so
            # the caller can still report a useful status to the user.
            has_git = (project_path / '.git').exists()
            git_analysis = {
                "error": None,
                "metrics": {},
                "statistics": None,
                "note": (
                    "No test smells were detected, so git-based prioritization "
                    "was not performed."
                    if has_git else
                    "The project does not include git history to prioritize the smells. "
                    "Upload a project that contains a .git folder (with commit history) "
                    "to enable CP, FP, and PS prioritization scores."
                ),
            }

    return {
        "total_files":   len(test_files),
        "total_smells":  total_smells,
        "details":       results,
        "git_metrics":   git_analysis,
    }


# =====================================================
# TOP-LEVEL DISPATCHER
# =====================================================

def detect_all_smells(test_file: Path):
    """
    Run all 15 smell detectors on a single test file.
    Returns a flat list of smell dicts:
      { 'type': str, 'line': int, 'message': str }
    """
    smells = []

    try:
        source = test_file.read_text(encoding="utf-8")
        tree   = ast.parse(source)
        lines  = source.splitlines()

        class_nodes    = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        function_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]

        for class_node in class_nodes:
            smells.extend(_analyze_class_smells(class_node))

        for func_node in function_nodes:
            smells.extend(_analyze_function_smells(func_node, lines))

    except Exception as exc:
        print(f"Error analyzing {test_file}: {exc}")

    return smells


# =====================================================
# CLASS-LEVEL SMELLS
# =====================================================

def _analyze_class_smells(class_node: ast.ClassDef):
    """
    Detects class-level smells:
      CI   - Constructor Initialization
      GF   - General Fixture
      TM   - Test Maverick
      LCTC - Lack of Cohesion of Test Cases
    """
    smells = []

    all_methods  = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]
    test_methods = [m for m in all_methods if m.name.startswith('test_')]

    # ── CI: Constructor Initialization ──────────────────────────────
    # Test class uses __init__ instead of setUp()
    if any(m.name == '__init__' for m in all_methods):
        smells.append({
            "type":    "Constructor Initialization",
            "line":    class_node.lineno,
            "message": "__init__ used in test class instead of setUp()",
        })

    # ── GF: General Fixture ─────────────────────────────────────────
    # setUp() initialises more objects than any single test needs
    setup_methods = [
        m for m in all_methods
        if m.name in ('setUp', 'setup', 'setup_method', 'setUpClass')
    ]
    for setup in setup_methods:
        assignments = [n for n in ast.walk(setup) if isinstance(n, ast.Assign)]
        if len(assignments) > 5:
            smells.append({
                "type":    "General Fixture",
                "line":    setup.lineno,
                "message": (
                    f"setUp() contains {len(assignments)} assignments — "
                    "likely initialises more than any single test needs"
                ),
            })

    # ── TM: Test Maverick ───────────────────────────────────────────
    # Test class with only one test method (isolated, non-cohesive)
    if len(test_methods) == 1:
        smells.append({
            "type":    "Test Maverick",
            "line":    class_node.lineno,
            "message": "Test class contains only one test method",
        })

    # ── LCTC: Lack of Cohesion of Test Cases ────────────────────────
    # Test methods share no common self.* attributes → unrelated concerns
    if len(test_methods) > 1:
        attr_sets = []
        for method in test_methods:
            attrs = {
                n.attr
                for n in ast.walk(method)
                if isinstance(n, ast.Attribute)
                and isinstance(n.value, ast.Name)
                and n.value.id == 'self'
            }
            attr_sets.append(attrs)

        # Only flag when methods actually USE self.* but share nothing
        non_empty = [s for s in attr_sets if s]
        if len(non_empty) == len(attr_sets) and len(attr_sets) > 1:
            common = set.intersection(*attr_sets)
            if not common:
                smells.append({
                    "type":    "Lack of Cohesion of Test Cases",
                    "line":    class_node.lineno,
                    "message": "Test methods share no common self.* attributes",
                })

    return smells


# =====================================================
# FUNCTION-LEVEL SMELLS
# =====================================================

def _analyze_function_smells(func_node: ast.FunctionDef, lines: list):
    """
    Detects function-level smells:
      ET  - Empty Test
      AR  - Assertion Roulette
      RA  - Redundant Assertion
      SA  - Suboptimal Assert
      DA  - Duplicate Assert
      MNT - Magic Number Test
      OS  - Obscure In-Line Setup
      CTL - Conditional Test Logic
      EH  - Exception Handling
      ST  - Sleepy Test
      RP  - Redundant Print
    """
    smells = []

    # Only analyse test functions/methods
    if not func_node.name.startswith('test_'):
        return smells

    body_nodes = func_node.body
    all_nodes  = list(ast.walk(func_node))

    # ── ET: Empty Test ───────────────────────────────────────────────
    if not body_nodes or (
        len(body_nodes) == 1 and isinstance(body_nodes[0], ast.Pass)
    ):
        smells.append({
            "type":    "Empty Test",
            "line":    func_node.lineno,
            "message": "Test has no body or contains only 'pass'",
        })
        return smells   # nothing else to check

    # Also treat a docstring-only body as empty
    if len(body_nodes) == 1 and isinstance(body_nodes[0], ast.Expr) and isinstance(body_nodes[0].value, ast.Constant):
        smells.append({
            "type":    "Empty Test",
            "line":    func_node.lineno,
            "message": "Test contains only a docstring — no assertions",
        })
        return smells

    # Collect assertions once — reused by multiple detectors below
    assertions = [n for n in all_nodes if isinstance(n, ast.Assert)]

    # ── AR: Assertion Roulette ───────────────────────────────────────
    # Multiple assertions with no explanatory message
    if len(assertions) > 3:
        no_msg = [a for a in assertions if a.msg is None]
        if len(no_msg) > 3:
            smells.append({
                "type":    "Assertion Roulette",
                "line":    func_node.lineno,
                "message": (
                    f"{len(no_msg)} assertions have no failure message — "
                    "hard to identify which one fails"
                ),
            })

    # ── RA: Redundant Assertion ──────────────────────────────────────
    # assert True  /  assert 1 == 1  — always passes, zero value
    for node in assertions:
        is_trivially_true = (
            isinstance(node.test, ast.Constant) and node.test.value is True
        )
        is_tautology = (
            isinstance(node.test, ast.Compare) and
            len(node.test.ops) == 1 and
            isinstance(node.test.ops[0], ast.Eq) and
            len(node.test.comparators) == 1 and
            isinstance(node.test.left, ast.Constant) and
            isinstance(node.test.comparators[0], ast.Constant) and
            node.test.left.value == node.test.comparators[0].value
        )
        if is_trivially_true or is_tautology:
            smells.append({
                "type":    "Redundant Assertion",
                "line":    node.lineno,
                "message": "Assertion always passes — provides no real verification",
            })

    # ── SA: Suboptimal Assert ────────────────────────────────────────
    # assertTrue(x == y) / assertTrue(x is True) instead of assertEqual
    for node in assertions:
        if isinstance(node.test, ast.Compare):
            for comparator in node.test.comparators:
                if (
                    isinstance(comparator, ast.Constant) and
                    comparator.value in (True, False)
                ):
                    smells.append({
                        "type":    "Suboptimal Assert",
                        "line":    node.lineno,
                        "message": (
                            "Comparing with True/False explicitly — "
                            "use assertTrue()/assertFalse() instead"
                        ),
                    })
                    break

    # ── DA: Duplicate Assert ─────────────────────────────────────────
    # Same assertion expression repeated more than once
    seen_assertions: dict = {}
    for node in assertions:
        try:
            text = ast.unparse(node.test)
            if text in seen_assertions:
                smells.append({
                    "type":    "Duplicate Assert",
                    "line":    node.lineno,
                    "message": (
                        f"Assertion '{text}' duplicates line "
                        f"{seen_assertions[text]}"
                    ),
                })
            else:
                seen_assertions[text] = node.lineno
        except Exception:
            pass

    # ── MNT: Magic Number Test ───────────────────────────────────────
    # Numeric literal in assertion comparator (not 0, 1, -1)
    for node in assertions:
        if isinstance(node.test, ast.Compare):
            for comp in node.test.comparators:
                if (
                    isinstance(comp, ast.Constant) and
                    isinstance(comp.value, (int, float)) and
                    comp.value not in (0, 1, -1, 0.0, 1.0, -1.0)
                ):
                    smells.append({
                        "type":    "Magic Number Test",
                        "line":    node.lineno,
                        "message": (
                            f"Magic number {comp.value!r} in assertion — "
                            "use a named constant"
                        ),
                    })
                    break   # one report per assertion is enough

    # ── OS: Obscure In-Line Setup ────────────────────────────────────
    # Significant object creation / variable assignment happens inside
    # the test body rather than in setUp(), obscuring the test's intent.
    # Heuristic: ≥ 3 assignments OR ≥ 2 constructor calls before any assertion.
    setup_assignments = 0
    constructor_calls = 0
    first_assert_line = min((a.lineno for a in assertions), default=None)

    for node in all_nodes:
        node_line = getattr(node, 'lineno', None)
        if first_assert_line and node_line and node_line >= first_assert_line:
            continue    # only count nodes BEFORE the first assertion
        if isinstance(node, ast.Assign):
            setup_assignments += 1
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            # Heuristic: capitalised name → likely a constructor call
            if node.func.id and node.func.id[0].isupper():
                constructor_calls += 1

    if setup_assignments >= 3 or constructor_calls >= 2:
        smells.append({
            "type":    "Obscure In-Line Setup",
            "line":    func_node.lineno,
            "message": (
                f"Test body contains {setup_assignments} assignments and "
                f"{constructor_calls} constructor calls before first assertion — "
                "move setup to setUp()"
            ),
        })

    # ── CTL: Conditional Test Logic ──────────────────────────────────
    # if / for / while inside test method introduces multiple execution paths
    for node in all_nodes:
        if isinstance(node, ast.If):
            smells.append({
                "type":    "Conditional Test Logic",
                "line":    node.lineno,
                "message": "Test contains an if/else branch",
            })
            break   # one report per function
    for node in all_nodes:
        if isinstance(node, (ast.For, ast.While)):
            smells.append({
                "type":    "Conditional Test Logic",
                "line":    node.lineno,
                "message": "Test contains a loop (for/while)",
            })
            break

    # ── EH: Exception Handling ──────────────────────────────────────
    # try/except in test instead of using assertRaises()
    for node in all_nodes:
        if isinstance(node, ast.Try):
            for handler in node.handlers:
                is_generic = (
                    handler.type is None or
                    (isinstance(handler.type, ast.Name) and
                     handler.type.id == 'Exception')
                )
                if is_generic:
                    smells.append({
                        "type":    "Exception Handling",
                        "line":    node.lineno,
                        "message": (
                            "Generic try/except in test — "
                            "use assertRaises() instead"
                        ),
                    })
                    break   # one report per try block

    # ── ST: Sleepy Test ──────────────────────────────────────────────
    # time.sleep() call makes tests slow and non-deterministic
    for node in all_nodes:
        if (
            isinstance(node, ast.Call) and
            isinstance(node.func, ast.Attribute) and
            node.func.attr == 'sleep'
        ):
            smells.append({
                "type":    "Sleepy Test",
                "line":    node.lineno,
                "message": "Test uses time.sleep() — non-deterministic across machines",
            })
            break   # one report per function

    # ── RP: Redundant Print ──────────────────────────────────────────
    # print() calls inside test add noise, serve no assertion purpose
    print_lines = [
        node.lineno
        for node in all_nodes
        if (
            isinstance(node, ast.Call) and
            isinstance(node.func, ast.Name) and
            node.func.id == 'print'
        )
    ]
    if print_lines:
        smells.append({
            "type":    "Redundant Print",
            "line":    print_lines[0],
            "message": (
                f"Test contains {len(print_lines)} print statement(s) — "
                "remove or replace with logging"
            ),
        })

    return smells