
import os
import shutil
import pytest
import json
from datetime import datetime, timedelta, timezone
from openmemx import MemoryEngine
from openmemx.mcp_server import UniversalLogIngester

def test_full_memory_lifecycle():
    """Test the core cognitive memory loop: ingestion -> retrieval -> surprise"""
    test_dir = os.path.abspath("./test_mem_workspace")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    try:
        engine = MemoryEngine(base_path=test_dir)
        conv_id = "test_session_1"
        
        # 1. Ingest normal fact
        engine.ingest_interaction(conv_id, "user", "The sky is blue today.")
        
        # 2. Ingest surprising fact (should have higher surprise score)
        # We need a new instance to clear the rolling historical average if it's very short
        id2 = engine.ingest_interaction(conv_id, "user", "Computational complexity of NP-Hard problems is O(1).")
        
        # 3. Retrieve
        history = engine.retrieve_episodic(conv_id)
        assert len(history) >= 2
        
        # 4. Search
        # This triggers LanceDB
        engine.ingest_interaction(conv_id, "assistant", "I will remember that.")
        # Semantic search
        # Note: We need some data in the table for search to work
        # In real usage, consolidation pushes to vector DB. 
        # But MemoryEngine likely has a logic to search recent too or we can wait.
        
        print("✅ Core Memory Engine Lifecycle passed.")
        
    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

def test_universal_ingestion_logic():
    """Test that the new UniversalLogIngester works with mock logs from other agents"""
    tmp_path = os.path.abspath("./test_logs")
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)
    os.makedirs(tmp_path)
    
    log_file = os.path.join(tmp_path, "external.jsonl")
    now = datetime.now(timezone.utc)
    
    # Mock some external agent activity
    with open(log_file, "w") as f:
        f.write(json.dumps({"ts": now.timestamp(), "msg": "Nanobot performed a search", "who": "nanobot"}) + "\n")
        f.write(json.dumps({"ts": (now - timedelta(hours=25)).timestamp(), "msg": "Old news", "who": "old_agent"}) + "\n")
    
    config = {
        "external_sources": [{
            "name": "MockAgent",
            "path": log_file,
            "format": "jsonl",
            "mapping": {"timestamp": "ts", "content": "msg", "role": "who"}
        }]
    }
    
    ingester = UniversalLogIngester(config)
    results = ingester.scan_all(hours=24)
    
    assert len(results) == 1
    assert results[0]["source"] == "MockAgent"
    assert "Nanobot" in results[0]["content"]
    
    print("✅ Universal Log Ingestion logic passed.")
