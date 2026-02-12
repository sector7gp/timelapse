# Raspberry Pi Webcam Timelapse (Tony's Version)

This project allows a Raspberry Pi to create a timelapse using a standard USB Webcam, controlled via a modern **Navy Blue Web Interface**.

**Repository**: [https://github.com/sector7gp/timelapse](https://github.com/sector7gp/timelapse)

## Features

1.  **USB Webcam Support**: Uses OpenCV to capture high-quality images.
2.  **Web Interface**:
    - **Live Focus Mode**: When "Live View" runs, the UI transforms (hiding non-essentials) so settings are right below the video. Perfect for mobile use!
    - **Pro Controls**:
        - **Exposure**: Uses robust `v4l2-ctl` commands for reliable hardware control.
        - **Other Settings**: Brightness, Contrast, Saturation, White Balance.
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
    *   Install OpenCV (headless) and Flask:
    ```bash
    pip3 install -r requirements.txt
    ```
    *   **Crucial**: Install `v4l-utils` for exposure control:
    ```bash
    sudo apt update && sudo apt install v4l-utils
    ```

## Usage

1.  Start the web server:
    ```bash
    python3 app.py
    ```

2.  Open your browser and navigate to:
    `http://<RASPBERRY_PI_IP>:5000`

### Using Live View
1.  Click **"Start Live View"**.
2.  The interface switches to **Focus Mode**:
    -   Video Feed at the top.
    -   Sliders immediately below.
    -   Timelapse controls are hidden.
3.  Adjust sliders to perfect your shot.
    -   *Tip*: Setting Exposure will disable Auto-Exposure temporarily.
4.  Click **"Close Live View"** to return to the main dashboard.
