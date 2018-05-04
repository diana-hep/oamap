import unittest


class TestIssues(unittest.TestCase):

    def runTest(self):
        pass

    def test_issue7(self):
        with open('README.rst') as f:
            try:
                content = f.read()
            except UnicodeDecodeError, e:
                self.fail("Cannot read README.rst: " + str(e))
