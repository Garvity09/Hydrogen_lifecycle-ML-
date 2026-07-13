import os
import random
import pandas as pd
import numpy as np
from tea_calculator import (
    calculate_lcoh_green,
    calculate_lcoh_fossil,
    calculate_alternative_lcoe
)

def generate_scenarios(num_samples: int = 10000, seed: int = 42) -> pd.DataFrame:
    """Generates synthetic scenarios for techno-economic and ML training."""
    np.random.seed(seed)
    random.seed(seed)
    
    # Range parameters
    elec_prices = np.random.uniform(20.0, 150.0, num_samples)    # $/MWh
    gas_prices = np.random.uniform(2.0, 18.0, num_samples)       # $/MMBtu
    coal_prices = np.random.uniform(30.0, 150.0, num_samples)     # $/ton
    biomass_prices = np.random.uniform(20.0, 120.0, num_samples)  # $/ton
    carbon_taxes = np.random.uniform(0.0, 250.0, num_samples)     # $/tCO2
    discount_rates = np.random.uniform(3.0, 12.0, num_samples)    # %
    years = np.random.randint(2026, 2051, num_samples)            # Year
    distances = np.random.uniform(0.0, 2000.0, num_samples)       # km
    
    records = []
    
    for i in range(num_samples):
        # inputs
        ep = elec_prices[i]
        gp = gas_prices[i]
        cp = coal_prices[i]
        bp = biomass_prices[i]
        ct = carbon_taxes[i]
        dr = discount_rates[i]
        yr = int(years[i])
        dist = distances[i]
        
        # Transport cost calculation ($/kg H2)
        # base processing (compression/cooling/storage) = $0.50/kg
        # transmission = $0.0006 per km per kg
        tc = 0.50 + (0.0006 * dist)
        
        # Calculations
        green = calculate_lcoh_green(
            elec_price_mwh=ep,
            capex_per_kw=1000.0, # PEM base CAPEX
            opex_percent=3.0,
            discount_rate=dr,
            lifetime_years=25,
            efficiency_kwh_kg=53.0,
            capacity_factor=0.45, # Solar/wind hybrid
            water_cost_m3=2.0,
            carbon_tax=ct,
            transport_cost_kg=tc,
            year=yr
        )
        
        blue = calculate_lcoh_fossil(
            pathway="blue",
            fuel_price_unit=gp,
            capex_per_kg_annual=6.0,
            opex_percent=5.0,
            discount_rate=dr,
            lifetime_years=30,
            fuel_req_per_kg=0.18, # MMBtu/kg
            electricity_kwh_kg=1.8,
            electricity_price_mwh=ep,
            carbon_tax=ct,
            transport_cost_kg=tc,
            year=yr
        )
        
        gray = calculate_lcoh_fossil(
            pathway="gray",
            fuel_price_unit=gp,
            capex_per_kg_annual=3.5,
            opex_percent=4.0,
            discount_rate=dr,
            lifetime_years=30,
            fuel_req_per_kg=0.16, # MMBtu/kg
            electricity_kwh_kg=0.5,
            electricity_price_mwh=ep,
            carbon_tax=ct,
            transport_cost_kg=tc,
            year=yr
        )
        
        brown = calculate_lcoh_fossil(
            pathway="brown",
            fuel_price_unit=cp,
            capex_per_kg_annual=8.0,
            opex_percent=6.0,
            discount_rate=dr,
            lifetime_years=30,
            fuel_req_per_kg=0.015, # ton/kg
            electricity_kwh_kg=1.0,
            electricity_price_mwh=ep,
            carbon_tax=ct,
            transport_cost_kg=tc,
            year=yr
        )
        
        biomass = calculate_lcoh_fossil(
            pathway="biomass",
            fuel_price_unit=bp,
            capex_per_kg_annual=7.0,
            opex_percent=5.0,
            discount_rate=dr,
            lifetime_years=25,
            fuel_req_per_kg=0.018, # ton/kg
            electricity_kwh_kg=0.8,
            electricity_price_mwh=ep,
            carbon_tax=ct,
            transport_cost_kg=tc,
            year=yr
        )
        
        # Alternatives LCOE ($/MWh)
        alt_gas = calculate_alternative_lcoe("natural_gas", gp, ct, dr, yr)
        alt_coal = calculate_alternative_lcoe("coal", cp, ct, dr, yr)
        alt_diesel = calculate_alternative_lcoe("diesel", 1.20, ct, dr, yr) # Fixed $1.20/L base
        alt_gasoline = calculate_alternative_lcoe("gasoline", 1.10, ct, dr, yr) # Fixed $1.10/L base
        alt_solar = calculate_alternative_lcoe("solar", ep * 0.7, ct, dr, yr) # Solar is typically cheaper than grid
        alt_wind = calculate_alternative_lcoe("wind", ep * 0.8, ct, dr, yr)
        alt_grid = calculate_alternative_lcoe("grid", ep, ct, dr, yr)
        
        records.append({
            "electricity_price_mwh": ep,
            "natural_gas_price_mmbtu": gp,
            "coal_price_ton": cp,
            "biomass_price_ton": bp,
            "carbon_tax": ct,
            "discount_rate": dr,
            "year": yr,
            "transport_distance_km": dist,
            "transport_cost_kg": tc,
            
            # Outputs: LCOH in $/kg
            "lcoh_green": green["lcoh"],
            "lcoh_blue": blue["lcoh"],
            "lcoh_gray": gray["lcoh"],
            "lcoh_brown": brown["lcoh"],
            "lcoh_biomass": biomass["lcoh"],
            
            # Outputs: LCOE H2 in $/MWh
            "lcoe_h2_green": green["lcoe_mwh"],
            "lcoe_h2_blue": blue["lcoe_mwh"],
            "lcoe_h2_gray": gray["lcoe_mwh"],
            "lcoe_h2_brown": brown["lcoe_mwh"],
            "lcoe_h2_biomass": biomass["lcoe_mwh"],
            
            # Outputs: Emissions in kg CO2/kg H2
            "emissions_green": green["emissions_kg_co2"],
            "emissions_blue": blue["emissions_kg_co2"],
            "emissions_gray": gray["emissions_kg_co2"],
            "emissions_brown": brown["emissions_kg_co2"],
            "emissions_biomass": biomass["emissions_kg_co2"],
            
            # Outputs: Alternatives LCOE ($/MWh)
            "lcoe_alt_gas": alt_gas["lcoe"],
            "lcoe_alt_coal": alt_coal["lcoe"],
            "lcoe_alt_diesel": alt_diesel["lcoe"],
            "lcoe_alt_gasoline": alt_gasoline["lcoe"],
            "lcoe_alt_solar": alt_solar["lcoe"],
            "lcoe_alt_wind": alt_wind["lcoe"],
            "lcoe_alt_grid": alt_grid["lcoe"]
        })
        
    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    print("Generating scenario dataset...")
    os.makedirs("data", exist_ok=True)
    df = generate_scenarios(10000)
    df.to_csv("data/raw_data_scenarios.csv", index=False)
    print(f"Generated {len(df)} scenarios. Saved to data/raw_data_scenarios.csv")
    print(df.head())
