# Nobox — Design System

> Noticing what others miss.

Nobox is a studio-and-publishing brand built around **attention**: essays, field notes,
ebooks, LinkedIn carousels, and a weekly email. The brand voice is that of a thought
leader with a point of view — editorial, warm, and considered, never the polished gloss
of a consultancy. This design system encodes that into tokens, components, and templates
so every artifact reads as unmistakably Nobox.

## Sources provided
- `uploads/Primary lockup tp.png` → copied to **`assets/nobox-lockup.png`** — the stacked,
  overlapping **NOBOX** wordmark in the four brand colors.
- `uploads/BNHillman.otf` → copied to **`fonts/BNHillman.otf`** — the licensed *Hillman*
  display face (by Brandon Nickerson; license owned by Tiffany J. Hopkins).
- A written brand brief covering color and typography (reproduced and verified below).

No production codebase or Figma file was provided. The website UI kit and slide templates
are original layouts built strictly to the stated brand surfaces and foundations — not
recreations of an existing product.

> ⚠️ **Font discrepancy to confirm.** The brief describes Hillman as "a serif with
> editorial character." The actual `BNHillman.otf` file is a **heavy geometric display
> sans-serif** — and it matches the logo lockup perfectly. The system uses the real font
> as the display face. If you intended a serif, please send the correct file.

---

## Content fundamentals — how Nobox writes

**Voice:** A confident, observant thought leader. Makes a clear claim, then explains it
plainly. The premise is bold; the explanation is accessible. The typography enacts this —
Hillman makes the claim, DM Sans delivers the argument.

