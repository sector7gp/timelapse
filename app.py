from flask import Flask, render_template, jsonify, request, send_from_directory, Response
import logging
import sys
import os
from camera import TimelapseController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

app = Flask(__name__)
OUTPUT_DIR = os.path.abspath("images")
camera = TimelapseController(output_dir=OUTPUT_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    return jsonify({
        'running': camera.is_running,
        'preview': camera.preview_mode,
        'interval_mins': camera.interval / 60,
        'shots': camera.shots_taken,
        'errors': camera.errors,
        'width': camera.width,
        'height': camera.height,
        'latest_image': camera.latest_image_path,
        'settings': {
            'brightness': camera.brightness,
            'contrast': camera.contrast,
            'saturation': camera.saturation,
            'white_balance': camera.white_balance,
            'auto_wb': camera.auto_wb
        }
    })

@app.route('/api/control', methods=['POST'])
def control():
    data = request.json
    action = data.get('action')
    
    if action == 'start':
        camera.start()
    elif action == 'stop':
        # Stop both timelapse and preview
        camera.stop()
    elif action == 'update':
        try:
            interval_mins = float(data.get('interval', 10))
            width = int(data.get('width', 1920))
            height = int(data.get('height', 1080))
            camera.set_settings(interval_mins, width, height)
        except ValueError:
            return jsonify({'error': 'Invalid settings'}), 400
            
    return jsonify({'success': True})

@app.route('/api/settings', methods=['POST'])
def update_image_settings():
    data = request.json
    try:
        camera.update_image_settings(
            brightness=data.get('brightness', 100),
            contrast=data.get('contrast', 100),
            saturation=data.get('saturation', 100),
            white_balance=data.get('white_balance', 4000),
            auto_wb=data.get('auto_wb', False)
        )
    except ValueError:
        return jsonify({'error': 'Invalid values'}), 400
    return jsonify({'success': True})

@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(camera.get_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(OUTPUT_DIR, filename)

@app.route('/latest_image')
def latest_image():
    if camera.latest_image_path:
        return send_from_directory(OUTPUT_DIR, camera.latest_image_path)
    else:
        return "No image captured yet", 404

if __name__ == '__main__':
    # Listen on all interfaces so it's accessible from outside the Pi
    app.run(host='0.0.0.0', port=5001, threaded=True)
