import unittest
from unittest.mock import MagicMock, patch

from app.core import notify


class SendPushToTokensTest(unittest.TestCase):
    def test_returns_none_without_a_registered_token(self):
        with patch.object(notify, "_app", MagicMock()):
            self.assertIsNone(notify.send_push_to_tokens([], "Title", "Body"))

    def test_returns_none_when_firebase_was_never_initialized(self):
        with patch.object(notify, "_app", None):
            self.assertIsNone(notify.send_push_to_tokens(["token-1"], "Title", "Body"))

    def test_calls_send_each_for_multicast_not_the_removed_send_multicast(self):
        # Regression guard: firebase-admin 7.x removed `send_multicast`
        # (`AttributeError` at call time) — `send_each_for_multicast` is the
        # real replacement. This locks in the correct method name so a
        # future accidental revert fails a test instead of only failing in
        # production the next time a push is actually sent.
        with patch.object(notify, "_app", MagicMock()):
            with patch.object(notify.messaging, "send_each_for_multicast") as mock_send:
                mock_send.return_value = "batch-response"

                result = notify.send_push_to_tokens(["token-1", "token-2"], "Title", "Body")

                mock_send.assert_called_once()
                sent_message = mock_send.call_args.args[0]
                self.assertEqual(sent_message.tokens, ["token-1", "token-2"])
                self.assertEqual(result, "batch-response")
