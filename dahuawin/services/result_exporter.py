import csv
from typing import Dict, List


class ResultExporter:
    TRANSLATIONS = {
        "sk": {
            "headers": [
                "IP",
                "Nazov",
                "Vendor",
                "Model",
                "Status",
                "Cas",
                "Casova odchylka",
                "Problemy",
                "Typ autentifikacie",
                "Preskocena",
                "Dovod preskocenia",
            ],
            "yes": "Ano",
            "no": "Nie",
            "status": {
                "ok": "OK",
                "problem": "Problem",
                "auth_failed": "Auth failed",
                "skipped": "Preskocena",
            },
        },
        "en": {
            "headers": [
                "IP",
                "Name",
                "Vendor",
                "Model",
                "Status",
                "Time",
                "Time difference",
                "Issues",
                "Authentication type",
                "Skipped",
                "Skip reason",
            ],
            "yes": "Yes",
            "no": "No",
            "status": {
                "ok": "OK",
                "problem": "Problem",
                "auth_failed": "Auth failed",
                "skipped": "Skipped",
            },
        },
    }

    def export_csv(self, file_path: str, rows: List[Dict], language: str = "sk") -> None:
        texts = self.TRANSLATIONS.get(language, self.TRANSLATIONS["sk"])
        with open(file_path, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(texts["headers"])
            for row in self._normalized_rows(rows, texts):
                writer.writerow(row)

    def export_excel(self, file_path: str, rows: List[Dict], language: str = "sk") -> None:
        from openpyxl import Workbook

        texts = self.TRANSLATIONS.get(language, self.TRANSLATIONS["sk"])
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Vysledky kontroly" if language == "sk" else "Check Results"
        sheet.append(texts["headers"])

        normalized_rows = self._normalized_rows(rows, texts)
        for row in normalized_rows:
            sheet.append(row)

        for column_cells in sheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 2, 40)

        sheet.freeze_panes = "A2"
        workbook.save(file_path)

    def _normalized_rows(self, rows: List[Dict], texts: Dict) -> List[List[str]]:
        normalized = []
        for camera in rows:
            issues = ", ".join(camera.get("issues", [])) or camera.get("skip_reason", "")
            normalized.append(
                [
                    camera.get("ip", ""),
                    camera.get("name", ""),
                    camera.get("vendor", ""),
                    camera.get("model", "") or "",
                    self._camera_status(camera, texts),
                    camera.get("current_time", "") or "",
                    "" if camera.get("time_diff") is None else f"{camera.get('time_diff'):+.0f}s",
                    issues,
                    camera.get("auth_type", "") or "",
                    texts["yes"] if camera.get("skipped") else texts["no"],
                    camera.get("skip_reason", "") or "",
                ]
            )
        return normalized

    def _camera_status(self, camera: Dict, texts: Dict) -> str:
        if camera.get("skipped"):
            return texts["status"]["skipped"]
        if not camera.get("auth_ok"):
            return texts["status"]["auth_failed"]
        if camera.get("issues"):
            return texts["status"]["problem"]
        return texts["status"]["ok"]
