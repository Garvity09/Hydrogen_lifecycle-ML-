# HydroLCC: Hydrogen Life Cycle Cost (LCC) Analysis & Future Comparison

HydroLCC is an interactive machine learning and techno-economic simulation dashboard designed to analyze the **Levelized Cost of Hydrogen (LCOH)** across multiple production pathways and compare its viability against conventional and renewable energy alternatives up to the year 2050.

---

## 🌟 Key Features

1. **Multi-Pathway Hydrogen Modeling**:
   - **Green H₂** (PEM/Alkaline electrolysis powered by dedicated solar/wind).
   - **Blue H₂** (Steam Methane Reforming + Carbon Capture & Sequestration).
   - **Gray H₂** (Conventional Steam Methane Reforming).
   - **Brown H₂** (Coal Gasification).
   - **Biomass H₂** (Biomass Gasification).
2. **Alternative Energy Source Comparisons**:
   - Levelized Cost of Energy (LCOE, $/MWh LHV basis) for Natural Gas Boilers, Coal Power, Diesel Generators, Gasoline Engines, Solar, Wind, and Grid Electricity.
3. **Machine Learning Predictor**:
   - Random Forest Regression models trained on **10,000 synthetic scenario configurations** (varying electricity tariffs, gas costs, coal prices, carbon taxes, discount rates, technology year, and transport distances).
   - Real-time comparison between deterministic calculated physics models and ML model predictions.
4. **Technology Learning Curves**:
   - Interactive line chart projecting cost curves from **2026 to 2050** to demonstrate Green H₂ cost parity timelines based on electrolyzer CAPEX learning rates.
5. **ML Driver Insights (Feature Importance)**:
   - Evaluates and plots feature importances to highlight the major bottlenecks for each hydrogen production pathway.
6. **Premium Dark Mode Dashboard**:
   - Visualized using Chart.js with responsive range sliders, glassmorphic cards, and dynamic layout.

---

## 📊 Machine Learning Model Performance

The Random Forest Regressors are trained on 10,000 scenarios generated from techno-economic bounds, achieving high predictive accuracy:

| Target Parameter | R² Score | Mean Absolute Error (MAE) |
| :--- | :---: | :---: |
| **Green Hydrogen LCOH** | **99.71%** | $0.087 / kg |
| **Blue Hydrogen LCOH** | **99.08%** | $0.070 / kg |
| **Gray Hydrogen LCOH** | **99.40%** | $0.067 / kg |
| **Brown Hydrogen LCOH** | **99.35%** | $0.101 / kg |
| **Biomass Hydrogen LCOH** | **98.69%** | $0.059 / kg |

---

## 📂 Project Structure

```text
hydrogen-lcc-analysis/
├── data/
│   └── raw_data_scenarios.csv  # 10,000 generated scenarios
├── models/
│   ├── model_*.pkl            # Trained Random Forest regression models
│   └── model_metadata.json    # Model evaluation metrics & feature importances
├── src/
│   ├── tea_calculator.py      # Techno-economic calculations & constants
│   ├── data_generator.py      # Scenario data synthesizer
│   ├── model.py               # Machine learning training pipeline
│   └── server.py              # FastAPI application server
├── static/
│   ├── index.html             # Dashboard frontend HTML
│   ├── style.css              # Custom premium stylesheet
│   └── app.js                 # Javascript controller & Chart.js renderer
├── requirements.txt           # Python library dependencies
└── run.py                     # Root orchestrator script
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Git

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/Garvity09/Hydrogen_lifecycle-ML-.git
cd Hydrogen_lifecycle-ML-
pip install -r requirements.txt
```

### 3. Run the Application
Start the orchestrator script, which will automatically generate the datasets (if missing), train the machine learning models (if missing), and spin up the Uvicorn web server:
```bash
python run.py
```

Open **[http://localhost:8000](http://localhost:8000)** in your browser to interact with the dashboard.

### 4. Run with Docker
Alternatively, you can run the complete project inside a Docker container:
```bash
# Build the image and start the container
docker-compose up --build
```
This containerizes the FastAPI backend and static dashboard, exposing it on port `8000` with volumes to persist datasets and trained models locally.
