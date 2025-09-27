from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import unary_union
import folium
import joblib
import re
import json
import io
import base64
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

# Load the trained model
try:
    model = joblib.load('model.pkl')
    print("Model loaded successfully")
except FileNotFoundError:
    print("Model not found. Please run train_model.py first.")
    model = None

# Configure OSMnx
ox.settings.use_cache = True
ox.settings.timeout = 180


def extract_features_with_pois(lat, lng, radius=1000):
    """Extract urban features and return both features and POIs data"""
    try:
        # Get street network
        G = ox.graph_from_point((lat, lng), dist=radius, network_type='drive')
        nodes, edges = ox.graph_to_gdfs(G, nodes=True, edges=True)
        
        if edges.empty:
            area_poly = gpd.GeoSeries([Point(lng, lat).buffer(0.01)], crs="EPSG:4326").iloc[0]
        else:
            try:
                unioned = unary_union(edges.geometry.to_list())
                area_poly = unioned.convex_hull
            except Exception:
                area_poly = Point(lng, lat).buffer(0.01)
        
        area_km2 = gpd.GeoSeries([area_poly], crs="EPSG:4326").to_crs(3857).area.iloc[0]/1e6
        
        # Calculate street density
        total_street_m = edges.length.sum()
        street_km_per_km2 = (total_street_m/1000)/max(area_km2, 1e-6)
        
        # Calculate intersection density
        inters = nodes[nodes['street_count']>1].shape[0] if 'street_count' in nodes.columns else nodes.shape[0]
        inters_per_km2 = inters/max(area_km2, 1e-6)
        
        # Calculate average node degree
        avg_node_degree = float(np.mean(list(dict(G.degree()).values()))) if len(G) > 0 else 0.0
        
        # Get points of interest - try multiple methods
        pois = gpd.GeoDataFrame()
        try:
            # Try pois_from_point first
            pois = ox.pois_from_point((lat, lng), tags={'amenity': True, 'shop': True, 'leisure': True, 'landuse': True, 'natural': True}, dist=radius)
            print(f"Found {len(pois)} POIs using pois_from_point")
        except Exception as e1:
            print(f"pois_from_point failed: {e1}")
            try:
                # Try geometries_from_point as fallback
                pois = ox.geometries_from_point((lat, lng), tags={'amenity': True, 'shop': True, 'leisure': True, 'landuse': True, 'natural': True}, dist=radius)
                print(f"Found {len(pois)} POIs using geometries_from_point")
            except Exception as e2:
                print(f"geometries_from_point failed: {e2}")
                # Create empty GeoDataFrame if both fail
                pois = gpd.GeoDataFrame()
        
        # Calculate green space percentage
        green_pct = 0.0
        if not pois.empty and 'landuse' in pois.columns:
            greens = pois[pois['landuse'].isin(['park', 'grass', 'forest', 'recreation_ground'])]
            if not greens.empty:
                greens = greens.to_crs(3857)
                green_pct = float((greens.area.sum()/(area_km2*1e6))*100)
        
        features = {
            "street_km_per_km2": float(street_km_per_km2),
            "inters_per_km2": float(inters_per_km2),
            "green_pct": float(green_pct),
            "poi_count_total": int(len(pois)),
            "avg_node_degree": float(avg_node_degree),
            "area_km2": float(area_km2)
        }
        
        return features, pois
    except Exception as e:
        return {"error": str(e)}, gpd.GeoDataFrame()

def extract_features(lat, lng, radius=1000):
    """Extract urban features for the given location"""
    try:
        # Get street network
        G = ox.graph_from_point((lat, lng), dist=radius, network_type='drive')
        nodes, edges = ox.graph_to_gdfs(G, nodes=True, edges=True)
        
        if edges.empty:
            area_poly = gpd.GeoSeries([Point(lng, lat).buffer(0.01)], crs="EPSG:4326").iloc[0]
        else:
            try:
                unioned = unary_union(edges.geometry.to_list())
                area_poly = unioned.convex_hull
            except Exception:
                area_poly = Point(lng, lat).buffer(0.01)
        
        area_km2 = gpd.GeoSeries([area_poly], crs="EPSG:4326").to_crs(3857).area.iloc[0]/1e6
        
        # Calculate street density
        total_street_m = edges.length.sum()
        street_km_per_km2 = (total_street_m/1000)/max(area_km2, 1e-6)
        
        # Calculate intersection density
        inters = nodes[nodes['street_count']>1].shape[0] if 'street_count' in nodes.columns else nodes.shape[0]
        inters_per_km2 = inters/max(area_km2, 1e-6)
        
        # Calculate average node degree
        avg_node_degree = float(np.mean(list(dict(G.degree()).values()))) if len(G) > 0 else 0.0
        
        # Get points of interest - use pois_from_point which is more widely available
        try:
            pois = ox.pois_from_point((lat, lng), tags={'amenity': True, 'shop': True, 'leisure': True, 'landuse': True, 'natural': True}, dist=radius)
        except Exception as e:
            print(f"POI extraction failed: {e}")
            # Create empty GeoDataFrame if POI extraction fails
            pois = gpd.GeoDataFrame()
        
        # Calculate green space percentage
        green_pct = 0.0
        if not pois.empty and 'landuse' in pois.columns:
            greens = pois[pois['landuse'].isin(['park', 'grass', 'forest', 'recreation_ground'])]
            if not greens.empty:
                greens = greens.to_crs(3857)
                green_pct = float((greens.area.sum()/(area_km2*1e6))*100)
        
        return {
            "street_km_per_km2": float(street_km_per_km2),
            "inters_per_km2": float(inters_per_km2),
            "green_pct": float(green_pct),
            "poi_count_total": int(len(pois)),
            "avg_node_degree": float(avg_node_degree),
            "area_km2": float(area_km2)
        }
    except Exception as e:
        return {"error": str(e)}

