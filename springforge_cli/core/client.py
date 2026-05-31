import httpx
from springforge_cli.utils.config import REQUEST_TIMEOUT, MAX_RETRIES
from springforge_cli.utils.logger import error, warn, step


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=REQUEST_TIMEOUT)

    def health(self) -> dict:
        try:
            r = self.client.get(f"{self.base_url}/health")
            r.raise_for_status()
            return r.json()
        except httpx.HTTPError as e:
            return {"status": "error", "detail": str(e)}

    def _request(self, method: str, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                step(f"Calling {endpoint} (attempt {attempt}/{MAX_RETRIES})")
                if method == "POST":
                    r = self.client.post(url, json=payload)
                else:
                    r = self.client.get(url, params=payload)
                r.raise_for_status()
                return r.json()
            except httpx.HTTPStatusError as e:
                body = e.response.text[:300]
                if attempt < MAX_RETRIES:
                    warn(f"API error (HTTP {e.response.status_code}): {body}")
                    step("Retrying...")
                else:
                    error(f"API error (HTTP {e.response.status_code}): {body}")
                    return {"success": False, "message": body}
            except httpx.RequestError as e:
                if attempt < MAX_RETRIES:
                    warn(f"Connection error: {e}")
                    step("Retrying...")
                else:
                    error(f"Connection failed: {e}")
                    return {"success": False, "message": str(e)}
        return {"success": False, "message": "Max retries exhausted"}

    def generate(self, prompt: str) -> dict:
        return self._request("POST", "/generate", {"prompt": prompt})

    def edit(self, project_path: str, prompt: str) -> dict:
        return self._request("POST", "/edit", {"project_path": project_path, "prompt": prompt})

    def add(self, project_path: str, feature: str) -> dict:
        return self._request("POST", "/add", {"project_path": project_path, "feature": feature})

    def fix(self, project_path: str, bug_description: str) -> dict:
        return self._request("POST", "/fix", {"project_path": project_path, "bug_description": bug_description})

    def download_zip(self, project_id: str, dest: str) -> bool:
        try:
            r = self.client.get(f"{self.base_url}/download/{project_id}")
            r.raise_for_status()
            with open(dest, "wb") as f:
                f.write(r.content)
            return True
        except Exception as e:
            error(f"Download failed: {e}")
            return False
