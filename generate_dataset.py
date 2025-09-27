# generate_dataset.py (Fertile Crescent, parallel)
import pandas as pd
import numpy as np
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import unary_union
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import time

ox.settings.use_cache = True
ox.settings.timeout = 180

def extract_features(lat, lng, radius):
    try:
        G = ox.graph_from_point((lat,lng), dist=radius, network_type='drive')
        nodes, edges = ox.graph_to_gdfs(G, nodes=True, edges=True)
        if edges.empty:
            area_poly = gpd.GeoSeries([Point(lng,lat).buffer(0.01)], crs="EPSG:4326").iloc[0]
        else:
            try:
                unioned = unary_union(edges.geometry.to_list())
                area_poly = unioned.convex_hull
            except Exception:
                area_poly = Point(lng,lat).buffer(0.01)
        area_km2 = gpd.GeoSeries([area_poly], crs="EPSG:4326").to_crs(3857).area.iloc[0]/1e6

        total_street_m = edges.length.sum()
        street_km_per_km2 = (total_street_m/1000)/max(area_km2,1e-6)

        inters = nodes[nodes['street_count']>1].shape[0] if 'street_count' in nodes.columns else nodes.shape[0]
        inters_per_km2 = inters/max(area_km2,1e-6)

        avg_node_degree = float(np.mean(list(dict(G.degree()).values()))) if len(G)>0 else 0.0

        tags={'amenity':True,'shop':True,'leisure':True,'landuse':True,'natural':True}
        pois = ox.geometries_from_point((lat,lng), tags=tags, dist=radius)
        green_pct = 0.0
        if not pois.empty and 'landuse' in pois.columns:
            greens = pois[pois['landuse'].isin(['park','grass','forest','recreation_ground'])]
            if not greens.empty:
                greens = greens.to_crs(3857)
                green_pct = float((greens.area.sum()/(area_km2*1e6))*100)

        return {
            "street_km_per_km2": float(street_km_per_km2),
            "inters_per_km2": float(inters_per_km2),
            "green_pct": float(green_pct),
            "poi_count_total": int(len(pois)),
            "avg_node_degree": float(avg_node_degree)
        }
    except Exception as e:
        return {"error": str(e)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--radius", type=int, default=1000, help="radius in meters")
    ap.add_argument("--workers", type=int, default=4, help="parallel workers (keep modest to respect Overpass)")
    args = ap.parse_args()

    cities = pd.read_csv("data/cities.csv")
    out_rows = []

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {}
        for _, r in cities.iterrows():
            futures[ex.submit(extract_features, r['lat'], r['lng'], args.radius)] = r
        for fut in as_completed(futures):
            r = futures[fut]
            res = fut.result()
            row = {"name": r['name'], "lat": r['lat'], "lng": r['lng']}
            row.update(res)
            out_rows.append(row)
            print("Done:", r['name'], "->", "OK" if "error" not in res else res["error"])

    df = pd.DataFrame(out_rows)
    df.to_csv("data/features.csv", index=False)
    print(f"Saved data/features.csv with {len(df)} rows in {time.time()-start:.1f}s")

if __name__ == "__main__":
    main()
