import json
from datetime import date
from pathlib import Path
from typing import Mapping


class UsageTracker:
    def __init__(self, file_path: str | Path, limits: Mapping[str, int]):
        self.path = Path(file_path)
        self.limits = dict(limits)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _empty(self) -> dict:
        return {"date": date.today().isoformat(), **{k: 0 for k in self.limits}}

    def _load(self) -> dict:
        if not self.path.exists():
            data = self._empty()
            self._write(data)
            return data
        data = json.loads(self.path.read_text())
        if data.get("date") != date.today().isoformat():
            data = self._empty()
            self._write(data)
        for k in self.limits:
            data.setdefault(k, 0)
        return data

    def _write(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, indent=2))

    def _require(self, service: str) -> None:
        if service not in self.limits:
            raise ValueError(f"Unknown service: {service}")

    def record_usage(self, service: str, amount: int) -> None:
        self._require(service)
        self._data = self._load()
        self._data[service] = self._data.get(service, 0) + amount
        self._write(self._data)

    def check_limit(self, service: str, amount: int) -> bool:
        self._require(service)
        self._data = self._load()
        return self._data.get(service, 0) + amount <= self.limits[service]

    def get_usage_status(self) -> dict:
        self._data = self._load()
        out = {}
        for k, limit in self.limits.items():
            used = self._data.get(k, 0)
            out[k] = {
                "used": used,
                "limit": limit,
                "percent": round((used / limit) * 100, 2) if limit else 0.0,
            }
        return out
