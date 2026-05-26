from typing import Dict, List

from PySide6.QtCore import QSettings

from dahuawin import config


_GROUP = "expected"
_DST_KEYS = (
    "DSTEnable",
    "DSTStart.Month",
    "DSTStart.Week",
    "DSTStart.Day",
    "DSTStart.Hour",
    "DSTEnd.Month",
    "DSTEnd.Week",
    "DSTEnd.Day",
    "DSTEnd.Hour",
)


def _qs() -> QSettings:
    return QSettings(config.APP_ORG, config.APP_NAME)


def _to_bool(value, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes")
    return default


def expected_ntp_addresses() -> List[str]:
    raw = _qs().value(f"{_GROUP}/ntp_addresses", None)
    if raw is None:
        return list(config.EXPECTED_NTP_ADDRESSES)
    if isinstance(raw, list):
        items = [str(item).strip() for item in raw]
    else:
        items = [part.strip() for part in str(raw).split(",")]
    items = [item for item in items if item]
    return items or list(config.EXPECTED_NTP_ADDRESSES)


def expected_ntp_port() -> str:
    return str(_qs().value(f"{_GROUP}/ntp_port", config.EXPECTED_NTP_PORT))


def expected_ntp_enable() -> bool:
    return _to_bool(_qs().value(f"{_GROUP}/ntp_enable", config.EXPECTED_NTP_ENABLE), config.EXPECTED_NTP_ENABLE)


def expected_dst() -> Dict[str, str]:
    qs = _qs()
    result: Dict[str, str] = {}
    for key in _DST_KEYS:
        default = config.EXPECTED_DST.get(key, "")
        result[key] = str(qs.value(f"{_GROUP}/dst/{key}", default))
    return result


def max_time_diff_seconds() -> int:
    try:
        return int(_qs().value(f"{_GROUP}/max_time_diff_seconds", config.MAX_TIME_DIFF_SECONDS))
    except (TypeError, ValueError):
        return config.MAX_TIME_DIFF_SECONDS


def save_settings(
    ntp_addresses: List[str],
    ntp_port: str,
    ntp_enable: bool,
    dst: Dict[str, str],
    max_time_diff: int,
) -> None:
    qs = _qs()
    qs.setValue(f"{_GROUP}/ntp_addresses", list(ntp_addresses))
    qs.setValue(f"{_GROUP}/ntp_port", str(ntp_port))
    qs.setValue(f"{_GROUP}/ntp_enable", bool(ntp_enable))
    for key in _DST_KEYS:
        if key in dst:
            qs.setValue(f"{_GROUP}/dst/{key}", str(dst[key]))
    qs.setValue(f"{_GROUP}/max_time_diff_seconds", int(max_time_diff))
    qs.sync()


def reset_to_defaults() -> None:
    qs = _qs()
    qs.remove(_GROUP)
    qs.sync()