- **Person:** Mostly declarative and second-person-adjacent ("Most teams optimize what's
  easy to measure"). Speaks *to* the reader about their work, not about itself. First-person
  "we" appears only when the studio is the subject.
- **Casing:** Sentence case everywhere. Mixed-case wordmark (`Nobox`, never `NOBOX`).
  The *only* uppercase is the small DM Sans eyebrow/kicker label, set with wide tracking.
- **Tone:** Calm, precise, unhurried. Short declarative sentences. A claim, then the
  reasoning. No hype, no growth-hack vocabulary, no exclamation points.
- **Punctuation & rhythm:** Em-dashes for the considered aside. Periods over exclamation.
  Numbers spelled out in prose where natural; figures in stats and metadata.
- **Emoji:** None. Never. They break the register entirely.
- **Examples of the voice:**
  - Headline: *"Noticing what others miss."*
  - Claim: *"Most teams optimize what's easy to measure."*
  - Follow-through: *"The signal that matters is usually the one nobody put on the dashboard."*
  - Pull quote: *"The brands that last are the ones that noticed something true."*
  - CTA: *"One thing worth noticing, every Thursday."* / *"Follow Nobox →"*
  - Anti-example (wrong register): ~~"🚀 Unlock 10x brand growth NOW!!!"~~

---

## Visual foundations

**Color** — four values, used with discipline (see `tokens/colors.css`):

| Role | Name | Hex | Job |
|------|------|-----|-----|
| Primary dark | Warm Brown | `#28211E` | Type, wordmark, strong backgrounds |
| Accent | Soft Teal | `#8DD9BF` | CTAs, highlights, active states — the **exception**, never the rule |
| Background | Warm Off-White | `#F5F0EB` | All backgrounds, in place of white |
| Secondary | Greige | `#C4B5A5` | Dividers, on-dark support text, mid-tones |

- **Never** pure white (`#FFFFFF`) or pure black (`#000000`). Use `#F5F0EB` and `#28211E`.
- Teal is an accent: one teal moment per layout, not a field of it.
- **Accessibility (verified):** Brown↔Off-White 13.9:1 (AAA). Greige on Brown 7.8:1 (AAA).
  Brown on Teal 9.7:1 (AAA). **Greige text on Off-White fails (1.8:1)** — so for secondary
  text *on light backgrounds* use the derived `--taupe-text` `#6E6258` (5.2:1, AA). Reserve
  raw greige for dividers, on-dark text, and decorative fills.

**Type** — two faces, each with a job (see `tokens/typography.css`):
- **Hillman** (`--font-display`) — page titles, section headings, carousel headers, pull
  quotes, ebook chapter titles, wordmark. Heavy and geometric; tighten tracking slightly
  (`-0.01em`). **Never below 28px** — letterforms lose legibility. Mixed case only.
- **DM Sans** (`--font-body`) — all running text, nav, labels, captions, buttons, forms.
  Regular 400 for body, Medium 500 for UI labels and the eyebrow.
- Two typefaces maximum in any layout. No Times, Helvetica, system defaults, or scripts.

**Backgrounds:** Flat warm-paper fields. No photographic hero washes by default; no
gradients as decoration. The one sanctioned "graphic" move is a large, very low-opacity
teal circle (`opacity ~0.14`) bleeding off a dark panel's corner. Color-block thumbnails
(brown / teal / greige) with a Hillman index number stand in for imagery until real art exists.

**Spacing & layout:** 8px base grid (`tokens/spacing.css`). Generous, editorial whitespace.
Reading measure capped ~680px for prose; content max ~1200px. Section padding is large
(72px blocks) — the brand breathes.

**Corner radii:** Soft, not pill. `10px` default for cards/inputs/buttons; `16–24px` for
large panels. Pill (`999px`) is reserved for tags and the eyebrow chip.

**Cards:** Warm-paper surface (`--surface-card` `#FBF8F4`, a hair lighter than the page —
never white), 1px greige-200 hairline border, soft corner, low shadow. Optional 3px teal
top rule for emphasis. Interactive cards lift 2px on hover.

**Shadows:** Low, warm, **brown-tinted** (`rgba(40,33,30,…)`) — never neutral gray.
Four steps from hairline to overlay (`tokens/spacing.css`).

**Borders & dividers:** 1px greige hairlines. Active/selected states use a 2px teal
underline (tabs) or teal fill (switch, primary button).

**Motion:** Quiet and considered. `140–360ms`, standard ease (`cubic-bezier(.4,0,.2,1)`)
or a soft ease-out for entrances. **No bounce, no spring.** Buttons nudge down 1px on press;
hovers darken the fill or shift to greige-200. Fades and short slides only.

**Hover / press states:** Hover darkens fills (teal→`--teal-600`, brown→`--brown-700`) or
fills transparent buttons with greige-200; text links shift greige→brown. Press translates
1px down. No scale-up, no glow except the teal focus ring on inputs (`3px --accent-wash`).

**Transparency & blur:** Used once, deliberately — the sticky header is translucent
off-white with a backdrop blur. Otherwise surfaces are opaque.

**Imagery vibe (when added):** Warm, natural light; muted, slightly desaturated; never cold
or clinical. Should sit comfortably on warm paper.

---

## Iconography

- **No bundled icon font or sprite was provided.** The brand's existing artifacts lean on
  **typographic** cues rather than icons: the Hillman wordmark, numeric indices (`01`, `02`),
  the teal underline/rule, and a single text arrow (`→`) for "more / next."
- **Default approach:** Prefer the **text arrow `→`** for directional CTAs (it's already used
  throughout). Where true icons are needed (UI chrome, future product surfaces), use
  **[Lucide](https://lucide.dev)** via CDN — a humanist, ~1.75px-stroke outline set that
  matches DM Sans's warmth. This is a **flagged substitution**: no icon set was specified, so
  Lucide is a recommendation, not a brand decision. Confirm or replace.
  ```html
  <script src="https://unpkg.com/lucide@latest"></script>
  ```
- **Emoji:** never used as icons (or anywhere). **Unicode** is used sparingly and only the
  arrow `→`. Avoid decorative glyphs.

---

## Index — what's in this system

**Root**
- `styles.css` — global entry point (import lines only). Consumers link this one file.
- `readme.md` — this guide.
- `SKILL.md` — Agent Skill manifest for downloading into Claude Code.

**`tokens/`** — `fonts.css` (Hillman @font-face + DM Sans import), `colors.css`,
`typography.css`, `spacing.css` (spacing, radius, shadow, motion).

**`fonts/`** — `BNHillman.otf` (Hillman display face).

**`assets/`** — `nobox-lockup.png` (primary stacked wordmark).

**`components/`** — reusable React primitives (namespace `window.DesignSystem_2fdbf7`):
- `core/` — **Button**, **Tag**, **Card**, **Eyebrow**, **PullQuote**
- `forms/` — **Input**, **Switch**
- `navigation/` — **Tabs**
- `content/` — **Avatar**

**`guidelines/cards/`** — foundation specimen cards (Colors, Type, Spacing, Brand) shown in
the Design System tab.

**`slides/`** — carousel / presentation templates (Title, Statement, List, Quote, CTA),
1280×720, ready for LinkedIn carousels and decks.

**`ui_kits/website/`** — high-fidelity Nobox marketing homepage built from the primitives.
