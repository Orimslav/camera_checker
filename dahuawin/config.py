from pathlib import Path


APP_NAME = "Camera Checker"
APP_ORG = "OFZ"

DEFAULT_CSV_FILE = ""
APP_DIR = Path(__file__).resolve().parent.parent

EXPECTED_NTP_ADDRESSES = ["192.168.10.5", "cams.ofz.sk"]
EXPECTED_NTP_PORT = "123"
EXPECTED_NTP_ENABLE = True

EXPECTED_DST = {
    "DSTEnable": "true",
    "DSTStart.Month": "3",
    "DSTStart.Week": "-1",
    "DSTStart.Day": "0",
    "DSTStart.Hour": "2",
    "DSTEnd.Month": "10",
    "DSTEnd.Week": "-1",
    "DSTEnd.Day": "0",
    "DSTEnd.Hour": "3",
}

MAX_TIME_DIFF_SECONDS = 60

TIMEOUT = 10
TIMEOUT_SLOW = 20

SLOW_IPS = [
    "192.168.10.100",
    "192.168.10.120",
    "192.168.10.140",
    "192.168.10.170",
    "192.168.10.171",
    "192.168.10.190",
    "192.168.11.10",
    "192.168.11.130",
    "192.168.11.160",
    "192.168.11.170",
    "192.168.11.182",
]

SKIP_IPS = []

MAX_WORKERS = 10

HIKVISION_KEYWORDS = ["DS-", "HIKVISION"]
SWITCH_KEYWORDS = ["SWITCH", "POE SWITCH", "DGS-", "PORTS POE"]
SERVER_KEYWORDS = ["SERVER"]
DAHUA_PREFIXES = ["DH-", "DHI-", "IPC-", "NVR", "DVR", "XVR", "HCVR", "VTO", "VTH"]
