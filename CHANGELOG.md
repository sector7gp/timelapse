# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-02-12
- [x] v1.2 Feature Enhancements
    - [x] Add "Download Day as ZIP" feature <!-- id: 70 -->
    - [x] Add "Delete Day" feature to Gallery <!-- id: 71 -->
    - [x] Improve UI for action buttons (Download/Delete) with localized tooltips.
    - [x] Conduct Privacy Audit (verified names, paths, configs are safe for public distribution).
- [x] Refactoring for Distribution
    - [x] Refactor backend for on-the-fly ZIP compression and folder removal.
    - [x] Update version fallbacks in code <!-- id: 63 -->
    - [x] Clean up logs/debugging prints <!-- id: 64 -->
- [ ] Documentation Update
    - [x] Update `README.md` for distribution <!-- id: 65 -->
    - [x] Update `CHANGELOG.md` for v1.2 <!-- id: 66 -->

## [1.1.0] - 2026-02-12
### Added
- **Daily Folder Organization**: Images are now stored in subfolders named by date (`images/YYYYMMDD/`).
- **Standardized Naming**: Filenames follow the format `img_YYYYMMDD_HHMMSS.jpg` (strictly seconds).
- **Web Gallery**: Integrated an interactive gallery in the web UI for browsing past captures.
- **Lightbox Viewer**: View full-size images from the gallery.
- **Multi-language Support**: Dual language support (English/Spanish) with flag toggles in the footer.
- **Git Branch Tracking**: Backend logic to automatically fetch the active branch as the version name.

### Fixed
- Prevents infinite settings-save loops when polling status.
- Reduced log verbosity (moved non-critical settings logs to DEBUG level).

## [1.0.0] - 2026-02-11
### Added
- **Core Controller**: Class-based `TimelapseController` for robust camera management.
- **Web UI**: Modern Navy Blue responsive dashboard.
- **Live View**: Real-time MJPEG preview for camera alignment.
- **Settings Persistence**: All camera and timelapse settings are saved to `camera_settings.json`.
- **Systemd Service**: Instructions for running the app as a background service on boot.
- **API Reference**: Documented REST endpoints for external integration.

### Changed
- Port changed from default `5000` to `5001`.
- Silenced noisy Werkzeug INFO logs.

### Removed
- Unstable manual exposure controls (reverted to auto for hardware compatibility).
