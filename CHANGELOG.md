# Changelog

All notable changes to this project will be documented in this file.

## [1.3.0] - 2026-03-07
### Added
- **Camera Rotation**: Added support for 0°, 90°, 180°, and 270° rotation. This affects both the Live View preview and the saved timelapse images.
    - [x] Backend Implementation
        - [x] Update `camera.py` with rotation logic <!-- id: 80 -->
        - [x] Update `app.py` API endpoints <!-- id: 81 -->
    - [x] Frontend Implementation
        - [x] Add rotation control to `index.html` <!-- id: 82 -->
        - [x] Add translations (EN/ES) <!-- id: 83 -->
    - [x] Verification
        - [x] Test rotation in Live View <!-- id: 84 -->
        - [x] Test rotation in captured images <!-- id: 85 -->
        - [x] Verify settings persistence <!-- id: 86 -->
- **Rotation Persistent Setting**: The rotation choice is saved to `camera_settings.json` and persisted across restarts.
- **Bilingual Rotation UI**: Localized rotation labels in English and Spanish.

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
