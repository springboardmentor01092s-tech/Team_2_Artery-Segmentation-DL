# Watermelon dashboard adaptation

Source: https://registry.watermelon.sh/r/library-dashboard.json

The requested shadcn command was previewed with `--dry-run`. Direct installation
would add a second shell/theme, demo data, 11 dependencies and overwrite a shared
utility. Instead, the template's header, metric cards, quick actions, circulation /
collection composition is adapted in `corovision-library-dashboard.tsx` using the
existing app components, theme tokens and Lucide icons. No template mock statistics,
organizations, notifications or library branding are exposed in the application.

The new study-intake chart counts accessible cases by creation date over seven
local calendar days. It does not imply access to all institution-wide records.
The case overview partitions visible cases into reviewed, awaiting review and
other/preparation. Search, filter, open-case and quick actions call existing app
handlers. Existing detailed analytics remain in an expandable section.

ViewerWorkspace remains separate and read-only. Backend authorization and case
scope are unchanged. No model training or clinical deployment is introduced.
