# Raspberry Pi Webcam Timelapse (Tony's Version)

This project allows a Raspberry Pi to create a timelapse using a standard USB Webcam, controlled via a modern **Navy Blue Web Interface**.

**Repository**: [https://github.com/sector7gp/timelapse](https://github.com/sector7gp/timelapse)

## Features

1.  **USB Webcam Support**: Uses OpenCV to capture high-quality images.
2.  **Web Interface**:
    - **Live Focus Mode**: When "Live View" runs, the UI transforms (hiding non-essentials) so settings are right below the video. Perfect for mobile use!
    - **Persistence**: All settings (Brightness, Interval, Resolution, etc.) are saved automatically to `camera_settings.json`.
    - **Controls**: Brightness, Contrast, Saturation, White Balance.
    - **Presets**: Full HD / HD resolutions.
    - **Status**: Monitor shots taken and errors.
3.  **Background Processing**: Image capture runs in a separate thread.
4.  **Robust Error Handling**: Automatically retries on capture failures.

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


## API Reference

The system provides a simple REST API on port `5001`.

### Status
- **GET `/api/status`**: Returns current state, settings, and capture stats.

### Execution Control
- **POST `/api/control`**: 
  - `{"action": "start"}`: Start timelapse.
  - `{"action": "stop"}`: Stop everything.
  - `{"action": "update", "interval": 10, "width": 1920, "height": 1080}`: Update basics.

### Image Settings
- **POST `/api/settings`**: 
  - Body: `{"brightness": 100, "contrast": 110, "saturation": 110, "white_balance": 4000, "auto_wb": true}`

### Media
- **GET `/latest_image`**: Returns the most recent JPEG shot.
- **GET `/video_feed`**: MJPEG stream for live previews.

