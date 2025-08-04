"""
Enterprise-Grade Embedding Generation Module

Generates high-quality sentence embeddings using SentenceTransformers 
with all-MiniLM-L6-v2 for optimal RAG performance.

Author: Enterprise RAG Pipeline
"""

import numpy as np
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer


class EmbeddingGenerationError(Exception):
    """Custom exception for embedding generation errors"""
    pass


class EnterpriseEmbeddingGenerator:
    """
    Production-grade embedding generator optimized for SMB RAG applications.
    
    Uses SentenceTransformers with all-MiniLM-L6-v2 model:
    - 384-dimensional embeddings: Optimal balance of quality vs. speed
    - 22.7M parameters: Lightweight yet powerful
    - Trained on 1B+ sentence pairs: Excellent semantic understanding
    - Max input: 256 word pieces (automatically truncated)
    
    Key Features:
    - Batch processing for efficiency
    - Automatic normalization for cosine similarity
    - Comprehensive error handling
    - Performance monitoring and statistics
    - Memory-efficient processing
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: Optional[str] = None,
        normalize_embeddings: bool = True,
        batch_size: int = 32
    ):
        """
        Initialize the embedding generator with production-optimized settings.
        
        Args:
            model_name: SentenceTransformers model identifier (default: all-MiniLM-L6-v2)
            device: Device to run on ('cpu', 'cuda', or None for auto-detection)
            normalize_embeddings: Whether to normalize embeddings for cosine similarity
            batch_size: Batch size for processing multiple texts (default: 32)
        """
        self.model_name = model_name
        self.normalize_embeddings = normalize_embeddings
        self.batch_size = batch_size
        
        try:
            print(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name, device=device)
            print(f"✅ Model loaded successfully")
            print(f"   Model: {model_name}")
            print(f"   Embedding dimensions: {self.model.get_sentence_embedding_dimension()}")
            print(f"   Device: {self.model.device}")
            
        except Exception as e:
            raise EmbeddingGenerationError(f"Failed to load model {model_name}: {str(e)}")
        
        # Statistics tracking
        self.stats = {
            "total_texts_processed": 0,
            "total_embeddings_generated": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
            "batch_count": 0
        }
        
    def generate_embeddings(
        self, 
        texts: List[str], 
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            show_progress: Whether to show progress bar during processing
            
        Returns:
            NumPy array of embeddings (shape: [len(texts), embedding_dim])
            
        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        if not texts:
            raise EmbeddingGenerationError("No texts provided for embedding generation")
        
        # Filter out empty texts
        valid_texts = [text.strip() for text in texts if text and text.strip()]
        if not valid_texts:
            raise EmbeddingGenerationError("No valid texts found after filtering empty strings")
        
        try:
            import time
            start_time = time.time()
            
            # Generate embeddings using SentenceTransformers
            embeddings = self.model.encode(
                valid_texts,
                batch_size=self.batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=self.normalize_embeddings,
                convert_to_numpy=True
            )
            
            processing_time = time.time() - start_time
            
            # Update statistics
            self._update_stats(len(valid_texts), processing_time)
            
            print(f"✅ Generated {len(embeddings)} embeddings")
            print(f"   Shape: {embeddings.shape}")
            print(f"   Processing time: {processing_time:.2f}s")
            print(f"   Rate: {len(valid_texts)/processing_time:.1f} texts/second")
            
            return embeddings
            
        except Exception as e:
            raise EmbeddingGenerationError(f"Failed to generate embeddings: {str(e)}")
    
    def embed_documents(
        self, 
        documents: List[Document], 
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for Document objects and return enhanced documents.
        
        Args:
            documents: List of LangChain Document objects
            show_progress: Whether to show progress during processing
            
        Returns:
            List of dictionaries containing document content, metadata, and embeddings
            
        Raises:
            EmbeddingGenerationError: If document embedding fails
        """
        if not documents:
            raise EmbeddingGenerationError("No documents provided for embedding")
        
        try:
            # Extract text content from documents
            texts = [doc.page_content for doc in documents]
            
            # Generate embeddings
            embeddings = self.generate_embeddings(texts, show_progress=show_progress)
            
            # Create enhanced document objects
            embedded_docs = []
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                embedded_doc = {
                    "content": doc.page_content,
                    "metadata": {
                        **doc.metadata,  # Preserve original metadata
                        "embedding_model": self.model_name,
                        "embedding_dimensions": len(embedding),
                        "embedding_normalized": self.normalize_embeddings,
                        "document_index": i
                    },
                    "embedding": embedding.tolist(),  # Convert to list for JSON serialization
                    "embedding_array": embedding  # Keep as numpy array for calculations
                }
                embedded_docs.append(embedded_doc)
            
            return embedded_docs
            
        except Exception as e:
            raise EmbeddingGenerationError(f"Failed to embed documents: {str(e)}")
    
    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query string.
        
        Args:
            query: Query string to embed
            
        Returns:
            NumPy array representing the query embedding
            
        Raises:
            EmbeddingGenerationError: If query embedding fails
        """
        if not query or not query.strip():
            raise EmbeddingGenerationError("Empty query provided")
        
        try:
            # Generate embedding for single query
            embedding = self.model.encode(
                [query.strip()],
                normalize_embeddings=self.normalize_embeddings,
                convert_to_numpy=True
            )[0]  # Extract single embedding from batch
            
            return embedding
            
        except Exception as e:
            raise EmbeddingGenerationError(f"Failed to generate query embedding: {str(e)}")
    
    def calculate_similarity(
        self, 
        embedding1: np.ndarray, 
        embedding2: np.ndarray,
        metric: str = "cosine"
    ) -> float:
        """
        Calculate similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector  
            metric: Similarity metric ('cosine' or 'dot')
            
        Returns:
            Similarity score (higher = more similar)
            
        Raises:
            EmbeddingGenerationError: If similarity calculation fails
        """
        try:
            if metric == "cosine":
                # Cosine similarity (assumes normalized embeddings)
                similarity = np.dot(embedding1, embedding2)
            elif metric == "dot":
                # Dot product similarity
                similarity = np.dot(embedding1, embedding2)
            else:
                raise ValueError(f"Unsupported metric: {metric}")
            
            return float(similarity)
            
        except Exception as e:
            raise EmbeddingGenerationError(f"Failed to calculate similarity: {str(e)}")
    
    def find_most_similar(
        self, 
        query_embedding: np.ndarray, 
        document_embeddings: List[np.ndarray],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find the most similar documents to a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            document_embeddings: List of document embedding vectors
            top_k: Number of most similar documents to return
            
        Returns:
            List of dictionaries with similarity scores and indices
        """
        try:
            similarities = []
            
            for i, doc_embedding in enumerate(document_embeddings):
                similarity = self.calculate_similarity(query_embedding, doc_embedding)
                similarities.append({
                    "index": i,
                    "similarity": similarity
                })
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Return top-k results
            return similarities[:top_k]
            
        except Exception as e:
            raise EmbeddingGenerationError(f"Failed to find similar documents: {str(e)}")
    
    def _update_stats(self, text_count: int, processing_time: float):
        """Update internal statistics after processing."""
        self.stats["total_texts_processed"] += text_count
        self.stats["total_embeddings_generated"] += text_count
        self.stats["total_processing_time"] += processing_time
        self.stats["batch_count"] += 1
        
        # Calculate running average
        if self.stats["batch_count"] > 0:
            self.stats["average_processing_time"] = (
                self.stats["total_processing_time"] / self.stats["batch_count"]
            )
    
    def get_embedding_summary(self, embeddings: np.ndarray) -> Dict[str, Any]:
        """
        Generate comprehensive summary of embeddings for validation.
        
        Args:
            embeddings: NumPy array of embeddings
            
        Returns:
            Dictionary with embedding statistics
        """
        if embeddings.size == 0:
            return {"total_embeddings": 0}
        
        # Calculate statistics
        embedding_norms = np.linalg.norm(embeddings, axis=1)
        
        return {
            "total_embeddings": len(embeddings),
            "embedding_dimensions": embeddings.shape[1] if len(embeddings.shape) > 1 else 0,
            "embedding_stats": {
                "mean_norm": float(np.mean(embedding_norms)),
                "std_norm": float(np.std(embedding_norms)),
                "min_norm": float(np.min(embedding_norms)),
                "max_norm": float(np.max(embedding_norms))
            },
            "model_info": {
                "model_name": self.model_name,
                "normalized": self.normalize_embeddings,
                "batch_size": self.batch_size
            },
            "data_quality": {
                "has_nan_values": bool(np.isnan(embeddings).any()),
                "has_inf_values": bool(np.isinf(embeddings).any()),
                "all_zeros": bool(np.all(embeddings == 0))
            }
        }
    
    def validate_embeddings(self, embeddings: np.ndarray) -> Dict[str, Any]:
        """
        Validate embedding quality and detect potential issues.
        
        Args:
            embeddings: NumPy array of embeddings to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "embedding_count": len(embeddings) if embeddings.size > 0 else 0
        }
        
        if embeddings.size == 0:
            validation_results["is_valid"] = False
            validation_results["issues"].append("No embeddings provided")
            return validation_results
        
        # Check for NaN values
        if np.isnan(embeddings).any():
            validation_results["is_valid"] = False
            validation_results["issues"].append("Embeddings contain NaN values")
        
        # Check for infinite values
        if np.isinf(embeddings).any():
            validation_results["is_valid"] = False
            validation_results["issues"].append("Embeddings contain infinite values")
        
        # Check for all-zero embeddings
        zero_embeddings = np.all(embeddings == 0, axis=1)
        if zero_embeddings.any():
            zero_count = np.sum(zero_embeddings)
            validation_results["warnings"].append(f"Found {zero_count} all-zero embeddings")
        
        # Check embedding norms (should be ~1.0 if normalized)
        if self.normalize_embeddings:
            norms = np.linalg.norm(embeddings, axis=1)
            abnormal_norms = np.abs(norms - 1.0) > 0.1  # More than 10% deviation from 1.0
            if abnormal_norms.any():
                abnormal_count = np.sum(abnormal_norms)
                validation_results["warnings"].append(
                    f"Found {abnormal_count} embeddings with abnormal norms (expected ~1.0)"
                )
        
        # Check for duplicate embeddings (might indicate processing issues)
        unique_embeddings = np.unique(embeddings, axis=0)
        if len(unique_embeddings) < len(embeddings):
            duplicate_count = len(embeddings) - len(unique_embeddings)
            validation_results["warnings"].append(f"Found {duplicate_count} duplicate embeddings")
        
        return validation_results
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        return self.stats.copy()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information."""
        try:
            return {
                "model_name": self.model_name,
                "embedding_dimension": self.model.get_sentence_embedding_dimension(),
                "max_seq_length": self.model.max_seq_length,
                "device": str(self.model.device),
                "normalize_embeddings": self.normalize_embeddings,
                "batch_size": self.batch_size,
                "model_architecture": str(type(self.model._modules['0']).__name__) if hasattr(self.model, '_modules') else "Unknown"
            }
        except Exception as e:
            return {"error": f"Failed to get model info: {str(e)}"}