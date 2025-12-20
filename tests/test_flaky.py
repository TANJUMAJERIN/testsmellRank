global_counter = 0

def test_flaky_1():
    global global_counter
    global_counter += 1

def test_flaky_2():
    assert global_counter == 0  # Fails unless tests run in isolation
