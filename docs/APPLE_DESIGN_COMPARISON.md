# CoroVision design comparison — 15 October 2026

Status: two live URL-scoped previews. Awaiting the user's choice. No automatic
design promotion and no training restart.

- Existing: http://127.0.0.1:5173/?design=existing
- Apple-inspired: http://127.0.0.1:5173/?design=apple
- Default URL keeps the existing design.

Both use the same application, authentication, permissions, case data, upload
engine, notification panel and model reports. The design parameter is not an
access-control mechanism. No tokens or credentials are embedded in preview URLs.
Chrome was signed in through the normal login form as the existing sample
researcher account. This is not institutional SSO.

## Downloaded guides

Installed with the skill installer into project-local `.agents/skills/` using
distinct directory names. No external helper scripts from these repositories
were executed. Downloads retained certificate verification using the existing
trusted certificate bundle. Guides are retained for subsequent project work.

- `apple-design-emil`: https://github.com/emilkowalski/skills/tree/main/skills/apple-design
- `apple-design-dickwu`: https://github.com/dickwu/apple-design-skill

The original downloaded guidance is preserved. Application CSS is an original
web interpretation, not a native Apple component implementation or certified
HIG conformance. No Apple font binaries or SF Symbols were redistributed.

## Design thesis and review

Audience: researchers reviewing de-identified vascular imaging. Job: move from
case intake to inspectable evidence without allowing visual styling to imply
clinical validation. Signature: a calm, grouped imaging workstation, with blue
reserved for actions/selection and actual study data kept on solid surfaces.
No decorative image, fake chart, sample clinical finding or extra animation was
added. Existing research caveats and permission labels remain visible.

Regular layout: toolbar and comparison switch, leading collapsible sidebar,
study/workflow content and grouped metrics. Compact layout: wrapping toolbar,
existing collapsible navigation, stacked content. Functions remain the same.

Tokens are named by purpose in `apple-design.css`, with separate dark values.
Computed solid-surface contrast: light text #1d1d1f on white 16.83:1,
secondary #575760 on white 7.15:1, accent #005ec4 on white 6.18:1;
dark text #f5f5f7 on #222225 14.57:1, secondary #b9b9c3 8.15:1,
accent #8fc2ff 8.56:1. These figures do not certify every inherited app color.
System font stack; body near 16px; utility text uses rem; headings use tighter
tracking. Solid content cards, blur restricted to structural navigation/chrome.
Reduced motion, reduced transparency and increased contrast have CSS overrides.
Existing spring sidebar behavior is retained; no decorative looping motion.

References actually read include accessibility, layout, typography, color,
designing-for-macos, sidebars, materials, buttons and cross-platform translation.
Applied principles: `layout.md › Visual hierarchy` grouping/alignment;
`materials.md › Liquid Glass` reserve glass for navigation;
`buttons.md › Best practices` press feedback; Emil's typography, response and
reduced-motion guidance. This is React/web: no fake traffic-light window controls
or native-menu-bar claims. The existing user-facing appearance switch is retained
for comparison rather than removed to mimic native conventions.

## Verification and limits

TypeScript and Vite production build passed. Both desktop pages were opened and
visually inspected while signed in as a researcher; the existing design remains
visually distinct and its core styles are not overwritten. The new CSS is scoped
to `html[data-design=apple]`; only the comparison selector is shared.

Desktop screenshots support visual layout checks, not proof of every control's
behavior or clinical correctness. Mobile, 200% zoom, dark-mode screenshots and a
full assistive-technology audit remain unverified; media-query and focus support
are implemented but are not represented as fully tested. Existing Vite large
bundle advisory remains. No additional dependencies or GPU workloads were added.
