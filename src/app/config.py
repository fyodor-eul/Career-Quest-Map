from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    width: int = 900
    height: int = 600
    fps: int = 60

    # Azure OpenAI
    azure_endpoint: str | None = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key: str | None = os.getenv("AZURE_OPENAI_API_KEY")
    azure_api_version: str | None = os.getenv(
        "AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    azure_deployment: str | None = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    # Save file
    save_dir: str = os.path.join(os.getcwd(), "Output")
