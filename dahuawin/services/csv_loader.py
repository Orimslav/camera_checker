import csv
import re
from typing import Dict, List, Optional


class CSVLoader:
    def __init__(self, csv_file: str):
        self.csv_file = csv_file

    def load_cameras(self) -> List[Dict]:
        cameras = []

        with open(self.csv_file, "r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                ip = self._extract_ip(row.get("Web Site", "") or "")
                if not ip:
                    continue

                username = row.get("Login Name", "") or row.get("Username", "") or ""
                password = row.get("Password", "") or ""
                if not username or not password:
                    continue

                name = row.get("Account", "") or ""
                comments = row.get("Comments", "") or ""
                model = self._extract_model(comments)

                cameras.append(
                    {
                        "ip": ip,
                        "username": username,
                        "password": password,
                        "name": name,
                        "model": model,
                        "comments": comments,
                    }
                )

        return cameras

    def get_camera_by_ip(self, ip: str) -> Optional[Dict]:
        for camera in self.load_cameras():
            if camera["ip"] == ip:
                return camera
        return None

    def _extract_ip(self, url: str) -> Optional[str]:
        match = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})", url)
        return match.group(1) if match else None

    def _extract_model(self, comments: str) -> str:
        patterns = [
            r"(IPC-[A-Z0-9\-]+)",
            r"(DH-[A-Z0-9\-]+)",
            r"(DHI-[A-Z0-9\-]+)",
            r"(DS-[A-Z0-9\-]+)",
            r"(NVR[A-Z0-9\-]+)",
            r"(DVR[A-Z0-9\-]+)",
            r"(XVR[A-Z0-9\-]+)",
            r"(VTO[A-Z0-9\-]+)",
            r"(VTH[A-Z0-9\-]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, comments, re.IGNORECASE)
            if match:
                return match.group(1)
        return ""
