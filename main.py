import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow browser-based cross-origin requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Lowest precedence: hardcoded defaults
config = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# 2. Environment-specific YAML
yaml_path = Path("config.development.yaml")

if yaml_path.exists():
    with yaml_path.open() as f:
        yaml_values = yaml.safe_load(f) or {}

    config.update(yaml_values)

# 3. .env file
load_dotenv()

# 4. OS environment variables
env_to_config = {
    "APP_PORT": "port",
    "NUM_WORKERS": "workers",
    "APP_WORKERS": "workers",
    "APP_DEBUG": "debug",
    "APP_LOG_LEVEL": "log_level",
    "APP_API_KEY": "api_key",
}

for env_name, config_name in env_to_config.items():
    value = os.getenv(env_name)

    if value is not None:
        config[config_name] = value


def coerce(key, value):
    """Convert values into the required types."""
    if key in ("port", "workers"):
        return int(value)

    if key == "debug":
        if isinstance(value, bool):
            return value

        return str(value).strip().lower() in ("true", "1", "yes", "on")

    return str(value)


# Convert all merged values to correct types.
config = {
    key: coerce(key, value)
    for key, value in config.items()
}


@app.get("/effective-config")
def get_effective_config(set: list[str] = Query(default=[])):
    # Copy the merged configuration.
    final_config = dict(config)

    # 5. Highest precedence: ?set=key=value overrides.
    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        key = key.strip()

        if key:
            final_config[key] = coerce(key, value)

    # Always hide the real API key.
    final_config["api_key"] = "****"

    return final_config