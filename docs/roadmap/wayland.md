# Validate GNOME Wayland and KDE Plasma support

v0.1.0 is verified on Ubuntu 22.04 / GNOME / X11. Qt can render on other backends, but this does not establish desktop behavior.

## Scope

- Test Ubuntu 24.04 / GNOME Wayland and KDE Plasma separately.
- Record tray support, always-on-top policy, dragging, position restore, multiple monitors and mixed scaling.
- Fix reproducible problems with native Qt behavior where possible; document compositor limitations.
- Update the compatibility matrix only after the checklist is verified on real desktops.

Contributions of structured environment reports and reproducible tests are welcome. This is a compatibility investigation, not a promise of a release date.