def predict_convenience_store_viability(features):
    """Predict convenience store viability using the trained model"""
    if model is None:
        return None, "Model not available"
    
    try:
        # Prepare features for prediction
        feature_vector = np.array([
            features['street_km_per_km2'],
            features['inters_per_km2'],
            features['green_pct'],
            features['poi_count_total'],
            features['avg_node_degree']
        ]).reshape(1, -1)
        
        # Get walkability score
        walkability_score = model.predict(feature_vector)[0]
        
        # Convert to convenience store viability (0-100 scale)
        # Higher walkability = better for convenience stores
        viability_score = min(100, max(0, walkability_score))
        
        # Determine recommendation
        if viability_score >= 70:
            recommendation = "YES - Excellent location for convenience store"
            confidence = "High"
        elif viability_score >= 50:
            recommendation = "YES - Good location for convenience store"
            confidence = "Medium"
        elif viability_score >= 30:
            recommendation = "MAYBE - Consider other factors"
            confidence = "Low"
        else:
            recommendation = "NO - Not recommended for convenience store"
            confidence = "High"
        
        return {
            "viability_score": round(viability_score, 1),
            "walkability_score": round(walkability_score, 1),
            "recommendation": recommendation,
            "confidence": confidence
        }, None
    except Exception as e:
        return None, str(e)

