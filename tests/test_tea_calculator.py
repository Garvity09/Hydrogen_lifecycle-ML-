import sys
import os
import unittest

# Adjust system path to find src/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../src'))

from tea_calculator import (
    get_learning_rate_multiplier,
    calculate_lcoh_green,
    calculate_lcoh_fossil,
    calculate_alternative_lcoe
)

class TestTEACalculator(unittest.TestCase):

    def test_learning_rate_multiplier(self):
        # Base year (2026) multiplier must be 1.0
        self.assertEqual(get_learning_rate_multiplier(2026, 0.05), 1.0)
        self.assertEqual(get_learning_rate_multiplier(2025, 0.05), 1.0)
        
        # 1 year of 5% learning rate decay
        decay_1yr = get_learning_rate_multiplier(2027, 0.05)
        self.assertAlmostEqual(decay_1yr, 0.95)
        
        # 2 years of 5% learning rate decay (0.95 * 0.95 = 0.9025)
        decay_2yr = get_learning_rate_multiplier(2028, 0.05)
        self.assertAlmostEqual(decay_2yr, 0.9025)

    def test_lcoh_green(self):
        # Base run
        res = calculate_lcoh_green(
            elec_price_mwh=50.0,
            capex_per_kw=1000.0,
            opex_percent=3.0,
            discount_rate=7.0,
            lifetime_years=25,
            efficiency_kwh_kg=53.0,
            capacity_factor=0.45,
            water_cost_m3=2.0,
            carbon_tax=50.0,
            transport_cost_kg=1.0,
            year=2026
        )
        
        self.assertIn("lcoh", res)
        self.assertIn("breakdown", res)
        self.assertIn("emissions_kg_co2", res)
        self.assertGreater(res["lcoh"], 0)
        
        # Verify electricity price sensitivity (if price rises, LCOH must rise)
        res_expensive_elec = calculate_lcoh_green(
            elec_price_mwh=100.0,  # Doubled
            capex_per_kw=1000.0,
            opex_percent=3.0,
            discount_rate=7.0,
            lifetime_years=25,
            efficiency_kwh_kg=53.0,
            capacity_factor=0.45,
            water_cost_m3=2.0,
            carbon_tax=50.0,
            transport_cost_kg=1.0,
            year=2026
        )
        self.assertGreater(res_expensive_elec["lcoh"], res["lcoh"])

    def test_lcoh_fossil(self):
        # SMR Gray
        res_gray = calculate_lcoh_fossil(
            pathway="gray",
            fuel_price_unit=6.0, # $/MMBtu natural gas
            capex_per_kg_annual=3.5,
            opex_percent=4.0,
            discount_rate=7.0,
            lifetime_years=30,
            fuel_req_per_kg=0.16,
            electricity_kwh_kg=0.5,
            electricity_price_mwh=50.0,
            carbon_tax=50.0,
            transport_cost_kg=1.0,
            year=2026
        )
        
        # SMR Blue (with CCS, higher CAPEX, lower emissions/tax)
        res_blue = calculate_lcoh_fossil(
            pathway="blue",
            fuel_price_unit=6.0,
            capex_per_kg_annual=6.0,  # higher capex
            opex_percent=5.0,
            discount_rate=7.0,
            lifetime_years=30,
            fuel_req_per_kg=0.18,  # slightly higher fuel penalty
            electricity_kwh_kg=1.8,  # higher aux power
            electricity_price_mwh=50.0,
            carbon_tax=50.0,
            transport_cost_kg=1.0,
            year=2026
        )
        
        self.assertNotEqual(res_gray["lcoh"], res_blue["lcoh"])
        self.assertEqual(res_gray["emissions_kg_co2"], 10.0)
        self.assertEqual(res_blue["emissions_kg_co2"], 1.5)

    def test_alternative_lcoe(self):
        # Solar LCOE
        res_solar = calculate_alternative_lcoe("solar", 50.0, 50.0, 7.0, 2026)
        self.assertGreater(res_solar["lcoe"], 0)
        
        # Grid LCOE
        res_grid = calculate_alternative_lcoe("grid", 50.0, 50.0, 7.0, 2026)
        self.assertGreater(res_grid["lcoe"], 0)
        
        # Grid must account for carbon tax (emissions = 0.4 tCO2/MWh, tax = 50 $/tCO2 -> +$20 carbon cost)
        # So LCOE should be 50 + 20 = 70
        self.assertEqual(res_grid["lcoe"], 70.0)

if __name__ == "__main__":
    unittest.main()
