from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import subprocess
import shlex
import requests

app = FastAPI(title="Core Tools MCP Server")

class ReadFileReq(BaseModel):
    file_path: str

class CallApiReq(BaseModel):
    url: str

class NmapReq(BaseModel):
    target: str
    options: str = "-sV"


@app.get("/tools")
def list_tools():
    return {
        "tools": [
            {"name": "read_file", "args": ["file_path"]},
            {"name": "call_api", "args": ["url"]},
            {"name": "run_nmap", "args": ["target", "options"]}
        ]
    }



@app.post("/tools/read_file")
def read_file(req: ReadFileReq):
    try:
        content = Path(req.file_path).read_text()
        return {"output":  content}
    except Exception as e:
        return {"error": str(e)}
    


@app.post("/tools/call_api")
def call_api(req: CallApiReq):
    try:
        r = requests.get(req.url, timeout=20)
        return {"output": r.text}
    
    except Exception as e:
        return {"error": str(e)}
    

def run_nmap(req: NmapReq):
    allowed_flags = ["-sV", "-sS", "-Pn", "-F", "-O"]

    option_list = shlex.split(req.options)

    for opt in option_list:
        if opt not in allowed_flags:
            return {"error":f"Disallowed switch {e}"}
        
    try:
        cmd = ["nmap"] + option_list + [req.target]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600
        )

        if result.returncode != 0:
            return {"error": result.stderr}
        
        return {"output": result.stdout}
    
    except subprocess.TimeoutExpired:
        return {"error": "Scan timed out"}
    
    except Exception as e:
        return {"error": str(e)}