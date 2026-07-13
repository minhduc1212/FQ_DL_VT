import os
import json

class ConfigManager:
    CONFIG_FILE = "config.json"
    DEFAULT_CONFIG = {
        "concurrency": 8,
        "retry_attempts": 3,
        "timeout": 10,
        "download_dir": "downloads",
        "save_format": "Một file TXT duy nhất",
        "request_delay": 0.3,
    }

    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    # Sync default keys if missing
                    for k, v in self.DEFAULT_CONFIG.items():
                        if k not in config:
                            config[k] = v
                    return config
            except Exception:
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def save(self):
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Không thể lưu cấu hình: {e}")

    def get(self, key):
        return self.config.get(key, self.DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save()
