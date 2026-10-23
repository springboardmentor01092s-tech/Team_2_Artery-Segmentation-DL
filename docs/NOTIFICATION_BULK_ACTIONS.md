# Notification selection and bulk actions

The bell panel supports individual checkboxes and Select all shown (up to the
100 loaded notifications). The action bar offers Mark selected as read and
Delete selected, with an explicit delete confirmation. Selection is preserved
on failure and controls are disabled while an operation is running.

Deletion is recoverable: notification_dismissals stores a per-owner deletion
record while the original notification remains intact. Deleted lists dismissed
notifications and Restore selected returns them to Inbox. Cases, reports and
audit history are not deleted. The new table is added on backend startup through
the existing SQLAlchemy metadata initialization; existing rows need no rewrite.

POST /api/notifications/bulk accepts ids (1-100) and action read/delete/restore.
Every ID must belong to the signed-in user or the whole request fails with 404.
Operations are committed together, idempotent and audited. GET /api/notifications
lists the active inbox; ?deleted=true lists recoverable deleted notifications.

Verification: backend/tests/test_notification_bulk.py covers owner scoping,
mixed-owner atomic rejection, read persistence, idempotent deletion, restoration,
preserved originals, empty-input rejection and unauthenticated requests.
