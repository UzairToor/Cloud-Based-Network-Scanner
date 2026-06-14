from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    BackgroundTasks,
    Request,
    Path
)
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from utils import (
    validate_ip_range,
    validate_port_list,
    validate_gateway
)
from database import SessionLocal
from database import engine
from models import Base
from models import Scan, Host, OpenPort
from tasks import run_scan

# -------------------- App --------------------

app = FastAPI(
    title="Live Network Scanner",
    description="FastAPI-based live network scanning service",
    version="2.7.2"
)

# -------------------- Create DB Tables --------------------
Base.metadata.create_all(bind=engine)

# -------------------- Static & Templates --------------------

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# -------------------- DB Dependency --------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------- Schemas --------------------

class ScanRequest(BaseModel):
    ip_range: str = Field(..., example="192.168.1.0/24")
    gateway: Optional[str] = Field(None, example="192.168.1.1")
    ports: Optional[List[int]] = Field(default_factory=lambda: [22, 80, 443])
    demo: Optional[bool] = False


class ScanResponse(BaseModel):
    scan_id: int
    status: str
    message: str

# -------------------- Frontend --------------------

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request}
    )

# -------------------- API --------------------

@app.post("/scan", response_model=ScanResponse)
def start_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # 1️⃣ Validate IP range
    if not validate_ip_range(request.ip_range):
        raise HTTPException(
            status_code=400,
            detail="Invalid IP range or CIDR notation"
        )

    # 2️⃣ Validate gateway
    if request.gateway:
        if not validate_gateway(request.ip_range, request.gateway):
            raise HTTPException(
                status_code=400,
                detail="Gateway must belong to the selected IP range"
            )

    # 3️⃣ Validate ports
    if not validate_port_list(request.ports):
        raise HTTPException(
            status_code=400,
            detail="Invalid port list (ports must be 1–65535)"
        )

    # 4️⃣ Create scan entry
    scan = Scan(
        ip_range=request.ip_range,
        gateway=request.gateway,
        ports_scanned=",".join(map(str, request.ports)),
        status="queued",
        mode="demo" if request.demo else "cloud"
    )

    db.add(scan)
    db.commit()
    db.refresh(scan)

    # 5️⃣ Background execution
    background_tasks.add_task(
        run_scan,
        scan.id,
        request.ip_range,
        request.ports,
        request.gateway,
        request.demo
    )

    return {
        "scan_id": scan.id,
        "status": scan.status,
        "message": "Scan queued successfully"
    }

# -------------------- RESULTS ENDPOINT (FIX) --------------------

@app.get("/results/{scan_id}")
def get_scan_results(
    scan_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
):
    scan = (
        db.query(Scan)
        .options(joinedload(Scan.hosts).joinedload(Host.open_ports))
        .filter(Scan.id == scan_id)
        .first()
    )

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    results = []

    for host in scan.hosts:
        results.append({
            "ip": host.ip_address,
            "mac": host.mac_address,
            "ports": [p.port for p in host.open_ports]
        })

    return {
        "scan_id": scan.id,
        "status": scan.status,
        "mode": scan.mode,
        "gateway": scan.gateway,
        "created_at": scan.created_at,
        "results": results
    }
