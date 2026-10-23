# Theme and settings form consistency

- Shared semantic tokens now connect application text, muted text, accents,
  surfaces, borders, focus states and control colours to the selected design.
- Existing and Journal use neutral actions. Apple-inspired and Atlas use their
  blue accents. Paper uses warm accents; Editorial Focus uses restrained slate.
- Shared system typography is used for controls and body text. Editorial-family
  page/section headings use Georgia. Theme selection still lives in Settings.
- Viewer dashboard icons and links inherit the same accent as action buttons.
- Clinical overlays and meaningful error/warning/status colours are not recoloured
  as decoration.
- Access-request and operational-grant forms have a single-column layout, full-width
  fields, visible borders, a resizable textarea and a left-aligned submit button.
  The action becomes full-width on narrow screens. Session actions wrap with gaps.
- The access heading icon now stays beside the heading instead of on its own line.

TypeScript/Vite build passed. Thirty static text/secondary-text/filled-button
contrast pairs from the five alternate light/dark palettes passed 4.5:1. The
Existing-theme access form was visually checked in Chrome. This is not a complete
accessibility audit or visual verification of every theme, role and screen size.
Authentication, permissions, records and training behaviour were not changed.
