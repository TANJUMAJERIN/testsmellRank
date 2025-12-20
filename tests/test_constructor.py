class TestSomething:
    def __init__(self):  # Constructor Initialization smell
        self.x = 10

    def test_value(self):
        assert self.x == 10
