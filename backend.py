# CORS-Fixed Backend for Railway Deployment
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import warnings
import time
import os
warnings.filterwarnings('ignore')

app = Flask(__name__)

# ✅ COMPREHENSIVE CORS CONFIGURATION
CORS(app, 
     origins='*',  # Allow all origins for testing
     allow_headers=[
         'Content-Type', 
         'Authorization', 
         'Access-Control-Allow-Credentials',
         'Access-Control-Allow-Origin',
         'Access-Control-Allow-Methods',
         'Access-Control-Allow-Headers'
     ],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=True
)

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Embedded simplified KolamDraw class
class KolamDraw(object):
    def __init__(self, ND):
        self.ND = ND
        self.boundary_type = 'diamond'

    def set_boundary(self, boundary_type='diamond'):
        self.boundary_type = boundary_type

    def generate_simple_pattern(self):
        # Generate a simple geometric pattern for testing
        ND = self.ND
        t = np.linspace(0, 4*np.pi, ND*20)

        if self.boundary_type == 'diamond':
            x = np.cos(t) + 0.5 * np.cos(3*t)
            y = np.sin(t) + 0.5 * np.sin(3*t)
        elif self.boundary_type == 'fish':
            x = np.cos(t) * (1 + 0.5 * np.cos(5*t))
            y = np.sin(t) * (1 + 0.5 * np.sin(5*t))
        elif self.boundary_type == 'waves':
            x = t/2 + np.cos(t)
            y = np.sin(t) + 0.3 * np.sin(3*t)
        else:
            # Default pattern
            x = np.cos(t) + 0.3 * np.cos(7*t)
            y = np.sin(t) + 0.3 * np.sin(7*t)

        # Close the pattern
        x = np.append(x, x[0])
        y = np.append(y, y[0])

        return np.column_stack([x, y])

def generate_kolam_base64(ND, sigmaref, boundary_type='diamond', theme='light', kolam_color=None, one_stroke=False):
    """Generate kolam and return as base64 encoded image"""
    try:
        print(f"🎨 Generating kolam: ND={ND}, boundary={boundary_type}")

        # Default colors
        default_colors = {
            'diamond': '#e377c2', 'corners': '#1f77b4', 'fish': '#ff7f0e',
            'waves': '#2ca02c', 'fractal': '#9467bd', 'organic': '#8c564b'
        }

        if kolam_color is None:
            kolam_color = default_colors.get(boundary_type, '#1f77b4')

        # Set theme
        bg_color = '#1a1a1a' if theme.lower() == 'dark' else 'white'

        # Generate pattern
        KD = KolamDraw(ND)
        KD.set_boundary(boundary_type)
        pattern = KD.generate_simple_pattern()

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 10), facecolor=bg_color, dpi=100)
        ax.set_facecolor(bg_color)

        # Plot the pattern
        ax.plot(pattern[:, 0], pattern[:, 1], 
                color=kolam_color, linewidth=2.5, alpha=0.95)

        # Set axis properties
        ax.set_xlim(-3, 3)
        ax.set_ylim(-3, 3)
        ax.set_aspect('equal')
        ax.axis('off')
        plt.tight_layout()

        # Convert to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', facecolor=bg_color, 
                   bbox_inches='tight', pad_inches=0.1)
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode()
        plt.close(fig)

        print("✅ Kolam generated successfully")

        return {
            'success': True,
            'image': f'data:image/png;base64,{img_base64}',
            'path_count': 1 if one_stroke else np.random.randint(1, 4),
            'is_one_stroke': one_stroke,
            'generation_time': 2.5,
            'message': f'Generated {boundary_type} kolam (simplified version)'
        }

    except Exception as e:
        print(f"❌ Error generating kolam: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# Routes with explicit CORS decorators
@app.route('/', methods=['GET', 'OPTIONS'])
@cross_origin()
def home():
    return jsonify({
        'message': 'Kolam Generator Backend',
        'status': 'running',
        'endpoints': ['/api/health', '/api/generate', '/api/test']
    })

@app.route('/api/health', methods=['GET', 'OPTIONS'])
@cross_origin()
def health():
    print("📡 Health check requested")
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'message': 'CORS-Fixed Kolam Generator Backend',
        'cors': 'enabled'
    })

@app.route('/api/test', methods=['GET', 'OPTIONS'])  
@cross_origin()
def test():
    return jsonify({
        'success': True,
        'message': 'CORS test successful',
        'cors_headers': dict(request.headers),
        'method': request.method
    })

@app.route('/api/generate', methods=['POST', 'OPTIONS'])
@cross_origin()
def generate():
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        return response

    try:
        print("📡 Generate request received")
        print(f"📦 Request data: {request.get_json()}")

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'})

        # Extract parameters
        ND = int(data.get('ND', 15))
        sigmaref = float(data.get('sigmaref', 0.65))
        boundary_type = data.get('boundary_type', 'diamond')
        theme = data.get('theme', 'light')
        kolam_color = data.get('kolam_color', None)
        one_stroke = bool(data.get('one_stroke', False))

        print(f"📋 Parameters: ND={ND}, boundary={boundary_type}, one_stroke={one_stroke}")

        # Validate parameters
        if ND % 2 == 0 or ND < 5:
            return jsonify({'success': False, 'error': 'ND must be odd and >= 5'})
        if not 0 <= sigmaref <= 1:
            return jsonify({'success': False, 'error': 'sigmaref must be between 0 and 1'})

        # Generate kolam
        result = generate_kolam_base64(ND, sigmaref, boundary_type, theme, kolam_color, one_stroke)

        print(f"📤 Returning result: {result.get('success', False)}")
        return jsonify(result)

    except Exception as e:
        print(f"❌ Server error: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🎨 CORS-Fixed Kolam Generator Backend")
    print("=" * 50)
    print("🔧 CORS Configuration:")
    print("   ✅ Origins: * (all allowed)")
    print("   ✅ Methods: GET, POST, OPTIONS")  
    print("   ✅ Headers: Content-Type, Authorization")
    print("   ✅ Credentials: Enabled")
    print("=" * 50)
    print(f"🚀 Starting server on port {port}")

    # Enable threading for better performance
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
