# FlexMix Hub UI Design System

## Purpose
FlexMix Hub is a light industrial control center for operating a beverage-machine fleet. It prioritizes readability, operational status, and compact data tables over decorative dashboard patterns.

## Design tokens
- Canvas: `#f6f8fb`; surface: `#ffffff`; subtle surface: `#f1f4f8`
- Ink: `#172033`; muted: `#667085`; faint: `#98a2b3`
- Border: `#e4e7ec`; strong border: `#d0d5dd`
- Primary blue: `#1769e0`; blue soft: `#eaf2ff`
- Healthy: `#168a4a` / `#e8f7ee`
- Warning: `#b54708` / `#fff3e6`
- Error/offline: `#c4323c` / `#fff0f1`
- Radius: 6px controls, 8px panels. Shadows are limited to a single, subtle 1px elevation.

## Typography and spacing
Use Inter/system sans. Page title 27px/760, panel title 15px/700, body 12–13px. Use a 4px spacing rhythm; typical panel padding is 18px and page padding is 32px.

## Layout
Desktop uses a fixed 250px white sidebar and a wide main content region. Tablet turns the sidebar into a drawer; mobile keeps horizontal table scrolling and stacks cards. The topbar shows hierarchy, current system state, and account actions.

## Components
- Primary actions use blue only when an action is genuinely primary.
- Panels are white with a light border, no heavy shadow or large radius.
- Badges communicate semantic status: green healthy, amber attention, red fault/offline, blue active, gray unknown.
- Tables are compact (12px), use a subtle header background, and only horizontal row dividers. Hover is a faint gray.
- Empty and unavailable states explain the actual system limitation; do not imply absent backend capability.
- Tabs use a blue bottom border, not filled pills.
- Inputs have clear labels/placeholders, a 6px radius, and a blue focus ring.

## Dashboard hierarchy
1. Four KPIs only: total machines, online machines, offline/error machines, backup state.
2. Machine Fleet is the largest primary panel and includes client-side search, filter, and MID sort.
3. Operations follows: recent errors, pending commands, backup state, then recent activity.

## Do / don't
Do use calm whitespace, one primary blue, compact real data, and semantic status colors.
Do not use dark mode, gradients, oversized icons, decorative KPI cards, heavy shadows, invented data, or generic SaaS revenue metrics.
