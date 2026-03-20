from pathlib import Path
import unittest


class RouterWrapperGuardrailsTest(unittest.TestCase):
    def test_legacy_routers_are_thin_wrappers(self):
        root = Path(__file__).resolve().parents[1]
        expected = {
            "app/routers/auth.py": "from app.modules.auth.presentation.router import router",
            "app/routers/appointments.py": "from app.modules.appointments.presentation.router import router",
            "app/routers/patients.py": "from app.modules.patients.presentation.router import router",
            "app/routers/me.py": "from app.modules.me.presentation.router import router",
            "app/routers/plans.py": "from app.modules.plans.presentation.router import router",
        }

        for relative_path, expected_line in expected.items():
            content = (root / relative_path).read_text().strip()
            self.assertEqual(content, expected_line, msg=relative_path)
