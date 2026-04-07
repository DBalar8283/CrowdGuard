import unittest

from app.services.logic import FallSignal, classify_fruin_los, density_per_m2, is_fall, should_override_micro_logic


class LogicTests(unittest.TestCase):
    def test_density(self) -> None:
        self.assertAlmostEqual(density_per_m2(20, 100), 0.2)

    def test_fruin_levels(self) -> None:
        self.assertEqual(classify_fruin_los(0.1), "A")
        self.assertEqual(classify_fruin_los(0.7), "C")
        self.assertEqual(classify_fruin_los(1.7), "F")

    def test_fall_rule(self) -> None:
        self.assertTrue(is_fall(FallSignal("P1", 20, 1.2, 5.1)))
        self.assertFalse(is_fall(FallSignal("P1", 35, 1.2, 5.1)))

    def test_override(self) -> None:
        self.assertTrue(should_override_micro_logic("E"))
        self.assertFalse(should_override_micro_logic("D"))


if __name__ == "__main__":
    unittest.main()
