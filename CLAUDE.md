# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Flask web app that drives a USB webcam on a Raspberry Pi to shoot timelapses. Three source files plus one template — no build step, no test suite, no linter configured.

## Commands

```bash
pip3 install -r requirements.txt   # opencv-python-headless + flask
python3 app.py                     # serves on 0.0.0.0:5001
python3 check_controls.py          # dumps v4l2-ctl --list-ctrls for /dev/video0 (Pi only)
```

On the Pi it runs under systemd (`timelapse.service`); logs via `journalctl -u timelapse.service -f`. See README.md for the unit file.

Note: the dev machine (macOS) has no `/dev/video0` and OpenCV camera access will fail there — capture/preview code paths can only be verified on the Pi. Flask routes *can* be tested locally by stubbing `cv2` and the `camera` module before importing `app`.

## Deployment

Production is reached through a **Cloudflare Tunnel** to the Pi, with Cloudflare Access (Zero Trust, email one-time-PIN) in front for authentication. The app itself has no auth of its own and binds `0.0.0.0:5001`, so LAN access bypasses Access entirely — that is a deliberate, accepted choice, not an oversight.

This makes `nginx/timelapse.conf` and the HTTPS section of README.md **obsolete**: Cloudflare terminates TLS at its edge and `cloudflared` dials out, so no nginx, no certbot, no open ports. Don't invest in that config. (It also wouldn't start as written — `listen 443 ssl` with both `ssl_certificate` lines commented out fails `nginx -t`.)

Anything long-running served through the tunnel must stream its first byte promptly; Cloudflare returns 524 when the origin takes on the order of 100s to start responding.

## Architecture

**`camera.py` — `TimelapseController`** owns all camera state and is instantiated once in `app.py` as a module-level singleton. Key invariants:

- **The camera device can only be held by one code path at a time.** `_capture_loop()` (timelapse thread) and `get_stream()` (MJPEG preview generator) each open their own `cv2.VideoCapture`. `get_stream()` therefore calls `stop()` and sleeps 2s to let the device release before opening its own handle. Any new code that touches the camera must respect this hand-off.
- `is_running` (timelapse thread alive) and `preview_mode` (stream generator alive) are mutually exclusive by construction; both are cleared by `stop()`.
- All mutable state is guarded by `self.lock`. The capture thread is a daemon thread; `stop()` joins it.
- `settings_changed` is a dirty flag: applying V4L2 properties is expensive, so `_apply_camera_settings()` only runs on the next frame/shot after a settings change, not every iteration.
- The capture loop sleeps in 1-second chunks so `stop()` takes effect quickly instead of waiting out a full interval.
- `_rotate_frame()` ([camera.py:142](camera.py#L142)) is applied to both the preview and the saved image, so rotation is baked into the JPEGs rather than being a display-only setting. It does not update the reported `width`/`height`, which stay landscape even at 90°/270°.

**Settings persistence**: every mutation (`set_settings`, `update_image_settings`) writes the full `camera_settings.json` immediately, and `load_settings()` reads it at construction. `interval` is stored in **seconds** in the JSON and on the controller, but the API and UI speak **minutes** — conversion happens at the boundary ([app.py:51](app.py#L51), [camera.py:103](camera.py#L103)). Don't let seconds leak into the UI or minutes into the controller. `camera_settings.json` is gitignored, so the Pi's tuned values live only on the Pi — a fresh clone starts from the defaults in `__init__`.

**Image storage**: `images/` (gitignored) → one folder per day `YYYYMMDD/` → `img_YYYYMMDD_HHMMSS.jpg`. `latest_image_path` holds the *relative* `YYYYMMDD/filename.jpg` form, which is what `/latest_image` and `/images/<path>` expect. Gallery endpoints rely on this layout: `/api/gallery` filters for 8-digit numeric directory names, and listing sorts filenames descending (works only because the name is time-sortable).

**Gallery endpoints take a user-supplied `date_str` and join it onto `OUTPUT_DIR`.** Every one of them must go through `resolve_day_dir()` ([app.py:25](app.py#L25)), which enforces the 8-digit shape; a bare `..` otherwise escapes the images directory, and the download handler's `os.walk` then recurses from there. Any new endpoint taking a date belongs behind the same guard.

**`templates/index.html`** is the entire frontend — one 960-line file with inline CSS and JS, no framework, no bundler. It polls `/api/status` every 2s while live view is *not* active, and drives everything through the REST API documented in README.md. Three things live here that are easy to break:
- **i18n**: strings are marked with `data-i18n="key"` attributes and swapped by `setLanguage()` against an inline `i18n` object (en/es). New user-facing text needs a key in both languages. Default language is Spanish, persisted in `localStorage.pref_lang`.
- **Live focus mode**: starting the preview hides non-essential panels so settings sit directly under the video (mobile use). Layout changes should preserve that.
- **Gallery modal**: dates render as a horizontally scrolling row of pills, each pill carrying a 📥 (ZIP download) and 🗑️ (delete day) button on its right edge. Download navigates via `window.location.href`; delete goes through `fetch(..., {method: 'DELETE'})`.

## Conventions

- Releases are annotated tags, `vMAJOR.MINOR.PATCH` (`v1.4.0`), matching the `## [1.4.0]` headings in `CHANGELOG.md`.
- `CHANGELOG.md` is maintained by hand — add an entry for user-visible changes.
- Feature work happens on version branches (`v1.1`) merged to `main`. Note the branch names are *not* pinned to one version: `v1.1` accumulated v1.2, v1.3 and v1.4 work, so a branch name says nothing about which features a checkout has. Check the commit.
- Commit messages use `type(scope): summary`, e.g. `feat(v1.3): ...`, `fix(v1.2): ...`.
- Manual exposure control was deliberately removed for hardware stability; don't reintroduce `CAP_PROP_EXPOSURE` without a reason.

## Known issues

Found by review, not yet fixed:

- **ZIP download builds the whole archive in RAM** ([app.py:182](app.py#L182)). A day of captures is ~100MB+; the Pi Zero W has 512MB. `ZIP_DEFLATED` also burns CPU for ~0% gain on already-compressed JPEGs. Fix is a streaming generator writing into an unseekable sink with `ZIP_STORED`.
- **`deleteDay()` calls `loadDates()`** ([index.html:755](templates/index.html#L755)), which does not exist — the function is `fetchDates()`. The `ReferenceError` aborts the rest of the callback, so a deleted day stays in the list with broken thumbnails even though the server deleted it.
- **`get_git_branch()` fallback returns the hardcoded `"v1.2"`** ([app.py:40](app.py#L40)) and is stale. The UI footer shows this, so don't trust it to identify a deployment.
- **`cv2.imwrite` returns `False` on failure rather than raising**, so a full SD card increments `shots_taken` and logs nothing.
- **No validation that `interval > 0`** — `set_settings(0, ...)` turns the capture loop into a tight loop.
- **A second `/video_feed` client** opens a competing handle on the same device and, when it disconnects, clears `preview_mode` and kills the first client's stream.
