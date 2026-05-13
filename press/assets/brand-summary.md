# The Quiet Pilgrim Brand Summary

> Source of truth: `docs/superpowers/specs/2026-05-13-tqp-brand-foundation-design.md`. This file is a quick reference distilled from the master spec. When in doubt, open the spec.

Locked 2026-05-13 by Barrie after a 4-screen visual brainstorming session.

## Brand identity (spec section 1)

The Quiet Pilgrim is a personal-scope, Ubud-based bespoke hospitality umbrella owned by Barrie and Fanny. Five live services run beneath it:

1. **Moon & Spoon Kitchen**: private chef, villa catering, culinary journeys. Run by Fanny.
2. **Pilgrim Journeys**: curated multi-day villa experiences and itineraries.
3. **Pilgrim Care**: childcare, family support, in-villa staff (renamed from "Nanny").
4. **Pilgrim Transport**: private drivers, airport transfers, day tours.
5. **Pilgrim Wellness**: sound, breath, and movement experiences.

## Brand soul (spec section 3)

### Story

The Quiet Pilgrim is for the traveler who has done loud holidays and wants the opposite. The kind of guest who books a villa not to be served, but to be cared for. Who notices the small things first: how the breakfast tray is composed, how the driver does not speak when the road is quiet, how the kitchen knows what a Tuesday in March wants to eat. We are five small services in Ubud, run by hand by Fanny and Barrie, that together make one promise: that nothing about your time here is generic, transactional, or rushed.

### Vision

To be the most quietly trusted hand-finished hospitality presence in Ubud, Bali.

### Mission

Curate five services (Kitchen, Journeys, Care, Transport, Wellness) into a single quiet promise: every guest cared for the way Fanny and Barrie would care for a friend who came to stay.

## Four pillars (spec section 3.4)

Every brief, menu description, and press paragraph should honor at least two of these:

1. **Invited, not sold.** Copy reads like an invitation from a friend who lives here, not a pitch.
2. **Quietly excellent.** The standard is high. We do not announce that it is high.
3. **Of Ubud.** Place-specific. Indonesian ingredients, Balinese rhythm, Ubud's particular kind of green.
4. **Curated by hand.** No chain, no script, no franchise. A real pair of hands behind every service.

## Audience and anti-audience (spec section 3.5)

**Audience.** Slow-travel villa guests in Ubud, 35 to 65, design-aware, often returning. Villa owners and concierges. Wellness retreat hosts and yoga teachers. Press and design media writing the next round of Bali-as-considered-destination stories.

**Anti-audience.** Party villas, large destination weddings, packaged tour operators, influencer-trade placements.

## Voice (spec section 5)

**Six voice principles:**

1. Sentence rhythm matters more than information density.
2. Sensory before specifying.
3. Quiet superlatives (never "best in Bali," never "world-class," no exclamation marks).
4. Place over abstraction (Sukawati market in March, not "fresh local produce").
5. Invite, do not sell.
6. Honor stillness (whitespace in layout, pauses in copy).

**Anti-patterns (never use):**

- Em-dash (U+2014), en-dash (U+2013); see `feedback_no_em_or_en_dashes_ever`
- Exclamation marks
- "Discover", "experience", "indulge", "pamper", "transform", "authentic"
- Pressure CTAs ("book now", "limited spots", "don't miss out")
- Numbered marketing copy ("3 reasons", "5 things you'll love")

**Locked sample patterns** (full library in `applications/voice-and-copy.md`):

- Homepage hero: *"The pilgrim arrives in Ubud knowing only this: that they came to be still."*
- Sub-brand intro (M&S): *"Moon & Spoon is the kitchen at the heart of the house. Fanny is the chef. The menus change with the rice harvest and what is at Sukawati market on Wednesday morning."*
- Menu description (Floating Breakfast): *"A tray brought to your pool while the air is still cool. Sliced papaya. Coconut whose flesh you eat with a spoon. Black coffee, the kopi the staff drink themselves."*
- Footer mark: *"made quietly in Ubud since 2023"*
- Email sign-off: *"Warmly, Fanny & Barrie. The Quiet Pilgrim, Ubud."*

## Palette (spec section 6.1)

**Primary:**

