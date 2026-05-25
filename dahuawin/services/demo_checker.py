import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional


_DEMO_CAMERAS: List[Dict] = [
    {
        "ip": "192.0.2.10", "name": "Main Entrance", "vendor": "Dahua",
        "model": "IPC-HFW2831T-AS", "status": "ok",
        "time_diff": 2, "issues": [],
    },
    {
        "ip": "192.0.2.11", "name": "Parking Gate", "vendor": "Dahua",
        "model": "IPC-HDW1230S", "status": "ok",
        "time_diff": -4, "issues": [],
    },
    {
        "ip": "192.0.2.12", "name": "Warehouse North", "vendor": "Dahua",
        "model": "IPC-HFW2831T-AS", "status": "problem",
        "time_diff": 8,
        "issues": ["NTP server mismatch: 0.pool.ntp.org (expected 192.0.2.5)"],
    },
    {
        "ip": "192.0.2.13", "name": "Reception", "vendor": "Hikvision",
        "model": "DS-2CD2143G0-I", "status": "ok",
        "time_diff": -1, "issues": [],
    },
    {
        "ip": "192.0.2.14", "name": "Loading Bay", "vendor": "Dahua",
        "model": "IPC-HFW4631E-SE", "status": "problem",
        "time_diff": 6,
        "issues": ["DST disabled"],
    },
    {
        "ip": "192.0.2.15", "name": "Office Hall", "vendor": "Hikvision",
        "model": "DS-2CD2185FWD-I", "status": "problem",
        "time_diff": 142,
        "issues": ["Time drift: +142s", "DST end month mismatch: 11 (expected 10)"],
    },
    {
        "ip": "192.0.2.16", "name": "Server Room", "vendor": "Dahua",
        "model": "IPC-HDBW3441R-ZS", "status": "auth_failed",
    },
    {
        "ip": "192.0.2.17", "name": "Roof Camera", "vendor": "Dahua",
        "model": "IPC-HFW5442T-ASE", "status": "ok",
        "time_diff": 1, "issues": [],
    },
    {
        "ip": "192.0.2.18", "name": "Side Gate", "vendor": "Hikvision",
        "model": "DS-2CD2T47G2-L", "status": "problem",
        "time_diff": -73,
        "issues": [
            "Time drift: -73s",
            "NTP server mismatch: time.google.com (expected 192.0.2.5)",
            "DST disabled",
        ],
    },
    {
        "ip": "192.0.2.19", "name": "POE Switch Rack A", "vendor": "Switch",
        "model": "DGS-1210-28P", "status": "skipped",
        "skip_reason": "Switch",
    },
    {
        "ip": "192.0.2.20", "name": "Recording Server", "vendor": "Server",
        "model": "", "status": "skipped",
        "skip_reason": "Server",
    },
    {
        "ip": "192.0.2.21", "name": "Backyard", "vendor": "Dahua",
        "model": "IPC-HDW3849H-AS-PV", "status": "auth_failed",
    },
    {
        "ip": "192.0.2.22", "name": "Lobby", "vendor": "Dahua",
        "model": "IPC-HFW2231T-ZS", "status": "ok",
        "time_diff": 0, "issues": [],
    },
]


def _build_result(spec: Dict) -> Dict:
    status = spec["status"]
    now = datetime.now()
    time_diff = spec.get("time_diff", 0)
    current_time = (now + timedelta(seconds=time_diff)).strftime("%Y-%m-%d %H:%M:%S")

    base = {
        "ip": spec["ip"],
        "name": spec["name"],
        "vendor": spec["vendor"],
        "model": spec["model"],
        "auth_ok": status != "auth_failed",
        "auth_type": "digest" if status != "auth_failed" else None,
        "current_time": current_time if status != "auth_failed" else None,
        "time_diff": time_diff if status != "auth_failed" else None,
        "ntp_settings": {},
        "ntp_issues": [],
        "dst_settings": {},
        "dst_issues": [],
        "issues": list(spec.get("issues", [])),
        "skipped": status == "skipped",
        "skip_reason": spec.get("skip_reason", ""),
    }

    if status == "auth_failed":
        base["issues"] = ["Login failed"]
        base["current_time"] = None
        base["time_diff"] = None

    return base


class DemoCameraChecker:
    """Drop-in replacement for CameraChecker that returns canned data on fake IPs.

    Uses the RFC 5737 192.0.2.0/24 documentation range so no real host is ever contacted.
    """

    PER_CAMERA_DELAY_SECONDS = 0.18

    def __init__(self, csv_file: str = ""):
        self.csv_file = csv_file
        self.results: List[Dict] = []
        self.csv_loader = self

    def load_cameras(self) -> List[Dict]:
        return [
            {
                "ip": spec["ip"],
                "username": "admin",
                "password": "demo",
                "name": spec["name"],
                "model": spec["model"],
                "comments": "",
            }
            for spec in _DEMO_CAMERAS
        ]

    def get_camera_by_ip(self, ip: str) -> Optional[Dict]:
        for camera in self.load_cameras():
            if camera["ip"] == ip:
                return camera
        return None

    def check_camera(self, camera_data: Dict) -> Dict:
        for spec in _DEMO_CAMERAS:
            if spec["ip"] == camera_data["ip"]:
                return _build_result(spec)
        return _build_result({
            "ip": camera_data["ip"], "name": camera_data.get("name", ""),
            "vendor": "Unknown", "model": camera_data.get("model", ""),
            "status": "auth_failed",
        })

    def run_check(self, progress_callback=None) -> List[Dict]:
        results: List[Dict] = []
        total = len(_DEMO_CAMERAS)
        for index, spec in enumerate(_DEMO_CAMERAS, start=1):
            time.sleep(self.PER_CAMERA_DELAY_SECONDS)
            result = _build_result(spec)
            results.append(result)
            if progress_callback:
                progress_callback(index, total, result)
        self.results = results
        return results

    def summarize(self, results: Optional[List[Dict]] = None) -> Dict:
        data = results if results is not None else self.results
        skipped = [row for row in data if row.get("skipped", False)]
        processed = [row for row in data if not row.get("skipped", False)]
        ok_cameras = [row for row in processed if row.get("auth_ok", False) and not row.get("issues")]
        problem_cameras = [row for row in processed if row.get("auth_ok", False) and row.get("issues")]
        auth_failed = [row for row in processed if not row.get("auth_ok", False)]
        return {
            "total": len(data),
            "skipped": len(skipped),
            "processed": len(processed),
            "ok": len(ok_cameras),
            "problems": len(problem_cameras),
            "auth_failed": len(auth_failed),
            "ok_cameras": ok_cameras,
            "problem_cameras": problem_cameras,
            "auth_failed_cameras": auth_failed,
            "skipped_cameras": skipped,
        }
