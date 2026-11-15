# Inbox Copilot --- Design System

A reusable visual and interaction guide for the Inbox Copilot web
application. The interface should feel like a thoughtfully designed
productivity tool: calm, editorial, precise, and human. It should not
resemble a generic AI dashboard or a template assembled from gradients
and glowing cards.

## 1. Design direction

### Core character

-   **Editorial, not corporate:** use confident typography, deliberate
    spacing, and clear hierarchy.
-   **Warm, not sterile:** prefer paper-like neutrals and restrained
    natural accents over pure white, blue, or neon palettes.
-   **Product-first:** show real interface elements and useful states
    rather than abstract AI illustrations.
-   **Quietly capable:** interactions should feel responsive and
    considered, not theatrical.
-   **Trustworthy:** privacy, user control, and clear action states are
    part of the visual language.

### Design principles

1.  Make the purpose of each page obvious within a few seconds.
2.  Prefer concrete product UI, email examples, and workflow previews to
    decorative graphics.
3.  Use whitespace to establish hierarchy; do not fill every empty area
    with cards.
4.  Use color to communicate state and priority, not merely to decorate.
5.  Keep motion subtle, short, and functional.
6.  Make destructive, external, and email-sending actions visually
    distinct from safe actions.

## 2. Color system

Use the following palette as the default foundation. Keep the warm
off-white background dominant and reserve saturated colors for small
accents or meaningful states.

  -------------------------------------------------------------------------
  Token                     Hex                     Usage
  ------------------------- ----------------------- -----------------------
  `--color-paper`           `#F7F6F0`               Main page background

  `--color-surface`         `#FFFFFF`               Cards, menus, elevated
                                                    content

  `--color-surface-muted`   `#F0EFE8`               Secondary panels and
                                                    subtle fills

  `--color-ink`             `#263B32`               Primary text, strong
                                                    headings, dark panels

  `--color-ink-soft`        `#52645A`               Secondary text

  `--color-muted`           `#858B80`               Supporting labels and
                                                    metadata

  `--color-line`            `#E5E3D9`               Borders and dividers

  `--color-forest`          `#354F42`               Primary actions and
                                                    selected states

  `--color-forest-hover`    `#293F35`               Hover state for primary
                                                    actions

  `--color-terracotta`      `#C8795D`               Small highlights and
                                                    occasional emphasis

  `--color-sage`            `#DCE6D9`               Soft positive or
                                                    selected backgrounds

  `--color-cream`           `#EEE9DA`               Warm supporting
                                                    surfaces
  -------------------------------------------------------------------------

### Semantic states

Use semantic colors consistently. Do not rely on color alone; pair each
state with a label, icon, or other cue.

  State              Suggested treatment
  ------------------ --------------------------------------------------
  High priority      Muted terracotta accent, explicit priority label
  Normal priority    Neutral ink or muted label
  Completed / safe   Forest or sage
  Needs review       Warm amber/cream treatment
  Error / failed     Muted red with clear explanatory text
  Disabled           Reduced contrast, while retaining readable text

Avoid bright red, electric blue, purple gradients, and glowing neon
treatments unless a specific product state genuinely requires them.

## 3. Typography

Use typography to create the editorial character of the product.

### Typeface roles

-   **Display / hero headings:** a restrained serif such as
    `DM Serif Display`, `Instrument Serif`, or an available equivalent.
-   **Interface / body:** a clean sans-serif such as `Inter`, `Geist`,
    or the system sans-serif stack.
-   **Metadata:** the interface sans-serif, with slightly tighter sizing
    and muted color.

If a font cannot be loaded reliably, use a sensible fallback rather than
blocking rendering.

### Type scale

  ------------------------------------------------------------------------------
  Role                            Desktop guidance               Mobile guidance
  ------------------- ---------------------------- -----------------------------
  Hero heading          `clamp(3rem, 6vw, 5.5rem)`   `clamp(2.6rem, 12vw, 4rem)`

  Page heading                        `2.5–3.5rem`                  `2.1–2.7rem`

  Section heading                       `2–2.8rem`                  `1.8–2.3rem`

  Card heading                       `1.1–1.35rem`                `1.05–1.25rem`

  Body                              `0.95–1.05rem`                   `0.95–1rem`

  Supporting text                    `0.82–0.9rem`                 `0.82–0.9rem`

  Metadata                           `0.7–0.78rem`                 `0.7–0.78rem`
  ------------------------------------------------------------------------------

