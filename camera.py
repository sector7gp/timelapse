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

        self.settings_changed = True # Dirty flag

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
            self.settings_changed = True
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

            # Exposure via v4l2-ctl (DISABLED due to conflict with OpenCV on propertys)
            # The v4l2-ctl calls were causing 'select() timeout' errors and video freeze.
            # We are reverting to standard OpenCV props or disabling it for now.
            try:
                # Attempt standard OpenCV exposure if supported
                if self.exposure != 0:
                     cap.set(cv2.CAP_PROP_EXPOSURE, self.exposure)
                # Note: This often doesn't work on Pi, but it doesn't crash the stream.
            except:
                pass

            # device_path = f"/dev/video{self.device_index}"
            # cmd = ['v4l2-ctl', '-d', device_path]
            
            # # Helper to run v4l2 commands without spamming errors
            # def run_v4l2(args):
            #     try:
            #         subprocess.run(cmd + args, capture_output=True, check=True)
            #         return True
            #     except subprocess.CalledProcessError:
            #         return False

            # if self.exposure == 0:
            #     # User's camera: value=0 (Auto Mode) implies 0 is Auto.
            #     # Standard UVC: 3 is Auto. We try both.
            #     if not run_v4l2(['-c', 'auto_exposure=0']):
            #         if not run_v4l2(['-c', 'auto_exposure=3']):
            #             run_v4l2(['-c', 'exposure_auto=3']) # Fallback
            # else:
            #     # Manual Exposure
            #     # User's camera: likely 1 for Manual.
            #     if not run_v4l2(['-c', 'auto_exposure=1']):
            #          run_v4l2(['-c', 'exposure_auto=1'])
            #     
            #     # Set Absolute Exposure
            #     # ... (Mapping logic removed for stability) ...
            #     val = ...
            #     # ...
                
        except Exception as e:
            logger.warning(f"Error applying settings: {e}")

    def get_stream(self):
        """Generator function for MJPEG stream. Pauses timelapse loop if running."""
        was_running = self.is_running
        if was_running:
            self.stop() 
            time.sleep(2) # Allow camera creation to fully release
        
        # Revert to default backend (Auto) as V4L2 enforcement caused timeouts
        cap = cv2.VideoCapture(self.device_index)
        
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
                # Optimized: Only apply heavy v4l2 settings if they changed
                if self.settings_changed:
                    self._apply_camera_settings(cap)
                    with self.lock:
                        self.settings_changed = False
                
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

    def _capture_loop(self):
        time.sleep(1) # Safety delay
        cap = cv2.VideoCapture(self.device_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._apply_camera_settings(cap)
        with self.lock:
             self.settings_changed = False
        
        if not cap.isOpened():
            logger.error("Could not open camera.")
            self.is_running = False
            return

        # Warmup
        time.sleep(2)

        while self.is_running:
            start_time = time.time()
            
            # Re-apply settings before shot only if changed
            if self.settings_changed:
                self._apply_camera_settings(cap)
                with self.lock:
                    self.settings_changed = False

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
