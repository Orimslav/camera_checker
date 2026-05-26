from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional


class BaseCamera(ABC):
    def __init__(self, ip: str, username: str, password: str, name: str = "", model: str = ""):
        self.ip = ip
        self.username = username
        self.password = password
        self.name = name
        self.model_from_csv = model

        self.vendor = ""
        self.model = None
        self.auth_ok = False
        self.auth_type = None

        self.current_time: Optional[datetime] = None
        self.time_diff: Optional[float] = None

        self.ntp_settings: Dict = {}
        self.ntp_issues: List[str] = []

        self.dst_settings: Dict = {}
        self.dst_issues: List[str] = []

        self.issues: List[str] = []

        self.skipped = False
        self.skip_reason = ""

    @abstractmethod
    def authenticate(self) -> bool:
        pass

    @abstractmethod
    def get_current_time(self) -> bool:
        pass

    @abstractmethod
    def get_ntp_settings(self) -> bool:
        pass

    @abstractmethod
    def get_dst_settings(self) -> bool:
        pass

    @abstractmethod
    def set_ntp_settings(self, address: str = None, port: str = "123", enable: bool = True) -> bool:
        pass

    @abstractmethod
    def set_dst_settings(self) -> bool:
        pass

    @abstractmethod
    def sync_time_now(self) -> bool:
        pass

    def get_timeout(self) -> int:
        from dahuawin.config import SLOW_IPS, TIMEOUT, TIMEOUT_SLOW

        return TIMEOUT_SLOW if self.ip in SLOW_IPS else TIMEOUT

    def check_all(self) -> Dict:
        if self.skipped:
            return self.to_dict()

        if not self.authenticate():
            self.issues.append("Prihlasenie zlyhalo")
            return self.to_dict()

        self.get_current_time()
        self.get_ntp_settings()
        self.get_dst_settings()

        self.issues = self.ntp_issues + self.dst_issues
        from dahuawin import settings_store

        if self.time_diff and abs(self.time_diff) > settings_store.max_time_diff_seconds():
            self.issues.insert(0, f"Casova odchylka: {self.time_diff:+.0f}s")

        return self.to_dict()

    def to_dict(self) -> Dict:
        return {
            "ip": self.ip,
            "name": self.name,
            "vendor": self.vendor,
            "model": self.model or self.model_from_csv,
            "auth_ok": self.auth_ok,
            "auth_type": self.auth_type,
            "current_time": self.current_time.strftime("%Y-%m-%d %H:%M:%S") if self.current_time else None,
            "time_diff": self.time_diff,
            "ntp_settings": self.ntp_settings,
            "ntp_issues": self.ntp_issues,
            "dst_settings": self.dst_settings,
            "dst_issues": self.dst_issues,
            "issues": self.issues,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
        }
