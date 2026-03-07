# Changelog

All notable changes to this project will be documented in this file.

## [1.4.0] - 2026-03-07
### Added
- **HTTPS Support (Documentation)**: Added Nginx reverse proxy templates and instructions for enabling secure access via Let's Encrypt.
- **Nginx Config**: Included `nginx/timelapse.conf` for standard reverse proxying with WebSocket support for MJPEG streams.

## [1.3.0] - 2026-03-07
### Added
- **Camera Rotation**: Added support for 0°, 90°, 180°, and 270° rotation. This affects both the Live View preview and the saved timelapse images.
- **Rotation Persistent Setting**: The rotation choice is saved to `camera_settings.json` and persisted across restarts.
- **Bilingual Rotation UI**: Localized rotation labels in English and Spanish.
## [1.2.0] - 2026-02-12
### Added
- **ZIP Download**: Users can now download a whole day of captures in a single ZIP file directly from the Gallery.
- **Media Deletion**: Added a "Delete Day" feature to the Gallery for easy maintenance.
- **Improved UI**: Action buttons (Download/Delete) integrated into the date selector with localized tooltips.
- **Privacy Audit**: Verified all names, paths, and configurations are safe for public distribution.

### Changed
- Refactored backend to support on-the-fly ZIP compression and folder removal.
- Updated version fallback to v1.2.

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
