import unittest

from app.modules.payments.application import connect_webhook_handlers as wh
from app.modules.payments.application.connect_service import ConnectService
from app.modules.payments.application.consultation_charges_service import (
    ConsultationChargesService,
)
from app.modules.payments.application.stripe_customers import StripeCustomers
from app.modules.payments.domain.payment_entities import ConnectAccount, Payment
from tests._fakes.fake_stripe import FakeStripe


class _FakePaymentsRepo:
    def __init__(self):
        self.payments: dict[str, Payment] = {}
        self.accounts: dict[str, ConnectAccount] = {}
        self._seq = 0

    # payments
    async def create_payment(self, p: Payment):
        self._seq += 1
        pid = f"pay_{self._seq}"
        stored = Payment(**{**p.__dict__, "id": pid})
        self.payments[pid] = stored
        return stored

    async def get_payment(self, pid):
        return self.payments.get(pid)

    async def get_payment_by_intent(self, pi_id):
        return next((p for p in self.payments.values() if p.payment_intent_id == pi_id), None)

    async def update_payment(self, pid, updates):
        p = self.payments[pid]
        self.payments[pid] = Payment(**{**p.__dict__, **updates})
        return self.payments[pid]

    async def list_for_patient(self, patient_id):
        return [p for p in self.payments.values() if p.patient_id == patient_id]

    async def list_for_nutritionist(self, nid):
        return [p for p in self.payments.values() if p.nutritionist_id == nid]

    # connect
    async def get_connect_account(self, owner_id):
        return self.accounts.get(owner_id)

    async def get_connect_account_by_id(self, account_id):
        return next((a for a in self.accounts.values() if a.account_id == account_id), None)

    async def upsert_connect_account(self, account: ConnectAccount):
        self.accounts[account.owner_id] = account
        return account


class _FakeCustomersRepo:
    def __init__(self):
        self._m = {}

    async def get_customer_id(self, user_id):
        return self._m.get(user_id)

    async def set_customer_id(self, user_id, customer_id):
        self._m[user_id] = customer_id


def _charges(stripe, repo, *, price=500.0, patient_owner="nutri-1",
             consultation_patient="patient-rec-1"):
    customers = StripeCustomers(stripe, _FakeCustomersRepo())

    async def get_patient_for_user(uid):
        return {"id": "patient-rec-1", "owner_id": patient_owner} if uid == "patient-user" else None

    async def get_consultation(owner_id, cid):
        if owner_id == patient_owner and cid == "c-1":
            return {"patient_id": consultation_patient, "appointment_id": "a-1"}
        return None

    async def get_session_price(owner_id):
        return price, "MXN"

    return ConsultationChargesService(
        stripe, customers, repo,
        get_patient_for_user=get_patient_for_user,
        get_consultation=get_consultation,
        get_session_price=get_session_price,
    )


class ConnectServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_account_link_creates_account_once(self):
        stripe = FakeStripe()
        repo = _FakePaymentsRepo()
        svc = ConnectService(stripe, repo, country="MX")

        url1 = await svc.account_link("nutri-1", email="n@x.com",
                                     refresh_url="r", return_url="ret")
        url2 = await svc.account_link("nutri-1", email="n@x.com",
                                     refresh_url="r", return_url="ret")
        self.assertTrue(url1.startswith("https://connect.stripe.test/"))
        self.assertEqual(len(stripe._accounts), 1)
        self.assertEqual(url1, url2)

    async def test_status_reflects_charges_enabled(self):
        stripe = FakeStripe()
        repo = _FakePaymentsRepo()
        svc = ConnectService(stripe, repo, country="MX")
        await svc.account_link("nutri-1", email=None, refresh_url="r", return_url="ret")

        status = await svc.status("nutri-1")
        self.assertTrue(status["connected"])
        self.assertTrue(status["charges_enabled"])

    async def test_status_when_never_connected(self):
        svc = ConnectService(FakeStripe(), _FakePaymentsRepo(), country="MX")
        self.assertEqual(await svc.status("nutri-x"), {
            "connected": False, "charges_enabled": False, "payouts_enabled": False
        })


