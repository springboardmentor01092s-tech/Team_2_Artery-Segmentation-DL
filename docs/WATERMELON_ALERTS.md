# Alert notifications

Adapted from https://registry.watermelon.sh/r/alert-1.json. The registry's static
icon-and-title alert is extended with content, informational/success/warning/error
icons, optional dismissal and existing semantic theme tokens. No demo messages
or duplicate notification service are added.

The notification bell renders historical items as silent alert cards, preserving
unread state, timestamps and existing Open case / Mark as read handlers. Loading
and failed updates remain explicit. Runtime application success/error messages
and saved preprocessing warnings use the shared component. Errors announce with
role=alert; routine status uses role=status; saved notifications/warnings are not
competing live regions. No automatic timeout hides important errors.

Colours follow the selected design. Severity is communicated by text and icons,
not colour alone. Backend notification scope and permissions remain unchanged.
