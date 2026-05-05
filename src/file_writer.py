import json
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

class JsonFileWriter:

    def __init__(self, base_dir):

        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def exists(self, message_id: str) -> bool:
        """
        Проверяет, существует ли уже файл для данного message_id.
        """
        return any(self.base_dir.glob(f"**/{message_id}.json"))

    def _get_path(self, message_id: str, date_str: str) -> Path:
        """
        Определяет полный путь к файлу JSON:
        base_dir/YYYY-MM-DD/message_id.json
        """        
        date_part = date_str.split("T")[0] if "T" in date_str else date_str[:10]
        date_dir = self.base_dir / date_part
        date_dir.mkdir(parents=True, exist_ok=True)
        return date_dir / f"{message_id}.json"

    def save(self, record: Dict):
        """
        Сохраняет тело письма в JSON.
        record должен содержать ключи 'message_id' и 'received_at'.
        """
        message_id = record["message_id"]
        received_at = record["received_at"]

        filepath = self._get_path(message_id, received_at)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2, default=str)
        logger.info("File was saved: %s", filepath)