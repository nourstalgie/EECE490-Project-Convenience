#!/usr/bin/env python3
"""
Project Convenience - AI Location Intelligence Platform
Single-file runner for local development and testing
"""

import os
import sys
import subprocess
import webbrowser
import time
import threading
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'flask', 'pandas', 'numpy', 'osmnx', 'geopandas', 
        'shapely', 'scikit-learn', 'joblib', 'folium', 
        'requests', 'beautifulsoup4'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
        print("✅ All packages installed successfully!")
    else:
        print("✅ All required packages are available!")

def ensure_model_exists():
    """Ensure the ML model exists, create if not"""
    if not os.path.exists('model.pkl'):
        print("🤖 ML model not found. Training model...")
        try:
            subprocess.check_call([sys.executable, 'train_model.py'])
            print("✅ Model trained successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to train model. Please check your data files.")
            return False
    else:
        print("✅ ML model found!")
    return True

def ensure_data_exists():
    """Ensure data files exist"""
    if not os.path.exists('data/features.csv'):
        print("📊 Features data not found. Generating dataset...")
        try:
            subprocess.check_call([sys.executable, 'generate_dataset.py'])
            print("✅ Dataset generated successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to generate dataset. Please check your setup.")
            return False
    else:
        print("✅ Data files found!")
    return True

def create_directories():
    """Create necessary directories"""
    directories = ['templates', 'static/css', 'static/js', 'cache']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("✅ Directories created!")

def open_browser():
    """Open browser after a short delay"""
    time.sleep(3)
    webbrowser.open('http://localhost:5000')
    print("🌐 Browser opened at http://localhost:5000")

def main():
    """Main function to run Project Convenience"""
    print("🚀 Starting Project Convenience - AI Location Intelligence Platform")
    print("=" * 60)
    
    # Check and install requirements
    check_requirements()
    
    # Create necessary directories
    create_directories()
    
    # Ensure data exists
    if not ensure_data_exists():
        print("❌ Data preparation failed. Exiting.")
        return
    
    # Ensure model exists
    if not ensure_model_exists():
        print("❌ Model preparation failed. Exiting.")
        return
    
    print("\n🎯 Starting Flask application...")
    print("📍 The application will be available at: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Open browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start the Flask app
    try:
        from app import app
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Project Convenience stopped. Thank you for using our platform!")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("Please check your setup and try again.")

if __name__ == '__main__':
    main()