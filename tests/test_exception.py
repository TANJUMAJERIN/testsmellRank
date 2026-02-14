def test_exception_handling():
    try:                       # Exception Handling smell
        int("abc")
    except:
        assert True

# Bug: Fixed exception handling
