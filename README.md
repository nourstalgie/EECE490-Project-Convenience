## 👥 **Contributors**

**Team Members:**
- Adam Yahya
- Yasmina Hanna  
- Nour El Semrani

**Course:** ECE 490 - Ammar Mohanna

---

# Project Convenience 🏪 - AI Location Intelligence Platform

**Project Convenience** is an AI-powered platform that analyzes any location to determine if it's a good spot for opening a convenience store. Simply enter coordinates and get instant, data-driven recommendations with interactive maps.

---

## 👤 **User Guide**

### What Does This Do?
Project Convenience analyzes locations using AI to tell you **YES**, **NO**, or **MAYBE** for opening a convenience store. It looks at:
- How busy the streets are
- How many intersections there are  
- How much green space exists
- How many shops/services are nearby
- How well-connected the area is

> **⚠️ Important**: This model is trained specifically for the **Fertile Crescent region** (Lebanon, Syria, Jordan, Palestine, Iraq, Turkey). Locations outside this region will produce **random/unreliable results**.

### How to Use (Super Simple!)

1. **Run the app**: `python run_convenience.py`
2. **Open your browser**: Go to `http://localhost:5000` (localhost only)
3. **Enter coordinates**: Type latitude and longitude (like 33.5138, 36.2765 for Damascus, Syria)
4. **Click "Analyze Location"**
5. **See results**: Get a score (0-100) and recommendation
6. **Explore the map**: See all the features that influenced the decision

> **Note**: This application is designed to run on localhost (127.0.0.1:5000) for local development and testing purposes.

### What You'll See
- **Viability Score**: 0-100 (higher = better for convenience store)
- **Recommendation**: Clear YES/NO/MAYBE with confidence level

### Example Results
- **Score: 85/100** → "YES - Excellent location for convenience store"
- **Score: 45/100** → "MAYBE - Consider other factors"  
- **Score: 15/100** → "NO - Not recommended for convenience store"

---

## 🔧 **Developer Technicalities**

### Quick Setup Options

**Option 1: Single Command (Recommended)**
```bash
python run_convenience.py
```
*Auto-installs dependencies, trains model, starts localhost server*

**Option 2: Manual Setup**
```bash
pip install -r requirements.txt
python generate_dataset.py --radius 1000 --workers 4
python train_model.py
python app.py
```

**Option 3: Docker**
```bash
docker-compose up --build
```

### Technical Architecture

**Core Components:**
- `app.py` - Flask web server with ML integration (localhost:5000)
- `run_convenience.py` - One-command launcher for localhost
- `generate_dataset.py` - OpenStreetMap data extraction
- `train_model.py` - Random Forest model training
- `templates/index.html` - Futuristic web interface

**ML Model:**
- **Algorithm**: Random Forest Regressor
- **Features**: 5 urban indicators (street density, intersections, green space, POIs, network density)
- **Performance**: R² ~0.85, MAE ~8.5
- **Training Data**: 37+ cities across Fertile Crescent region **ONLY**
- **⚠️ Geographic Limitation**: Model only works reliably within Fertile Crescent region

**Data Sources:**
- OpenStreetMap (street networks, POIs, land use)
- Pre-configured city dataset
- Real-time feature extraction

### Project Structure
```
Project Convenience/
├── app.py                 # Main Flask application
├── run_convenience.py     # Single-file runner
├── generate_dataset.py    # OSM data extraction
├── train_model.py         # ML model training
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
├── templates/
│   └── index.html        # Web interface
├── data/
│   ├── cities.csv        # City coordinates
│   └── features.csv      # Extracted features
├── cache/                # OSMnx cache
└── model.pkl            # Trained ML model
```

### Geographic Coverage
**⚠️ CRITICAL LIMITATION**: This model is **ONLY** optimized for the **Fertile Crescent** region:
- 🇱🇧 Lebanon, 🇸🇾 Syria, 🇯🇴 Jordan
- 🇵🇸 Palestine, 🇮🇶 Iraq, 🇹🇷 Turkey

**Locations outside this region will produce random/unreliable predictions** as the model was not trained on data from other geographic areas.

### Configuration
- **OSMnx**: Cache enabled, 180s timeout, 4 workers default
- **Flask**: Production-ready with environment variables
- **Analysis Radius**: 1000m (configurable 500-2000m)

### Development
- **Adding Cities**: Edit `data/cities.csv`
- **Custom Features**: Modify `extract_features()` in `app.py`
- **Model Tuning**: Adjust parameters in `train_model.py`

### Troubleshooting
- **Model Missing**: Run `python train_model.py`
- **Data Missing**: Run `python generate_dataset.py`
- **Dependencies**: Use `python run_convenience.py` for auto-install
- **Port Conflicts**: Change port in `app.py`

---

