import os
import pickle
import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from tea_calculator import (
    calculate_lcoh_green,
    calculate_lcoh_fossil,
    calculate_alternative_lcoe,
    LHV_H2_MWH_KG
)

app = FastAPI(title="Hydrogen Life Cycle Cost Analysis & Future comparison API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class PredictionRequest(BaseModel):
    electricity_price_mwh: float
    natural_gas_price_mmbtu: float
    coal_price_ton: float
    biomass_price_ton: float
    carbon_tax: float
    discount_rate: float
    year: int
    transport_distance_km: float

# Global variables to store models and metadata
models = {}
metadata = {}

@app.on_event("startup")
def load_models_and_metadata():
    global models, metadata
    
    # Load metadata
    metadata_path = "models/model_metadata.json"
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    else:
        print("Warning: model_metadata.json not found. Run training first.")
        
    # Load pickles
    targets = [
        "lcoh_green", "lcoh_blue", "lcoh_gray", "lcoh_brown", "lcoh_biomass",
        "lcoe_alt_gas", "lcoe_alt_coal", "lcoe_alt_diesel", "lcoe_alt_gasoline",
        "lcoe_alt_solar", "lcoe_alt_wind", "lcoe_alt_grid"
    ]
    for target in targets:
        model_path = f"models/model_{target}.pkl"
        if os.path.exists(model_path):
            with open(model_path, "rb") as f:
                models[target] = pickle.load(f)
        else:
            print(f"Warning: Model {model_path} not found. Run training first.")

@app.post("/api/predict")
def predict(req: PredictionRequest):
    # Form feature list for prediction
    features = [[
        req.electricity_price_mwh,
        req.natural_gas_price_mmbtu,
        req.coal_price_ton,
        req.biomass_price_ton,
        req.carbon_tax,
        req.discount_rate,
        req.year,
        req.transport_distance_km
    ]]
    
    # 1. Predict values using ML models if available
    predictions = {}
    for target, model in models.items():
        try:
            pred_val = model.predict(features)[0]
            predictions[target] = float(round(pred_val, 2))
        except Exception as e:
            predictions[target] = None
            
    # 2. Run deterministic calculations to get exact breakdowns
    tc = 0.50 + (0.0006 * req.transport_distance_km)
    
    calc_green = calculate_lcoh_green(
        elec_price_mwh=req.electricity_price_mwh,
        capex_per_kw=1000.0,
        opex_percent=3.0,
        discount_rate=req.discount_rate,
        lifetime_years=25,
        efficiency_kwh_kg=53.0,
        capacity_factor=0.45,
        water_cost_m3=2.0,
        carbon_tax=req.carbon_tax,
        transport_cost_kg=tc,
        year=req.year
    )
    
    calc_blue = calculate_lcoh_fossil(
        pathway="blue",
        fuel_price_unit=req.natural_gas_price_mmbtu,
        capex_per_kg_annual=6.0,
        opex_percent=5.0,
        discount_rate=req.discount_rate,
        lifetime_years=30,
        fuel_req_per_kg=0.18,
        electricity_kwh_kg=1.8,
        electricity_price_mwh=req.electricity_price_mwh,
        carbon_tax=req.carbon_tax,
        transport_cost_kg=tc,
        year=req.year
    )
    
    calc_gray = calculate_lcoh_fossil(
        pathway="gray",
        fuel_price_unit=req.natural_gas_price_mmbtu,
        capex_per_kg_annual=3.5,
        opex_percent=4.0,
        discount_rate=req.discount_rate,
        lifetime_years=30,
        fuel_req_per_kg=0.16,
        electricity_kwh_kg=0.5,
        electricity_price_mwh=req.electricity_price_mwh,
        carbon_tax=req.carbon_tax,
        transport_cost_kg=tc,
        year=req.year
    )
    
    calc_brown = calculate_lcoh_fossil(
        pathway="brown",
        fuel_price_unit=req.coal_price_ton,
        capex_per_kg_annual=8.0,
        opex_percent=6.0,
        discount_rate=req.discount_rate,
        lifetime_years=30,
        fuel_req_per_kg=0.015,
        electricity_kwh_kg=1.0,
        electricity_price_mwh=req.electricity_price_mwh,
        carbon_tax=req.carbon_tax,
        transport_cost_kg=tc,
        year=req.year
    )
    
    calc_biomass = calculate_lcoh_fossil(
        pathway="biomass",
        fuel_price_unit=req.biomass_price_ton,
        capex_per_kg_annual=7.0,
        opex_percent=5.0,
        discount_rate=req.discount_rate,
        lifetime_years=25,
        fuel_req_per_kg=0.018,
        electricity_kwh_kg=0.8,
        electricity_price_mwh=req.electricity_price_mwh,
        carbon_tax=req.carbon_tax,
        transport_cost_kg=tc,
        year=req.year
    )
    
    # Alternatives calculated
    alt_gas = calculate_alternative_lcoe("natural_gas", req.natural_gas_price_mmbtu, req.carbon_tax, req.discount_rate, req.year)
    alt_coal = calculate_alternative_lcoe("coal", req.coal_price_ton, req.carbon_tax, req.discount_rate, req.year)
    alt_diesel = calculate_alternative_lcoe("diesel", 1.20, req.carbon_tax, req.discount_rate, req.year)
    alt_gasoline = calculate_alternative_lcoe("gasoline", 1.10, req.carbon_tax, req.discount_rate, req.year)
    alt_solar = calculate_alternative_lcoe("solar", req.electricity_price_mwh * 0.7, req.carbon_tax, req.discount_rate, req.year)
    alt_wind = calculate_alternative_lcoe("wind", req.electricity_price_mwh * 0.8, req.carbon_tax, req.discount_rate, req.year)
    alt_grid = calculate_alternative_lcoe("grid", req.electricity_price_mwh, req.carbon_tax, req.discount_rate, req.year)
    
    return {
        "predictions": predictions,
        "calculations": {
            "green": calc_green,
            "blue": calc_blue,
            "gray": calc_gray,
            "brown": calc_brown,
            "biomass": calc_biomass,
            "alt_gas": alt_gas,
            "alt_coal": alt_coal,
            "alt_diesel": alt_diesel,
            "alt_gasoline": alt_gasoline,
            "alt_solar": alt_solar,
            "alt_wind": alt_wind,
            "alt_grid": alt_grid
        }
    }

@app.get("/api/metadata")
def get_metadata():
    if not metadata:
        raise HTTPException(status_code=404, detail="Model metadata not loaded.")
    return metadata

@app.get("/api/learning_rates")
def get_learning_rate_projections(elec_price: float = 50.0, gas_price: float = 6.0, carbon_tax: float = 50.0):
    """Generates LCOH trend over time (2026-2050) to demonstrate technology learning effects."""
    years = list(range(2026, 2051, 2))
    tc = 0.50 + (0.0006 * 500.0) # Fixed 500 km transport
    dr = 7.0
    
    green_trend = []
    blue_trend = []
    gray_trend = []
    
    for yr in years:
        g = calculate_lcoh_green(
            elec_price_mwh=elec_price, capex_per_kw=1000.0, opex_percent=3.0,
            discount_rate=dr, lifetime_years=25, efficiency_kwh_kg=53.0,
            capacity_factor=0.45, water_cost_m3=2.0, carbon_tax=carbon_tax,
            transport_cost_kg=tc, year=yr
        )
        b = calculate_lcoh_fossil(
            pathway="blue", fuel_price_unit=gas_price, capex_per_kg_annual=6.0,
            opex_percent=5.0, discount_rate=dr, lifetime_years=30,
            fuel_req_per_kg=0.18, electricity_kwh_kg=1.8,
            electricity_price_mwh=elec_price, carbon_tax=carbon_tax,
            transport_cost_kg=tc, year=yr
        )
        gr = calculate_lcoh_fossil(
            pathway="gray", fuel_price_unit=gas_price, capex_per_kg_annual=3.5,
            opex_percent=4.0, discount_rate=dr, lifetime_years=30,
            fuel_req_per_kg=0.16, electricity_kwh_kg=0.5,
            electricity_price_mwh=elec_price, carbon_tax=carbon_tax,
            transport_cost_kg=tc, year=yr
        )
        green_trend.append(g["lcoh"])
        blue_trend.append(b["lcoh"])
        gray_trend.append(gr["lcoh"])
        
    return {
        "years": years,
        "green": green_trend,
        "blue": blue_trend,
        "gray": gray_trend
    }

# Mount static folder
app.mount("/", StaticFiles(directory="static", html=True), name="static")
