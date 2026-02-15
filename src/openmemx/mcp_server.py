import sys
import os
import json
import uuid
from datetime import datetime
from functools import wraps

# Redirect stdout to stderr immediately to catch all library noise during imports
_original_stdout = sys.stdout
sys.stdout = sys.stderr

import asyncio
from mcp.server.fastmcp import FastMCP
from typing import List, Optional, Dict, Any
import logging
from .ingestion import UniversalLogIngester

# Suppress Transformers/HF logs from stdout
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Suppress Transformers/HF logs
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Initialize FastMCP server
mcp = FastMCP("OpenMemX")

_engine = None
_config = None
_current_conversation_id = None

# Default configuration
DEFAULT_CONFIG = {
    "auto_ingest": {
        "enabled": True,
        "log_queries": True,
        "log_responses": True,
        "conversation_timeout_minutes": 30
    },
    "storage": {
        "base_path": "~/.openmemx",
        "max_episodic_items": 1000
    },
    "external_sources": [
        {
            "name": "Nanobot",
            "path": "~/.nanobot/sessions/cli_direct.jsonl",
            "format": "jsonl",
            "mapping": {"timestamp": "created_at", "role": "role", "content": "content", "project": "project"}
        },
        {
            "name": "OpenWork",
            "path": "~/.openwork/owpenbot/logs/*.log",
            "format": "text",
            "mapping": {}
        },
        {
            "name": "Gemini CLI",
            "path": "~/.gemini/tmp/**/chats/*.json",
            "format": "json",
            "mapping": {"timestamp": "timestamp", "role": "role", "content": "text"}
        }
    ]
}

def get_config_path():
    """Get the path to the configuration file."""
    base_path = os.path.expanduser("~/.openmemx")
    return os.path.join(base_path, "config.json")

