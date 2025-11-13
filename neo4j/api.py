# api.py
# Run with: uv run uvicorn api:app --reload --port 8000

import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from neo4j_runner import run_neo4j_task

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY not found in environment.")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

app = FastAPI(title="Neo4j MCP UI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # you can restrict this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExecuteRequest(BaseModel):
    prompt: str

class ExecuteResponse(BaseModel):
    success: bool
    result: str

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/execute", response_model=ExecuteResponse)
async def execute(req: ExecuteRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    try:
        result = await run_neo4j_task(req.prompt)
        return ExecuteResponse(success=True, result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {e}")
