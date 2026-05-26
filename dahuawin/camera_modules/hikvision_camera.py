from datetime import datetime
import re
import xml.etree.ElementTree as ET

import requests
import urllib3
from requests.auth import HTTPDigestAuth

from dahuawin.camera_modules.base_camera import BaseCamera
from dahuawin import settings_store

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HikvisionCamera(BaseCamera):
    def __init__(self, ip: str, username: str, password: str, name: str = "", model: str = ""):
        super().__init__(ip, username, password, name, model)
        self.vendor = "Hikvision"

    def authenticate(self) -> bool:
        try:
            response = requests.get(
                f"http://{self.ip}/ISAPI/System/deviceInfo",
                auth=HTTPDigestAuth(self.username, self.password),
                timeout=self.get_timeout(),
                verify=False,
            )
            if response.status_code == 200:
                self.auth_ok = True
                self.auth_type = "digest"
                try:
                    root = ET.fromstring(response.content)
                    model_elem = root.find(".//model")
                    if model_elem is not None:
                        self.model = model_elem.text
                except Exception:
                    pass
                return True
        except Exception:
            pass
        return False

    def get_current_time(self) -> bool:
        try:
            response = requests.get(
                f"http://{self.ip}/ISAPI/System/time",
                auth=HTTPDigestAuth(self.username, self.password),
                timeout=self.get_timeout(),
                verify=False,
            )
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for elem in root.iter():
                    if "}" in elem.tag:
                        elem.tag = elem.tag.split("}", 1)[1]
                local_time = root.find(".//localTime")
                if local_time is not None:
                    time_str = local_time.text
                    self.current_time = datetime.fromisoformat(time_str.replace("Z", "+00:00").split("+")[0])
                    self.time_diff = (self.current_time - datetime.now()).total_seconds()
                    return True
        except Exception as exc:
            self.issues.append(f"Chyba citania casu: {exc}")
        return False

    def get_ntp_settings(self) -> bool:
        try:
            response = requests.get(
                f"http://{self.ip}/ISAPI/System/time/ntpServers",
                auth=HTTPDigestAuth(self.username, self.password),
                timeout=self.get_timeout(),
                verify=False,
            )
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for elem in root.iter():
                    if "}" in elem.tag:
                        elem.tag = elem.tag.split("}", 1)[1]
                for ntp_server in root.findall(".//NTPServer"):
                    server_id = ntp_server.find("id")
                    if server_id is not None and server_id.text == "1":
                        ip_elem = ntp_server.find("ipAddress")
                        hostname_elem = ntp_server.find("hostName")
                        port_elem = ntp_server.find("portNo")
                        if ip_elem is not None and ip_elem.text:
                            self.ntp_settings["Address"] = ip_elem.text
                        elif hostname_elem is not None and hostname_elem.text:
                            self.ntp_settings["Address"] = hostname_elem.text
                        if port_elem is not None:
                            self.ntp_settings["Port"] = port_elem.text
                        self.ntp_settings["Enable"] = "true"
                self._check_ntp_settings()
                return True
        except Exception as exc:
            self.ntp_issues.append(f"Chyba citania NTP: {exc}")
        return False

    def _check_ntp_settings(self):
        expected_addresses = settings_store.expected_ntp_addresses()
        expected_port = settings_store.expected_ntp_port()

        actual_addr = self.ntp_settings.get("Address", "")
        if actual_addr.lower() not in [addr.lower() for addr in expected_addresses]:
            self.ntp_issues.append(
                f"NTP.Address: '{actual_addr}' (ocakava sa '{expected_addresses[0]}')"
            )
        actual_port = self.ntp_settings.get("Port", "")
        if actual_port != expected_port:
            self.ntp_issues.append(f"NTP.Port: '{actual_port}' (ocakava sa '{expected_port}')")

    def get_dst_settings(self) -> bool:
        try:
            response = requests.get(
                f"http://{self.ip}/ISAPI/System/time",
                auth=HTTPDigestAuth(self.username, self.password),
                timeout=self.get_timeout(),
                verify=False,
            )
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for elem in root.iter():
                    if "}" in elem.tag:
                        elem.tag = elem.tag.split("}", 1)[1]
                dst_elem = root.find(".//daylightSavingTime")
                if dst_elem is not None:
                    enabled_elem = dst_elem.find("enabled")
                    if enabled_elem is not None:
                        self.dst_settings["DSTEnable"] = enabled_elem.text.lower()
                    manual_dst = dst_elem.find(".//manualDst")
                    if manual_dst is not None:
                        mapping = {
                            "startMonth": "DSTStart.Month",
                            "startWeek": "DSTStart.Week",
                            "startWeekDay": "DSTStart.Day",
                            "startHour": "DSTStart.Hour",
                            "endMonth": "DSTEnd.Month",
                            "endWeek": "DSTEnd.Week",
                            "endWeekDay": "DSTEnd.Day",
                            "endHour": "DSTEnd.Hour",
                        }
                        for source_key, target_key in mapping.items():
                            found = manual_dst.find(source_key)
                            if found is not None and found.text is not None:
                                self.dst_settings[target_key] = found.text
                else:
                    timezone_elem = root.find(".//timeZone")
                    if timezone_elem is not None and timezone_elem.text:
                        self._parse_dst_from_timezone(timezone_elem.text)
                self._check_dst_settings()
                return True
        except Exception as exc:
            self.dst_issues.append(f"Chyba citania DST: {exc}")
        return False

    def _parse_dst_from_timezone(self, timezone_str: str):
        if "DST" not in timezone_str:
            self.dst_settings["DSTEnable"] = "false"
            return

        self.dst_settings["DSTEnable"] = "true"
        matches = list(re.finditer(r"M(\d+)\.(\d+)\.(\d+)/(\d+):", timezone_str))
        if matches:
            start = matches[0]
            self.dst_settings["DSTStart.Month"] = str(int(start.group(1)) - 1) if int(start.group(1)) == 4 else "3"
            self.dst_settings["DSTStart.Week"] = "-1" if int(start.group(2)) == 5 else start.group(2)
            self.dst_settings["DSTStart.Day"] = start.group(3)
            self.dst_settings["DSTStart.Hour"] = start.group(4).lstrip("0") or "0"
        if len(matches) >= 2:
            end = matches[1]
            self.dst_settings["DSTEnd.Month"] = end.group(1)
            self.dst_settings["DSTEnd.Week"] = "-1" if int(end.group(2)) == 5 else end.group(2)
            self.dst_settings["DSTEnd.Day"] = end.group(3)
            self.dst_settings["DSTEnd.Hour"] = end.group(4).lstrip("0") or "0"

    def _check_dst_settings(self):
        for key, expected in settings_store.expected_dst().items():
            actual = self.dst_settings.get(key, "")
            if actual.lower() != expected.lower():
                self.dst_issues.append(f"DST.{key}: '{actual}' (ocakava sa '{expected}')")

    def set_ntp_settings(self, address: str = None, port: str = None, enable: bool = None) -> bool:
        if address is None:
            address = settings_store.expected_ntp_addresses()[0]
        if port is None:
            port = settings_store.expected_ntp_port()
        if enable is None:
            enable = settings_store.expected_ntp_enable()

        xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<NTPServerList>
    <NTPServer>
        <id>1</id>
        <addressingFormatType>ipaddress</addressingFormatType>
        <ipAddress>{address}</ipAddress>
        <portNo>{port}</portNo>
        <synchronizeInterval>60</synchronizeInterval>
    </NTPServer>
