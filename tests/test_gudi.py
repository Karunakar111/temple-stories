"""Run the mock demonstrations as a test: python3 -m unittest tests.test_gudi"""
import unittest


class MockScenarios(unittest.TestCase):
    def test_all_scenarios(self):
        from gudi.demo import main

        self.assertEqual(main(), 0)


class WeeklyBatch(unittest.TestCase):
    def test_week(self):
        from gudi.batch_demo import main as week

        self.assertEqual(week(), 0)


if __name__ == "__main__":
    unittest.main()
