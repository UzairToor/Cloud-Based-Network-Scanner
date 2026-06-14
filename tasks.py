import os
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Scan, Host, OpenPort
from network_scanner import scan_network
from port_scanner import scan_ports


def run_scan(
    scan_id: int,
    ip_range: str,
    ports: list[int],
    gateway: str | None = None,
    demo: bool = False
):
    db: Session = SessionLocal()
    scan: Scan | None = None

    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return

        # ---- Lifecycle: pending → running ----
        scan.status = "running"
        scan.started_at = datetime.utcnow()
        db.commit()

        # ---------------- DEMO MODE ----------------
        if demo:
            scan.mode = "demo"

            demo_hosts = [
                {"ip": "192.168.1.10", "mac": "AA:BB:CC:DD:EE:01"},
                {"ip": "192.168.1.20", "mac": "AA:BB:CC:DD:EE:02"},
            ]

            demo_ports = {
                "192.168.1.10": [22, 80],
                "192.168.1.20": [443],
            }

            for host in demo_hosts:
                host_obj = Host(
                    scan_id=scan.id,
                    ip_address=host["ip"],
                    mac_address=host["mac"]
                )
                db.add(host_obj)
                db.flush()  # get host_obj.id without full commit

                for port in demo_ports.get(host["ip"], []):
                    db.add(OpenPort(
                        host_id=host_obj.id,
                        port=port
                    ))

            scan.status = "completed"
            scan.completed_at = datetime.utcnow()
            db.commit()
            return

        # ---------------- CLOUD SAFETY ----------------
        if os.getenv("RENDER") == "true":
            scan.mode = "cloud"
            scan.status = "completed"
            scan.completed_at = datetime.utcnow()
            db.commit()
            return

        # ---------------- LIVE MODE ----------------
        scan.mode = "live"

        # gateway reserved for future routing logic
        active_hosts = scan_network(ip_range)

        for host in active_hosts:
            host_obj = Host(
                scan_id=scan.id,
                ip_address=host["ip"],
                mac_address=host["mac"]
            )
            db.add(host_obj)
            db.flush()

            open_ports = scan_ports(host["ip"], ports)
            for port in open_ports:
                db.add(OpenPort(
                    host_id=host_obj.id,
                    port=port
                ))

        scan.status = "completed"
        scan.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        print(f"[SCAN ERROR] Scan ID {scan_id}: {e}")

        if scan:
            scan.status = "failed"
            scan.failed_at = datetime.utcnow()
            db.commit()

    finally:
        db.close()
