"""
Enterprise-Grade Vector Storage Module

Manages ChromaDB vector database operations for optimal RAG performance
with production-ready features and comprehensive error handling.

Author: Enterprise RAG Pipeline
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection


class VectorStorageError(Exception):
    """Custom exception for vector storage errors"""
    pass


class EnterpriseVectorStorage:
    """
    Production-grade vector storage using ChromaDB for SMB RAG applications.
    
    Features:
    - Persistent storage with automatic backup capabilities
    - Optimized for similarity search with cosine distance
    - Batch operations for performance
    - Comprehensive metadata management
    - Production monitoring and statistics
    - Error handling and recovery mechanisms
    
    ChromaDB Configuration:
    - Distance metric: cosine (optimal for normalized embeddings)
    - Storage: DuckDB + Parquet (production-ready backend)
    - Persistence: Local file system with configurable path
    """
    
    def __init__(
        self,
        storage_path: str = "./chroma_db",
        collection_name: str = "smb_documents",
        distance_metric: str = "cosine",
        batch_size: int = 100
    ):
        """
        Initialize the vector storage with production settings.
        
        Args:
            storage_path: Path for persistent storage (default: "./chroma_db")
            collection_name: Name of the collection to use (default: "smb_documents")
            distance_metric: Distance metric for similarity search (default: "cosine")
            batch_size: Batch size for operations (default: 100)
        """
        self.storage_path = storage_path
        self.collection_name = collection_name
        self.distance_metric = distance_metric
        self.batch_size = batch_size
        
        # Ensure storage directory exists
        os.makedirs(storage_path, exist_ok=True)
        
        try:
            # Initialize ChromaDB client with persistent storage
            print(f"Initializing ChromaDB at: {storage_path}")
            self.client = chromadb.PersistentClient(
                path=storage_path,
                settings=Settings(
                    anonymized_telemetry=False,  # Disable telemetry for production
                    allow_reset=False  # Prevent accidental data loss
                )
            )
            
            # Get or create collection with optimized settings
            self.collection = self._get_or_create_collection()
            
            print(f"✅ Vector storage initialized successfully")
            print(f"   Collection: {self.collection_name}")
            print(f"   Storage path: {storage_path}")
            print(f"   Distance metric: {distance_metric}")
            print(f"   Document count: {self.collection.count()}")
            
        except Exception as e:
            raise VectorStorageError(f"Failed to initialize vector storage: {str(e)}")
        
        # Statistics tracking
        self.stats = {
            "total_documents_stored": 0,
            "total_queries_performed": 0,
            "total_batch_operations": 0,
            "last_updated": None,
            "storage_size_mb": 0.0
        }
        
        # Update initial stats
        self._update_stats()
    
    def _get_or_create_collection(self) -> Collection:
        """Get existing collection or create new one with optimized settings."""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(name=self.collection_name)
            print(f"   Using existing collection: {self.collection_name}")
            
        except Exception:
            # Create new collection with production settings
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={
                    "hnsw:space": self.distance_metric,  # Cosine distance for normalized embeddings
                    "hnsw:batch_size": self.batch_size,  # Batch size for indexing
                    "hnsw:sync_threshold": 1000,  # Sync threshold for performance
                    "description": "Enterprise SMB document embeddings",
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0"
                }
            )
            print(f"   Created new collection: {self.collection_name}")
        
        return collection
    
    def add_documents(
        self, 
        embedded_docs: List[Dict[str, Any]], 
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add embedded documents to the vector storage.
        
        Args:
            embedded_docs: List of documents with embeddings from EmbeddingGenerator
            batch_size: Override default batch size for this operation
            
        Returns:
            Dictionary with operation results and statistics
            
        Raises:
            VectorStorageError: If document addition fails
        """
        if not embedded_docs:
            raise VectorStorageError("No documents provided for storage")
        
        batch_size = batch_size or self.batch_size
        
        try:
            total_docs = len(embedded_docs)
            added_count = 0
            
            print(f"Adding {total_docs} documents to vector storage...")
            
            # Process documents in batches for performance
            for i in range(0, total_docs, batch_size):
                batch = embedded_docs[i:i + batch_size]
                batch_end = min(i + batch_size, total_docs)
                
                # Prepare batch data
                ids = []
                documents = []
                embeddings = []
                metadatas = []
                
                for doc in batch:
                    # Generate unique ID if not present
                    doc_id = doc['metadata'].get('doc_id', str(uuid.uuid4()))
                    ids.append(doc_id)
                    
                    documents.append(doc['content'])
                    embeddings.append(doc['embedding'])  # Use list form for ChromaDB
                    
                    # Prepare metadata (ChromaDB has some restrictions)
                    metadata = self._prepare_metadata(doc['metadata'])
                    metadatas.append(metadata)
                
                # Add batch to collection
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                
                added_count += len(batch)
                print(f"   Processed batch {i//batch_size + 1}: {added_count}/{total_docs} documents")
            
            # Update statistics
            self.stats["total_documents_stored"] += added_count
            self.stats["total_batch_operations"] += 1
            self.stats["last_updated"] = datetime.now().isoformat()
            self._update_stats()
            
            result = {
                "success": True,
                "documents_added": added_count,
                "total_documents": self.collection.count(),
                "batch_count": (total_docs + batch_size - 1) // batch_size,
                "processing_time": "calculated_elsewhere"
            }
            
            print(f"✅ Successfully added {added_count} documents to vector storage")
            return result
            
        except Exception as e:
            raise VectorStorageError(f"Failed to add documents to vector storage: {str(e)}")
    
    def similarity_search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None,
        include_distances: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search against stored embeddings.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of most similar documents to return
            metadata_filter: Optional metadata filter for pre-filtering
            include_distances: Whether to include similarity distances
            
        Returns:
            List of most similar documents with metadata and optional distances
            
        Raises:
            VectorStorageError: If similarity search fails
        """
        if query_embedding is None or query_embedding.size == 0:
            raise VectorStorageError("Invalid query embedding provided")
        
        try:
            # Prepare query parameters
            query_params = {
                "query_embeddings": [query_embedding.tolist()],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"] if include_distances else ["documents", "metadatas"]
            }
            
            # Add metadata filter if provided
            if metadata_filter:
                query_params["where"] = metadata_filter
            
            # Perform similarity search
            results = self.collection.query(**query_params)
            
            # Update statistics
            self.stats["total_queries_performed"] += 1
            
            # Format results for consistency
            formatted_results = []
            
            if results["ids"] and results["ids"][0]:  # Check if we have results
                for i in range(len(results["ids"][0])):
                    result_doc = {
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                    }
                    
                    if include_distances and "distances" in results:
                        # Convert ChromaDB distance to similarity score
                        # For cosine distance: similarity = 1 - distance
                        distance = results["distances"][0][i]
                        similarity = 1 - distance if self.distance_metric == "cosine" else distance
                        result_doc["similarity"] = float(similarity)
                        result_doc["distance"] = float(distance)
                    
                    formatted_results.append(result_doc)
            
            print(f"✅ Similarity search completed: {len(formatted_results)} results found")
            return formatted_results
            
        except Exception as e:
            raise VectorStorageError(f"Similarity search failed: {str(e)}")
    
    def search_by_text(
        self,
        query_text: str,
        top_k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform text-based similarity search (requires embedding generation).
        
        Args:
            query_text: Text query to search for
            top_k: Number of results to return
            metadata_filter: Optional metadata filter
            
        Returns:
            List of similar documents
            
        Note:
            This method requires an embedding generator to convert text to embeddings.
            For production use, integrate with EnterpriseEmbeddingGenerator.
        """
        # This is a placeholder - in production, you'd integrate with the embedding generator
        raise NotImplementedError(
            "Text search requires integration with EnterpriseEmbeddingGenerator. "
            "Use similarity_search() with pre-computed embeddings instead."
        )
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by its ID.
        
        Args:
            doc_id: Document ID to retrieve
            
        Returns:
            Document data if found, None otherwise
        """
        try:
            results = self.collection.get(
                ids=[doc_id],
                include=["documents", "metadatas"]
            )
            
            if results["ids"] and len(results["ids"]) > 0:
                return {
                    "id": results["ids"][0],
                    "content": results["documents"][0],
                    "metadata": results["metadatas"][0]
                }
            
            return None
            
        except Exception as e:
            raise VectorStorageError(f"Failed to retrieve document {doc_id}: {str(e)}")
    
    def delete_documents(self, doc_ids: List[str]) -> Dict[str, Any]:
        """
        Delete documents by their IDs.
        
        Args:
            doc_ids: List of document IDs to delete
            
        Returns:
            Dictionary with deletion results
        """
        try:
            initial_count = self.collection.count()
            
            self.collection.delete(ids=doc_ids)
            
            final_count = self.collection.count()
            deleted_count = initial_count - final_count
            
            print(f"✅ Deleted {deleted_count} documents from vector storage")
            
            return {
                "success": True,
                "documents_deleted": deleted_count,
                "remaining_documents": final_count
            }
            
        except Exception as e:
            raise VectorStorageError(f"Failed to delete documents: {str(e)}")
    
    def _prepare_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare metadata for ChromaDB storage (handle type restrictions).
        
        Args:
            metadata: Original metadata dictionary
            
        Returns:
            ChromaDB-compatible metadata dictionary
        """
        prepared = {}
        
        for key, value in metadata.items():
            # ChromaDB supports strings, integers, floats, and booleans
            if isinstance(value, (str, int, float, bool)):
                prepared[key] = value
            elif isinstance(value, (list, dict)):
                # Convert complex types to JSON strings
                prepared[key] = json.dumps(value)
            else:
                # Convert other types to strings
                prepared[key] = str(value)
        
        return prepared
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about the collection.
        
        Returns:
            Dictionary with collection statistics and metadata
        """
        try:
            doc_count = self.collection.count()
            collection_metadata = self.collection.metadata or {}
            
            # Get storage size
            storage_size = self._calculate_storage_size()
            
            return {
                "collection_name": self.collection_name,
                "document_count": doc_count,
                "storage_path": self.storage_path,
                "distance_metric": self.distance_metric,
                "storage_size_mb": storage_size,
                "collection_metadata": collection_metadata,
                "last_updated": self.stats.get("last_updated"),
                "total_queries": self.stats.get("total_queries_performed", 0)
            }
            
        except Exception as e:
            raise VectorStorageError(f"Failed to get collection info: {str(e)}")
    
    def _calculate_storage_size(self) -> float:
        """Calculate storage size in MB."""
        try:
            total_size = 0
            for root, dirs, files in os.walk(self.storage_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            return total_size / (1024 * 1024)  # Convert to MB
        except Exception:
            return 0.0
    
    def _update_stats(self):
        """Update internal statistics."""
        self.stats["storage_size_mb"] = self._calculate_storage_size()
    
    def backup_collection(self, backup_path: str) -> Dict[str, Any]:
        """
        Create a backup of the collection.
        
        Args:
            backup_path: Path to store the backup
            
        Returns:
            Dictionary with backup results
        """
        try:
            import shutil
            
            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            # Copy storage files
            shutil.copytree(self.storage_path, backup_path, dirs_exist_ok=True)
            
            backup_info = {
                "success": True,
                "backup_path": backup_path,
                "document_count": self.collection.count(),
                "backup_time": datetime.now().isoformat(),
                "backup_size_mb": self._calculate_storage_size()
            }
            
            print(f"✅ Collection backed up to: {backup_path}")
            return backup_info
            
        except Exception as e:
            raise VectorStorageError(f"Failed to backup collection: {str(e)}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        return {
            **self.stats,
            "collection_info": self.get_collection_info()
        }