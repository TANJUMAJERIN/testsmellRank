def test_case1():
    x = 10
    assert x > 5

def test_case2():  # Lazy Test (duplicate logic)
    x = 10
    assert x > 5

# Defect: Fixed lazy evaluation
#bug: Fixed lazy test case