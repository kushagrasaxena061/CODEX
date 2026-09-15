import os
import chromadb
from backend.events.bus import event_bus

class RAGManager:
    def __init__(self):
        self.db_dir = os.path.abspath(os.path.join(os.getcwd(), "backend", "chroma_db"))
        os.makedirs(self.db_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.db_dir)

    def _get_collection(self, session_id: int):
        return self.client.get_or_create_collection(name=f"workspace_session_{session_id}")

    def shred_and_embed(self, workspace_root: str, session_id: int):
        event_bus.emit("SCANNER", f"Indexing vector chunks for Session #{session_id}...")
        collection = self._get_collection(session_id)
        try:
            collection.delete(where={"session": str(session_id)})
        except Exception:
            pass
            
        docs, metadatas, ids = [], [], []
        
        for root, dirs, files in os.walk(workspace_root):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.venv']]
            for file in files:
                if not file.startswith('.'):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        lines = content.split('\n')
                        for j in range(0, len(lines), 50):
                            chunk = '\n'.join(lines[j:j+50])
                            if chunk.strip():
                                rel_path = os.path.relpath(path, workspace_root)
                                docs.append(chunk)
                                metadatas.append({"session": str(session_id), "file": rel_path})
                                ids.append(f"s{session_id}_{rel_path}_chk_{j}")
                    except Exception:
                        pass
        
        if docs:
            collection.add(documents=docs, metadatas=metadatas, ids=ids)
            event_bus.emit("SCANNER", f"Embedded {len(docs)} code chunks into isolated vector store.", level="SUCCESS")

    def query_code(self, prompt: str, session_id: int, top_k: int = 3) -> str:
        collection = self._get_collection(session_id)
        if collection.count() == 0:
            return ""
            
        results = collection.query(query_texts=[prompt], n_results=top_k)
        if not results['documents'] or not results['documents'][0]:
            return ""
            
        context = []
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            context.append(f"--- Snippet from {meta['file']} ---\n{doc}")
            
        return "\n\n".join(context)

rag_db = RAGManager()
