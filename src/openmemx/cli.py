import sys
import os
import argparse
import json
from .memory_engine import MemoryEngine
from .mcp_server import get_memory_instructions, load_config, save_config, get_conversation_id, reset_conversation_id

def update_json_config(path, key_path, config_val):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {}
    else:
        with open(path, 'r') as f:
            try:
                data = json.load(f)
            except:
                data = {}

    # Navigate to mcpServers
    if "mcpServers" not in data:
        data["mcpServers"] = {}
    
    data["mcpServers"]["openmemx"] = config_val
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Successfully updated config at: {path}")

def instruct_command(args):
    """Prints agentic initialization guidelines or performs automatic setup."""
    # Proactively ensure the memory folder exists
    try:
        MemoryEngine() 
    except Exception as e:
        print(f"Warning: Could not initialize memory directory: {e}")

    # Initialize/Ensure config exists with defaults (including universal ingestion patterns)
    try:
        load_config() # This loads defaults if file missing
        save_config() # This writes defaults to file
        print("✓ OpenMemX configuration initialized.")
    except Exception as e:
        print(f"Warning: Could not initialize configuration: {e}")

    if not args.gemini and not args.claude and not args.openclaw:
        instructions = get_memory_instructions()
        print("\n--- OPENMEMX AGENTIC INSTRUCTIONS ---")
        print(instructions)
        print("\nInitialization Prompts for Agents:")
        print("   - [Gemini CLI]: /openmemx_system_init")
        print("   - [Claude Desktop]: Select 'openmemx_system_init' from Prompts menu")
        print("   - [Nanobot]: Add the project to your skills/ (see below)")
        print("   - [Generic]: 'Run the openmemx_system_init prompt from OpenMemX'")
        return

    # Use the current python executable to run the module directly
    # This works for both local development (venv) and installed package
    python_exe = sys.executable
    config = {
        "command": python_exe,
        "args": ["-m", "openmemx.mcp_server"]
    }

    grounding_info = ""
    if args.gemini:
        gemini_path = os.path.expanduser("~/.gemini/settings.json")
        update_json_config(gemini_path, "openmemx", config)
        grounding_info += "   - [Gemini CLI]: Type: /openmemx_system_init\n"

    if args.claude:
        claude_path = os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
        update_json_config(claude_path, "openmemx", config)
        grounding_info += "   - [Claude Desktop]: Small 'paper' icon (Prompts) -> Select 'openmemx_system_init'\n"

    if args.openclaw:
        # OpenClaw/Moltbot standard MCP config path
        openclaw_path = os.path.expanduser("~/.openclaw/mcp_config.json")
        update_json_config(openclaw_path, "openmemx", config)
        grounding_info += "   - [OpenClaw]: Trigger the 'openmemx_system_init' prompt via your agent's interface.\n"

    print("\n" + "="*50)
    print("OPENMEMX CONFIGURATION SUCCESSFUL")
    print("="*50)
    print("\nNext Steps to Ground your Agent:")
    print("1. RESTART your AI application (Gemini CLI, Claude Desktop, etc.) to load the new config.")
    print("2. Initialize the OpenMemX strategy by running the prompt:")
    print(f"\n{grounding_info}")
    
    print("💡 TIP: To avoid running this command in every new session, add the project's")
    print("   '.agent/skills/openmemx' folder to your agent's 'Skills' or 'Custom Instructions'.")
    print("   This makes the memory strategy persistent and automatic!")
    
    print("\nThis grounding step is critical for the agent to utilize its new memory tools.")

