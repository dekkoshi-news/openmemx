# OpenMemX: The Intelligent Memory Stack for AI Agents

> **Beyond Vector RAG.** OpenMemX is a token-optimized cognitive layer for autonomous agents, implementing hierarchical abstraction, Bayesian surprise-driven forgetting, and multi-hop reasoning.

---

## 🧠 The Theory: Why OpenMemX?

Most AI agents suffer from the **"Memory Wall"**: their context windows fill up with redundant information, leading to high latency and "forgetfulness." OpenMemX solves this through three pillars:

### 1. Bayesian Surprise-Driven Forgetting
Instead of a simple "Last In, First Out" (LRU) buffer, OpenMemX calculates the **informational novelty** of every interaction. 
- **High Surprise**: Stored in episodic memory and promoted to the semantic knowledge graph.
- **Low Surprise**: Summarized or pruned to save tokens.

### 2. Hierarchical Semantic Abstraction (H-MEM)
- **Episodic (SQLite/LanceDB)**: Fast, temporal log of recent events.
- **Semantic (Knowledge Graph)**: Crystallized facts and relationships (GraphRAG) for multi-hop reasoning (e.g., *"How does delay X impact goal Y?"*).
- **Archival (Git)**: "Time-travel" versioning of your agent's entire world-view.

### 3. Faithful Prompt Compression (LLMLingua-2)
Using bidirectional BERT-based extractive compression, OpenMemX reduces prompt size by **20-40%** without losing semantic coherence, effectively doubling your agent's virtual context window.

---

## 📈 Performance Benchmarks

| Metric | Vector RAG (Standard) | OpenMemX (Optimized) |
| :--- | :--- | :--- |
| **Token Density** | 1.0x (Raw) | **1.4x - 2.0x** (Compressed) |
| **Reasoning Depth** | Single-hop only | **Multi-hop (Graph Traversal)** |
| **Search Speed** | Fast (Vector) | **Ultra-Fast (LanceDB Zero-Copy)** |
| **Versioning** | None | **Git-backed (Commits/Diffs)** |

---

## 🚀 Installation & Setup

### 1. Install the Core Engine
Open a terminal and run:
```bash
pip install openmemx
```

### 2. Connect Your Agents (Grounding)
OpenMemX works by connecting to your favorite AI tools. Choose your agent below to set up its "Brain":

#### 💎 Gemini CLI (Automated)
Run this command to automatically configure your Gemini sessions:
```bash
openmemx instruct --gemini
```
*Restart your Gemini terminal and type `/openmemx_system_init` to begin.*

#### ☁️ Claude Desktop (Automated)
Run this command to add OpenMemX to Claude's toolbelt:
```bash
openmemx instruct --claude
```
*Restart Claude, click the **paper icon (Prompts)**, and select **openmemx_system_init**.*

#### 🦀 OpenClaw (Automated)
Run this command to add OpenMemX to OpenClaw/Moltbot:
```bash
openmemx instruct --openclaw
```
*Restart OpenClaw and trigger the `openmemx_system_init` prompt via your agent's interface.*

#### 🤖 Nanobot (Manual Skill Setup)
Nanobot uses a "Skills" system. To add OpenMemX:
1.  **Locate your Nanobot workspace**: (Usually `~/.nanobot/workspace/`)
2.  **Copy the OpenMemX Skill**:
    ```bash
    mkdir -p ~/.nanobot/workspace/skills
    cp -r .agent/skills/openmemx ~/.nanobot/workspace/skills/
    ```
3.  **Use it**: Simply tell Nanobot: *"Use the OpenMemX skill to manage my memory."*

#### 🏗️ Generic / Other Agents
If your agent supports MCP (Model Context Protocol), point it to:
**Command**: `python -m openmemx.mcp_server`

---

## 📅 The "Daily Standup" (Universal Monitoring)

OpenMemX is now a **Universal Activity Monitor**. It can read logs from **Nanobot**, **Gemini**, and **OpenClaw** to give you a bird's-eye view of your productivity.

### How to use it:
1.  **Initialize Patterns**: Run `openmemx instruct` at least once to set up your global config.
2.  **Ask your Agent**: *"Give me a global activity report for the last 24 hours."*
3.  **View Results**: Your agent will aggregate actions from across your entire system, even if they happened in different tools or folders.

---

