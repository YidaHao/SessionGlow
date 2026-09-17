# Add an English UI and a language preference

The repository landing page is bilingual; the current panel and settings still use Chinese labels.

## Scope

- Move visible labels into a small translation mapping or Qt's existing translation mechanism.
- Provide English and Simplified Chinese with a persisted user preference.
- Keep session titles exactly as supplied by OpenCode.
- Test both languages for clipped controls and status labels; update demo media to match real UI behavior.

This is suitable for a contributor familiar with Python/Qt. Keep it focused on localization, without changing session lifecycle rules.