### Typography rules

-   Use serif typography selectively for prominent headings, not for
    dense interface text.
-   Keep body copy readable with a line height around `1.5–1.7`.
-   Keep headings relatively tight, around `1.0–1.15`.
-   Use sentence case for headings and labels.
-   Avoid excessive uppercase labels, heavy letter spacing, and
    oversized bold text everywhere.
-   Do not use more than two font families on a page.

## 4. Layout and spacing

### Page structure

-   Use a centered content container with a maximum width around
    `1200–1280px`.
-   Use consistent horizontal page padding: approximately `24–32px` on
    desktop and `18–22px` on mobile.
-   Keep the main content aligned to a consistent grid.
-   Use generous vertical spacing between major sections.
-   Avoid making every section the same height or placing every element
    inside a bordered card.

### Spacing scale

Use a consistent spacing scale based on 4px increments:

`4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 120`

Recommended defaults:

-   Tight control spacing: `8–12px`
-   Related content: `16–24px`
-   Card padding: `20–28px`
-   Section spacing: `72–112px`
-   Hero spacing: `80–120px` on desktop, reduced on mobile

### Grid behavior

-   Use asymmetrical or varied-span grids where they improve the story
    of the page.
-   A bento layout is appropriate for feature overviews, but not every
    page needs one.
-   Keep card dimensions content-driven where possible.
-   On mobile, collapse multi-column layouts into a clear single-column
    sequence.
-   Never preserve a desktop two-column layout on mobile by shrinking
    text or controls until they become cramped.

## 5. Surfaces, borders, and depth

### Cards and panels

-   Use white or warm muted surfaces against the paper background.
-   Prefer a subtle 1px border to a strong shadow.
-   Use shadows sparingly and only to establish elevation.
-   Keep card radii consistent: generally `12–18px` for panels and
    `8–12px` for controls.
-   Use larger radii only for large feature panels or prominent preview
    surfaces.
-   Avoid stacking multiple nested cards without a clear information
    hierarchy.

### Suggested CSS tokens

``` css
:root {
  --color-paper: #F7F6F0;
  --color-surface: #FFFFFF;
  --color-surface-muted: #F0EFE8;
  --color-ink: #263B32;
  --color-ink-soft: #52645A;
  --color-muted: #858B80;
  --color-line: #E5E3D9;
  --color-forest: #354F42;
  --color-forest-hover: #293F35;
  --color-terracotta: #C8795D;
  --color-sage: #DCE6D9;
  --color-cream: #EEE9DA;

  --radius-control: 10px;
  --radius-card: 16px;
  --radius-feature: 22px;

  --shadow-soft: 0 8px 28px rgba(38, 59, 50, 0.06);
  --shadow-floating: 0 16px 44px rgba(38, 59, 50, 0.10);

  --content-width: 1240px;
}
```

## 6. Buttons and controls

### Primary button

-   Forest background with paper/white text.
-   Medium-to-large hit area; target at least `44px` high.
-   Rounded corners, not fully pill-shaped by default.
-   Hover: slightly darker forest and a subtle upward movement of at
    most 1px.
-   Focus: visible keyboard focus ring with sufficient contrast.
-   Disabled: clearly disabled without becoming unreadable.

### Secondary button

-   Transparent or white surface.
-   Thin warm border.
-   Ink text.
-   Hover: subtle muted surface fill.

### Text buttons and links

-   Use forest or ink for important links.
-   Use underline or another clear treatment where a link appears within
    body copy.
-   Do not make non-interactive text look clickable.

### Inputs

-   White surface, warm border, clear label.
-   Use a visible focus border/ring.
-   Place helper and validation text close to the field.
-   Preserve labels when a field contains a value; do not rely on
    placeholders as labels.
-   Make keyboard navigation and error states clear.

## 7. Inbox Copilot interface patterns

These patterns should be reused across authenticated product pages.

### Email list rows

-   Prioritize sender, subject, and a short preview.
-   Keep timestamps and category labels visually secondary.
-   Use a restrained left accent or small badge for priority.
-   Distinguish unread messages through weight and a small visual
    marker, not a large colored background.
-   Provide a clear hover and selected state.
-   Keep row density comfortable; avoid turning every email into a large
    card.

### Category filters

-   Use compact text tabs or small outlined pills.
-   Selected state: forest text with a soft sage or neutral fill.
-   Unselected state: muted ink with a subtle hover surface.
-   Show counts only when they help the user understand the inbox.

