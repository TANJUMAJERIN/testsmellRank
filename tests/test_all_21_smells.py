"""
Test file demonstrating all 21 unique test smells detected by the 5 methods
1. Magic Number Test
2. Code Warning
3. Assertion Roulette
4. Style Violation
5. Assertion-Less Test
6. Conditional Test Logic
7. Redundant Print
8. Exception Handling
9. Complex Test
10. Sleepy Test
11. Unknown Test
12. Duplicate Assert
13. Constructor Initialization
14. Empty Test
15. Low Maintainability
16. Test Logic in Loop
17. Verbose Test File
18. Default Test (NEW)
19. Redundant Assertion (NEW)
20. Resource Optimism (NEW)
21. Sensitive Equality (NEW)
"""

import time
import os
import sys


class TestAll17Smells:
    """Test class demonstrating all 21 test smells"""
    
    # Smell 13: Constructor Initialization
    def setup_method(self):
        """Complex setup with many initializations"""
        self.value1 = 100
        self.value2 = 200
        self.value3 = 300
        self.value4 = 400
        self.data = [1, 2, 3, 4, 5]
        self.config = {"key": "value"}
    
    # Smell 14: Empty Test
    def test_empty_test(self):
        """Empty test with only pass"""
        pass
    
    # Smell 5: Assertion-Less Test + Smell 11: Unknown Test
    def test_no_assertions(self):
        """Test without any assertions"""
        x = 5 + 5
        y = x * 2
    
    # Smell 3: Assertion Roulette (many assertions without messages)
    def test_assertion_roulette(self):
        """Test with too many assertions"""
        result1 = 42
        result2 = 84
        result3 = 126
        result4 = 168
        assert result1 == 42
        assert result2 == 84
        assert result3 == 126
        assert result4 == 168
        assert result1 < result2
    
    # Smell 1: Magic Number Test
    def test_magic_numbers(self):
        """Test using hardcoded magic numbers"""
        value = 10
        assert value == 10
        assert value * 5 == 50
        assert value + 23 == 33
        assert value - 7 == 3
    
    # Smell 6: Conditional Test Logic
    def test_conditional_logic(self):
        """Test with conditional logic"""
        x = 15
        if x > 10:
            assert x == 15
        else:
            assert x < 10
    
    # Smell 16: Test Logic in Loop
    def test_loop_logic(self):
        """Test with loop"""
        values = [1, 2, 3, 4, 5]
        for val in values:
            assert val > 0
    
    # Smell 8: Exception Handling
    def test_exception_handling(self):
        """Test with improper exception handling"""
        try:
            result = 10 / 2
            assert result == 5
        except Exception:
            pass
    
    # Smell 10: Sleepy Test
    def test_sleepy_test(self):
        """Test using time.sleep"""
        time.sleep(0.5)
        assert True
    
    # Smell 7: Redundant Print
    def test_with_print_statements(self):
        """Test with debug print statements"""
        value = 100
        print("Debug: Testing value", value)
        print("Another debug message")
        assert value == 100
    
    # Smell 12: Duplicate Assert
    def test_duplicate_assertions(self):
        """Test with duplicate assertions"""
        x = 50
        assert x == 50
        assert x == 50
        assert x == 50
    
    # Smell 9: Complex Test (high complexity)
    def test_complex_logic(self):
        """Test with complex logic and high cyclomatic complexity"""
        a = 10
        b = 20
        c = 30
        
        if a > 5:
            if b > 15:
                if c > 25:
                    result = a + b + c
                    assert result == 60
                else:
                    result = a + b
                    assert result == 30
            else:
                if c > 25:
                    result = a + c
                    assert result == 40
                else:
                    result = a
                    assert result == 10
        else:
            if b > 15:
                result = b + c
                assert result == 50
            else:
                result = c
                assert result == 30
    
    # Smell 4: Style Violation (undefined variable, wrong indentation, etc.)
    def test_style_violations(self):
        """Test with style violations"""
        x=10+20  # Missing spaces around operators
        y =  30  # Extra spaces
        assert x == 30
    
    # Smell 18: Default Test (DT) - Non-descriptive test name
    def test_1(self):
        """Test with default/non-descriptive name"""
        result = 5 + 5
        assert result == 10
    
    # Smell 19: Redundant Assertion (RA) - Meaningless assertions
    def test_redundant_assertions(self):
        """Test with redundant assertions"""
        x = 42
        assert True  # Always passes - redundant
        assert x == x  # Always true - redundant
        assert 1 == 1  # Constant assertion - redundant
    
    # Smell 20: Resource Optimism (RO) - File operations without error handling
    def test_resource_optimism(self):
        """Test assumes file exists without checking"""
        file = open('test_data.txt', 'r')  # No try/except or existence check
        content = file.read()
        file.close()
        assert len(content) > 0
    
    # Smell 21: Sensitive Equality (SE) - Float comparison with ==
    def test_sensitive_equality(self):
        """Test with fragile float equality checks"""
        result = 0.1 + 0.2
        assert result == 0.3  # Fails due to floating point precision
        
        x = 10 / 3
        assert x == 3.3333333333  # Fragile float comparison


# Additional tests to increase file length for "Verbose Test File" smell (Smell 17)
# and "Low Maintainability" (Smell 15)

def test_verbose_1():
    """Verbose test 1"""
    a=1;b=2;c=3;d=4;e=5;f=6;g=7;h=8;i=9;j=10
    assert a+b+c+d+e+f+g+h+i+j==55

def test_verbose_2():
    """Verbose test 2"""
    x=100;y=200;z=300
    assert x+y+z==600

def test_verbose_3():
    """Verbose test 3"""
    val1=10;val2=20;val3=30;val4=40;val5=50
    assert val1+val2+val3+val4+val5==150

def test_verbose_4():
    """Verbose test 4"""
    data=[1,2,3,4,5,6,7,8,9,10]
    assert sum(data)==55

def test_verbose_5():
    """Verbose test 5"""
    n=5;result=n*n*n
    assert result==125

def test_verbose_6():
    """Verbose test 6"""
    s="test";assert len(s)==4

def test_verbose_7():
    """Verbose test 7"""
    items=[1,2,3];assert len(items)==3

def test_verbose_8():
    """Verbose test 8"""
    val=42;assert val==42

def test_verbose_9():
    """Verbose test 9"""
    x=7;y=8;assert x*y==56

def test_verbose_10():
    """Verbose test 10"""
    a=15;b=25;c=a+b;assert c==40

def test_verbose_11():
    """Verbose test 11"""
    nums=[10,20,30];assert max(nums)==30

def test_verbose_12():
    """Verbose test 12"""
    val=99;assert val<100

def test_verbose_13():
    """Verbose test 13"""
    x=3;y=4;z=5;assert x**2+y**2==z**2

def test_verbose_14():
    """Verbose test 14"""
    data={"a":1,"b":2};assert data["a"]==1

def test_verbose_15():
    """Verbose test 15"""
    lst=[5,10,15,20];assert lst[2]==15

def test_verbose_16():
    """Verbose test 16"""
    val=77;assert val>50

def test_verbose_17():
    """Verbose test 17"""
    x=12;y=13;assert x+y==25

def test_verbose_18():
    """Verbose test 18"""
    result=9*9;assert result==81

def test_verbose_19():
    """Verbose test 19"""
    a=5;b=10;c=15;d=20;e=25;assert a+b+c+d+e==75

def test_verbose_20():
    """Verbose test 20"""
    val=123;assert val==123
