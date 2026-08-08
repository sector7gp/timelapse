# Raspberry Pi Webcam Timelapse (Tony's Version)

This project allows a Raspberry Pi to create a timelapse using a standard USB Webcam, controlled via a modern **Navy Blue Web Interface**.

**Repository**: [https://github.com/sector7gp/timelapse](https://github.com/sector7gp/timelapse)

## Features

1.  **USB Webcam Support**: Uses OpenCV to capture high-quality images.
2.  **Web Interface**:
    - **Live Focus Mode**: When "Live View" runs, the UI transforms (hiding non-essentials) so settings are right below the video. Perfect for mobile use!
    - **Persistence**: All settings (Brightness, Interval, Resolution, etc.) are saved automatically to `camera_settings.json`.
    - **Controls**: Brightness, Contrast, Saturation, White Balance, Rotation (0°/90°/180°/270°).
    - **Presets**: Full HD / HD resolutions.
    - **Status**: Monitor shots taken and errors.
    - **Bilingual**: English / Spanish, toggled from the footer.
3.  **Gallery**: Browse past captures by day, view them full-size in a lightbox,
    download a whole day as a ZIP, or delete a day you no longer need.
4.  **Background Processing**: Image capture runs in a separate thread.
5.  **Robust Error Handling**: Automatically retries on capture failures.

Images are stored as `images/YYYYMMDD/img_YYYYMMDD_HHMMSS.jpg` — one folder per day.

## Setup

1.  **Hardware**:
    *   Raspberry Pi (Zero W or other)
    *   USB Webcam
    *   Sufficient SD Card space

2.  **Dependencies**:
    *   Install requirements:
    ```bash
    pip3 install -r requirements.txt
    ```

## Usage

1.  Start the web server:
    ```bash
    python3 app.py
    ```

2.  Open your browser and navigate to:
    `http://<RASPBERRY_PI_IP>:5001`

On first run the app creates `camera_settings.json` with sensible defaults and
rewrites it whenever you change a setting in the UI. It is **not** tracked in
git, so your tuned brightness/contrast/white balance live only on the device.
Back it up before wiping a checkout.

## Run as a Service (systemd)

To make the script start automatically when the Pi boots:

1. Create a service file:
   ```bash
   sudo nano /etc/systemd/system/timelapse.service
   ```

2. Paste the following content (update `/path/to/timelapse` to your actual folder path):
   ```ini
   [Unit]
   Description=Tony Timelapse Web Service
   After=network.target

   [Service]
   WorkingDirectory=/Python/timelapse
   ExecStart=/usr/bin/python3 app.py
   Restart=always
   User=root

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable timelapse.service
   sudo systemctl start timelapse.service
   ```

To check logs: `journalctl -u timelapse.service -f`

## Remote Access

**The app has no authentication of its own.** Anyone who can reach port `5001`
can change settings and delete images. Put something in front of it before
exposing it beyond your LAN.

### Cloudflare Tunnel + Access (what this project uses)

`cloudflared` runs on the Pi and dials out to Cloudflare, so there is nothing to
forward on the router and no certificate to manage — TLS terminates at
Cloudflare's edge.

1.  Install `cloudflared` on the Pi and create a tunnel pointing at
    `http://localhost:5001`.
2.  In the Cloudflare dashboard: **Zero Trust → Access → Applications → Add an
    application → Self-hosted**, using the tunnel's hostname.
3.  Add a policy with **Action: Allow** and **Include → Emails**, listing the
    addresses that may sign in. Each person gets a one-time PIN by email; no
    Cloudflare account needed on their side.
4.  To grant access later, add the address to the same policy. To revoke it,
    remove the address *and* end any live session under **Access → Users →
    Revoke session** — sessions outlive the policy change otherwise.

Access protects the tunnel hostname only. Reaching the Pi directly by LAN IP
still bypasses it, which is fine on a trusted network and is the current setup.

Note that Cloudflare returns **524** if the origin takes too long to send its
first byte, so anything slow must stream rather than buffer.

### Nginx + Let's Encrypt (alternative)

`nginx/timelapse.conf` is a reverse-proxy template for setups without a tunnel.
It is not what this project runs and is unmaintained. Two things to fix before
using it: uncomment the `ssl_certificate` lines (nginx refuses to start with
`listen 443 ssl` and no certificate, which also blocks the certbot run that
would create them — start from the port 80 block only and let
`certbot --nginx -d your_domain.com` add the TLS block), and drop the
unconditional `Connection "upgrade"` header, since MJPEG is not WebSocket and
sending it breaks proxy keep-alive. `proxy_buffering off` is the directive that
actually matters for the live stream.

## API Reference

The system provides a simple REST API on port `5001`. It is unauthenticated —
see [Remote Access](#remote-access).

### Status
- **GET `/api/status`**: Returns current state, settings, and capture stats.

### Execution Control
- **POST `/api/control`**: 
  - `{"action": "start"}`: Start timelapse.
  - `{"action": "stop"}`: Stop everything.
  - `{"action": "update", "interval": 10, "width": 1920, "height": 1080}`: Update basics.

### Image Settings
- **POST `/api/settings`**: 
  - Body: `{"brightness": 100, "contrast": 110, "saturation": 110, "white_balance": 4000, "auto_wb": true, "rotation": 0}`
  - `rotation` accepts `0`, `90`, `180` or `270` and is applied to both the live
    preview and the saved images. Omitted fields fall back to their defaults
    rather than keeping the current value, so send the full body.

### Media
- **GET `/latest_image`**: Returns the most recent JPEG shot.
- **GET `/video_feed`**: MJPEG stream for live previews.

### Gallery
All `<date>` values must be exactly 8 digits (`YYYYMMDD`); anything else returns
`400`.

- **GET `/api/gallery`**: Lists the available day folders, newest first.
- **GET `/api/gallery/<date>`**: Lists the JPEG filenames for that day, newest first.
- **GET `/api/gallery/<date>/download`**: Returns that day's images as a single ZIP.
- **DELETE `/api/gallery/<date>`**: Permanently deletes the day's folder and every image in it.
- **GET `/images/<date>/<filename>`**: Serves a single stored image.

