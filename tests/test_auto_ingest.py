
import asyncio
import os
import shutil
from openmemx.mcp_server import (
    configure_auto_ingest, 
    retrieve_memory, 
    get_engine, 
    get_conversation_id,
    get_auto_ingest_status
)

async def test_auto_ingest_flow():
    print("Testing Auto-Ingest Feature...")
    
    # 1. Setup fresh test environment
    test_base = os.path.abspath("./test_auto_ingest")
    if os.path.exists(test_base):
        shutil.rmtree(test_base)
    
    # Force engine to use test path
    from openmemx.memory_engine import MemoryEngine
    engine = MemoryEngine(base_path=test_base)
    
    # We need to monkeypatch the mcp_server's engine so the tools use our test engine
    import openmemx.mcp_server as mcp_server
    mcp_server._engine = engine
    
    try:
        # 2. Enable Auto-Ingest
        print("Enabling auto-ingest...")
        await configure_auto_ingest(enabled=True, log_queries=True, log_responses=True)
        
        status = await get_auto_ingest_status()
        print(f"Current Status:\n{status}")
        
        # 3. Trigger a tool that auto-logs (retrieve_memory)
        conv_id = get_conversation_id()
        query = "What is the capital of France?"
        print(f"Calling retrieve_memory with query: '{query}'")
        
        # This should log the query automatically
        await retrieve_memory(conversation_id=conv_id, query=query)
        
        # 4. Verify episodic memory contains the auto-logged query
        memories = engine.retrieve_episodic(conv_id)
        
        found_query = False
        for m in memories:
            if query in m.content:
                found_query = True
                print(f"✅ Found auto-logged query in memory: '{m.content}'")
            if "Memory retrieval" in m.content:
                 print(f"✅ Found auto-logged response in memory: '{m.content[:50]}...'")

        if found_query:
            print("\n✨ AUTO-INGEST TEST SUCCESSFUL! ✨")
            print("The system automatically captured your interaction without an explicit 'ingest' call.")
        else:
            print("\n❌ AUTO-INGEST TEST FAILED!")
            
    finally:
        if os.path.exists(test_base):
            shutil.rmtree(test_base)

if __name__ == "__main__":
    asyncio.run(test_auto_ingest_flow())
