import dahuawin.config as config


class DeviceDetector:
    @staticmethod
    def is_hikvision(model: str, name: str = "") -> bool:
        if not model and not name:
            return False

        text = f"{model} {name}".upper()
        return any(keyword in text for keyword in config.HIKVISION_KEYWORDS)

    @staticmethod
    def is_switch(model: str, name: str = "", device_type: str = "") -> bool:
        if not model and not name and not device_type:
            return False

        text = f"{model} {name} {device_type}".upper()
        return any(keyword in text for keyword in config.SWITCH_KEYWORDS)

    @staticmethod
    def is_server(device_type: str = "", name: str = "") -> bool:
        if not device_type:
            return False

        text = f"{device_type}".upper()
        return any(keyword in text for keyword in config.SERVER_KEYWORDS)

    @staticmethod
    def is_dahua(model: str) -> bool:
        if not model:
            return True

        model_upper = str(model).upper()
        return any(model_upper.startswith(prefix) or prefix in model_upper for prefix in config.DAHUA_PREFIXES)

    @staticmethod
    def detect_vendor(model: str, name: str = "") -> str:
        if DeviceDetector.is_hikvision(model, name):
            return "Hikvision"
        if DeviceDetector.is_switch(model, name):
            return "Switch"
        if DeviceDetector.is_server(name=name):
            return "Server"
        if DeviceDetector.is_dahua(model):
            return "Dahua"
        return "Unknown"
