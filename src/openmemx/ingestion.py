
import os
import json
import glob
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

class UniversalLogIngester:
    """
    A generic log ingestion engine that can read activity data from ANY external source
    configured via JSON patterns.
    This eliminates hardcoded adapters by allowing the user to specify file paths,
    glob patterns, and field mappings dynamically.
    """

    def __init__(self, config: Dict[str, Any]):
        self.sources = config.get("external_sources", [])

    def scan_all(self, hours: int = 24) -> List[Dict[str, Any]]:
        activities = []
        # Calculate naive cutoff timestamp
        cutoff_ts = (datetime.now(timezone.utc).timestamp()) - (hours * 3600)
        
        for source in self.sources:
            try:
                activities.extend(self._scan_source(source, cutoff_ts))
            except Exception:
                # Log error but don't crash
                # print(f"Error scanning source {source.get('name')}: {e}")
                pass
                
        return activities

    def _scan_source(self, source_config: Dict[str, Any], cutoff_ts: float) -> List[Dict[str, Any]]:
        name = source_config.get("name", "Unknown Source")
        path_pattern = os.path.expanduser(source_config.get("path", ""))
        format_type = source_config.get("format", "json") # json, jsonl, text
        mapping = source_config.get("mapping", {})
        
        results = []
        
        # Glob Support (recursive if ** used)
        files = glob.glob(path_pattern, recursive=True)
        
        for file_path in files:
            # Skip old files by modification time first (optimization)
            if os.path.getmtime(file_path) < cutoff_ts:
                continue
                
            if format_type == "jsonl":
                results.extend(self._parse_jsonl(file_path, name, mapping, cutoff_ts))
            elif format_type == "json":
                results.extend(self._parse_json(file_path, name, mapping, cutoff_ts))
            elif format_type == "text":
                results.extend(self._parse_text(file_path, name, mapping, cutoff_ts))
                
        return results

    def _extract_field(self, record: Dict[str, Any], field_path: str) -> Any:
        """Helper to extract nested fields like 'metadata.created_at'"""
        if not field_path:
            return None
        keys = field_path.split('.')
        val = record
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return None
        return val

    def _parse_timestamp(self, ts_val: Any) -> Optional[float]:
        """ Tries to parse a timestamp into float seconds """
        if not ts_val:
            return None
        if isinstance(ts_val, (int, float)):
            # Assume seconds if small, milliseconds?
            # Heuristic: 2020 in seconds > 1.5e9
            if ts_val > 1e11:
                return ts_val / 1000.0
            return float(ts_val)
        
        if isinstance(ts_val, str):
            try:
                # Try ISO
                dt = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                return dt.timestamp()
            except Exception:
                pass
        return None

    def _map_record(self, raw_record: Dict[str, Any], name: str, mapping: Dict[str, str], file_ts: float, cutoff_ts: float) -> Optional[Dict[str, Any]]:
        # 1. Project Logic
        project = "External"
        if "project" in mapping:
            project = self._extract_field(raw_record, mapping["project"]) or project
        
        # 2. Timestamp Logic
        ts = file_ts
        if "timestamp" in mapping:
            extracted_ts = self._extract_field(raw_record, mapping["timestamp"])
            parsed_ts = self._parse_timestamp(extracted_ts)
            if parsed_ts:
                ts = parsed_ts
        
        if ts < cutoff_ts:
            return None

        # 3. Role/Content
        role = "unknown"
        if "role" in mapping:
            role = self._extract_field(raw_record, mapping["role"]) or role
            
        content = ""
        if "content" in mapping:
            content = self._extract_field(raw_record, mapping["content"]) or ""
            
        if not content:
            return None

        return {
            "source": name,
            "project": project,
            "timestamp": datetime.fromtimestamp(ts),
            "role": role,
            "content": content
        }

    def _parse_jsonl(self, path: str, name: str, mapping: Dict[str, str], cutoff_ts: float) -> List[Dict[str, Any]]:
        items = []
        file_ts = os.path.getmtime(path)
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        item = self._map_record(record, name, mapping, file_ts, cutoff_ts)
                        if item:
                            items.append(item)
                    except Exception:
                        continue
        except Exception:
            pass
        return items

    def _parse_json(self, path: str, name: str, mapping: Dict[str, str], cutoff_ts: float) -> List[Dict[str, Any]]:
        items = []
        file_ts = os.path.getmtime(path)
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                
                # Check if root is list
                records = data if isinstance(data, list) else [data]
                
                # Special case: Gemini often has "messages": []
                if isinstance(data, dict) and "messages" in data:
                    records = data["messages"]
                
                for record in records:
                    item = self._map_record(record, name, mapping, file_ts, cutoff_ts)
                    if item:
                        items.append(item)
        except Exception:
            pass
        return items

    def _parse_text(self, path: str, name: str, mapping: Dict[str, str], cutoff_ts: float) -> List[Dict[str, Any]]:
        # Text is harder. We assume the whole line is content unless regex is added (future enhancement).
        # For now: Timestamp = file mtime, Content = line
        items = []
        file_ts = os.path.getmtime(path)
        if file_ts < cutoff_ts:
            return []
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read last 100 lines
                lines = f.readlines()[-100:]
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    items.append({
                        "source": name,
                        "project": "Log File",
                        "timestamp": datetime.fromtimestamp(file_ts),
                        "role": "system",
                        "content": line
                    })
        except Exception:
            pass
        return items
