import os
import zipfile
import time
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

from src.System_Agentic.config import OUTPUT_DIR
from src.System_Agentic.rate_limiter import get_manager, get_call_stats, reset_global_calls
from src.System_Agentic.single_generator import generate_project

load_dotenv()

app = FastAPI(
    title="SpringBoot Agentic Generator",
    description="Single-shot Spring Boot generator",
    version="3.0.0",
)


class PromptRequest(BaseModel):
    prompt: str


@app.get("/")
def root():
    calls = get_call_stats()
    mgr = get_manager()
    return {
        "message": "SpringBoot Generator API",
        "version": "3.0.0",
        "global_llm_calls": calls["global_calls"],
        "providers": mgr.summary(),
        "endpoints": {
            "POST /generate": "Generate a complete Spring Boot project from a single prompt",
            "GET /health": "Provider & call stats",
            "GET /projects": "List generated projects",
            "GET /download/{id}": "Download project ZIP",
        },
    }


@app.post("/generate")
def generate_application(body: PromptRequest, http_request: Request):
    rid = uuid.uuid4().hex[:8]
    start = time.time()

    if not body.prompt or len(body.prompt.strip()) < 5:
        return {"success": False, "message": "Prompt too short", "request_id": rid}

    print(f"[{rid}] generate: {body.prompt[:80]}...")

    result = generate_project(body.prompt, request_id=rid)
    elapsed = time.time() - start

    if not result["success"]:
        print(f"[{rid}] FAILED ({elapsed:.1f}s): {result.get('error','')[:120]}")
        return {
            "success": False,
            "message": result.get("error", "Unknown error"),
            "request_id": rid,
            "duration_seconds": round(elapsed, 1),
            "llm_calls": result.get("llm_calls", 0),
        }

    project_id = result["project_id"]
    project_dir = os.path.join(OUTPUT_DIR, project_id)

    zip_path = os.path.join(OUTPUT_DIR, f"{project_id}.zip")
    if os.path.exists(project_dir) and not os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(project_dir):
                for fn in files:
                    fp = os.path.join(root, fn)
                    zf.write(fp, os.path.relpath(fp, project_dir))

    base = f"{http_request.url.scheme}://{http_request.url.netloc}"
    calls = get_call_stats()
    print(f"[{rid}] OK {project_id} ({elapsed:.1f}s, {result['llm_calls']} LLM calls). Total={calls['global_calls']}")

    return {
        "success": True,
        "project_id": project_id,
        "message": "Projet genere avec succes",
        "download_url": f"{base}/download/{project_id}",
        "filename": f"{project_id}.zip",
        "request_id": rid,
        "duration_seconds": round(elapsed, 1),
        "llm_calls": result["llm_calls"],
        "files_generated": result.get("files", 0),
        "provider": result.get("provider", "?"),
        "cached": result.get("cached", False),
    }


@app.get("/health")
def health():
    mgr = get_manager()
    calls = get_call_stats()
    return {
        "status": "running",
        "version": "3.0.0",
        "timestamp": time.time(),
        "providers": mgr.summary(),
        "call_stats": calls,
    }


@app.get("/projects")
def list_projects():
    if not os.path.exists(OUTPUT_DIR):
        return {"projects": []}
    dirs = [
        d for d in os.listdir(OUTPUT_DIR)
        if os.path.isdir(os.path.join(OUTPUT_DIR, d)) and d.startswith("proj_")
    ]
    return {"projects": sorted(dirs, reverse=True)}


@app.get("/download/{project_id}")
def download_project(project_id: str):
    project_dir = os.path.join(OUTPUT_DIR, project_id)
    if not os.path.exists(project_dir):
        raise HTTPException(status_code=404, detail="Project not found")
    zip_path = os.path.join(OUTPUT_DIR, f"{project_id}.zip")
    if not os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(project_dir):
                for fn in files:
                    fp = os.path.join(root, fn)
                    zf.write(fp, os.path.relpath(fp, project_dir))
    return FileResponse(zip_path, media_type="application/zip", filename=f"{project_id}.zip")


@app.get("/admin/reset")
def admin_reset():
    get_manager().reset_all()
    reset_global_calls()
    from src.System_Agentic.single_generator import _CACHE
    n = len(_CACHE)
    _CACHE.clear()
    return {"message": f"Reset OK ({n} cache entries cleared)"}


if __name__ == "__main__":
    uvicorn.run("src.Server:app", host="0.0.0.0", port=8000, reload=True)