| Name | Hex | Use |
|---|---|---|
| Mist | `#FAFAFA` | Default page surface, slightly cool off-white |
| Sage | `#7A8F76` | Signature accent: glyph, endorsement, italic words in wordmarks |
| Deep Slate | `#2A323A` | Primary text color (replaces black) |
| Forest | `#1F2A26` | Deepest tone, dark register background |

**Secondary:**

| Name | Hex | Use |
|---|---|---|
| Sand | `#C5B693` | Warmth accent: deck sections, menu paper, photography frames |
| Stone | `#E8ECE8` | Section dividers, card surfaces on Mist |

Both **light register** (Mist background) and **dark register** (Forest background) are first-class. Light for marketing, menus, decks, web. Dark for atmospheric hero sections, dinner-menu PDFs, low-light hospitality cards.

## Typography (spec section 6.2)

- **Headline serif**: **Fraunces** (OFL, variable, with opsz axis). Free and self-hostable. Pattern from GVP build.
- **Body sans**: **Inter** (OFL, variable). Free and self-hostable.
- **Italic accent**: Fraunces Italic colors a single word in each major headline in Sage.
- **Round 2 upgrade path**: PP Editorial New (Pangram Pangram, paid commercial) replaces Fraunces for marketing surfaces once Round 1 validates the system.

## Mark system (spec section 7)

**Master mark**: a horizontal lockup of two elements:

1. **Wordmark**: "The Quiet Pilgrim" in Fraunces. "Quiet" is italic and Sage; "The" and "Pilgrim" are Deep Slate.
2. **Glyph**: a stylized arch (pilgrim's gateway + Balinese candi bentar split gate), Sage stroke, sized to roughly 1.1x the cap-height of the wordmark, anchored to the left of the lockup with half-glyph-width clearspace.

**Sub-brand marks** follow the same wordmark formula. The accent word is italic Sage; the rest is Deep Slate. The glyph appears as a smaller left-bullet:

- Moon & Spoon **Kitchen**
- Pilgrim **Journeys**
- Pilgrim **Care**
- Pilgrim **Transport**
- Pilgrim **Wellness**

**Endorsement signature**: beneath every sub-brand wordmark, in Sage, all caps, 2.5px letter-spaced: *"A Quiet Pilgrim service"*.

**Lockup deliverables (Phase 2)**: 6 marks × 3 color states (Colored, Black, White) × 4 lockup forms (Horizontal, Vertical, Wordmark-only, Glyph-only) × 4 formats (SVG, PNG @1x, PNG @3x, EPS). Approximately 288 mark files in `01 Marks/` on Drive.

**Rules of avoidance:** never stretch, never alter the italic-Sage rule, never mix umbrella glyph with sub-brand wordmark, never place on busy photography without a Sage or Forest underlay, never rotate, never drop-shadow.

## How to apply (Skipper + Aya, spec section 10)

Before producing or proposing any TQP-facing visual or copy:

1. Read this summary or the design spec, confirm the relevant sections.
2. Pull marks from `assets/` (or `01 Marks/` on Drive), never re-export a logo by hand.
3. Use only the documented palette and typeface stack.
4. State explicitly which spec section informed each design choice when presenting drafts.
5. If the spec is silent on a needed element, default to the closest documented analogue and flag the gap to Barrie.
6. Never deviate without Barrie's explicit go.
7. Never apply this guideline outside TQP and its five sub-brands. Regenesis, GVP, HELM, Plaud, Aurelius each have or will have their own visual identity.

## Out of scope (spec section 11)

- Phase 2: mark production. Phase 3: application templates. Separate plans.
- Website rebuild of `thequietpilgrim.com` and `moonspoon.thequietpilgrim.com`: own project, follows brand pack.
- Regenesis, GVP, HELM, Plaud, Aurelius, and other personal-stack brands.

## Related

- Design spec: `docs/superpowers/specs/2026-05-13-tqp-brand-foundation-design.md`
- Voice doc: `applications/voice-and-copy.md`
- Drive folder map: `reference_tqp_drive_structure_2026_05_13.md`
- Brand memory anchor: `reference_tqp_brand_design_2026_05_13.md`
- Hard-rule memory: `feedback_tqp_brand_locked.md`
