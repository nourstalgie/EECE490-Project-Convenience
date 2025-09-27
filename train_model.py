# train_model.py (you can replace target later with real labels)
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import joblib

df = pd.read_csv("data/features.csv")

# TEMP target construction (replace with real labels when you have them)
df['walkability_score'] = (
    0.5*df['street_km_per_km2'] +
    (df['inters_per_km2']/3) +
    0.2*df['green_pct'] +
    (df['poi_count_total']/50)
).clip(0,100)

X = df[['street_km_per_km2','inters_per_km2','green_pct','poi_count_total','avg_node_degree']]
y = df['walkability_score']

X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.2,random_state=42)
model = RandomForestRegressor(n_estimators=300, random_state=42)
model.fit(X_train,y_train)
y_pred = model.predict(X_test)
print("R^2:", r2_score(y_test,y_pred), "MAE:", mean_absolute_error(y_test,y_pred))

joblib.dump(model,"model.pkl")
print("Saved model.pkl")
