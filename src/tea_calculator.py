import math

# Technical Constants
LHV_H2_KWH_KG = 33.33  # Lower Heating Value of H2 in kWh/kg
LHV_H2_MWH_KG = 0.03333 # Lower Heating Value of H2 in MWh/kg
HHV_H2_KWH_KG = 39.39  # Higher Heating Value of H2 in kWh/kg

# Conversion factors for energy sources to MWh (LHV basis)
MMBTU_TO_MWH = 0.29307  # 1 MMBtu = 0.293 MWh
LITERS_DIESEL_TO_MWH = 0.010    # 1 liter diesel = 10 kWh = 0.01 MWh LHV
LITERS_GASOLINE_TO_MWH = 0.0089  # 1 liter gasoline = 8.9 kWh = 0.0089 MWh LHV
TON_COAL_TO_MWH = 7.0           # 1 ton of coal = 7.0 MWh LHV
TON_BIOMASS_TO_MWH = 4.4        # 1 ton of biomass = 4.4 MWh LHV

# CO2 Emission Intensities (tCO2 / MWh of fuel or electricity)
# Cradle-to-gate / combustion emissions
EMISSIONS_NATURAL_GAS = 0.185 # tCO2 / MWh thermal
EMISSIONS_DIESEL = 0.268      # tCO2 / MWh thermal
EMISSIONS_GASOLINE = 0.249    # tCO2 / MWh thermal
EMISSIONS_COAL = 0.340        # tCO2 / MWh thermal
EMISSIONS_BIOMASS = 0.015     # tCO2 / MWh thermal (biogenic lifecycle)
EMISSIONS_GRID_DEFAULT = 0.400 # tCO2 / MWh electrical (average grid)

# Direct CO2 emissions for H2 production methods (kg CO2 / kg H2 produced)
EMISSIONS_GRAY_H2 = 10.0   # SMR Gray
EMISSIONS_BLUE_H2 = 1.5    # SMR Blue (85% CCS)
EMISSIONS_BROWN_H2 = 20.0  # Coal Gasification Gray
EMISSIONS_BIOMASS_H2 = 1.2 # Biomass Gasification
EMISSIONS_GREEN_H2_EMBEDDED = 0.5 # Solar/Wind manufacturing footprint

def get_learning_rate_multiplier(year: int, learning_rate: float, base_year: int = 2026) -> float:
    """Calculates cost reduction factor based on target year and learning rate."""
    if year <= base_year:
        return 1.0
    return math.pow(1.0 - learning_rate, year - base_year)

def calculate_lcoh_green(
    elec_price_mwh: float,
    capex_per_kw: float,
    opex_percent: float,
    discount_rate: float,
    lifetime_years: int,
    efficiency_kwh_kg: float,
    capacity_factor: float,
    water_cost_m3: float,
    carbon_tax: float,
    transport_cost_kg: float,
    year: int
) -> dict:
    """
    Calculates LCOH for Green Hydrogen (PEM/Alkaline Electrolysis).
    capex_per_kw is adjusted by learning rate.
    """
    # Adjust CAPEX based on tech learning (assume 5% base learning rate)
    learning_mult = get_learning_rate_multiplier(year, 0.045)
    adjusted_capex = capex_per_kw * learning_mult
    
    # Sizing electrolyzer: 1 kg H2 needs efficiency_kwh_kg of electrical energy.
    # Annual production per kW of capacity:
    # 1 kW * 8760 hours * capacity_factor = annual kWh electricity input
    # Annual H2 production (kg) = input / efficiency
    annual_prod_kg = (1.0 * 8760 * capacity_factor) / efficiency_kwh_kg
    
    # CAPEX annualized: PMT formula
    r = discount_rate / 100.0
    if r == 0:
        annualized_capex = adjusted_capex / lifetime_years
    else:
        annualized_capex = adjusted_capex * (r * math.pow(1 + r, lifetime_years)) / (math.pow(1 + r, lifetime_years) - 1)
        
    capex_contribution = annualized_capex / annual_prod_kg
    
    # OPEX: e.g., 3% of CAPEX annually
    annualized_opex = adjusted_capex * (opex_percent / 100.0)
    opex_contribution = annualized_opex / annual_prod_kg
    
    # Electricity cost contribution
    # electricity price in $/MWh -> $/kWh is / 1000.
    elec_contribution = (elec_price_mwh / 1000.0) * efficiency_kwh_kg
    
    # Water cost: 9 kg water needed per kg of H2, water density is 1000 kg/m3.
    # So 0.009 m3 water per kg of H2.
    water_contribution = 0.009 * water_cost_m3
    
    # Carbon tax contribution (Green H2 has minimal embedded footprint, no direct)
    # Carbon tax in $/tCO2 = $/kg CO2 / 1000.
    carbon_tax_contribution = (EMISSIONS_GREEN_H2_EMBEDDED / 1000.0) * carbon_tax
    
    total_lcoh = capex_contribution + opex_contribution + elec_contribution + water_contribution + carbon_tax_contribution + transport_cost_kg
    
    return {
        "lcoh": round(total_lcoh, 2),
        "breakdown": {
            "capex": round(capex_contribution, 2),
            "opex": round(opex_contribution, 2),
            "energy": round(elec_contribution, 2),
            "water": round(water_contribution, 2),
            "carbon_tax": round(carbon_tax_contribution, 2),
            "transport_storage": round(transport_cost_kg, 2)
        },
        "emissions_kg_co2": EMISSIONS_GREEN_H2_EMBEDDED,
        "lcoe_mwh": round(total_lcoh / LHV_H2_MWH_KG, 2)
    }

