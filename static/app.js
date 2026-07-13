// Global chart variables
let chartLcohCompare = null;
let chartLcohBreakdown = null;
let chartLcoeCompare = null;
let chartLearningRate = null;
let chartFeatureImportance = null;

// Global metadata cache for ML insights
let mlMetadata = null;

// Debounce timer for slider inputs
let inputTimer = null;

// Server URL (defaults to current window location)
const API_BASE = window.location.origin;

document.addEventListener("DOMContentLoaded", () => {
    // Register slider listeners
    const sliders = [
        "year", "elec", "gas", "coal", "biomass", "tax", "dr", "dist"
    ];
    
    sliders.forEach(sliderId => {
        const input = document.getElementById(`input-${sliderId}`);
        input.addEventListener("input", (e) => {
            // Update the text label dynamically
            updateLabel(sliderId, e.target.value);
            
            // Debounce API requests
            clearTimeout(inputTimer);
            inputTimer = setTimeout(() => {
                triggerAnalysis();
            }, 100);
        });
    });

    // Pathway Select for LCOH cost breakdown chart
    document.getElementById("select-breakdown-pathway").addEventListener("change", () => {
        triggerAnalysis(); // Redraw breakdown
    });

    // Target Select for feature importance chart
    document.getElementById("select-importance-target").addEventListener("change", (e) => {
        renderFeatureImportanceChart(e.target.value);
    });

    // Initialize Page
    loadMetadata();
    triggerAnalysis();
});

function updateLabel(id, val) {
    const display = document.getElementById(`val-${id}`);
    if (id === "year") {
        display.innerText = val;
        document.getElementById("badge-year").innerText = val;
    } else if (id === "elec") {
        display.innerText = `$${val}`;
    } else if (id === "gas") {
        display.innerText = `$${parseFloat(val).toFixed(1)}`;
    } else if (id === "coal" || id === "biomass") {
        display.innerText = `$${val}`;
    } else if (id === "tax") {
        display.innerText = `$${val}`;
    } else if (id === "dr") {
        display.innerText = `${parseFloat(val).toFixed(1)}%`;
    } else if (id === "dist") {
        display.innerText = `${val} km`;
    }
}