### Priority indicators

-   Use a small label, icon, or accent.
-   Keep priority levels understandable and consistent throughout the
    application.
-   Do not communicate priority through color alone.

### Email thread view

-   Make the subject the primary heading.
-   Show sender, recipients, and date as structured metadata.
-   Keep message body typography comfortable and readable.
-   Separate messages with whitespace or a subtle divider.
-   Clearly distinguish quoted content and collapsed history.
-   Keep actions such as reply, archive, and delete visually separated
    from message content.

### AI-generated summaries

-   Label summaries as AI-generated.
-   Keep them visually secondary to the original email.
-   Avoid presenting generated interpretation as verified fact.
-   Preserve access to the original email content.

### Draft reply composer

-   Make the editable draft the central element.
-   Clearly indicate that the content is a draft and has not been sent.
-   Keep regenerate, edit, and discard actions separate from Send.
-   Use a confirmation step when the product requires one for sending.
-   Never style an AI suggestion as if it were already sent.

### Needs Review state

-   Use a warm cream or muted amber treatment.
-   Explain why review is needed when the reason is available, such as
    low confidence.
-   Give the user a direct path to inspect and correct the
    classification.
-   Avoid alarmist warning visuals for routine uncertainty.

### AI assistant panel

-   Keep the assistant visually integrated with the application rather
    than using a generic floating chatbot bubble.
-   Use concise prompts and suggested actions grounded in available
    product capabilities.
-   Make it clear when the assistant is searching, retrieving, or
    preparing a draft.
-   Distinguish assistant output from source email content.
-   Do not imply that the assistant can send email if the backend does
    not expose a send capability.

## 8. Landing-page patterns

The marketing site should communicate the product through tangible
interface previews and clear language.

### Navigation

-   Simple wordmark on the left.
-   A small number of useful links.
-   One clear primary action, such as "Get started".
-   Keep navigation height restrained and consistent.
-   On mobile, use a compact menu with accessible controls.

### Hero

-   Lead with the product outcome, not a list of AI technologies.
-   Use a large editorial heading and a short supporting paragraph.
-   Include one clear primary CTA and, if needed, a quieter secondary
    action.
-   Show a realistic inbox or product preview near the hero.
-   Keep the preview legible and visually connected to the product.
-   Do not use abstract AI brains, glowing orbs, generic robot
    illustrations, or decorative chat bubbles.

### Feature sections

-   Describe concrete user benefits: email organization, summaries,
    reply assistance, and user-controlled sending.
-   Use varied layouts to maintain rhythm.
-   Pair each feature with a relevant interface detail or workflow
    example.
-   Avoid generic claims such as "revolutionary AI" or "the future of
    productivity".

### Trust and privacy section

-   Explain what the application actually does with email data.
-   Use specific, verifiable statements only.
-   Explain external AI processing where applicable.
-   Do not claim end-to-end encryption, zero data retention, or absolute
    privacy unless those claims are technically and contractually true.
-   Show user control and permission boundaries clearly.

### Final CTA

-   Restate the practical value.
-   Use one clear action.
-   Avoid urgency, fake scarcity, or fabricated user counts.

## 9. Motion and interaction

Motion should clarify state and provide feedback. It should not compete
with the content.

### Recommended motion

-   Button hover: `120–180ms`
-   Hover surface transitions: `150–200ms`
-   Dropdown or popover: `140–200ms`
-   Small panel entrance: `180–260ms`
-   Scroll reveal: optional, subtle, and used sparingly

Use restrained easing such as `ease-out` for entrances and `ease-in-out`
for state transitions.

### Interaction rules

-   Every interactive element needs hover, focus, active, and disabled
    states where applicable.
-   Use loading indicators for asynchronous operations.
-   Prevent duplicate submissions while an action is processing.
-   Show clear success and error feedback.
-   Preserve user input when an operation fails where possible.
-   Do not use motion as the only indicator of a state change.
-   Respect `prefers-reduced-motion`.

Avoid parallax-heavy sections, cursor-following decorations, constant
floating animations, excessive blur, and spring effects on ordinary
controls.

## 10. Icons and imagery

-   Use one consistent icon family throughout the application, such as
    Lucide.
-   Prefer simple line icons with consistent stroke weight.
-   Use icons to support labels, not replace important labels.
-   Product screenshots and interface previews should use realistic,
    coherent sample data.
-   Clearly mark synthetic demo data where a user could mistake it for a
    live inbox.