def calculate_lcoh_fossil(
    pathway: str,  # "blue", "gray", "brown", "biomass"
    fuel_price_unit: float,  # $/MMBtu for gas, $/ton for coal/biomass
    capex_per_kg_annual: float,
    opex_percent: float,
    discount_rate: float,
    lifetime_years: int,
    fuel_req_per_kg: float,  # MMBtu gas/ton coal per kg H2
    electricity_kwh_kg: float,
    electricity_price_mwh: float,
    carbon_tax: float,
    transport_cost_kg: float,
    year: int
) -> dict:
    """
    Calculates LCOH for Gray, Blue, Brown, or Biomass H2.
    - Pathway specific emissions apply.
    - Fuel price is inputted per raw unit.
    """
    learning_rates = {
        "gray": 0.01,
        "blue": 0.02,
        "brown": 0.015,
        "biomass": 0.03
    }
    lr = learning_rates.get(pathway, 0.01)
    learning_mult = get_learning_rate_multiplier(year, lr)
    adjusted_capex = capex_per_kg_annual * learning_mult
    
    r = discount_rate / 100.0
    if r == 0:
        annualized_capex = adjusted_capex / lifetime_years
    else:
        annualized_capex = adjusted_capex * (r * math.pow(1 + r, lifetime_years)) / (math.pow(1 + r, lifetime_years) - 1)
        
    capex_contribution = annualized_capex
    opex_contribution = annualized_capex * (opex_percent / 100.0)
    
    # Fuel cost
    fuel_contribution = fuel_price_unit * fuel_req_per_kg
    
    # Electricity (auxiliary power for pumps, compressors, CCS if applicable)
    elec_contribution = (electricity_price_mwh / 1000.0) * electricity_kwh_kg
    
    # Carbon tax
    emissions_map = {
        "gray": EMISSIONS_GRAY_H2,
        "blue": EMISSIONS_BLUE_H2,
        "brown": EMISSIONS_BROWN_H2,
        "biomass": EMISSIONS_BIOMASS_H2
    }
    emissions_intensity = emissions_map.get(pathway, EMISSIONS_GRAY_H2)
    carbon_tax_contribution = (emissions_intensity / 1000.0) * carbon_tax
    
    total_lcoh = capex_contribution + opex_contribution + fuel_contribution + elec_contribution + carbon_tax_contribution + transport_cost_kg
    
    return {
        "lcoh": round(total_lcoh, 2),
        "breakdown": {
            "capex": round(capex_contribution, 2),
            "opex": round(opex_contribution, 2),
            "energy": round(fuel_contribution + elec_contribution, 2),
            "water": 0.0,
            "carbon_tax": round(carbon_tax_contribution, 2),
            "transport_storage": round(transport_cost_kg, 2)
        },
        "emissions_kg_co2": emissions_intensity,
        "lcoe_mwh": round(total_lcoh / LHV_H2_MWH_KG, 2)
    }

