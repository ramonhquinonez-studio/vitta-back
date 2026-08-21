import unittest

from app.modules.appointments.presentation.router import router as appointments_router
from app.modules.auth.presentation.router import router as auth_router
from app.modules.consultations.presentation.router import router as consultations_router
from app.modules.content_library.presentation.router import router as content_library_router
from app.modules.equivalencies.presentation.router import router as equivalencies_router
from app.modules.me.presentation.router import router as me_router
from app.modules.nutritionist_profile.presentation.router import (
    router as nutritionist_profile_router,
)
from app.modules.patients.presentation.router import router as patients_router
from app.modules.plans.presentation.router import router as plans_router
from app.modules.recipes.presentation.router import router as recipes_router
from app.modules.recommendations.presentation.router import router as recommendations_router


class ModuleRouterSmokeTest(unittest.TestCase):
    def test_modular_routers_expose_routes(self):
        routers = {
            "auth": auth_router,
            "appointments": appointments_router,
            "patients": patients_router,
            "me": me_router,
            "plans": plans_router,
            "nutritionist_profile": nutritionist_profile_router,
            "recipes": recipes_router,
            "recommendations": recommendations_router,
            "equivalencies": equivalencies_router,
            "consultations": consultations_router,
            "content_library": content_library_router,
        }

        for name, router in routers.items():
            with self.subTest(router=name):
                self.assertGreater(len(router.routes), 0)

    def test_expected_core_paths_exist(self):
        paths = {
            route.path
            for router in [
                auth_router,
                appointments_router,
                patients_router,
                me_router,
                plans_router,
                nutritionist_profile_router,
                recipes_router,
                recommendations_router,
                equivalencies_router,
                consultations_router,
                content_library_router,
            ]
            for route in router.routes
        }

        self.assertIn("/auth/login", paths)
        self.assertIn("/appointments", paths)
        self.assertIn("/patients", paths)
        self.assertIn("/me/profile", paths)
        self.assertIn("/plans", paths)
        self.assertIn("/nutritionist_profile/me", paths)
        self.assertIn("/recipe_collections", paths)
        self.assertIn("/recommendations", paths)
        self.assertIn("/equivalencies/groups", paths)
        self.assertIn("/consultations/start", paths)
        self.assertIn("/content/articles", paths)
