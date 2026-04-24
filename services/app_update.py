import requests
from typing import Optional, Tuple

class AppUpdater:
    def __init__(self, repo: str, current_version: str) -> None:
        self.repo = repo
        self.current_version = current_version
        self.url = f"https://api.github.com/repos/{repo}/releases/latest"

    def get_latest_release(self) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        try:
            response = requests.get(self.url, timeout=5)
            response.raise_for_status()
            data = response.json()

            version = data.get("tag_name")
            url = data.get("html_url")
            changelog = data.get("body", "")

            assets = data.get("assets", [])
            download_url = None

            for asset in assets:
                name = asset.get("name", "")
                if name.endswith(".exe"):
                    download_url = asset.get("browser_download_url")
                    break

            return version, url, changelog, download_url

        except requests.RequestException:
            return None, None, None, None

    def is_update_available(self) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        latest_version, url, changelog, download_url = self.get_latest_release()

        if not latest_version:
            return False, None, None, None

        if self._normalize_version(latest_version) > self._normalize_version(self.current_version):
            return True, url, changelog, download_url

        return False, None, None, None

    def _normalize_version(self, v:str) -> tuple:
        """Yu-Gi-Oh! Desktop Companion App v1.0.0 -> (1,0,0)"""
        v = v.lower().replace("v", "")
        return tuple(int(x) for x in v.split(".") if x.isdigit())