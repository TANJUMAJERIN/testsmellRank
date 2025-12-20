"""
Test file containing all 11 test smells detectable by pytest-smell:
1. Assertion Roulette - Multiple assertions without messages
2. Conditional Test Logic - If/else in test
3. Constructor Initialization - Setup in test method
4. Duplicate Assert - Same assertion repeated
5. Empty Test - Test with no body
6. Exception Handling - Improper exception testing
7. General Fixture - Overly complex fixture
8. Mystery Guest - External dependencies
9. Redundant Print - Print statements
10. Sleepy Test - Using time.sleep()
11. Unknown Test - Test without clear purpose
"""

import time
import os


# Smell 7: General Fixture - Overly complex fixture
class TestWithAllSmells:
    """Test class demonstrating all pytest-smell detectable smells"""
    
    # Smell 3: Constructor Initialization
    def setup_method(self):
        """Complex setup - Constructor Initialization smell"""
        self.value1 = 10
        self.value2 = 20
        self.value3 = 30
        self.data = [1, 2, 3, 4, 5]
        self.result = None
    
    # Smell 1: Assertion Roulette (multiple assertions without messages)
    def test_assertion_roulette(self):
        """Multiple assertions without descriptive messages"""
        x = 10
        y = 20
        z = x + y
        assert z == 30  # No message
        assert z > 20   # No message
        assert z < 50   # No message
        assert x < y    # No message
        assert y > 5    # No message
    
    # Smell 2: Conditional Test Logic (if/else in test)
    def test_conditional_logic(self):
        """Test with conditional logic"""
        value = 15
        if value > 10:
            result = "high"
        else:
            result = "low"
        assert result == "high"
    
    # Smell 4: Duplicate Assert (same assertion repeated)
    def test_duplicate_assertions(self):
        """Test with duplicate assertions"""
        x = 5
        y = 5
        assert x == 5
        assert y == 5
        assert x == 5  # Duplicate
        assert y == 5  # Duplicate
    
    # Smell 5: Empty Test (no body or only pass)
    def test_empty_test(self):
        """Empty test that does nothing"""
        pass
    
    # Smell 6: Exception Handling (improper exception testing)
    def test_exception_handling(self):
        """Test with improper exception handling"""
        try:
            x = 1 / 0
        except Exception:
            pass  # Catching generic exception
        
        try:
            result = int("not a number")
        except:
            result = 0
        
        assert result == 0
    
    # Smell 8: Mystery Guest (external dependencies)
    def test_mystery_guest(self):
        """Test with external dependencies"""
        # Reading environment variable
        env_value = os.getenv("SOME_VAR", "default")
        
        # File system dependency
        file_exists = os.path.exists("/some/random/path.txt")
        
        assert env_value is not None
        assert isinstance(file_exists, bool)
    
    # Smell 9: Redundant Print (print statements in test)
    def test_redundant_print(self):
        """Test with print statements"""
        x = 10
        y = 20
        print(f"Testing with x={x}")  # Redundant print
        result = x + y
        print(f"Result is: {result}")  # Redundant print
        assert result == 30
    
    # Smell 10: Sleepy Test (using time.sleep)
    def test_sleepy_test(self):
        """Test using time.sleep"""
        start = time.time()
        time.sleep(0.1)  # Sleep call makes test flaky
        end = time.time()
        duration = end - start
        assert duration >= 0.1
    
    # Smell 11: Unknown Test (unclear purpose)
    def test_unknown_purpose(self):
        """Test with unclear purpose"""
        a = 1
        b = 2
        c = 3
        d = a + b + c
        assert d > 0
    
    # BONUS: Combining multiple smells in one test
    def test_multiple_smells_combined(self):
        """Test combining several smells"""
        # Constructor initialization smell
        self.temp_value = 100
        
        # Redundant print
        print("Starting test")
        
        # Conditional logic
        if self.temp_value > 50:
            result = "large"
        else:
            result = "small"
        
        # Mystery guest
        current_dir = os.getcwd()
        print(f"Current directory: {current_dir}")
        
        # Sleepy test
        time.sleep(0.05)
        
        # Assertion roulette (multiple assertions)
        assert result == "large"
        assert self.temp_value == 100
        assert isinstance(current_dir, str)
        assert len(current_dir) > 0
        
        # Exception handling
        try:
            value = 10 / 2
        except:
            value = 0


# Standalone function tests demonstrating smells

# Smell 1 & 4: Assertion Roulette + Duplicate Assert
def test_combined_assertion_smells():
    """Multiple and duplicate assertions"""
    numbers = [1, 2, 3, 4, 5]
    assert len(numbers) == 5
    assert numbers[0] == 1
    assert numbers[-1] == 5
    assert len(numbers) == 5  # Duplicate
    assert sum(numbers) == 15
    assert numbers[0] == 1  # Duplicate


# Smell 2 & 9: Conditional Logic + Redundant Print
def test_conditional_with_print():
    """Conditional logic with print statements"""
    value = 42
    print(f"Testing value: {value}")
    
    if value > 40:
        category = "high"
        print("Value is high")
    else:
        category = "low"
        print("Value is low")
    
    assert category == "high"


# Smell 6 & 8: Exception Handling + Mystery Guest
def test_exception_with_external_deps():
    """Exception handling with external dependencies"""
    try:
        # Mystery guest - accessing file system
        files = os.listdir(".")
        print(f"Found {len(files)} files")
    except Exception as e:
        print(f"Error: {e}")
        files = []
    
    assert isinstance(files, list)


# Smell 10: Sleepy Test
def test_another_sleepy_test():
    """Another test using sleep"""
    initial = 0
    time.sleep(0.2)
    final = 100
    assert final > initial


# Smell 5: Empty Test
def test_another_empty_test():
    """Another empty test"""
    pass


# Smell 11: Unknown Test
def test_random_calculations():
    """Test doing random calculations without clear purpose"""
    x = 7
    y = 13
    z = x * y - x + y
    w = z / 2
    assert w > 0