class ConsultationChargeTest(unittest.IsolatedAsyncioTestCase):
    async def _enabled_account(self, repo, owner="nutri-1"):
        repo.accounts[owner] = ConnectAccount(owner_id=owner, account_id="acct_x",
                                              charges_enabled=True)

    async def test_sheet_creates_pi_with_fee_and_transfer(self):
        stripe = FakeStripe()
        repo = _FakePaymentsRepo()
        await self._enabled_account(repo)
        svc = _charges(stripe, repo, price=500.0)

        out = await svc.create_sheet("patient-user", "c-1", email="p@x.com")

        self.assertEqual(out["amount_cents"], 50000)
        pi = next(iter(stripe._payment_intents.values()))
        self.assertEqual(pi["application_fee_amount"], 5000)  # 10% of 50000
        self.assertEqual(pi["transfer_data"]["destination"], "acct_x")
        self.assertEqual(len(repo.payments), 1)
        row = next(iter(repo.payments.values()))
        self.assertEqual(row.nutritionist_id, "nutri-1")
        self.assertEqual(row.fee_cents, 5000)

    async def test_sheet_rejects_when_nutritionist_not_enabled(self):
        repo = _FakePaymentsRepo()  # no account
        svc = _charges(FakeStripe(), repo)
        with self.assertRaises(Exception) as ctx:
            await svc.create_sheet("patient-user", "c-1", email=None)
        self.assertEqual(getattr(ctx.exception, "status_code", None), 400)

    async def test_sheet_rejects_consultation_not_belonging_to_patient(self):
        repo = _FakePaymentsRepo()
        await self._enabled_account(repo)
        svc = _charges(FakeStripe(), repo, consultation_patient="someone-else")
        with self.assertRaises(Exception) as ctx:
            await svc.create_sheet("patient-user", "c-1", email=None)
        self.assertEqual(getattr(ctx.exception, "status_code", None), 404)

    async def test_verify_marks_paid_after_confirmation(self):
        stripe = FakeStripe()
        repo = _FakePaymentsRepo()
        await self._enabled_account(repo)
        svc = _charges(stripe, repo)
        out = await svc.create_sheet("patient-user", "c-1", email=None)
        pid = out["payment_id"]
        # client confirmed
        list(stripe._payment_intents.values())[0]["status"] = "succeeded"

        result = await svc.verify("patient-user", pid)
        self.assertEqual(result["status"], "paid")
        self.assertEqual(repo.payments[pid].status, "paid")

    async def test_refund_only_paid_and_by_owner(self):
        stripe = FakeStripe()
        repo = _FakePaymentsRepo()
        await self._enabled_account(repo)
        svc = _charges(stripe, repo)
        out = await svc.create_sheet("patient-user", "c-1", email=None)
        pid = out["payment_id"]
        await repo.update_payment(pid, {"status": "paid"})

        # wrong nutritionist
        with self.assertRaises(Exception) as ctx:
            await svc.refund("nutri-other", pid)
        self.assertEqual(getattr(ctx.exception, "status_code", None), 404)

        refunded = await svc.refund("nutri-1", pid)
        self.assertEqual(refunded["status"], "refunded")
        self.assertEqual(len(stripe._refunds), 1)
        # Destination charge → the refund must unwind the transfer + app fee,
        # not just pay the patient from the platform balance.
        self.assertTrue(stripe._refunds[0]["reverse_transfer"])
        self.assertTrue(stripe._refunds[0]["refund_application_fee"])

    async def test_double_charge_blocked_when_already_paid(self):
        stripe = FakeStripe()
        repo = _FakePaymentsRepo()
        await self._enabled_account(repo)
        svc = _charges(stripe, repo)
        out = await svc.create_sheet("patient-user", "c-1", email=None)
        await repo.update_payment(out["payment_id"], {"status": "paid"})

        with self.assertRaises(Exception) as ctx:
            await svc.create_sheet("patient-user", "c-1", email=None)
        self.assertEqual(getattr(ctx.exception, "status_code", None), 409)


class ConnectWebhookApplyTest(unittest.IsolatedAsyncioTestCase):
    async def _repo_with_pending(self):
        repo = _FakePaymentsRepo()
        p = await repo.create_payment(Payment(
            id="", kind="consultation", consultation_id="c-1", appointment_id=None,
            patient_id="pat-1", nutritionist_id="nut-1", amount_cents=50000, fee_cents=5000,
            currency="mxn", status="pending", payment_intent_id="pi_1",
        ))
        return repo, p.id

    async def test_pi_succeeded_marks_paid(self):
        repo, pid = await self._repo_with_pending()
        await wh.apply_payment_intent_succeeded(repo, {"id": "pi_1"})
        self.assertEqual(repo.payments[pid].status, "paid")

    async def test_pi_failed_marks_failed(self):
        repo, pid = await self._repo_with_pending()
        await wh.apply_payment_intent_failed(repo, {"id": "pi_1"})
        self.assertEqual(repo.payments[pid].status, "failed")

    async def test_charge_refunded_full(self):
        repo, pid = await self._repo_with_pending()
        await repo.update_payment(pid, {"status": "paid"})
        await wh.apply_charge_refunded(repo, {
            "payment_intent": "pi_1", "amount": 50000, "amount_refunded": 50000
        })
        self.assertEqual(repo.payments[pid].status, "refunded")
        self.assertEqual(repo.payments[pid].refunded_cents, 50000)

    async def test_charge_refunded_is_idempotent(self):
        repo, pid = await self._repo_with_pending()
        await repo.update_payment(pid, {"status": "paid"})
        for _ in range(3):
            await wh.apply_charge_refunded(repo, {
                "payment_intent": "pi_1", "amount": 50000, "amount_refunded": 50000
            })
        self.assertEqual(repo.payments[pid].refunded_cents, 50000)

    async def test_account_updated_caches_flags(self):
        repo = _FakePaymentsRepo()
        repo.accounts["nut-1"] = ConnectAccount(owner_id="nut-1", account_id="acct_1")
        await wh.apply_account_updated(repo, {
            "id": "acct_1", "charges_enabled": True, "payouts_enabled": True,
            "requirements": {"currently_due": []},
        })
        self.assertTrue(repo.accounts["nut-1"].charges_enabled)


if __name__ == "__main__":
    unittest.main()
