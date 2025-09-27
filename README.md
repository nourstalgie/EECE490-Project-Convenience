## 👥 **Contributors**

**Team Members:**
- Adam Yahya
- Yasmina Hanna  
- Nour El Semrani

**Course:** ECE 490 - Ammar Mohanna

---

# Project Convenience 🏪 - AI Location Intelligence Platform

**Project Convenience** is an AI-powered platform that analyzes any location to determine if it's a good spot for opening a convenience store. Simply enter coordinates and get instant, data-driven recommendations with interactive maps.

> **💡 Business Planning Tool**: While this tool focuses on convenience stores, the underlying methodology can be adapted for **any retail business location planning**. This serves as an excellent **starting point** for entrepreneurs and business planners, though many other factors (demographics, competition analysis, market research, etc.) should be considered in real-world business decisions.

---

## 🎯 **Project Scope & Rationale**

### Why Convenience Stores?
This project focuses specifically on **convenience stores** for two key reasons:

1. **Time Limitation**: As an academic project with limited development time, we chose to focus on one specific business type rather than attempting to create a universal solution
2. **Common Business Model**: Convenience stores are ubiquitous across the Fertile Crescent region, making them an ideal case study for location analysis

### Broader Applications
While this tool analyzes convenience store viability, the **core methodology can be adapted** for:
- **Retail businesses** (restaurants, pharmacies, gas stations)
- **Service businesses** (banks, clinics, repair shops)
- **Commercial real estate** evaluation
- **Urban planning** and development

### Important Disclaimer
This tool provides a **data-driven starting point** for business location planning, but real-world business decisions require considering many additional factors:
- **Demographics** and target market analysis
- **Competition** assessment and market saturation
- **Economic indicators** and purchasing power
- **Regulatory** and zoning requirements
- **Accessibility** and transportation patterns
- **Seasonal** and temporal factors

> **⚠️ Use Case**: This is a **proof-of-concept** and **educational tool** designed for the Fertile Crescent region. Always conduct comprehensive market research before making actual business investments.

---

## 👤 **User Guide**

### What Does This Do?
Project Convenience analyzes locations using AI to tell you **YES**, **NO**, or **MAYBE** for opening a convenience store. It looks at:
- How busy the streets are
- How many intersections there are  
- How much green space exists
- How many shops/services are nearby
- How well-connected the area is

> **⚠️ Important**: This model is trained specifically for the **Fertile Crescent region** (Lebanon, Syria, Jordan, Israel/Palestine, Iraq, Turkey). Locations outside this region will produce **random/unreliable results**.

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
- **OpenStreetMap (OSM)**: Primary data source for all geographic information
  - Street networks and road infrastructure
  - Points of Interest (POIs) - shops, restaurants, amenities
  - Land use data (parks, green spaces, commercial areas)
  - Real-time data extraction via Overpass API
- **Pre-configured city dataset**: 37+ cities across Fertile Crescent region
- **Caching system**: OSMnx cache directory stores API responses locally

### 📊 **Dataset Acquisition Process**

**How We Get the Data:**

1. **Initial City Dataset** (`data/cities.csv`):
   - Contains 37+ cities across the Fertile Crescent region
   - Each city has: name, latitude, longitude coordinates
   - Covers Lebanon, Syria, Jordan, Israel/Palestine, Iraq, and Turkey
   - Manually curated to ensure geographic diversity

2. **Feature Extraction** (`generate_dataset.py`):
   - **OSMnx Library**: Connects to OpenStreetMap's Overpass API
   - **Street Network Analysis**: Downloads road networks within 1000m radius
   - **POI Collection**: Extracts amenities, shops, leisure facilities, land use
   - **Parallel Processing**: Uses ThreadPoolExecutor for efficient data gathering
   - **Error Handling**: Graceful fallbacks when API calls fail

3. **Data Processing Pipeline**:
   ```
   Cities CSV → OSMnx API Calls → Feature Extraction → Features CSV
   ```
   - **Input**: City coordinates from `data/cities.csv`
   - **Processing**: Real-time API calls to OpenStreetMap
   - **Output**: Processed features saved to `data/features.csv`

4. **Caching System** (`cache/` directory):
   - **OSMnx Cache**: Stores API responses locally (88+ cached files)
   - **Performance**: Avoids repeated API calls for same locations
   - **Reliability**: Works offline after initial data collection

**Data Features Extracted:**
- `street_km_per_km2`: Street density per square kilometer
- `inters_per_km2`: Intersection density per square kilometer  
- `green_pct`: Percentage of green space in the area
- `poi_count_total`: Total number of points of interest
- `avg_node_degree`: Average connectivity of road network nodes

**API Usage:**
- **Overpass API**: OpenStreetMap's query service
- **Rate Limiting**: Respects OSM's usage policies (modest worker count)
- **Timeout**: 180-second timeout for large queries
- **Fallback Methods**: Multiple POI extraction strategies for reliability

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
- 🇮🇱 Israel/Palestine, 🇮🇶 Iraq, 🇹🇷 Turkey

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

