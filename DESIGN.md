---
name: Mod Manager FS25
description: Dashboard locale per inventario delle mod, mod attive nel gioco e partita nuova
colors:
  primary: "#4ade80"
  primary-hover: "#22c55e"
  primary-dark: "#15803d"
  neutral-bg: "#0a0f0c"
  neutral-surface: "#131f17"
  neutral-surface-hover: "#19271e"
  neutral-border: "#2b3e30"
  neutral-border-soft: "#203025"
  text-primary: "#f4f8f3"
  text-secondary: "#d3e0d1"
  text-muted: "#a6b8a4"
  text-muted-dark: "#80967e"
  accent-amber: "#fbbf24"
  accent-blue: "#60a5fa"
  accent-red: "#f87171"
typography:
  display:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 800
    lineHeight: "1.2"
    letterSpacing: "0.04em"
  body:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: "1.5"
    letterSpacing: "0.01em"
  code:
    fontFamily: "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "0.8125rem"
    fontWeight: 500
    lineHeight: "1.4"
rounded:
  sm: "6px"
  md: "10px"
  lg: "14px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "14px"
  lg: "20px"
  xl: "28px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#08130a"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
---

## Overview
A purpose-built agricultural telemetry console for Farming Simulator 25 power users. The aesthetic rejects generic SaaS bloat, neon purple mesh gradients, and decorative AI slop in favor of purposeful dark slate, tractor telemetry greens, high-contrast typography, and tactile data density.

## Colors
- **Ground & Panels**: Deep charcoal soil (`#0a0f0c`) with elevated slate panels (`#131f17` and `#19271e`).
- **Borders**: Crisp, structural separators (`#2b3e30`), giving physical definition without fuzzy drop-shadows.
- **Accents**: Functional agricultural green (`#4ade80`), harvest amber (`#fbbf24`), and critical red (`#f87171`).
- **Contrast**: All body text and functional labels maintain a minimum contrast ratio of 4.8:1 against their backdrops, passing WCAG AA requirements with zero low-contrast muddy grays.

## Typography
- **Primary Typeface**: `Inter`, clean sans-serif designed for high legibility at dense data scales.
- **Monospace Typeface**: `JetBrains Mono` for file names, SHA256 hashes, mod IDs, and directory paths.
- **Strict Size Floor**: No functional text below 11.5px. Interactive elements, table cells, and status indicators are never rendered in unreadable micro-type.

## Layout
- **Density**: Workstation grade. High information density without visual crowding.
- **Header**: Persistent brand mark, active game state pill, map launcher quick-action.
- **Navigation Tabs**: Clean toggle pill navigation with clear active state indication.
- **Tables**: Tabular numerals, fixed column widths for toggles, clear hover states on rows.

## Elevation & Depth
- **Depth Hierarchy**: Defined strictly by surface color stepped shading and sharp 1px borders, never by blurry floating drop-shadows.
- **Overlays & Modals**: Grounded in 85% opacity dark slate with 12px blur backdrop filter restricted to modals only.

## Shapes
- **Corner Radii**: Disciplined scale (6px for controls, 10px for cards, 14px for master containers). No arbitrary pill shapes for rectilinear cards.

## Components
- **Mod Activation Checkbox**: Explicit, high-contrast toggle cell in tables with instantaneous state reaction.
- **Quick Preset Chips**: Flat, tactile buttons indicating mod counts and active status.
- **Auto-Launcher Panel**: Comprehensive savegame synthesis controller with clear step validation.
- **External KingMods Search**: Live responsive grid displaying mod metadata, versioning, and download actions.

## Do's and Don'ts
- **DO**: Keep text sharp and legible against the dark background.
- **DO**: Use exact tabular figures for file sizes and dates.
- **DO**: Give every interactive element immediate visual and state feedback.
- **DON'T**: Introduce purple-to-blue generic AI gradients.
- **DON'T**: Use colored left-border side-tabs on cards (AI card tell).
- **DON'T**: Render functional text smaller than 11px.
- **DON'T**: Add decorative SVG grid lines or unmotivated floating elements.

