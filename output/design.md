# Problem 10 — Visual Design System

Campus Customs' styling is built to read as close to Yale's actual official brand as a Google-Fonts-only, no-license-budget student project can get — sourced from Yale's own identity guidelines, not guessed.

## Sources

- [Yale Brand Guidelines (2023 PDF)](https://licensing.yale.edu/sites/default/files/yale_brand_guidelines_2023.pdf)
- [yaleidentity.yale.edu/colors](https://yaleidentity.yale.edu/colors) — official color specifications
- [yaleidentity.yale.edu/guidelines/websites](https://yaleidentity.yale.edu/guidelines/websites) — official website typography/hierarchy guidance

## Colors — used as documented, with one deliberate exception

| Variable | Hex | Source |
|---|---|---|
| `--yale-blue` | `#00356b` | Official Yale Blue, PMS 289 — Yale's primary identifying color |
| `--yale-blue-bright` | `#286dc0` | Official "Higher Intensity Blue," PMS 660 — used as the site's one accent color (eyebrows, focus rings, hover underlines, card borders) |
| `--yale-gray` | `#978d85` | Official Yale Gray, PMS Warm Gray 7 — base for every muted/secondary tone (`--yale-gray-light`, `--yale-gray-border`), instead of a generic cool gray |
| `--yale-blue-dark` | `#00264d` | **Not an official swatch.** An algorithmically darkened Yale Blue, used only for hover/pressed states on blue buttons/nav — Yale's guidelines don't specify a hover shade, so this stays close to the real color rather than introducing an unrelated one. |
| `--urgency` | `#bd5319` | **Deliberately not from Yale's brand palette.** Scoped only to the two functional stock-urgency UI elements (grid badges, low-stock chat phrasing) — kept separate on purpose, the same way real storefronts keep a "sale/low stock" red-orange distinct from their brand colors specifically so scarcity signals still stand out against an otherwise all-blue site. Everything else on the site uses only the three sourced Yale colors above plus black/white. |

## Typography

Yale's own guidelines specify a proprietary serif typeface for headings and **Mallory** (a commercial sans-serif, licensed through YaleSites) for body text — both unavailable outside Yale's own licensing. Substituted with the closest free equivalent in spirit, not just appearance: **Source Serif 4** (headings, logo, price emphasis) + **Source Sans 3** (body, nav, buttons, forms) — Adobe's open-source superfamily, explicitly co-designed to pair together the same way Yale pairs its own serif/Mallory combination, loaded via Google Fonts.

Hierarchy follows Yale's own documented structure (serif for H1–H3, sans for body) rather than inventing a new one.

## Hierarchy, motion, and presentation

- **Hierarchy:** larger, tighter-tracked serif H1 (44px desktop / 32px mobile); consistent eyebrow treatment in the bright accent blue across Home and the product detail page; sticky navbar with an underline-on-hover/active indicator instead of a filled block, reading as more editorial and less like a generic template.
- **Motion:** page-content fade-in on route change; product cards lift + border-highlight + image zoom on hover; buttons lift with a soft blue shadow on hover; chat panel scales in on open; each chat message fades/slides in on arrival; a genuine animated typing-indicator (three bouncing dots) replaces the old plain "…" text; the chat toggle button gives two gentle pulses shortly after page load to invite a first-time visitor to notice it, then settles.
- **Product presentation:** product detail price now set in serif at a larger size (reads as a confident retail price, not a form field); product images get a soft elevated shadow; size options get a subtle blue hover border; stock badges (Problem 9) recolored to the dedicated urgency color so they still pop against the new all-blue palette.
- **Color-filtered stock (product detail page):** color chips are now clickable — selecting one re-filters the size grid to that color's estimated stock, active chip styled in Yale Blue. This is a computed split of the one real per-size total, not separately-tracked data (the database has no per-color inventory at all); see `output/harness.md`'s "Known open gaps" for the full explanation and the exact math used (`colorShareOfSize` in `ProductDetail.tsx`), and the small disclosure line shown under the heading whenever a color is selected.
- **Chat feel:** panel header gets a subtle Yale Blue → Yale Blue Dark gradient and switches to the serif face for "Campus Customs Assistant"; user/assistant bubbles get asymmetric corner radii (a real speech-bubble read) instead of uniform rounding; the chat toggle button is now a clean line-art speech-bubble icon (inline SVG) instead of a generic 💬 emoji, which reads as a deliberate, designed product rather than a placeholder.
- **Yale personality touches:** the "..." loading state now cycles short in-character status lines ("Asking the Bulldog…", "Consulting Handsome Dan…") alongside the typing dots. Typing Yale's "Boola Boola" fight cheer into chat triggers a one-time, brand-colored confetti burst (detected client-side, so it's guaranteed to fire regardless of what the model does) plus a one-line spirited reply from the agent before it returns straight to business (`prompts/prompt.md`'s "Yale school spirit" section) — same for asking about Handsome Dan or the mascot. Bounded on purpose: one line, then every other rule (scope, grounding, safety) applies immediately afterward, confirmed live against the existing off-topic refusal behavior.

## Verification

Checked live in the browser pane at desktop and mobile (375px) widths: both Google Fonts confirmed actually downloaded (not falling back) via network inspection; focus-state styling confirmed via computed-style inspection (border/shadow correctly switch to the bright accent blue); full flow re-tested (home → products → detail → chat exchange with a markdown-formatted reply → login form) with zero console errors. No functional behavior changed — this was a CSS/visual-only pass plus two small presentational JSX tweaks (chat toggle icon, typing-indicator markup).
