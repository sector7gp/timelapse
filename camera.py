import cv2
import time
import logging
import threading
import os
import subprocess
from datetime import datetime

logger = logging.getLogger("Camera")

class TimelapseController:
    def __init__(self, output_dir="images"):
        self.output_dir = output_dir
        self.interval = 10 * 60 # Default to 10 minutes (in seconds)
        self.is_running = False
        self.preview_mode = False # Flag for Live View
        self.thread = None
        self.lock = threading.Lock()
        
        # Camera Settings
        self.device_index = 0
        self.width = 1920
        self.height = 1080
        self.brightness = 100
        self.contrast = 100
        self.saturation = 100
        self.exposure = 0 # 0 usually means auto or default, depends on camera
        self.white_balance = 4000 # Auto usually, but specific values needed for manual
        self.auto_wb = True
        
        # State
        self.latest_image_path = None
        self.shots_taken = 0
        self.errors = 0

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def start(self):
        with self.lock:
            if self.is_running:
                return
            self.is_running = True
            self.preview_mode = False
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            logger.info("Timelapse started.")

    def stop(self):
        with self.lock:
            self.is_running = False
            self.preview_mode = False
        if self.thread:
            self.thread.join()
            logger.info("Timelapse stopped.")

    def set_settings(self, interval_mins, width, height):
        with self.lock:
            self.interval = int(float(interval_mins) * 60)
            self.width = int(width)
            self.height = int(height)
            logger.info(f"Settings updated: Interval={self.interval/60}m, Res={self.width}x{self.height}")

    def update_image_settings(self, brightness, contrast, saturation, exposure, white_balance, auto_wb):
        with self.lock:
            self.brightness = int(brightness)
            self.contrast = int(contrast)
            self.saturation = int(saturation)
            self.exposure = int(exposure)
            self.white_balance = int(white_balance)
            self.auto_wb = bool(auto_wb)
            logger.info(f"Image settings updated: B={self.brightness} C={self.contrast} S={self.saturation}")

    def _apply_camera_settings(self, cap):
        """Applies current settings to the OpenCV capture object and via v4l2-ctl."""
        try:
            # Standard OpenCV properties
            cap.set(cv2.CAP_PROP_BRIGHTNESS, self.brightness / 100.0 if self.brightness < 1 else self.brightness) 
            cap.set(cv2.CAP_PROP_CONTRAST, self.contrast)
            cap.set(cv2.CAP_PROP_SATURATION, self.saturation)
            
            if self.auto_wb:
                 cap.set(cv2.CAP_PROP_AUTO_WB, 1)
            else:
                 cap.set(cv2.CAP_PROP_AUTO_WB, 0)
                 cap.set(cv2.CAP_PROP_WB_TEMPERATURE, self.white_balance)

            # Exposure via v4l2-ctl
            device_path = f"/dev/video{self.device_index}"
            cmd = ['v4l2-ctl', '-d', device_path]
            
            # Helper to run v4l2 commands without spamming errors
            def run_v4l2(args):
                try:
                    subprocess.run(cmd + args, capture_output=True, check=True)
                    return True
                except subprocess.CalledProcessError:
                    return False

            if self.exposure == 0:
                # Try setting Auto Exposure (Standard V4L2: 3=Auto, 1=Manual)
                # Some cameras use 'exposure_auto', others 'auto_exposure'
                if not run_v4l2(['-c', 'exposure_auto=3']):
                    run_v4l2(['-c', 'auto_exposure=3'])
            else:
                # Manual Exposure
                # 1. Turn off Auto
                if not run_v4l2(['-c', 'exposure_auto=1']):
                    run_v4l2(['-c', 'auto_exposure=1'])
                
                # 2. Set Absolute Exposure
                # Map range -10..10 to camera range. 
                # Safe assumption: 156 is often a default "center" for generic drivers
                base_exposure = 156
                val = max(1, base_exposure + (self.exposure * 50))
                
                if not run_v4l2(['-c', f'exposure_absolute={val}']):
                    # Fallback for cameras using just 'exposure'
                    run_v4l2(['-c', f'exposure={val}'])
                
        except Exception as e:
            logger.warning(f"Error applying settings: {e}")

    def get_stream(self):
        """Generator function for MJPEG stream. Pauses timelapse loop if running."""
        was_running = self.is_running
        if was_running:
            self.stop() 
        
        # Force V4L2 backend to avoid GStreamer warnings/errors
        cap = cv2.VideoCapture(self.device_index, cv2.CAP_V4L2)
        
        # Set MJPG format directly to ensure high fps preview if supported
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._apply_camera_settings(cap)
        
        if not cap.isOpened():
            yield b''
            return

        with self.lock:
            self.preview_mode = True

        try:
            while self.preview_mode:
                self._apply_camera_settings(cap)
                
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                time.sleep(0.05) 
        finally:
            cap.release()
            with self.lock:
                self.preview_mode = False
            # If it was running, we leave it stopped as per design decision

    def _capture_loop(self):
        # Force V4L2
        cap = cv2.VideoCapture(self.device_index, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._apply_camera_settings(cap)
        
        if not cap.isOpened():
            logger.error("Could not open camera.")
            self.is_running = False
            return

        # Warmup
        time.sleep(2)

        while self.is_running:
            start_time = time.time()
            
            # Re-apply settings before shot
            self._apply_camera_settings(cap)

            # Flush buffer
            for _ in range(2):
                cap.grab()
            
            ret, frame = cap.read()
            if ret:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"img_{timestamp}.jpg"
                filepath = os.path.join(self.output_dir, filename)
                
                try:
                    cv2.imwrite(filepath, frame)
                    with self.lock:
                        self.latest_image_path = filename 
                        self.shots_taken += 1
                    logger.info(f"Captured {filename}")
                except Exception as e:
                    logger.error(f"Error saving image: {e}")
                    with self.lock:
                        self.errors += 1
            else:
                logger.error("Failed to capture frame")
                with self.lock:
                    self.errors += 1
            
            # Smart Sleep
            elapsed = time.time() - start_time
            sleep_time = max(0, self.interval - elapsed)
            
            # Break sleep into chunks to allow quicker stopping
            for _ in range(int(sleep_time)):
                if not self.is_running: break
                time.sleep(1)
            # Sleep remainder
            if self.is_running:
                time.sleep(sleep_time - int(sleep_time))
            
        cap.release()
