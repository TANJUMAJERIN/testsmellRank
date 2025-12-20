def test_verbose():
    # 40 dummy lines to simulate Verbose Test
    x = 1
    for i in range(50):  # Long + verbose
        x += i
    assert x > 0