## 🛠 Management CLI
```bash
# Ingest your existing notes/markdown files
openmemx migrate my_notes.md --conversation_id "research_project"

# Reset your local configuration
openmemx instruct

# Manage automatic memory logging
openmemx auto-ingest --status           # See if it's currently recording
openmemx auto-ingest --enable           # Start recording everything automatically
openmemx auto-ingest --disable          # Stop recording
openmemx auto-ingest --new-conversation # Start a fresh conversation session
```

---

## 🤖 AI Agent Use Cases

### 1. The Coding Assistant
Use `openmemx migrate` to ingest your existing project documentation or Obsidian dev-notes. The agent gains a permanent, vectorized understanding of your coding style.

### 2. Personal Assistant (OpenClaw / Moltbot)
OpenMemX is the perfect companion for **OpenClaw (Moltbot)**. 
- **Persistence**: Your memories survive restarts.
- **Sync**: Use the Git layer to sync your agent's memory across multiple devices.
- **Efficiency**: Keep your local LLM snappy by compressing long chat histories.

---

##  Auto-Ingest & Project-Aware Memory (NEW)

**OpenMemX is now context-aware.** It automatically manages sessions based on your current working directory, allowing you to "resume" memory context simply by navigating to a project folder.

### 1. Project-Aware Sessions
- **Automatic Context**: When you run OpenMemX in `/projects/backend`, it loads that specific project's memory history.
- **Seamless Resumption**: Switch folders, and your agent switches context automatically.
- **Registry System**: Keeps track of which Conversation ID belongs to which directory.

### 2. Auto-Ingest
- **Zero-Friction**: Your queries to `retrieve_memory` are automatically logged.
- **Smart Logging**: Use `configure_auto_ingest` to toggle query/response logging preferences.

### 3. Global Awareness (The "Daily Standup")
Even with isolated project memories, your agent maintains a global view.
- **`get_recent_activity`**: This tool returns a summary of **all** interactions across **all** projects from the last 24 hours.
- **Use Case**: Ask your agent *"What did I work on yesterday?"* and it will aggregate context from your backend, frontend, and infrastructure projects into a single report.

### MCP Tools:
**Core Memory Operations:**
- `ingest_interaction` - Store a new interaction in episodic memory with Bayesian Surprise scoring
- `retrieve_memory` - Semantic search across all conversation history
- `consolidate_memory` - Trigger "sleep cycle" to identify high-surprise items and prune low-surprise noise

**Knowledge Graph (GraphRAG):**
- `add_knowledge_node` - Add entities to the semantic knowledge graph
- `add_knowledge_edge` - Create relationships between entities
- `traverse_knowledge_graph` - Multi-hop reasoning over crystallized facts

**Prompt Optimization:**
- `compress_prompt` - Reduce prompt size using LLMLingua-2 (20-40% compression)
- `snapshot_memory` - Create Git-backed version checkpoint

**Auto-Ingest & Sessions:**
- `get_recent_activity` - Global report of actions across all project directories
- `log_interaction` - Quick logging without managing conversation IDs
- `configure_auto_ingest` - Customize auto-ingest behavior
- `get_auto_ingest_status` - Check current configuration
- `start_new_conversation` - Force a fresh conversation thread for the current project

---

## 🧩 Architecture Details
- **Location**: All memory data is stored in the `~/.openmemx` directory (persistent across sessions).
- **Python 3.10+** (Optimized for Apple Silicon & NVIDIA RTX)
- **Model Context Protocol (MCP)** v1.0
- **Extractive Pruning**: LLMLingua-2
- **Vector Engine**: LanceDB (In-Process)

---

## 🛠 Developer & Release Process

OpenMemX uses a standardized release process to ensure stability.

### 1. Local Development
Clone the repo and install dependencies in a virtual environment:
```bash
git clone https://github.com/dekkoshi-news/openmemx.git
cd openmemx
python3 -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

### 2. Pre-release Checks
Before every release, run the check script to verify tests, linting, and build integrity:
```bash
./scripts/release.sh
```

### 3. Creating a Release
To release a new version (e.g., `1.1.0`):
1. Use the release script to bump the version: `./scripts/release.sh 1.1.0`.
2. Update `CHANGELOG.md`.
3. Create a git tag: `git tag v1.1.0`.
4. Push to main: `git push origin main --tags`.

The project is configured with **Trusted Publishing (OIDC)**. Once you push a tag and create a "Release" on GitHub, the GitHub Action will automatically build and publish the package to PyPI.

---

## 📜 License & Research
OpenMemX is based on the research report: *Computational Architectures for Efficient Long-Term Memory in Localized Agentic Systems.* See the `doc/` folder for the full whitepaper.
