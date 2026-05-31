import os
import zipfile
import tempfile
from pathlib import Path
from springforge_cli.core.client import ApiClient
from springforge_cli.core.parser import parse_llm_response, parse_diff_response
from springforge_cli.utils.logger import info, success, error, step, warn


class Agent:
    def __init__(self, client: ApiClient):
        self.client = client

    def generate(self, prompt: str, output_dir: str | None = None) -> bool:
        info(f"Prompt: {prompt}")
        result = self.client.generate(prompt)
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
            if self.client.download_zip(project_id, zip_path):
                success(f"Saved: {zip_path}")
                self._extract_and_cleanup(zip_path, dest_dir)
            else:
                info(f"Download URL: {download_url}")
        else:
            info(f"Download URL: {result.get('download_url', 'N/A')}")
        return True

    def edit(self, project_path: str, prompt: str) -> bool:
        abs_path = os.path.abspath(project_path)
        if not os.path.isdir(abs_path):
            error(f"Project path not found: {abs_path}")
            return False
        info(f"Project : {abs_path}")
        info(f"Request : {prompt}")
        result = self.client.edit(abs_path, prompt)
        if not result.get("success"):
            warn(f"Edit failed: {result.get('message', 'Unknown error')}")
            return False
        success("Project modified successfully")
        changes = result.get("changes", [])
        for c in changes:
            info(f"  {c}")
        return True

    def add(self, feature: str, project_path: str | None = None) -> bool:
        if not project_path:
            project_path = os.getcwd()
        abs_path = os.path.abspath(project_path)
        if not os.path.isdir(abs_path):
            error(f"Project path not found: {abs_path}")
            return False
        info(f"Project : {abs_path}")
        info(f"Feature : {feature}")
        prompt = f"Add the following feature to the existing Spring Boot project: {feature}"
        result = self.client.add(abs_path, prompt)
        if not result.get("success"):
            warn(f"Add feature failed: {result.get('message', 'Unknown error')}")
            return False
        success(f"Feature added: {feature}")
        changes = result.get("changes", [])
        for c in changes:
            info(f"  {c}")
        return True

    def fix(self, bug_description: str, project_path: str | None = None) -> bool:
        if not project_path:
            project_path = os.getcwd()
        abs_path = os.path.abspath(project_path)
        if not os.path.isdir(abs_path):
            error(f"Project path not found: {abs_path}")
            return False
        info(f"Project : {abs_path}")
        info(f"Bug     : {bug_description}")
        result = self.client.fix(abs_path, bug_description)
        if not result.get("success"):
            warn(f"Fix failed: {result.get('message', 'Unknown error')}")
            return False
        success("Bug fixed successfully")
        changes = result.get("changes", [])
        for c in changes:
            info(f"  {c}")
        return True

    def health(self) -> dict:
        return self.client.health()

    def _extract_and_cleanup(self, zip_path: str, dest_dir: str):
        extract_dir = os.path.join(dest_dir, Path(zip_path).stem)
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        os.remove(zip_path)
        success(f"Extracted to: {extract_dir}")
