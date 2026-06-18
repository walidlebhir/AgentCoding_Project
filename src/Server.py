import os
import zipfile
import time
import uuid
import json
import traceback
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
from sqlalchemy.orm import Session

from src.Config.database import create_tables, get_db
from src.System_Agentic.config import OUTPUT_DIR
from src.System_Agentic.rate_limiter import get_manager, get_call_stats, reset_global_calls
from src.System_Agentic.single_generator import generate_project
from src.Controllers.auth_controller import router as auth_router
from src.Controllers.user_controller import router as user_router
from src.Controllers.project_controller import router as project_router
from src.Controllers.agent_controller import router as agent_router
from src.dependencies.auth_dependency import get_current_user
from src.models.user import User
from src.models.project import Project

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    create_tables()
    yield


app = FastAPI(
    title="SpringBoot Agentic Generator",
    description="Single-shot Spring Boot generator",
    version="3.0.0",
    lifespan=lifespan,
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"ERROR: Global exception caught: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal Server Error", "error": str(exc)},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(project_router, prefix="/api")
app.include_router(agent_router, prefix="/api")


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
def generate_application(
    body: PromptRequest, 
    http_request: Request, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rid = uuid.uuid4().hex[:8]
    start = time.time()

    if not body.prompt or len(body.prompt.strip()) < 5:
        return {"success": False, "message": "Prompt too short", "request_id": rid}

    print(f"[{rid}] generate for user {current_user.email}: {body.prompt[:80]}...")

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
    download_url = f"{base}/download/{project_id}"

    # Sauvegarde en base de données
    db_id = None
    try:
        new_project = Project(
            user_id=current_user.id,
            name=f"Spring Project {project_id}",
            description=f"Généré à partir de: {body.prompt[:50]}...",
            language="Java",
            prompt=body.prompt,
            folder_name=project_id,
            download_url=download_url,
            provider=result.get("provider"),
            model=result.get("provider"),
            generation_time=round(elapsed, 2),
            steps=json.dumps([
                "Analyse du besoin utilisateur",
                "Sélection du meilleur modèle LLM ({})".format(result.get("provider", "?")),
                "Génération de l'architecture Spring Boot",
                "Création des entités et repositories",
                "Finalisation et compression"
            ])
        )
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        db_id = new_project.id
    except Exception as e:
        print(f"ERROR: DB save failed: {e}")

    calls = get_call_stats()
    print(f"[{rid}] OK {project_id} ({elapsed:.1f}s, {result['llm_calls']} LLM calls). Total={calls['global_calls']}")

    return {
        "success": True,
        "project_id": project_id,
        "db_id": db_id,
        "message": "Projet genere avec succes",
        "download_url": download_url,
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


@app.get("/download/{project_id}")
def download_project(project_id: str):
    # Sanitize project_id
    project_id = os.path.basename(project_id).replace("..", "")
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


@app.get("/projects/{project_id}/files")
def list_project_files(project_id: str):
    project_id = os.path.basename(project_id).replace("..", "")
    project_dir = os.path.join(OUTPUT_DIR, project_id)
    if not os.path.exists(project_dir):
        raise HTTPException(status_code=404, detail="Project not found")
    
    file_list = []
    for root, dirs, files in os.walk(project_dir):
        for fn in files:
            fp = os.path.join(root, fn)
            rel_path = os.path.relpath(fp, project_dir).replace("\\", "/")
            file_list.append(rel_path)
    return {"files": sorted(file_list)}


@app.get("/projects/{project_id}/files/{file_path:path}")
def get_file_content(project_id: str, file_path: str):
    project_id = os.path.basename(project_id).replace("..", "")
    # Sanitize file_path
    file_path = file_path.replace("..", "").lstrip("/")
    full_path = os.path.join(OUTPUT_DIR, project_id, file_path)
    
    if not os.path.exists(full_path) or os.path.isdir(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content, "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
