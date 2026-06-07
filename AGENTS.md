# AGENTS.md — Oído Project

## Project Overview
Oído is a free, lightweight ear-training tool for adult Spanish-speaking learners of English. It focuses on pronunciation discrimination (especially minimal pairs), listening skills, verb conjugations, and practical daily use. The site is hosted on GitHub Pages as a simple static site.

## Target Audience
- Adult Spanish speakers (mostly Latin American)
- Intermediate level or above
- Want practical improvement in listening and pronunciation, not academic grammar
- Value clarity, immediate feedback, and low-friction practice

## Core Principles

### Pedagogy
- Prioritize listening discrimination and minimal pairs above all
- Give clear, simple explanations in both English and Spanish when helpful
- Use progressive difficulty
- Provide immediate, useful feedback
- Focus on high-frequency, practical language

### Design & UX
- Keep the interface clean, minimal, and calm
- Prioritize accessibility and readability
- Avoid visual clutter or unnecessary animations
- Make it feel professional but friendly and encouraging
- Mobile-friendly is important

### Tone
- Respectful and encouraging
- Clear and direct (avoid overly cute or childish language)
- Bilingual-friendly — Spanish can be used to support understanding when it helps learning

## Technical Guidelines

- This is a static GitHub Pages site — keep everything lightweight
- Prefer vanilla HTML, CSS, and JavaScript
- Avoid heavy frameworks or dependencies unless they bring clear value
- Keep file sizes small and loading fast
- Maintain good semantic HTML and accessibility (labels, ARIA where needed)
- Changes should be easy to review and maintain long-term

## Content Rules

### Minimal Pairs
- Focus on pairs that are genuinely difficult for Spanish speakers (/b/ vs /v/, /s/ vs /z/, /ʃ/ vs /tʃ/, vowel contrasts, etc.)
- Include clear audio cues and visual support
- Add example words + short, natural sentences
- Provide contrastive explanations when useful

### Feedback & Interaction
- Feedback should be encouraging but honest
- Explain *why* something was correct or incorrect when possible
- Allow users to retry easily

### New Features / Content
- When adding new sets or sections, follow the existing structure and style
- Keep navigation simple and consistent
- Document any new patterns or components clearly

## When Making Changes

- Always work in **plan mode** first for non-trivial changes
- Show clear diffs before applying changes
- Prioritize small, reviewable improvements over big refactors unless specifically requested
- Respect the current minimal aesthetic — don't add complexity without strong justification
- If something improves learning outcomes or accessibility, it should be seriously considered

## Do's and Don'ts

**Do:**
- Make practice feel effective and motivating
- Think about real classroom or self-study use cases
- Keep the experience focused and distraction-free
- Suggest improvements that respect the existing simple architecture

**Don't:**
- Overcomplicate the UI or add heavy dependencies
- Use overly academic or complicated explanations
- Assume advanced English knowledge from the user
- Add features just because they're technically interesting

---

This file should live in the root of the `oido` folder as `AGENTS.md`.