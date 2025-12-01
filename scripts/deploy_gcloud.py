import os
import json
import subprocess
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
FIREBASE_KEY_FILE = PROJECT_ROOT / "firebase_service_key.json"

def read_env_file():
    """Read .env file and return a dictionary of variables."""
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

def read_firebase_key():
    """Read firebase_service_key.json and return its content as a minified JSON string."""
    if not FIREBASE_KEY_FILE.exists():
        print(f"Error: {FIREBASE_KEY_FILE} not found!")
        return None
    
    try:
        with open(FIREBASE_KEY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return json.dumps(data, separators=(',', ':')) # Minify JSON
    except Exception as e:
        print(f"Error reading firebase key: {e}")
        return None

def run_command(command):
    """Run a shell command."""
    print(f"Running: {command}")
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        sys.exit(1)

def main():
    print("=== BIMO-BE Google Cloud Run Deployer ===")
    
    # 1. Check gcloud
    try:
        subprocess.run("gcloud --version", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Error: 'gcloud' CLI is not installed or not in PATH.")
        sys.exit(1)

    # 2. Read configuration
    env_vars = read_env_file()
    firebase_json = read_firebase_key()
    
    if not firebase_json:
        print("Cannot proceed without Firebase key.")
        sys.exit(1)

    # 3. Prepare environment variables for Cloud Run
    # We need to format them as KEY=VALUE,KEY2=VALUE2
    deploy_env_vars = []
    
    # Add standard env vars from .env
    keys_to_deploy = [
        "GEMINI_API_KEY", 
        "API_SECRET_KEY", 
        "API_TOKEN_ALGORITHM", 
        "API_TOKEN_EXPIRE_MINUTES",
        "GEMINI_MODEL_NAME"
    ]
    
    for key in keys_to_deploy:
        if key in env_vars:
            deploy_env_vars.append(f"{key}={env_vars[key]}")
    
    # Add Firebase JSON
    # Note: We use a special separator for gcloud if needed, but standard comma usually works 
    # if we escape correctly. However, passing complex JSON via command line is risky.
    # A better way for the script is to write a temporary env file or use --set-env-vars with care.
    # Python's subprocess handles arguments better if we don't use shell=True, but gcloud on Windows needs shell=True often.
    
    # Strategy: We will use `gcloud run deploy --set-env-vars ...`
    # But for the huge JSON, it might hit command line length limits or quoting issues.
    
    print("\nPreparing to deploy...")
    service_name = "bimo-be"
    region = "asia-northeast3" # Seoul region
    
    # Construct the command
    # We will build the image first to ensure it's fresh
    # Get Project ID
    try:
        project_id = subprocess.check_output("gcloud config get-value project", shell=True).decode().strip()
        print(f"Target Project: {project_id}")
    except:
        project_id = env_vars.get('GOOGLE_CLOUD_PROJECT', 'bimo-813c3')
        print(f"Using fallback Project ID: {project_id}")

    print("\n[1/2] Building Container Image...")
    run_command(f"gcloud builds submit --tag gcr.io/{project_id}/{service_name} .")
    
    print("\n[2/2] Deploying to Cloud Run...")
    
    # We will use a temporary file for env vars to avoid quoting hell
    # gcloud run deploy supports --env-vars-file
    env_yaml_content = {}
    for key in keys_to_deploy:
        if key in env_vars:
            env_yaml_content[key] = env_vars[key]
    
    env_yaml_content["FIREBASE_CREDENTIALS_JSON"] = firebase_json
    
    env_yaml_path = PROJECT_ROOT / "env_vars.yaml"
    with open(env_yaml_path, "w", encoding="utf-8") as f:
        import yaml
        yaml.dump(env_yaml_content, f)
        
    try:
        cmd = (
            f"gcloud run deploy {service_name} "
            f"--image gcr.io/{project_id}/{service_name} "
            f"--region {region} "
            f"--platform managed "
            f"--allow-unauthenticated "
            f"--env-vars-file env_vars.yaml"
        )
        run_command(cmd)
    finally:
        # Cleanup
        if env_yaml_path.exists():
            os.remove(env_yaml_path)

    print("\n✅ Deployment Complete!")

if __name__ == "__main__":
    main()
