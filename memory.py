import sqlite3
import json
import numpy as np
import os
from database import DB_PATH

class LocalVectorMemory:
    def __init__(self, client):
        """
        Initializes the local vector memory.
        :param client: The google-genai Client instance.
        """
        self.client = client
        self.init_memory_db()

    def init_memory_db(self):
        """Creates the memory vectors table in SQLite if it does not exist."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_vectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            embedding TEXT NOT NULL,  -- JSON list of floats
            metadata TEXT             -- JSON metadata dict
        )
        """)
        conn.commit()
        conn.close()

    def _get_embedding(self, text):
        """Fetches embedding for a given text using text-embedding-004."""
        try:
            # Using the new google-genai SDK embedding API
            response = self.client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            # Extracted embedding values
            embedding_list = response.embeddings[0].values
            return embedding_list
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return dummy vector if it fails to prevent complete crash
            return [0.0] * 768

    def add_memory(self, text, metadata=None):
        """Embeds and saves text into local SQLite vector table."""
        if not text or not text.strip():
            return
        
        embedding = self._get_embedding(text)
        embedding_str = json.dumps(embedding)
        metadata_str = json.dumps(metadata or {})

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO memory_vectors (text, embedding, metadata)
        VALUES (?, ?, ?)
        """, (text, embedding_str, metadata_str))
        conn.commit()
        conn.close()

    def search_memory(self, query, limit=3):
        """
        Retrieves top similar items from the memory using cosine similarity.
        :returns: List of tuples (text, metadata, score)
        """
        query_vector = np.array(self._get_embedding(query))
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT text, embedding, metadata FROM memory_vectors")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return []

        results = []
        for text, embedding_str, metadata_str in rows:
            vector = np.array(json.loads(embedding_str))
            
            # Compute cosine similarity
            dot_product = np.dot(query_vector, vector)
            norm_q = np.linalg.norm(query_vector)
            norm_v = np.linalg.norm(vector)
            
            if norm_q == 0 or norm_v == 0:
                score = 0.0
            else:
                score = float(dot_product / (norm_q * norm_v))
            
            results.append((text, json.loads(metadata_str), score))

        # Sort descending by score
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:limit]
