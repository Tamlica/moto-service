# Moto Service — design system

Locked system for every page. Pages share it; they don't diverge.

## Theme: custom "Night dash + stamps"
- **Genre:** atmospheric. **Vibe:** a motorcycle instrument cluster at night, plus the rubber stamps in a dealer service booklet.
- **Axes:** dark / tech-geometric sans / warm (amber).
- **Tokens:** `frontend/src/tokens.css` is the only source of colors, fonts, spacing, radii and motion. No inline hex or oklch values in components.
  - Paper `oklch(14.5% 0.012 250)`, panels `--color-paper-2`, insets `--color-paper-3`.
  - One signal: amber backlight `--color-accent oklch(81% 0.16 72)` with `--color-accent-glow`. Used for primary buttons, the LCD numerals and the active nav.
  - Status (functional only, always shown with a word and a shape): ok green, soon yellow, overdue red, due/never-logged violet.
  - Stamp inks: `--color-stamp-done` (blue), `--color-stamp-red`.
- **Type:**
  - Oxanium for headings, numerals and uppercase labels.
  - Barlow for body text.
  - Barlow Condensed for stamps and chips.
  - Headings are always roman (never italic).

## Components (app.css)
- `.panel-box`: a dash panel with the paper-2 background, a hairline border and a 14px radius.
- `.lcd`: amber Oxanium numerals with a glow. Used only for odometer and km readouts.
- `.btn`, `.btn--primary` (amber), `--ghost`, `--danger`, `--small`: all 8 states.
- `.chip--{state}`: a small flat stamp for status.
- `.stamp`, plus `--red`, `--soon`, `--round` and `.thunk`:
  - a tilted double-ruled rubber stamp;
  - `.thunk` plays the press-down animation when you mark something done;
  - used for OVERDUE / DUE SOON on the next job, DONE on visits, and DONE after Mark done.
- `.step-set`: a numbered form fieldset. The step number sits above the legend, not beside it.
- `Gauge.svelte`: a ring gauge showing the share of the interval used. Center text is "!" when overdue, "?" when never logged, otherwise a %.

## Pages
- **Garage (Index-First):**
  - summary counts;
  - a "Next job" panel with its stamp and one-tap Done (optimistic, with Undo);
  - one dash card per bike, sorted by worst state: schematic, LCD odometer, 3 gauges, update km.
  - A dashed "Add a bike" tile.
- **Bike (Stat-Led):**
  - a cluster panel: LCD odometer, four warning lamps (they glow only when the count is above 0), update km, Log a service;
  - the schematic stage with an exploded-view toggle;
  - gauge tiles grouped by state;
  - the "Service book": visits shown as dashed slips, each with a round DONE stamp.
- **Part panel:** a bottom sheet on mobile, a floating right panel on desktop. Big gauge, LCD readouts, Mark done (stamps DONE, Undo toast).
- **Forms:**
  - Log service and Add a bike use `.step-set` panels.
  - Log service keeps the sticky save bar.
  - Order for a new bike: type → name → km → plate (optional).
- **Nav:** N9 sticky bar: glowing dot wordmark, Garage and Settings, one amber "+ Log service".
- **Landing (logged-out `/`):** typographic hero (Create account / Self-host it) → a live demo cluster: the sport schematic plus an engine-oil gauge and stamp driven by km and day sliders, using the same rule as `app/due.py` → a two-column ledger of what it tracks → a self-host panel (copyable `docker compose` commands, GitHub link, MIT stamp) → a closing CTA → Ft4 colophon. `REPO_URL` is set at the top of `Landing.svelte`. Shell commands use `--font-code`.
- **Login:** form in a panel, schematic stage with a SERVICED stamp, Ft4 colophon line.

## Rules
- Root `overflow-x: clip`. Check at 320 / 375 / 414 / 768 px.
- `.page` must not use `isolation`: the part panel's scrim (z 70) has to sit above the sticky nav (z 50).
- Mix colors `in srgb` (oklch hue interpolation turns red→slate into purple).
- Motion: gauge sweep, stamp thunk, explode, panel slide. All reduce to ~1ms under `prefers-reduced-motion`.
- Successful km updates are silent. Toasts are only for undoable actions.