def load_config():
    """Load configuration from file or create default."""
    global _config
    if _config is not None:
        return _config
    
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                _config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in DEFAULT_CONFIG.items():
                    if key not in _config:
                        _config[key] = value
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if sub_key not in _config[key]:
                                _config[key][sub_key] = sub_value
        except Exception as e:
            print(f"Warning: Could not load config, using defaults: {e}", file=sys.stderr)
            _config = DEFAULT_CONFIG.copy()
    else:
        _config = DEFAULT_CONFIG.copy()
        # Save default config
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        try:
            with open(config_path, 'w') as f:
                json.dump(_config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save default config: {e}", file=sys.stderr)
    
    return _config

def save_config():
    """Save current configuration to file."""
    global _config
    config_path = get_config_path()
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(_config, f, indent=2)

def get_project_registry_path():
    """Get the path to the project registry file."""
    base_path = os.path.expanduser("~/.openmemx")
    return os.path.join(base_path, "project_registry.json")

def load_project_registry():
    """Load the project registry."""
    path = get_project_registry_path()
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_project_registry(registry):
    """Save the project registry."""
    path = get_project_registry_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(registry, f, indent=2)

def get_conversation_id():
    """
    Get or create a conversation ID for the current session.
    Persists the ID based on the current working directory to allow session resumption.
    """
    global _current_conversation_id
    
    if _current_conversation_id is None:
        # 1. Try to load from registry based on CWD
        cwd = os.getcwd() # MCP servers usually run in the project root
        registry = load_project_registry()
        
        if cwd in registry:
            _current_conversation_id = registry[cwd]
        else:
            # 2. Generate new ID if none exists for this project
            _current_conversation_id = f"auto_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            registry[cwd] = _current_conversation_id
            save_project_registry(registry)
            
    return _current_conversation_id

def reset_conversation_id():
    """Reset the conversation ID (start a new conversation) and update registry."""
    global _current_conversation_id
    
    # Generate new ID
    new_id = f"auto_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    _current_conversation_id = new_id
    
    # Update registry for current project
    cwd = os.getcwd()
    registry = load_project_registry()
    registry[cwd] = new_id
    save_project_registry(registry)
    
    return new_id

def get_engine():
    global _engine
    if _engine is None:
        from .memory_engine import MemoryEngine
        config = load_config()
        base_path = config.get("storage", {}).get("base_path", "~/.openmemx")
        _engine = MemoryEngine(base_path=os.path.expanduser(base_path))
    return _engine

def auto_log_interaction(query_text: str = None, response_text: str = None, conversation_id: str = None):
    """
    Automatically log interactions if auto_ingest is enabled.
    This is called by tools to capture context automatically.
    """
    config = load_config()
    if not config.get("auto_ingest", {}).get("enabled", True):
        return
    
    engine = get_engine()
    conv_id = conversation_id or get_conversation_id()
    
    if query_text and config.get("auto_ingest", {}).get("log_queries", True):
        try:
            engine.ingest_interaction(conv_id, "user", query_text)
        except Exception as e:
            print(f"Warning: Auto-ingest query failed: {e}", file=sys.stderr)
    
    if response_text and config.get("auto_ingest", {}).get("log_responses", True):
        try:
            engine.ingest_interaction(conv_id, "assistant", response_text)
        except Exception as e:
            print(f"Warning: Auto-ingest response failed: {e}", file=sys.stderr)

# Do NOT eagerly initialize here to ensure the MCP server starts instantly.
# get_engine()

@mcp.tool()
async def ingest_interaction(conversation_id: str, role: str, content: str) -> str:
    """
    Ingests a new interaction into episodic memory.
    AGENTIC HINT: Call this after every meaningful interaction to track Bayesian Surprise and enable future retrieval.
    """
    engine = get_engine()
    interaction_id = engine.ingest_interaction(conversation_id, role, content)
    return f"Interaction {interaction_id} ingested successfully."

@mcp.tool()
async def retrieve_memory(conversation_id: str, query: str, limit: int = 5) -> str:
    """
    Retrieves relevant memories across all history using semantic search.
    AUTO-INGEST: This tool automatically logs your query for future reference.
    """
    # Auto-log the query
    auto_log_interaction(query_text=query, conversation_id=conversation_id)
    
    engine = get_engine()
    # Search the master vector table (contains all previous sessions)
    table_name = "master_vectors"
    try:
        if table_name not in engine.lancedb.table_names():
            return "No memories have been recorded yet. Call ingest_interaction to start building your knowledge base."
            
        table = engine.lancedb.open_table(table_name)
        embedding = engine.logic.model.encode([query])[0]
        results = table.search(embedding).limit(limit).to_list()
        
        if not results:
            return "No relevant memories found for this query."
            
        formatted_results = []
        for r in results:
            tag = "[Recent]" if r['conversation_id'] == conversation_id else f"[Past Session: {r['conversation_id'][:8]}...]"
            formatted_results.append(f"{tag} ({r['role']}): {r['content']}")
        
        result_text = "\n---\n".join(formatted_results)
        
        # Auto-log the response
        auto_log_interaction(response_text=f"Memory retrieval: {result_text[:200]}...", conversation_id=conversation_id)
        
        return result_text
    except Exception as e:
        return f"Error occurred during retrieval: {str(e)}"

@mcp.tool()
async def compress_prompt(context: str, instruction: str = "", target_token: int = 500) -> str:
    """
    Compresses a long prompt using LLMLingua-2 to fit within context limits.
    """
    engine = get_engine()
    try:
        compressed = engine.compressor.compress(context, instruction, target_token)
        return compressed
    except Exception as e:
        return f"Compression failed: {str(e)}"

@mcp.tool()
async def snapshot_memory(message: str) -> str:
    """
    Creates a Git snapshot of the current state of memory for versioning.
    """
    engine = get_engine()
    try:
        engine.snapshot(message)
        return "Memory snapshot committed successfully."
    except Exception as e:
        return f"Snapshot failed: {str(e)}"

@mcp.tool()
async def add_knowledge_node(entity: str, description: str, node_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Adds or updates a node in the semantic knowledge graph.
    """
    engine = get_engine()
    try:
        node_id = engine.add_knowledge_node(entity, description, node_data)
        return f"Knowledge node '{entity}' (ID: {node_id}) added/updated."
    except Exception as e:
        return f"Failed to add knowledge node: {str(e)}"

@mcp.tool()
async def add_knowledge_edge(source_entity: str, target_entity: str, relationship: str) -> str:
    """
    Adds a relationship between two existing entities in the knowledge graph.
    """
    engine = get_engine()
    try:
        edge_id = engine.add_knowledge_edge(source_entity, target_entity, relationship)
        return f"Relationship '{relationship}' between '{source_entity}' and '{target_entity}' added (ID: {edge_id})."
    except Exception as e:
        return f"Failed to add knowledge edge: {str(e)}"

@mcp.tool()
async def traverse_knowledge_graph(start_entity: str, max_depth: int = 2) -> str:
    """
    Walks the knowledge graph from a starting entity to find connected concepts.
    AGENTIC HINT: Use this for multi-hop reasoning when simple retrieval isn't enough.
    """
    engine = get_engine()
    try:
        results = engine.traverse_graph(start_entity, max_depth)
        if not results:
            return f"No connections found for entity '{start_entity}'."
            
        formatted = [f"{r['source']} --({r['relationship']})--> {r['target']}: {r['description']}" for r in results]
        return "\n".join(formatted)
    except Exception as e:
        return f"Graph traversal failed: {str(e)}"

@mcp.tool()
async def configure_auto_ingest(enabled: bool = True, log_queries: bool = True, log_responses: bool = True) -> str:
    """
    Configure the automatic memory ingestion settings.
    When enabled, queries and responses are automatically logged without explicit ingest_interaction calls.
    """
    global _config
    config = load_config()
    
    config["auto_ingest"]["enabled"] = enabled
    config["auto_ingest"]["log_queries"] = log_queries
    config["auto_ingest"]["log_responses"] = log_responses
    
    save_config()
    
    status = "ENABLED" if enabled else "DISABLED"
    return f"Auto-ingest is now {status}.\n" \
           f"- Log queries: {log_queries}\n" \
           f"- Log responses: {log_responses}\n" \
           f"Configuration saved to ~/.openmemx/config.json"

@mcp.tool()
async def get_auto_ingest_status() -> str:
    """
    Get the current auto-ingest configuration status.
    """
    config = load_config()
    auto_ingest = config.get("auto_ingest", {})
    
    return f"Auto-Ingest Configuration:\n" \
           f"- Enabled: {auto_ingest.get('enabled', True)}\n" \
           f"- Log queries: {auto_ingest.get('log_queries', True)}\n" \
           f"- Log responses: {auto_ingest.get('log_responses', True)}\n" \
           f"- Conversation timeout: {auto_ingest.get('conversation_timeout_minutes', 30)} minutes\n" \
           f"- Current conversation ID: {get_conversation_id()}"

@mcp.tool()
async def start_new_conversation() -> str:
    """
    Start a new conversation session with a fresh conversation ID.
    Use this when you want to separate different topics or sessions.
    """
    new_id = reset_conversation_id()
    return f"Started new conversation with ID: {new_id}"

@mcp.tool()
async def log_interaction(content: str, role: str = "user") -> str:
    """
    Log an interaction to memory using the current auto-generated conversation ID.
    This is a convenience tool for quick logging without managing conversation IDs.
    AUTO-INGEST: Automatically uses the current session's conversation ID.
    """
    conv_id = get_conversation_id()
    engine = get_engine()
    interaction_id = engine.ingest_interaction(conv_id, role, content)
    return f"Logged interaction {interaction_id} to conversation {conv_id}"

@mcp.resource("memory://instructions")
def get_memory_instructions() -> str:
    """
    Provides the 'OpenMemX' agentic instructions.
    Agents should read this to understand how to manage memory.
    """
    get_engine()  # Force folder/engine initialization
    return """
# OpenMemX: Agentic Memory Guide
You are equipped with a hierarchical memory system designed for token optimization and long-term reasoning.

## 🎉 NEW: Auto-Ingest & Global Memory
**Your memories are now Project-Aware and Persistent!**
- **Persistence**: Usage in a folder (e.g., `~/projects/app`) resumes that project's specific memory session.
- **Global Awareness**: Use `get_recent_activity` to see what you (or other agents) did across ALL projects today.
- **Auto-Log**: Queries are automatically logged.

## Your Strategy:
1. **Multi-Project Status**: Start your day with `get_recent_activity` to catch up on all ongoing work.
2. **Context Retrieval**: Use `retrieve_memory` to get relevant semantic context for the current query.
3. **Reasoning**: Use `traverse_knowledge_graph` to perform multi-hop reasoning over crystallized facts.
4. **Compression**: If context is too long, use `compress_prompt` (LLMLingua-2) before sending to your internal model.
5. **Sleep Cycle**: Periodically call `consolidate_memory`. It identifies high-surprise items. You should then create Knowledge Nodes (`add_knowledge_node`) and Edges (`add_knowledge_edge`) for these insights.
6. **Persistence**: Use `snapshot_memory` to checkpoint the entire memory state to Git.
7. **Session Management**: Use `start_new_conversation` to start fresh conversation threads.
    """

@mcp.prompt("openmemx_system_init")
def openmemx_system_init() -> str:
    """
    Prompt template to initialize the agent with OpenMemX capabilities.
    """
    return "Please read the memory instructions at 'memory://instructions' and use the available memory tools to manage your long-term context effectively."

@mcp.resource("memory://episodic/{conversation_id}")
def get_episodic_memory(conversation_id: str) -> str:
    """
    Returns the raw episodic memory log for a conversation.
    """
    engine = get_engine()
    memories = engine.retrieve_episodic(conversation_id)
    return "\n".join([f"{m.timestamp} [{m.role}]: {m.content} (Surprise: {m.surprise_score:.2f})" for m in memories])

@mcp.resource("memory://semantic/graph")
def get_semantic_graph() -> str:
    """
    Returns a summary of all entities in the semantic knowledge graph.
    """
    engine = get_engine()
    nodes = engine.get_all_nodes()
    return "\n".join([f"- {n.entity}: {n.description}" for n in nodes])

@mcp.tool()
async def consolidate_memory(conversation_id: str) -> str:
    """
    Triggers the 'sleep cycle' consolidation. Identifies high-surprise items 
    for semantic promotion and prunes low-surprise episodic noise.
    """
    engine = get_engine()
    try:
        # 1. Identify items for promotion (High Surprise)
        history = engine.retrieve_episodic(conversation_id, limit=100)
        high_surprise = [h for h in history if h.surprise_score > 0.5]
        
        # 2. Prune items (Low Surprise)
        # Threshold: 0.1 is very common/redundant. 
        # Research says: "prunes low-surprise episodic events"
        num_pruned = engine.prune_interactions(conversation_id, threshold=0.1)
        
        status = f"Consolidation complete. Pruned {num_pruned} low-surprise episodic memories."
        
        if high_surprise:
            summary = "\n".join([f"- {h.content}" for h in high_surprise])
            return f"{status}\n\nKey insights identified for semantic storage:\n{summary}\n\nPlease formalize these using 'add_knowledge_node'."
        
        return f"{status} No new key insights for semantic promotion found."
    except Exception as e:
        return f"Consolidation failed: {str(e)}"

@mcp.tool()
async def get_recent_activity(hours: int = 24) -> str:
    """
    Get a global summary of what has been done recently across ALL projects/directories.
    This aggregates:
    1. Internal OpenMemX memory
    2. Any external sources configured in config.json (external_sources)
    """
    engine = get_engine()
    
    # 1. Fetch Internal Activities
    internal_interactions = engine.fetch_recent_activities(hours=hours)
    
    # 2. Fetch External Activities via Universal Ingester
    config = load_config()
    ingester = UniversalLogIngester(config)
    external_activities = ingester.scan_all(hours=hours)
    
    all_items = []
    
    # Normalize Internal
    registry = load_project_registry()
    cid_to_path = {cid: path for path, cid in registry.items()}
    
    for i in internal_interactions:
        cid = i.conversation_id
        path = cid_to_path.get(cid, "Unknown Project")
        all_items.append({
            "source": "OpenMemX",
            "project": path,
            "conversation_id": cid,
            "timestamp": i.timestamp,
            "role": i.role,
            "content": i.content
        })
        
    # Normalize External
    for e in external_activities:
        all_items.append(e)
        
    if not all_items:
        return "No activity recorded in the last 24 hours across any agent."

    # Sort by timestamp (newest first)
    all_items.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Group by Source -> Project
    from collections import defaultdict
    grouped = defaultdict(lambda: defaultdict(list))
    
    for item in all_items:
        source = item.get("source", "Unknown Source")
        project = item.get("project", "Unknown Project")
        grouped[source][project].append(item)
    
    # Format output
    report = []
    report.append(f"# Global Activity Report (Last {hours} hours)\n")
    
    for source in sorted(grouped.keys()):
        report.append(f"## 🤖 Monitor: {source}")
        for project, items in grouped[source].items():
            report.append(f"  ### 📂 Project: {project}")
            
            # Limit items per project
            display_items = items[:5]
            for item in display_items:
                ts_str = item['timestamp'].strftime('%H:%M')
                role = item['role']
                content = item['content'].replace('\n', ' ')[:100]
                report.append(f"    - [{ts_str}] {role}: {content}...")
                
            if len(items) > 5:
                report.append(f"    ... ({len(items) - 5} more items)")
            report.append("")
        report.append("")
        
    return "\n".join(report)

if __name__ == "__main__":
    # Restore stdout for mcp.run() so it can use it for transport
    sys.stdout = _original_stdout
    mcp.run()
