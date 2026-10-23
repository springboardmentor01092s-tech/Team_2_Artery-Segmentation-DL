# Inline disclosure menus

Source: https://registry.watermelon.sh/r/inline-disclosure-menu.json

The requested registry import was previewed before adapting the existing menu.
Workspace options and case workflow actions use the same themed action-menu
component. It supports keyboard arrows, Home/End, Escape, focus return, outside
click dismissal, reduced motion and disabled unavailable actions. No demo
duplicate/share/delete operations are introduced. Destructive controls are opt-in.

Case filters, case creation selections and image selection retain listbox /
combobox semantics, with matching disclosure surfaces, headings and checkmarks.
These options stay in the document flow to avoid sidebar clipping and native
OS pop-ups that may be absent from window screen sharing. Escape closes an open
selection before its parent case disclosure. Existing selection handlers and
backend permissions are unchanged. Unrelated native selects are not globally
replaced with action-menu semantics.