-   Avoid generic stock photos and abstract AI imagery unless they serve
    a specific narrative purpose.

## 11. Responsive behavior

### Desktop

-   Use the full content width and considered multi-column layouts.
-   Keep line lengths comfortable; avoid very wide text blocks.
-   Use whitespace to separate content groups.

### Tablet

-   Reduce grid columns before reducing component padding too
    aggressively.
-   Keep navigation and controls comfortably tappable.
-   Reorder content only when the reading flow remains logical.

### Mobile

-   Use a single-column content flow for most sections.
-   Keep primary actions easy to reach.
-   Ensure email subjects and sender names wrap without overlapping
    metadata.
-   Make filters horizontally scrollable only when necessary, with clear
    selected states.
-   Avoid tiny text, dense tables, and hover-only interactions.
-   Keep touch targets at least `44px` where practical.

## 12. Accessibility requirements

-   Use semantic HTML landmarks and heading order.
-   Provide accessible names for icon-only buttons.
-   Ensure keyboard access to all interactive controls.
-   Use visible focus indicators.
-   Maintain sufficient text and UI contrast.
-   Do not use color as the only way to convey status.
-   Associate form labels, help text, and errors with their inputs.
-   Support reduced-motion preferences.
-   Ensure dialogs and menus manage focus correctly.
-   Use appropriate `aria-live` announcements for important asynchronous
    status updates.

## 13. Content and voice

The product voice should be clear, restrained, and useful.

### Prefer

-   "Your inbox, organized."
-   "Review the draft before sending."
-   "Emails that need your attention."
-   "A summary of the conversation."
-   "Needs review"

### Avoid

-   "Revolutionize your workflow with next-gen AI."
-   "Your autonomous email brain."
-   "Never touch your inbox again."
-   "100% secure" or other absolute security claims.
-   Vague labels such as "Magic", "Boost", or "AI-powered" when a direct
    action label is clearer.

Use action labels that describe what will happen: "Create draft",
"Review email", "Send reply", "Disconnect Gmail".

## 14. Do and don't

  -----------------------------------------------------------------------
  Do                                  Don't
  ----------------------------------- -----------------------------------
  Use warm neutral backgrounds        Default to a dark neon AI aesthetic

  Use serif display type selectively  Use decorative fonts throughout the
                                      interface

  Show realistic product UI           Lead with abstract AI illustrations

  Use subtle borders and restrained   Put every element in a floating
  shadows                             glass card

  Use varied but aligned layouts      Repeat the same three-card grid in
                                      every section

  Make user control visible           Hide important actions behind
                                      unexplained automation

  Label AI-generated content          Present generated output as
                                      verified source material

  Use specific, truthful privacy      Invent certifications, benchmarks,
  claims                              or guarantees

  Keep motion purposeful              Animate every element on scroll

  Make responsive layouts intentional Simply compress desktop layouts
  -----------------------------------------------------------------------

## 15. Implementation guidance for Next.js

-   Build shared primitives for buttons, badges, cards, inputs, and page
    containers rather than duplicating styles across routes.
-   Keep design tokens in a central stylesheet or Tailwind theme
    configuration.
-   Use the same typography, spacing, border, and radius rules across
    marketing and authenticated pages.
-   Keep page-specific composition flexible; the design system should
    provide consistency, not force every page into the same template.
-   Use `next/font` for locally optimized font loading when using Google
    or variable fonts.
-   Use semantic server components by default; add client components
    only where interaction or browser state requires them.
-   Keep loading, empty, error, and success states within the design
    system from the start.
-   Keep demo data separate from live application data and label it
    clearly.

## 16. Page review checklist

Before considering a page complete, verify:

-   [ ] The page has one clear primary purpose.
-   [ ] The visual hierarchy is obvious without relying on color.
-   [ ] The paper, ink, forest, and accent palette is used consistently.
-   [ ] Typography roles are consistent with the system.
-   [ ] Spacing and container widths align with the shared scale.
-   [ ] Cards and borders are used only where they add structure.
-   [ ] Interactive elements have hover, focus, active, loading, and
    disabled states as needed.
-   [ ] Mobile layout is intentionally designed and tested.
-   [ ] Keyboard navigation and focus visibility work.
-   [ ] AI-generated content is distinguishable from original email
    content.
-   [ ] Product capabilities and privacy claims match the actual
    implementation.
-   [ ] No fabricated metrics, testimonials, customer logos, or security
    claims appear.
