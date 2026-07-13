import os
import pickle
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score

# Features and targets
FEATURES = [
    "electricity_price_mwh",
    "natural_gas_price_mmbtu",
    "coal_price_ton",
    "biomass_price_ton",
    "carbon_tax",
    "discount_rate",
    "year",
    "transport_distance_km"
]

TARGETS = [
    "lcoh_green",
    "lcoh_blue",
    "lcoh_gray",
    "lcoh_brown",
    "lcoh_biomass",
    "lcoe_alt_gas",
    "lcoe_alt_coal",
    "lcoe_alt_diesel",
    "lcoe_alt_gasoline",
    "lcoe_alt_solar",
    "lcoe_alt_wind",
    "lcoe_alt_grid"
]

def train_and_evaluate():
    print("Loading scenario dataset...")
    df = pd.read_csv("data/raw_data_scenarios.csv")
    
    X = df[FEATURES]
    
    os.makedirs("models", exist_ok=True)
    
    model_metadata = {}
    
    for target in TARGETS:
        print(f"\n--- Training Model for Target: {target} ---")
        y = df[target]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # We'll use Random Forest to capture interactions and get clean feature importances
        model = RandomForestRegressor(n_estimators=50, max_depth=12, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        
        # Test performance
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"Random Forest - MAE: {mae:.4f}, R2: {r2:.4f}")
        
        # Linear model baseline for comparison
        linear_model = Ridge()
        linear_model.fit(X_train, y_train)
        y_pred_lin = linear_model.predict(X_test)
        mae_lin = mean_absolute_error(y_test, y_pred_lin)
        r2_lin = r2_score(y_test, y_pred_lin)
        print(f"Ridge Baseline - MAE: {mae_lin:.4f}, R2: {r2_lin:.4f}")
        
        # Get feature importances
        importances = model.feature_importances_
        feature_importance_dict = {feat: float(imp) for feat, imp in zip(FEATURES, importances)}
        
        # Sort features by importance
        sorted_importance = dict(sorted(feature_importance_dict.items(), key=lambda item: item[1], reverse=True))
        
        # Save model
        model_path = f"models/model_{target}.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(model, f)
            
        model_metadata[target] = {
            "model_path": model_path,
            "metrics": {
                "mae": float(mae),
                "r2": float(r2),
                "baseline_mae": float(mae_lin),
                "baseline_r2": float(r2_lin)
            },
            "feature_importances": sorted_importance
        }
        
    # Write metadata JSON
    with open("models/model_metadata.json", "w") as f:
        json.dump(model_metadata, f, indent=4)
        
    print("\nAll models trained and saved to models/ directory successfully!")

if __name__ == "__main__":
    train_and_evaluate()
