import os
import subprocess
import sys
import uvicorn

def main():
    print("====================================================")
    print("Starting HydroLCC Setup and Launch")
    print("====================================================")
    
    # Step 1: Ensure dataset is generated
    dataset_path = "data/raw_data_scenarios.csv"
    if not os.path.exists(dataset_path):
        print("Raw scenario data not found. Triggering data generator...")
        # Since uvicorn runs within the python env, we can import and run directly
        # or use subprocess. Let's run it.
        try:
            from data_generator import generate_scenarios
            df = generate_scenarios(10000)
            os.makedirs("data", exist_ok=True)
            df.to_csv(dataset_path, index=False)
            print("Successfully generated 10,000 scenario dataset.")
        except Exception as e:
            print(f"Error generating data inline: {e}. Trying via script call...")
            subprocess.run([sys.executable, "src/data_generator.py"], check=True)
    else:
        print("Raw scenario data found.")
        
    # Step 2: Ensure models are trained
    metadata_path = "models/model_metadata.json"
    if not os.path.exists(metadata_path):
        print("Trained models not found. Triggering training pipeline...")
        try:
            from model import train_and_evaluate
            train_and_evaluate()
            print("Successfully trained and saved all models.")
        except Exception as e:
            print(f"Error training inline: {e}. Trying via script call...")
            subprocess.run([sys.executable, "src/model.py"], check=True)
    else:
        print("Trained models and metadata found.")
        
    # Step 3: Run FastAPI server
    print("\nLaunching Uvicorn server on http://localhost:8000...")
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    
    # Import FastAPI app from server
    # Uvicorn run
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
