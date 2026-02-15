---
name: OpenMemX
description: Advanced hierarchical memory management with Bayesian Surprise and GraphRAG.
---

# OpenMemX Skill
This skill enables the agent to autonomously manage its long-term context, optimize token usage, and perform multi-hop reasoning.

## 🧠 Cognitive Strategy
You are equipped with the OpenMemX memory stack. Your goal is to maximize information density while minimizing token waste.

### 1. Proactive Logging
After **every** meaningful exchange, you MUST call `ingest_interaction(conversation_id, role, content)`. 
- The system will calculate a "Surprise Score."
- High-surprise items are flagged for long-term semantic storage.

### 2. Contextual Recall
Before answering complex questions, check your long-term memory:
- Use `retrieve_memory` for semantic/vector retrieval.
- Use `traverse_knowledge_graph` if you need to connect disparate facts (e.g., "How does Project X affect Person Y?").

### 3. Prompt Optimization 
If the current context is becoming full:
- Use `compress_prompt` (LLMLingua-2) to distill the history into its essential semantic parts.

### 4. Knowledge Consolidation
During idle moments or after a milestone, call `consolidate_memory`.
- Review the "High Surprise" items identified by the system.
- Formalize these into the Knowledge Graph using `add_knowledge_node` and `add_knowledge_edge`.

## 🛠 Available Tools
- `ingest_interaction`: Save current turn.
- `retrieve_memory`: Search past events.
- `traverse_knowledge_graph`: Multi-hop reasoning.
- `add_knowledge_node/edge`: Crystallize facts.
- `compress_prompt`: Reduce token usage.
- `snapshot_memory`: Commit state to Git.
