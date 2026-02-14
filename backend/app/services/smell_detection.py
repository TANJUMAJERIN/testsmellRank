# app/services/smell_detection.py

import subprocess
import ast
from pathlib import Path


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

    pytest_smells = run_pytest_smell(project_path)

    results = []
    total_smells = 0

    for file in test_files:
        rel_path = str(file.relative_to(project_path))
        file_smells = []

        # 1️⃣ pytest-smell results
        if rel_path in pytest_smells:
            file_smells.extend(pytest_smells[rel_path])

        # 2️⃣ AST custom smells
        ast_smells = detect_remaining_paper_smells(file)
        file_smells.extend(ast_smells)

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
# PYTEST-SMELL PARSER (FIXED)
# =====================================================
def run_pytest_smell(project_path: Path):

    try:
        result = subprocess.run(
            ["pytest", "--smell", "-q"],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        output = result.stdout
        parsed = {}
        current_file = None

        for line in output.splitlines():

            line = line.strip()

            # Detect test file line
            if ".py::" in line:
                file_path = line.split("::")[0]

                try:
                    file_path = str(Path(file_path).relative_to(project_path))
                except Exception:
                    file_path = file_path.replace("\\", "/")

                current_file = file_path

                if current_file not in parsed:
                    parsed[current_file] = []

            # Detect smell name line
            elif current_file and line and not line.startswith("="):
                parsed[current_file].append({
                    "type": line,
                    "line": 0,   # pytest-smell doesn't give exact line
                    "message": line
                })

        return parsed

    except Exception as e:
        print("pytest-smell error:", e)
        return {}


# =====================================================
# CUSTOM AST SMELLS (WITH LINE NUMBERS)
# =====================================================
def detect_remaining_paper_smells(test_file: Path):

    smells = []

    try:
        source = test_file.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):

            # Redundant Assertion
            if isinstance(node, ast.Assert):
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    smells.append({
                        "type": "Redundant Assertion",
                        "line": node.lineno,
                        "message": "assert True detected"
                    })

            # Suboptimal Assert
            if isinstance(node, ast.Assert):
                if isinstance(node.test, ast.Compare):
                    for comp in node.test.comparators:
                        if isinstance(comp, ast.Constant) and comp.value in [True, False]:
                            smells.append({
                                "type": "Suboptimal Assert",
                                "line": node.lineno,
                                "message": "Boolean comparison in assert"
                            })

            # Test Maverick
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) <= 1:
                    smells.append({
                        "type": "Test Maverick",
                        "line": node.lineno,
                        "message": "Isolated test class"
                    })

            # Lack of Cohesion
            if isinstance(node, ast.ClassDef):
                attr_usage = set()

                for method in node.body:
                    if isinstance(method, ast.FunctionDef):
                        for n in ast.walk(method):
                            if isinstance(n, ast.Attribute):
                                if isinstance(n.value, ast.Name) and n.value.id == "self":
                                    attr_usage.add(n.attr)

                if len(attr_usage) == 0 and len(node.body) > 2:
                    smells.append({
                        "type": "Lack of Cohesion of Test Cases",
                        "line": node.lineno,
                        "message": "Test methods do not share attributes"
                    })

    except Exception:
        pass

    return smells