</NTPServerList>"""

        try:
            response = requests.put(
                f"http://{self.ip}/ISAPI/System/time/ntpServers",
                auth=HTTPDigestAuth(self.username, self.password),
                data=xml_data,
                headers={"Content-Type": "application/xml"},
                timeout=self.get_timeout(),
                verify=False,
            )
            return response.status_code == 200
        except Exception as exc:
            self.issues.append(f"Chyba pri nastavovani NTP: {exc}")
            return False

    def set_dst_settings(self) -> bool:
        dst = settings_store.expected_dst()
        enabled = "true" if dst.get("DSTEnable", "true").lower() in ("1", "true") else "false"
        xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<Time>
    <timeMode>NTP</timeMode>
    <localTime>
        <timeZone>CST-1:00:00</timeZone>
        <daylightSavingTime>
            <enabled>{enabled}</enabled>
            <dstType>manual</dstType>
            <manualDst>
                <startMonth>{dst.get('DSTStart.Month', '3')}</startMonth>
                <startWeek>{dst.get('DSTStart.Week', '-1')}</startWeek>
                <startWeekDay>{dst.get('DSTStart.Day', '0')}</startWeekDay>
                <startHour>{dst.get('DSTStart.Hour', '2')}</startHour>
                <endMonth>{dst.get('DSTEnd.Month', '10')}</endMonth>
                <endWeek>{dst.get('DSTEnd.Week', '-1')}</endWeek>
                <endWeekDay>{dst.get('DSTEnd.Day', '0')}</endWeekDay>
                <endHour>{dst.get('DSTEnd.Hour', '3')}</endHour>
                <offset>60</offset>
            </manualDst>
        </daylightSavingTime>
    </localTime>
</Time>"""

        try:
            response = requests.put(
                f"http://{self.ip}/ISAPI/System/time",
                auth=HTTPDigestAuth(self.username, self.password),
                data=xml_data,
                headers={"Content-Type": "application/xml"},
                timeout=self.get_timeout(),
                verify=False,
            )
            return response.status_code == 200
        except Exception as exc:
            self.issues.append(f"Chyba pri nastavovani DST: {exc}")
            return False

    def sync_time_now(self) -> bool:
        return True