// Fetch ML metadata and populate performance tables on page load
async function loadMetadata() {
    try {
        const response = await fetch(`${API_BASE}/api/metadata`);
        if (!response.ok) throw new Error("Metadata request failed");
        
        mlMetadata = await response.json();
        
        // Populate HTML Table
        const tbody = document.getElementById("metrics-table-body");
        tbody.innerHTML = ""; // Clear loader
        
        const friendlyNames = {
            "lcoh_green": "Green Hydrogen LCOH",
            "lcoh_blue": "Blue Hydrogen LCOH",
            "lcoh_gray": "Gray Hydrogen LCOH",
            "lcoh_brown": "Brown Hydrogen LCOH",
            "lcoh_biomass": "Biomass Hydrogen LCOH",
            "lcoe_alt_gas": "Natural Gas LCOE",
            "lcoe_alt_coal": "Coal Power LCOE",
            "lcoe_alt_diesel": "Diesel Generator LCOE",
            "lcoe_alt_gasoline": "Gasoline Engine LCOE",
            "lcoe_alt_solar": "Utility Solar LCOE",
            "lcoe_alt_wind": "Utility Wind LCOE",
            "lcoe_alt_grid": "Grid Electricity"
        };
        
        // Show primary H2 metrics
        const h2Keys = ["lcoh_green", "lcoh_blue", "lcoh_gray", "lcoh_brown", "lcoh_biomass"];
        h2Keys.forEach(key => {
            if (mlMetadata[key]) {
                const data = mlMetadata[key];
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><strong>${friendlyNames[key]}</strong></td>
                    <td><span class="r2-badge">${(data.metrics.r2 * 100).toFixed(2)}%</span></td>
                    <td>$${data.metrics.mae.toFixed(3)}/kg</td>
                `;
                tbody.appendChild(tr);
            }
        });
        
        // Render default feature importance chart
        renderFeatureImportanceChart("lcoh_green");
        
    } catch (err) {
        console.error("Failed to load metadata:", err);
        document.getElementById("metrics-table-body").innerHTML = 
            `<tr><td colspan="3" style="color: var(--color-red);"><i class="fa-solid fa-triangle-exclamation"></i> Error loading ML metrics.</td></tr>`;
    }
}

// Triggers predictions and calculations
async function triggerAnalysis() {
    const payload = {
        electricity_price_mwh: parseFloat(document.getElementById("input-elec").value),
        natural_gas_price_mmbtu: parseFloat(document.getElementById("input-gas").value),
        coal_price_ton: parseFloat(document.getElementById("input-coal").value),
        biomass_price_ton: parseFloat(document.getElementById("input-biomass").value),
        carbon_tax: parseFloat(document.getElementById("input-tax").value),
        discount_rate: parseFloat(document.getElementById("input-dr").value),
        year: parseInt(document.getElementById("input-year").value),
        transport_distance_km: parseFloat(document.getElementById("input-dist").value)
    };
    
    try {
        // Post values to get predict + calculate results
        const res = await fetch(`${API_BASE}/api/predict`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        if (!res.ok) throw new Error("Prediction API call failed");
        
        const data = await res.json();
        
        // Update summary cards
        updateSummaryCards(data);
        
        // Render Charts
        renderLcohComparisonChart(data);
        renderLcohBreakdownChart(data);
        renderLcoeComparisonChart(data);
        updateLearningRateChart(payload);
        
    } catch (err) {
        console.error("Analysis execution error:", err);
    }
}

function updateSummaryCards(data) {
    const calc = data.calculations;
    const pred = data.predictions;
    
    // Green
    document.getElementById("card-lcoh-green").innerHTML = `$${calc.green.lcoh.toFixed(2)} <span class="unit">/kg</span>`;
    document.getElementById("ml-green").innerText = pred.lcoh_green ? `ML: $${pred.lcoh_green.toFixed(2)}` : "ML: --";
    document.getElementById("emissions-green").innerText = `${calc.green.emissions_kg_co2} kg CO₂/kg`;
    
    // Blue
    document.getElementById("card-lcoh-blue").innerHTML = `$${calc.blue.lcoh.toFixed(2)} <span class="unit">/kg</span>`;
    document.getElementById("ml-blue").innerText = pred.lcoh_blue ? `ML: $${pred.lcoh_blue.toFixed(2)}` : "ML: --";
    document.getElementById("emissions-blue").innerText = `${calc.blue.emissions_kg_co2} kg CO₂/kg`;
    
    // Gray
    document.getElementById("card-lcoh-gray").innerHTML = `$${calc.gray.lcoh.toFixed(2)} <span class="unit">/kg</span>`;
    document.getElementById("ml-gray").innerText = pred.lcoh_gray ? `ML: $${pred.lcoh_gray.toFixed(2)}` : "ML: --";
    document.getElementById("emissions-gray").innerText = `${calc.gray.emissions_kg_co2} kg CO₂/kg`;
    
    // Find cheapest LCOE fuel (LHV basis)
    const lcoes = [
        { name: "Gas Boiler", value: calc.alt_gas.lcoe },
        { name: "Coal Boiler", value: calc.alt_coal.lcoe },
        { name: "Diesel Engine", value: calc.alt_diesel.lcoe },
        { name: "Gasoline Engine", value: calc.alt_gasoline.lcoe },
        { name: "Utility Solar", value: calc.alt_solar.lcoe },
        { name: "Utility Wind", value: calc.alt_wind.lcoe },
        { name: "Green Hydrogen", value: calc.green.lcoe_mwh },
        { name: "Blue Hydrogen", value: calc.blue.lcoe_mwh }
    ];
    
    lcoes.sort((a, b) => a.value - b.value);
    const cheapest = lcoes[0];
    
    document.getElementById("card-cheapest-val").innerHTML = `$${cheapest.value.toFixed(0)} <span class="unit">/MWh</span>`;
    document.getElementById("card-cheapest-label").innerText = `Primary source: ${cheapest.name}`;
}

// Chart 1: LCOH Comparison (Calculated vs. ML Predicted)
function renderLcohComparisonChart(data) {
    const calc = data.calculations;
    const pred = data.predictions;
    
    const labels = ["Green H₂", "Blue H₂", "Gray H₂", "Brown H₂", "Biomass H₂"];
    const calculatedData = [calc.green.lcoh, calc.blue.lcoh, calc.gray.lcoh, calc.brown.lcoh, calc.biomass.lcoh];
    const predictedData = [pred.lcoh_green, pred.lcoh_blue, pred.lcoh_gray, pred.lcoh_brown, pred.lcoh_biomass];
    
    const ctx = document.getElementById("chart-lcoh-compare").getContext("2d");
    
    if (chartLcohCompare) {
        chartLcohCompare.data.datasets[0].data = calculatedData;
        chartLcohCompare.data.datasets[1].data = predictedData;
        chartLcohCompare.update();
        return;
    }
    
    chartLcohCompare = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Calculated Cost',
                    data: calculatedData,
                    backgroundColor: 'rgba(6, 182, 212, 0.7)',
                    borderColor: '#06b6d4',
                    borderWidth: 1,
                    borderRadius: 6
                },
                {
                    label: 'ML Model Prediction',
                    data: predictedData,
                    backgroundColor: 'rgba(139, 92, 246, 0.7)',
                    borderColor: '#8b5cf6',
                    borderWidth: 1,
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#f3f4f6', font: { family: 'Outfit' } } }
            },
            scales: {
                y: {
                    title: { display: true, text: 'Levelized Cost ($/kg H₂)', color: '#f3f4f6' },
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                },
                x: {
                    ticks: { color: '#9ca3af' },
                    grid: { display: false }
                }
            }
        }
    });
}

// Chart 2: Cost Breakdown Stacked Bar for Selected Pathway
function renderLcohBreakdownChart(data) {
    const selected = document.getElementById("select-breakdown-pathway").value;
    const calc = data.calculations[selected];
    
    const breakdown = calc.breakdown;
    const labels = ["Cost Contribution ($/kg)"];
    
    const ctx = document.getElementById("chart-lcoh-breakdown").getContext("2d");
    
    const datasets = [
        { label: "CAPEX", data: [breakdown.capex], backgroundColor: "#ef4444" },
        { label: "OPEX", data: [breakdown.opex], backgroundColor: "#f97316" },
        { label: "Fuel/Electricity", data: [breakdown.energy], backgroundColor: "#3b82f6" },
        { label: "Water", data: [breakdown.water], backgroundColor: "#38bdf8" },
        { label: "Carbon Tax", data: [breakdown.carbon_tax], backgroundColor: "#10b981" },
        { label: "Transport & Storage", data: [breakdown.transport_storage], backgroundColor: "#8b5cf6" }
    ];
    
    if (chartLcohBreakdown) {
        chartLcohBreakdown.data.datasets.forEach((dataset, idx) => {
            dataset.data = datasets[idx].data;
        });
        chartLcohBreakdown.update();
        return;
    }
    
    chartLcohBreakdown = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#f3f4f6', font: { family: 'Outfit' } } }
            },
            scales: {
                x: {
                    stacked: true,
                    title: { display: true, text: 'Cost ($/kg H₂)', color: '#f3f4f6' },
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                },
                y: {
                    stacked: true,
                    ticks: { display: false },
                    grid: { display: false }
                }
            }
        }
    });
}

// Chart 3: LCOE Comparison ($/MWh LHV basis)
function renderLcoeComparisonChart(data) {
    const calc = data.calculations;
    
    const labels = [
        "Green H₂", "Blue H₂", "Gray H₂", 
        "Solar LCOE", "Wind LCOE", "Grid LCOE",
        "Nat Gas Boiler", "Coal Boiler", "Diesel Engine", "Gasoline Engine"
    ];
    const lcoeValues = [
        calc.green.lcoe_mwh, calc.blue.lcoe_mwh, calc.gray.lcoe_mwh,
        calc.alt_solar.lcoe, calc.alt_wind.lcoe, calc.alt_grid.lcoe,
        calc.alt_gas.lcoe, calc.alt_coal.lcoe, calc.alt_diesel.lcoe, calc.alt_gasoline.lcoe
    ];
    
    const backgroundColors = [
        '#10b981', '#06b6d4', '#6b7280', // H2
        '#eab308', '#a3e635', '#a855f7', // Renewables/Grid
        '#f97316', '#b45309', '#ef4444', '#f87171' // Fossil thermal/power
    ];
    
    const ctx = document.getElementById("chart-lcoe-compare").getContext("2d");
    
    if (chartLcoeCompare) {
        chartLcoeCompare.data.datasets[0].data = lcoeValues;
        chartLcoeCompare.update();
        return;
    }
    
    chartLcoeCompare = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'LCOE ($/MWh LHV Equivalent)',
                data: lcoeValues,
                backgroundColor: backgroundColors,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    title: { display: true, text: 'LCOE ($/MWh)', color: '#f3f4f6' },
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                },
                x: {
                    ticks: { 
                        color: '#9ca3af',
                        font: { size: 9 },
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: { display: false }
                }
            }
        }
    });
}

// Chart 4: Learning curves over time projection (2026-2050)
async function updateLearningRateChart(payload) {
    try {
        const url = `${API_BASE}/api/learning_rates?elec_price=${payload.electricity_price_mwh}&gas_price=${payload.natural_gas_price_mmbtu}&carbon_tax=${payload.carbon_tax}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error("Failed to fetch learning rate projections");
        
        const data = await response.json();
        const ctx = document.getElementById("chart-learning-rate").getContext("2d");
        
        if (chartLearningRate) {
            chartLearningRate.data.labels = data.years;
            chartLearningRate.data.datasets[0].data = data.green;
            chartLearningRate.data.datasets[1].data = data.blue;
            chartLearningRate.data.datasets[2].data = data.gray;
            chartLearningRate.update();
            return;
        }
        
        chartLearningRate = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.years,
                datasets: [
                    {
                        label: 'Green H₂ LCOH',
                        data: data.green,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: false,
                        tension: 0.1,
                        borderWidth: 3
                    },
                    {
                        label: 'Blue H₂ LCOH',
                        data: data.blue,
                        borderColor: '#06b6d4',
                        backgroundColor: 'rgba(6, 182, 212, 0.1)',
                        fill: false,
                        tension: 0.1,
                        borderWidth: 3
                    },
                    {
                        label: 'Gray H₂ LCOH',
                        data: data.gray,
                        borderColor: '#8a99ad',
                        backgroundColor: 'rgba(138, 153, 173, 0.1)',
                        fill: false,
                        tension: 0.1,
                        borderWidth: 3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#f3f4f6', font: { family: 'Outfit' } } }
                },
                scales: {
                    y: {
                        title: { display: true, text: 'LCOH ($/kg H₂)', color: '#f3f4f6' },
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    x: {
                        ticks: { color: '#9ca3af' },
                        grid: { display: false }
                    }
                }
            }
        });
    } catch (err) {
        console.error("Learning curve projection update error:", err);
    }
}

// Chart 5: Feature Importance Horizontal Bar Chart
function renderFeatureImportanceChart(target) {
    if (!mlMetadata || !mlMetadata[target]) return;
    
    const importanceData = mlMetadata[target].feature_importances;
    
    // Translate features to friendly names
    const featureNameMap = {
        "electricity_price_mwh": "Electricity Tariff",
        "natural_gas_price_mmbtu": "Natural Gas Cost",
        "coal_price_ton": "Coal Feedstock",
        "biomass_price_ton": "Biomass Feedstock",
        "carbon_tax": "Carbon Tax Policy",
        "discount_rate": "Capital Cost (WACC)",
        "year": "Tech Learning Rate (Year)",
        "transport_distance_km": "Logistics & Transport"
    };
    
    const labels = Object.keys(importanceData).map(key => featureNameMap[key] || key);
    const values = Object.values(importanceData);
    
    const ctx = document.getElementById("chart-feature-importance").getContext("2d");
    
    if (chartFeatureImportance) {
        chartFeatureImportance.data.labels = labels;
        chartFeatureImportance.data.datasets[0].data = values;
        chartFeatureImportance.update();
        return;
    }
    
    chartFeatureImportance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Relative Driver Importance',
                data: values,
                backgroundColor: 'rgba(99, 102, 241, 0.75)',
                borderColor: '#6366f1',
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Importance Weight (0.0 to 1.0)', color: '#f3f4f6' },
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                },
                y: {
                    ticks: { color: '#9ca3af', font: { size: 10 } },
                    grid: { display: false }
                }
            }
        }
    });
}