def calculate_alternative_lcoe(
    source: str,  # "natural_gas", "coal", "diesel", "gasoline", "solar", "wind", "grid"
    raw_price: float, # $/MMBtu gas, $/ton coal, $/L diesel/gasoline, $/MWh solar/wind/grid
    carbon_tax: float,
    discount_rate: float,
    year: int
) -> dict:
    """
    Calculates LCOE ($/MWh electrical or thermal) for alternative energy sources.
    Includes combustion/grid emissions and carbon tax.
    """
    # Defaults and tech progress adjustments
    if source == "natural_gas":
        # Convert $/MMBtu to $/MWh thermal
        fuel_cost_mwh_th = raw_price / MMBTU_TO_MWH
        # Boiler/turbine efficiency ~ 90% for thermal heat
        eff = 0.90
        lcoe = fuel_cost_mwh_th / eff
        # OPEX & capital amortized for boiler ~ $3/MWh
        lcoe += 3.0
        emissions = EMISSIONS_NATURAL_GAS / eff
        carbon_cost = emissions * carbon_tax
        total_lcoe = lcoe + carbon_cost
        return {
            "lcoe": round(total_lcoe, 2),
            "emissions": round(emissions * 1000, 1), # kg CO2/MWh
            "breakdown": {"fuel": round(lcoe, 2), "carbon": round(carbon_cost, 2)}
        }
        
    elif source == "coal":
        # Convert $/ton to $/MWh thermal
        fuel_cost_mwh_th = raw_price / TON_COAL_TO_MWH
        eff = 0.85 # Boiler efficiency
        lcoe = fuel_cost_mwh_th / eff
        lcoe += 5.0 # Fixed costs
        emissions = EMISSIONS_COAL / eff
        carbon_cost = emissions * carbon_tax
        total_lcoe = lcoe + carbon_cost
        return {
            "lcoe": round(total_lcoe, 2),
            "emissions": round(emissions * 1000, 1),
            "breakdown": {"fuel": round(lcoe, 2), "carbon": round(carbon_cost, 2)}
        }
        
    elif source in ["diesel", "gasoline"]:
        liters_to_mwh = LITERS_DIESEL_TO_MWH if source == "diesel" else LITERS_GASOLINE_TO_MWH
        fuel_cost_mwh_th = raw_price / liters_to_mwh
        eff = 0.40 # Engine efficiency
        lcoe = fuel_cost_mwh_th / eff
        lcoe += 8.0 # Maintenance
        raw_emissions = EMISSIONS_DIESEL if source == "diesel" else EMISSIONS_GASOLINE
        emissions = raw_emissions / eff
        carbon_cost = emissions * carbon_tax
        total_lcoe = lcoe + carbon_cost
        return {
            "lcoe": round(total_lcoe, 2),
            "emissions": round(emissions * 1000, 1),
            "breakdown": {"fuel": round(lcoe, 2), "carbon": round(carbon_cost, 2)}
        }
        
    elif source in ["solar", "wind"]:
        # Direct LCOE is inputted. Adjust for technology learning curve.
        lr = 0.035 if source == "solar" else 0.02
        learning_mult = get_learning_rate_multiplier(year, lr)
        lcoe = raw_price * learning_mult
        # Negligible operational emissions, embedded footprint ~ 0.015 tCO2/MWh
        emissions = 0.015
        carbon_cost = emissions * carbon_tax
        total_lcoe = lcoe + carbon_cost
        return {
            "lcoe": round(total_lcoe, 2),
            "emissions": round(emissions * 1000, 1),
            "breakdown": {"fuel": round(lcoe, 2), "carbon": round(carbon_cost, 2)}
        }
        
    elif source == "grid":
        # Grid price raw input + average carbon tax
        emissions = EMISSIONS_GRID_DEFAULT
        carbon_cost = emissions * carbon_tax
        total_lcoe = raw_price + carbon_cost
        return {
            "lcoe": round(total_lcoe, 2),
            "emissions": round(emissions * 1000, 1),
            "breakdown": {"fuel": round(raw_price, 2), "carbon": round(carbon_cost, 2)}
        }
        
    return {"lcoe": 0.0, "emissions": 0.0, "breakdown": {"fuel": 0.0, "carbon": 0.0}}
