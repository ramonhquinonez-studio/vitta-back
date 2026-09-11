import unittest

from pydantic import ValidationError

from app.schemas.body_measurements import CIRCUMFERENCE_SITES, BodyMeasurementsIn
from app.schemas.patients import PatientUpdate


class BodyMeasurementsSchemaTest(unittest.TestCase):
    def test_paired_limbs_accept_left_right_keys(self):
        for site in ("arm", "thigh", "calf"):
            self.assertIn(f"{site}_left", CIRCUMFERENCE_SITES)
            self.assertIn(f"{site}_right", CIRCUMFERENCE_SITES)
            self.assertIn(site, CIRCUMFERENCE_SITES)  # bare key still valid

        cleaned = BodyMeasurementsIn(
            circumferences={"arm_left": 30, "arm_right": 31.04, "waist": 80}
        ).circumferences
        self.assertEqual(cleaned, {"arm_left": 30.0, "arm_right": 31.0, "waist": 80.0})

    def test_unpaired_sites_reject_a_side_suffix(self):
        with self.assertRaises(ValidationError):
            BodyMeasurementsIn(circumferences={"waist_left": 80})

    def test_circumference_goals_accept_per_side_targets(self):
        goals = PatientUpdate(
            circumference_goals={"thigh_left": 55, "thigh_right": 55}
        ).circumference_goals
        self.assertEqual(goals, {"thigh_left": 55.0, "thigh_right": 55.0})


if __name__ == "__main__":
    unittest.main()
