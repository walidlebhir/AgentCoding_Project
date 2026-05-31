import os
import zipfile
import tempfile
from pathlib import Path
from cli_agent.core.client import ApiClient
from cli_agent.utils.logger import info, success, error, step, header


def handle(client: ApiClient, prompt: str, output_dir: str | None):
    header("SpringForge — Generate")

    info(f"Prompt: {prompt}")

    result = client.generate(prompt)

    if not result.get("success"):
        error(f"Generation failed: {result.get('message', 'Unknown error')}")
        return False

    project_id = result["project_id"]
    provider = result.get("provider", "?")
    files = result.get("files_generated", 0)
    calls = result.get("llm_calls", 0)

    success(f"Project {project_id} generated")
    info(f"  Provider : {provider}")
    info(f"  Files    : {files}")
    info(f"  LLM calls: {calls}")

    if result.get("cached"):
        info("  (served from cache)")

    download_url = result.get("download_url")
    if download_url:
        dest_dir = output_dir or os.getcwd()
        zip_path = os.path.join(dest_dir, f"{project_id}.zip")
        step(f"Downloading to {zip_path}")
        if client.download_zip(project_id, zip_path):
            success(f"Saved: {zip_path}")
            _extract_and_cleanup(zip_path, dest_dir)
        else:
            info(f"Download URL: {download_url}")
    else:
        info(f"Download URL: {result.get('download_url', 'N/A')}")

    return True


def _extract_and_cleanup(zip_path: str, dest_dir: str):
    import shutil
    extract_dir = os.path.join(dest_dir, Path(zip_path).stem)
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
    os.remove(zip_path)
    success(f"Extracted to: {extract_dir}")