def create_landmark_map(lat, lng, features, prediction, pois):
    """Create an interactive map showing ML model features"""
    # Create base map
    m = folium.Map(
        location=[lat, lng],
        zoom_start=15,
        tiles='OpenStreetMap'
    )
    
    # Add the analyzed location marker
    folium.Marker(
        [lat, lng],
        popup=f"""
        <div style="font-family: 'Segoe UI', sans-serif;">
            <h3>📍 Analysis Location</h3>
            <p><strong>Coordinates:</strong> {lat:.6f}, {lng:.6f}</p>
            <p><strong>Viability Score:</strong> {prediction['viability_score']}/100</p>
            <p><strong>Recommendation:</strong> {prediction['recommendation']}</p>
            <p><strong>Confidence:</strong> {prediction['confidence']}</p>
        </div>
        """,
        tooltip="Analysis Location",
        icon=folium.Icon(color='red', icon='store', prefix='fa')
    ).add_to(m)
    
    # Define business categories relevant to convenience stores
    business_categories = {
        'convenience_store': {'color': 'red', 'icon': 'store', 'name': 'Convenience Stores'},
        'supermarket': {'color': 'darkgreen', 'icon': 'shopping-cart', 'name': 'Supermarkets'},
        'gas_station': {'color': 'orange', 'icon': 'gas-pump', 'name': 'Gas Stations'},
        'pharmacy': {'color': 'blue', 'icon': 'pills', 'name': 'Pharmacies'},
        'restaurant': {'color': 'purple', 'icon': 'utensils', 'name': 'Restaurants'},
        'cafe': {'color': 'brown', 'icon': 'coffee', 'name': 'Cafes'},
        'bank': {'color': 'green', 'icon': 'university', 'name': 'Banks'},
        'atm': {'color': 'lightgreen', 'icon': 'credit-card', 'name': 'ATMs'},
        'other': {'color': 'gray', 'icon': 'map-marker', 'name': 'Other Businesses'}
    }
    
    # Add business-specific markers
    business_counts = {}
    
    if not pois.empty:
        for idx, poi in pois.iterrows():
            if 'geometry' in poi and poi.geometry is not None:
                try:
                    # Get coordinates
                    if hasattr(poi.geometry, 'centroid'):
                        coords = [poi.geometry.centroid.y, poi.geometry.centroid.x]
                    else:
                        coords = [poi.geometry.y, poi.geometry.x]
                    
                    # Categorize based on business type
                    category = 'other'
                    business_type = 'Business'
                    
                    if 'amenity' in poi:
                        amenity = str(poi['amenity']).lower()
                        if 'convenience' in amenity or 'shop' in amenity:
                            category = 'convenience_store'
                            business_type = 'Convenience Store'
                        elif 'supermarket' in amenity or 'market' in amenity:
                            category = 'supermarket'
                            business_type = 'Supermarket'
                        elif 'fuel' in amenity or 'gas' in amenity:
                            category = 'gas_station'
                            business_type = 'Gas Station'
                        elif 'pharmacy' in amenity or 'chemist' in amenity:
                            category = 'pharmacy'
                            business_type = 'Pharmacy'
                        elif 'restaurant' in amenity:
                            category = 'restaurant'
                            business_type = 'Restaurant'
                        elif 'cafe' in amenity or 'coffee' in amenity:
                            category = 'cafe'
                            business_type = 'Cafe'
                        elif 'bank' in amenity:
                            category = 'bank'
                            business_type = 'Bank'
                        elif 'atm' in amenity:
                            category = 'atm'
                            business_type = 'ATM'
                    elif 'shop' in poi:
                        shop_type = str(poi['shop']).lower()
                        if 'convenience' in shop_type:
                            category = 'convenience_store'
                            business_type = 'Convenience Store'
                        elif 'supermarket' in shop_type:
                            category = 'supermarket'
                            business_type = 'Supermarket'
                        elif 'pharmacy' in shop_type:
                            category = 'pharmacy'
                            business_type = 'Pharmacy'
                        else:
                            category = 'other'
                            business_type = 'Shop'
                    
                    # Count businesses
                    business_counts[category] = business_counts.get(category, 0) + 1
                    
                    # Add marker with business context
                    folium.Marker(
                        coords,
                        popup=f"""
                        <div style="font-family: 'Segoe UI', sans-serif;">
                            <h4>🏪 {business_type}</h4>
                            <p><strong>Business Type:</strong> {business_categories[category]['name']}</p>
                            <p><strong>Category:</strong> {poi.get('amenity', poi.get('shop', 'Unknown'))}</p>
                            <p><strong>Name:</strong> {poi.get('name', 'Unnamed')}</p>
                            <hr>
                            <p><strong>Competition Level:</strong> {'High' if category in ['convenience_store', 'supermarket'] else 'Medium' if category in ['gas_station', 'pharmacy'] else 'Low'}</p>
                        </div>
                        """,
                        tooltip=f"{business_type}",
                        icon=folium.Icon(
                            color=business_categories[category]['color'],
                            icon=business_categories[category]['icon'],
                            prefix='fa'
                        )
                    ).add_to(m)
                except Exception as e:
                    print(f"Error adding marker: {e}")
                    continue
    
    # Add Business Competition Legend
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 300px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 15px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.3)">
    <h4 style="margin-top:0px; color: #333; text-align: center;">🏪 Business Competition</h4>
    <hr style="margin: 10px 0;">
    """
    
    # Add each business type with counts and competition level
    for category, config in business_categories.items():
        count = business_counts.get(category, 0)
        if count > 0:  # Only show categories that exist
            color = config['color']
            icon = config['icon']
            name = config['name']
            
            # Determine competition level
            if category in ['convenience_store', 'supermarket']:
                competition = '🔴 High Competition'
            elif category in ['gas_station', 'pharmacy']:
                competition = '🟡 Medium Competition'
            else:
                competition = '🟢 Low Competition'
            
            legend_html += f"""
            <p><i class="fa fa-{icon}" style="color:{color};"></i> 
               <strong>{name}:</strong> {count}</p>
            <p style="margin-left: 20px; font-size: 10px; color: #666;">{competition}</p>
            """
    
    legend_html += f"""
    <hr style="margin: 10px 0;">
    <p><i class="fa fa-store" style="color:red;"></i> <strong>Your Location</strong></p>
    <p style="margin-left: 20px; font-size: 10px; color: #666;">Viability Score: {prediction['viability_score']}/100</p>
    <p style="margin-left: 20px; font-size: 10px; color: #666;">Recommendation: {prediction['recommendation']}</p>
    </div>
    """
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_location():
    try:
        # Get JSON data
        data = request.get_json()
        
        # Get coordinates
        lat = data.get('lat')
        lng = data.get('lng')
        
        if lat is None or lng is None:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        try:
            lat = float(lat)
            lng = float(lng)
            print(f"Analyzing coordinates: {lat}, {lng}")
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid coordinates provided'}), 400
        
        # Extract features
        features, pois = extract_features_with_pois(lat, lng)
        
        if 'error' in features:
            return jsonify({'error': f'Feature extraction failed: {features["error"]}'}), 500
        
        # Predict convenience store viability
        prediction, error = predict_convenience_store_viability(features)
        
        if error:
            return jsonify({'error': f'Prediction failed: {error}'}), 500
        
        # Create landmark map
        landmark_map = create_landmark_map(lat, lng, features, prediction, pois)
        
        # Convert map to HTML string
        map_html = landmark_map._repr_html_()
        
        return jsonify({
            'success': True,
            'coordinates': {'lat': lat, 'lng': lng},
            'features': features,
            'prediction': prediction,
            'map_html': map_html
        })
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'model_loaded': model is not None})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)