def migrate_command(args):
    """Migrates Markdown files into OpenMemX memory."""
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found.")
        return

    engine = MemoryEngine()
    conv_id = args.conversation_id or "migration_import"
    
    print(f"Migrating '{args.file}' into conversation '{conv_id}'...")
    
    with open(args.file, 'r') as f:
        content = f.read()

    # Generic splitting strategy: by H2/H3 headers or horizontal rules
    # This covers Obsidian, VS Code notes, and generic markdown
    parts = []
    import re
    # Split by common delimiters (--- or # headers)
    parts = re.split(r'\n(?:---|\#\#+)\s+', content)
    
    count = 0
    for part in parts:
        clean_part = part.strip()
        if clean_part:
            engine.ingest_interaction(conv_id, "user", clean_part)
            count += 1
            print(f"Ingested segment {count}...")

    print(f"Migration complete! {count} segments ingested with Bayesian Surprise scoring.")

def auto_ingest_command(args):
    """Manage auto-ingest configuration."""
    config = load_config()
    
    if args.status:
        auto_ingest = config.get("auto_ingest", {})
        print("\n" + "="*50)
        print("AUTO-INGEST STATUS")
        print("="*50)
        print(f"  Enabled: {auto_ingest.get('enabled', True)}")
        print(f"  Log queries: {auto_ingest.get('log_queries', True)}")
        print(f"  Log responses: {auto_ingest.get('log_responses', True)}")
        print(f"  Conversation timeout: {auto_ingest.get('conversation_timeout_minutes', 30)} minutes")
        print(f"\n  Current conversation ID: {get_conversation_id()}")
        print("="*50)
        return
    
    if args.enable:
        config["auto_ingest"]["enabled"] = True
        save_config()
        print("✓ Auto-ingest ENABLED. Queries will be automatically logged to memory.")
        return
    
    if args.disable:
        config["auto_ingest"]["enabled"] = False
        save_config()
        print("✓ Auto-ingest DISABLED. Queries will NOT be automatically logged.")
        return
    
    if args.new_conversation:
        new_id = reset_conversation_id()
        print(f"✓ Started new conversation with ID: {new_id}")
        return
    
    # If no specific flag, show status
    auto_ingest = config.get("auto_ingest", {})
    print("\nUsage: openmemx auto-ingest [option]")
    print("\nOptions:")
    print("  --status           Show current auto-ingest status")
    print("  --enable           Enable automatic memory ingestion")
    print("  --disable          Disable automatic memory ingestion")
    print("  --new-conversation Start a new conversation session")
    print("\nCurrent Status:")
    print(f"  Auto-ingest is {'ENABLED' if auto_ingest.get('enabled', True) else 'DISABLED'}")

def main():
    parser = argparse.ArgumentParser(description="OpenMemX CLI - Management Tool")
    subparsers = parser.add_subparsers(help="Commands")

    # Instruct command
    parser_instruct = subparsers.add_parser('instruct', help='Show agentic instruction guidelines or setup configs')
    parser_instruct.add_argument('--gemini', action='store_true', help='Automatically setup Gemini CLI config')
    parser_instruct.add_argument('--claude', action='store_true', help='Automatically setup Claude Desktop config')
    parser_instruct.add_argument('--openclaw', action='store_true', help='Automatically setup OpenClaw config')
    parser_instruct.set_defaults(func=instruct_command)

    # Migrate command
    parser_migrate = subparsers.add_parser('migrate', help='Migrate markdown memory files')
    parser_migrate.add_argument('file', help='Path to the markdown file')
    parser_migrate.add_argument('--conversation_id', '-c', help='Target conversation ID')
    parser_migrate.add_argument('--role', '-r', default='user', help='Role for ingested content')
    parser_migrate.set_defaults(func=migrate_command)

    # Auto-ingest command
    parser_auto = subparsers.add_parser('auto-ingest', help='Manage automatic memory ingestion')
    parser_auto.add_argument('--status', action='store_true', help='Show auto-ingest status')
    parser_auto.add_argument('--enable', action='store_true', help='Enable auto-ingest')
    parser_auto.add_argument('--disable', action='store_true', help='Disable auto-ingest')
    parser_auto.add_argument('--new-conversation', action='store_true', help='Start a new conversation')
    parser_auto.set_defaults(func=auto_ingest_command)

    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
