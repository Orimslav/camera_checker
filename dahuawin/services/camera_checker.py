import concurrent.futures
from typing import Dict, List

import dahuawin.config as config
from dahuawin.camera_modules.dahua_camera import DahuaCamera
from dahuawin.camera_modules.device_detector import DeviceDetector
from dahuawin.camera_modules.hikvision_camera import HikvisionCamera
from dahuawin.services.csv_loader import CSVLoader


class CameraChecker:
    def __init__(self, csv_file: str):
        self.csv_loader = CSVLoader(csv_file)
        self.results: List[Dict] = []

    def load_cameras(self) -> List[Dict]:
        return self.csv_loader.load_cameras()

    def create_camera_instance(self, camera_data: Dict):
        vendor = DeviceDetector.detect_vendor(camera_data["model"], camera_data["name"])
        common_args = (
            camera_data["ip"],
            camera_data["username"],
            camera_data["password"],
            camera_data["name"],
            camera_data["model"],
        )

        if vendor == "Switch":
            camera = DahuaCamera(*common_args)
            camera.skipped = True
            camera.skip_reason = "Switch"
            return camera
        if vendor == "Server":
            camera = DahuaCamera(*common_args)
            camera.skipped = True
            camera.skip_reason = "Server"
            return camera
        if vendor == "Hikvision":
            return HikvisionCamera(*common_args)
        return DahuaCamera(*common_args)

    def check_camera(self, camera_data: Dict) -> Dict:
        if camera_data["ip"] in config.SKIP_IPS:
            return {
                "ip": camera_data["ip"],
                "name": camera_data["name"],
                "skipped": True,
                "skip_reason": "Manualne preskocene",
                "issues": [],
            }

        camera = self.create_camera_instance(camera_data)
        return camera.check_all()

    def run_check(self, progress_callback=None) -> List[Dict]:
        cameras_data = self.load_cameras()
        results: List[Dict] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            futures = {executor.submit(self.check_camera, camera): camera for camera in cameras_data}
            done = 0
            total = len(cameras_data)

            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
                done += 1
                if progress_callback:
                    progress_callback(done, total, result)

        self.results = results
        return results

    def summarize(self, results: List[Dict] = None) -> Dict:
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

    def fix_camera(self, camera_data: Dict, fix_ntp: bool = True, fix_dst: bool = True, sync_time: bool = True) -> Dict:
        camera = self.create_camera_instance(camera_data)
        if not camera.authenticate():
            return {"success": False, "error": "Authentication failed"}

        changes = []
        if fix_ntp:
            changes.append({"setting": "NTP", "success": camera.set_ntp_settings()})
        if fix_dst:
            changes.append({"setting": "DST", "success": camera.set_dst_settings()})
        if sync_time:
            changes.append({"setting": "Time Sync", "success": camera.sync_time_now()})

        camera.get_ntp_settings()
        camera.get_dst_settings()
        camera.get_current_time()

        verification = {
            "ntp_ok": len(camera.ntp_issues) == 0,
            "dst_ok": len(camera.dst_issues) == 0,
            "time_ok": abs(camera.time_diff) < config.MAX_TIME_DIFF_SECONDS if camera.time_diff is not None else False,
        }
        return {
            "success": all(change["success"] for change in changes) if changes else True,
            "changes": changes,
            "verification": verification,
        }
