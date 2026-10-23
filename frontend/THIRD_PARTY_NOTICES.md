# Third-party UI code

This frontend includes adapted source code from
[Codehagen/Prismui](https://github.com/Codehagen/Prismui), commit
`40854d9e9bfed7822a730fc5e0932f257725cbd6`.

Copied and adapted files:

- `src/components/prismui/button.tsx`
- `src/components/prismui/input.tsx`
- `src/components/prismui/label.tsx`
- `src/components/prismui/card.tsx`
- `src/lib/utils.ts` (the `cn` helper)
- `tailwind.config.ts` and `src/prismui.css` (selected theme tokens)
- `src/OverviewPanel.tsx` and `src/App.css` (dashboard layout and grid styling
  adapted from PrismUI's `linear-hero` component)

Changes include Vite-compatible import paths, a reduced theme configuration,
integration with this project's FastAPI endpoints, and the CoroVision AI layout.
The original repository's license is the GNU Affero General Public License
version 3; a copy is retained at `LICENSE.prismui.md`.

PrismUI's Next.js server actions, Better Auth, Prisma schema, documentation
site, and payment features are not used by this project.

## Watermelon UI auth-07

The login layout in `src/components/ui/auth-07.tsx` adapts the [auth-07 registry block](https://registry.watermelon.sh/r/auth-07.json) from [Watermelon UI](https://ui.watermelon.sh/). The image at `public/auth-7.avif` comes from the same block. The block is distributed under the MIT License; a copy is retained at `LICENSE.watermelon.md`. The original static signup form was adapted to CoroVision AI branding and the existing authentication flows.

## Watermelon UI switch-mode and file-upload-5

The theme control in `src/components/watermelon/switch-mode.tsx` adapts the [switch-mode registry block](https://registry.watermelon.sh/r/switch-mode.json). The study uploader in `src/components/ui/file-upload-5.tsx` adapts the [file-upload-5 registry block](https://registry.watermelon.sh/r/file-upload-5.json). Both are from Watermelon UI under the MIT License retained at `LICENSE.watermelon.md`. The uploader was tailored for multiple medical images, with per-file size validation and previews.

## Watermelon UI macos-sidebar

The navigation in `src/components/watermelon/macos-sidebar.tsx` adapts the [macos-sidebar registry block](https://registry.watermelon.sh/r/macos-sidebar.json) from Watermelon UI under the MIT License retained at `LICENSE.watermelon.md`. Its selection animation and collapsible layout were integrated with CoroVision AI's role-based views and case controls.
