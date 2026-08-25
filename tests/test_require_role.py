import unittest

from fastapi import HTTPException

from app.core.deps import require_role


class RequireRoleTest(unittest.IsolatedAsyncioTestCase):
    async def test_allows_a_matching_role(self):
        check = require_role("nutritionist")

        result = await check({"id": "u1", "role": "nutritionist"})

        self.assertEqual(result["role"], "nutritionist")

    async def test_rejects_a_non_matching_role(self):
        check = require_role("nutritionist")

        with self.assertRaises(HTTPException) as ctx:
            await check({"id": "u1", "role": "patient"})

        self.assertEqual(ctx.exception.status_code, 403)

    async def test_accepts_any_of_multiple_allowed_roles(self):
        check = require_role("nutritionist", "admin")

        result = await check({"id": "u1", "role": "admin"})

        self.assertEqual(result["role"], "admin")


if __name__ == "__main__":
    unittest.main()
