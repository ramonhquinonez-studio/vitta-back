# Implementation Plan: Fix Push Notification SDK Call

**Feature Branch**: `068-back-fix-push-notification-sdk`

## Summary

A one-line fix plus a small regression-guard test file.

## Steps

1. **`app/core/notify.py`**: `send_push_to_tokens`'s final line changes from `messaging.send_multicast(message)` to `messaging.send_each_for_multicast(message)`.
2. **`tests/test_notify.py`** (new): three tests — early return with no tokens, early return with `_app` unset, and a mocked assertion that `send_each_for_multicast` (not `send_multicast`) is the method actually called, with the right `MulticastMessage.tokens`.

## Constraints

- No call-site changes needed — `send_each_for_multicast` returns the same `BatchResponse` shape `send_multicast` did, and no caller inspects it beyond truthiness/length of the input token list.
