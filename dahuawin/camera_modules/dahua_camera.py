from datetime import datetime

import requests
import urllib3
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from dahuawin.camera_modules.base_camera import BaseCamera
from dahuawin import settings_store

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DahuaCamera(BaseCamera):
    def __init__(self, ip: str, username: str, password: str, name: str = "", model: str = ""):
        super().__init__(ip, username, password, name, model)
        self.vendor = "Dahua"

    def authenticate(self) -> bool:
        url = f"http://{self.ip}/cgi-bin/magicBox.cgi?action=getDeviceType"
        timeout = self.get_timeout()

        try:
            response = requests.get(
                url,
                auth=HTTPDigestAuth(self.username, self.password),
                timeout=timeout,
                verify=False,
            )
            if response.status_code == 200 and "type=" in response.text:
                self.auth_ok = True
                self.auth_type = "digest"
                self.model = response.text.split("type=")[1].strip()
                return True
        except Exception:
            pass

        try:
            response = requests.get(
                url,
                auth=HTTPBasicAuth(self.username, self.password),
                timeout=timeout,
                verify=False,
            )
            if response.status_code == 200 and "type=" in response.text:
                self.auth_ok = True
                self.auth_type = "basic"
                self.model = response.text.split("type=")[1].strip()
                return True
        except Exception:
            pass

        return False

    def _get_auth(self):
        if self.auth_type == "basic":
            return HTTPBasicAuth(self.username, self.password)
        return HTTPDigestAuth(self.username, self.password)

    def get_current_time(self) -> bool:
        try:
            response = requests.get(
                f"http://{self.ip}/cgi-bin/global.cgi?action=getCurrentTime",
                auth=self._get_auth(),
                timeout=self.get_timeout(),
                verify=False,
            )

            if response.status_code == 200 and "result=" in response.text:
                time_str = response.text.split("result=")[1].strip()
                self.current_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                self.time_diff = (self.current_time - datetime.now()).total_seconds()
                return True
        except Exception as exc:
            self.issues.append(f"Chyba citania casu: {exc}")

        return False

    def get_ntp_settings(self) -> bool:
        try:
            response = requests.get(
                f"http://{self.ip}/cgi-bin/configManager.cgi?action=getConfig&name=NTP",
                auth=self._get_auth(),
                timeout=self.get_timeout(),
                verify=False,
            )

            if response.status_code == 200:
                for line in response.text.strip().split("\n"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        self.ntp_settings[key.replace("table.NTP.", "")] = value.strip()
                self._check_ntp_settings()
                return True
        except Exception as exc:
            self.ntp_issues.append(f"Chyba citania NTP: {exc}")

        return False

    def _check_ntp_settings(self):
        expected_addresses = settings_store.expected_ntp_addresses()
        expected_port = settings_store.expected_ntp_port()
        expected_enable = settings_store.expected_ntp_enable()

        actual_addr = self.ntp_settings.get("Address", "")
        if actual_addr.lower() not in [addr.lower() for addr in expected_addresses]:
            self.ntp_issues.append(
                f"NTP.Address: '{actual_addr}' (ocakava sa '{expected_addresses[0]}')"
            )

        actual_port = self.ntp_settings.get("Port", "")
        if actual_port != expected_port:
            self.ntp_issues.append(f"NTP.Port: '{actual_port}' (ocakava sa '{expected_port}')")

        actual_enable = self.ntp_settings.get("Enable", "")
        actual_bool = actual_enable.lower() in ["1", "true"]
        if actual_bool != expected_enable:
            expected = "enabled (true/1)" if expected_enable else "disabled (false/0)"
            self.ntp_issues.append(f"NTP.Enable: '{actual_enable}' (ocakava sa {expected})")

    def get_dst_settings(self) -> bool:
        try:
            response = requests.get(
                f"http://{self.ip}/cgi-bin/configManager.cgi?action=getConfig&name=Locales",
                auth=self._get_auth(),
                timeout=self.get_timeout(),
                verify=False,
            )

            if response.status_code == 200:
                for line in response.text.strip().split("\n"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        self.dst_settings[key.replace("table.Locales.", "")] = value.strip()
                self._check_dst_settings()
                return True
        except Exception as exc:
            self.dst_issues.append(f"Chyba citania DST: {exc}")

        return False

    def _check_dst_settings(self):
        for key, expected in settings_store.expected_dst().items():
            actual = self.dst_settings.get(key, "")
            if key == "DSTEnable":
                actual_bool = actual.lower() in ["1", "true"]
                expected_bool = expected.lower() in ["1", "true"]
                if actual_bool != expected_bool:
                    self.dst_issues.append(f"DST.{key}: '{actual}' (ocakava sa '{expected}')")
            else:
                if (actual.lstrip("0") or "0") != (expected.lstrip("0") or "0"):
                    self.dst_issues.append(f"DST.{key}: '{actual}' (ocakava sa '{expected}')")

    def set_ntp_settings(self, address: str = None, port: str = None, enable: bool = None) -> bool:
        if address is None:
            address = settings_store.expected_ntp_addresses()[0]
        if port is None:
            port = settings_store.expected_ntp_port()
        if enable is None:
            enable = settings_store.expected_ntp_enable()

        config_data = f"""table.NTP.Enable={str(enable).lower()}
table.NTP.Address={address}
table.NTP.Port={port}
"""

        try:
            response = requests.post(
                f"http://{self.ip}/cgi-bin/configManager.cgi?action=setConfig&NTP",
                auth=self._get_auth(),
                data=config_data,
                timeout=self.get_timeout(),
                verify=False,
            )
            return response.status_code == 200
        except Exception as exc:
            self.issues.append(f"Chyba pri nastavovani NTP: {exc}")
            return False

    def set_dst_settings(self) -> bool:
        config_data = "".join(f"table.Locales.{key}={value}\n" for key, value in settings_store.expected_dst().items())
        try:
            response = requests.post(
                f"http://{self.ip}/cgi-bin/configManager.cgi?action=setConfig&Locales",
                auth=self._get_auth(),
                data=config_data,
                timeout=self.get_timeout(),
                verify=False,
            )
            return response.status_code == 200
        except Exception as exc:
            self.issues.append(f"Chyba pri nastavovani DST: {exc}")
            return False

    def sync_time_now(self) -> bool:
        try:
            response = requests.get(
                f"http://{self.ip}/cgi-bin/global.cgi?action=adjustTime",
                auth=self._get_auth(),
                timeout=self.get_timeout(),
                verify=False,
            )
            return response.status_code == 200
        except Exception as exc:
            self.issues.append(f"Chyba pri synchronizacii casu: {exc}")
            return False
