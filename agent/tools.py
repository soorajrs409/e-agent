import requests
from pathlib import Path
import subprocess 
import shlex


# Tool 1 - Read File 
def read_file(file_path: str) -> str:
    try:
        return Path(file_path).read_text()
    except Exception as e:
        return f"Script Error : {e}"



# Tool 2 - Call API

def call_api(url: str) -> str:

    try:
        r = requests.get(url, timeout=20)
        return r.text
    except Exception as e:
        return f"API error: {e}"
    

# Tool 3 - Nmap scan

def run_nmap(target: str, options: str = "-sV") -> str:
    """
    Run nmap scan safely

    target: domain or ip
    options: allowed nmao flags (default: service detection)
    """

    allowed_flags = ["-sV", "-sS", "-Pn", "-F", "-O", "-p 1-65535"]

    option_list = shlex.split(options)

    for opt in option_list:
        if opt not in allowed_flags:
            return f"[-] Disallowed switch {opt}"
        
    try:
        cmd = ["nmap"] + option_list + [target]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True, 
            timeout=600
        )

        if result.returncode != 0:
            return f"[-] Nmap scan error:\n{result.stderr}"
        
        return result.stdout
    
    except subprocess.TimeoutExpired:
        return f"[-] Scan timed out"
    
    except Exception as e:
        return f"[-] Nmap execution error: {e}"
    
    

