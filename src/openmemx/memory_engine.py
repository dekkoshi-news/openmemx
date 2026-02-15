import os
import lancedb
import pygit2
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from .core_logic import MemoryLogic, PromptCompressor
from sqlmodel import SQLModel, Field, create_engine, Session, select
import json

# Models for SQLite
class Interaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    role: str
    content: str
    surprise_score: float = 0.0
    conversation_id: str

class KnowledgeNode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    entity: str
    description: str
    node_data: str = "{}"

class KnowledgeEdge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int
    target_id: int
    relationship: str
    weight: float = 1.0

class MemoryEngine:
    def __init__(self, base_path: Optional[str] = None):
        if base_path is None:
            # Default to a persistent hidden folder in the user's home directory
            base_path = os.path.expanduser("~/.openmemx")
        
        self.base_path = os.path.abspath(base_path)
        os.makedirs(self.base_path, exist_ok=True)
        
        # 1. SQLite Setup
        self.db_path = os.path.join(self.base_path, "metadata.db")
        self.sqlite_engine = create_engine(f"sqlite:///{self.db_path}")
        SQLModel.metadata.create_all(self.sqlite_engine)
        
        # 2. LanceDB Setup
        self.lancedb_path = os.path.join(self.base_path, "vectors.lancedb")
        self.lancedb = lancedb.connect(self.lancedb_path)
        
        # 3. Git Archival Setup
        self.git_path = self.base_path
        if not os.path.exists(os.path.join(self.git_path, ".git")):
            pygit2.init_repository(self.git_path)
            self.repo = pygit2.Repository(self.git_path)
            # Initial commit
            self.snapshot("Initial memory state")
        else:
            self.repo = pygit2.Repository(self.git_path)

        # 4. Logic Setup
        self.logic = MemoryLogic()
        self.compressor = PromptCompressor()

    def ingest_interaction(self, conversation_id: str, role: str, content: str):
        # 1. Get history for surprise calculation
        history = self.retrieve_episodic(conversation_id, limit=50)
        hist_contents = [h.content for h in history]
        
        # 2. Calculate surprise
        surprise_score = self.logic.calculate_surprise(content, hist_contents)
        
        # 3. Store in SQLite
        with Session(self.sqlite_engine) as session:
            interaction = Interaction(
                conversation_id=conversation_id,
                role=role,
                content=content,
                surprise_score=surprise_score
            )
            session.add(interaction)
            session.commit()
            interaction_id = interaction.id

        # 4. Store in LanceDB (Global Master Table)
        # We use a single table for all context to enable cross-session retrieval
        table_name = "master_vectors"
        embedding = self.logic.model.encode([content])[0]
        
        data_packet = [{
            "vector": embedding,
            "id": str(interaction_id),
            "content": content,
            "role": role,
            "conversation_id": conversation_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]

        try:
            table = self.lancedb.open_table(table_name)
        except Exception:
            table = self.lancedb.create_table(table_name, data=data_packet)
        else:
            table.add(data_packet)
            
        return interaction_id

    def snapshot(self, message: str):
        index = self.repo.index
        index.add_all()
        index.write()
        tree = index.write_tree()
        
        author = pygit2.Signature("OpenMemX Agent", "agent@openmemx.ai")
        committer = author
        
        parent = []
        try:
            parent = [self.repo.head.target]
        except Exception:
            pass
            
        self.repo.create_commit('HEAD', author, committer, message, tree, parent)

    def retrieve_episodic(self, conversation_id: str, limit: int = 10):
        with Session(self.sqlite_engine) as session:
            statement = select(Interaction).where(Interaction.conversation_id == conversation_id).order_by(Interaction.timestamp.desc()).limit(limit)
            results = session.exec(statement).all()
            return results

    def fetch_recent_activities(self, hours: int = 24) -> List[Interaction]:
        """
        Fetches all interactions from all conversations within the last N hours.
        """
        from datetime import timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        with Session(self.sqlite_engine) as session:
            statement = select(Interaction).where(Interaction.timestamp >= cutoff).order_by(Interaction.timestamp.desc())
            results = session.exec(statement).all()
            return results

    # GraphRAG Operations
    def add_knowledge_node(self, entity: str, description: str, node_data: Dict[str, Any] = None) -> int:
        with Session(self.sqlite_engine) as session:
            # Check if exists
            statement = select(KnowledgeNode).where(KnowledgeNode.entity == entity)
            existing = session.exec(statement).first()
            if existing:
                existing.description = f"{existing.description}\n---\n{description}"
                if node_data:
                    current_data = json.loads(existing.node_data)
                    current_data.update(node_data)
                    existing.node_data = json.dumps(current_data)
                session.add(existing)
                session.commit()
                return existing.id
            
            node = KnowledgeNode(
                entity=entity,
                description=description,
                node_data=json.dumps(node_data or {})
            )
            session.add(node)
            session.commit()
            return node.id

    def add_knowledge_edge(self, source_entity: str, target_entity: str, relationship: str, weight: float = 1.0):
        with Session(self.sqlite_engine) as session:
            # Get IDs
            source = session.exec(select(KnowledgeNode).where(KnowledgeNode.entity == source_entity)).first()
            target = session.exec(select(KnowledgeNode).where(KnowledgeNode.entity == target_entity)).first()
            
            if not source or not target:
                raise ValueError("Source or Target entity not found in Knowledge Graph")
            
            edge = KnowledgeEdge(
                source_id=source.id,
                target_id=target.id,
                relationship=relationship,
                weight=weight
            )
            session.add(edge)
            session.commit()
            return edge.id

    def traverse_graph(self, start_entity: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        with Session(self.sqlite_engine) as session:
            start_node = session.exec(select(KnowledgeNode).where(KnowledgeNode.entity == start_entity)).first()
            if not start_node:
                return []
                
            results = []
            visited = {start_node.id}
            queue = [(start_node, 0)]
            
            while queue:
                current_node, depth = queue.pop(0)
                if depth >= max_depth:
                    continue
                    
                # Find edges from this node
                edges = session.exec(select(KnowledgeEdge).where(KnowledgeEdge.source_id == current_node.id)).all()
                for edge in edges:
                    target_node = session.get(KnowledgeNode, edge.target_id)
                    if target_node and target_node.id not in visited:
                        visited.add(target_node.id)
                        results.append({
                            "source": current_node.entity,
                            "relationship": edge.relationship,
                            "target": target_node.entity,
                            "description": target_node.description
                        })
                        queue.append((target_node, depth + 1))
            
            return results

    def get_all_nodes(self) -> List[KnowledgeNode]:
        with Session(self.sqlite_engine) as session:
            return session.exec(select(KnowledgeNode)).all()

    def prune_interactions(self, conversation_id: str, threshold: float = 0.1):
        """
        Prunes episodic interactions with surprise scores below the threshold.
        Syncs deletions between SQLite and LanceDB.
        """
        with Session(self.sqlite_engine) as session:
            # 1. Find IDs to prune
            statement = select(Interaction).where(
                Interaction.conversation_id == conversation_id,
                Interaction.surprise_score < threshold
            )
            to_prune = session.exec(statement).all()
            ids_to_prune = [str(i.id) for i in to_prune]
            
            if not ids_to_prune:
                return 0

            # 2. Delete from SQLite
            for interaction in to_prune:
                session.delete(interaction)
            session.commit()

            # 3. Delete from LanceDB
            table_name = "master_vectors"
            try:
                table = self.lancedb.open_table(table_name)
                # Filter by IDs
                id_filter = ", ".join([f"'{idx}'" for idx in ids_to_prune])
                table.delete(f"id IN ({id_filter})")
            except Exception as e:
                print(f"Warning: Failed to prune from LanceDB: {e}")

            return len(ids_to_prune)

# Singleton-like instance or factory can be used here
