# Provide a tested AppImage distribution

The first release ships an Ubuntu amd64 `.deb`. AppImage is a proposed additional format for users without a matching package manager.

## Acceptance criteria

- Reproducible build from a maintained base with the correct Python and Qt runtime.
- Include required third-party license notices and verify redistribution terms.
- Stable plugin path even when the image is mounted at a temporary location.
- Verify first launch, replacement/upgrade, uninstall and safe behavior when the image is absent.
- Test on clean supported desktops before listing the format in Quick Start.

Do not publish an untested placeholder AppImage or require users to disable normal security controls.
