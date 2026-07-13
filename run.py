import os
import sys
import uvicorn

# Add src/ to system path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def main():
    print("====================================================")
    print("Starting HydroLCC Setup and Launch")
    print("====================================================")
    
    # Step 1: Ensure dataset is generated
    dataset_path = "data/raw_data_scenarios.csv"
    if not os.path.exists(dataset_path):
        print("Raw scenario data not found. Triggering data generator...")
        from data_generator import generate_scenarios
        df = generate_scenarios(10000)
        os.makedirs("data", exist_ok=True)
        df.to_csv(dataset_path, index=False)
        print("Successfully generated 10,000 scenario dataset.")
    else:
        print("Raw scenario data found.")
        
    # Step 2: Ensure models are trained
    metadata_path = "models/model_metadata.json"
    if not os.path.exists(metadata_path):
        print("Trained models not found. Triggering training pipeline...")
        from model import train_and_evaluate
        train_and_evaluate()
        print("Successfully trained and saved all models.")
    else:
        print("Trained models and metadata found.")
        
    # Step 3: Run FastAPI server
    print("\nLaunching Uvicorn server on http://localhost:8000...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
