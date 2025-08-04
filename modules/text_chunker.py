"""
Enterprise-Grade Text Chunking Module

Handles intelligent text chunking for optimal RAG performance using 
RecursiveCharacterTextSplitter with production-ready configuration.

Author: Enterprise RAG Pipeline
"""

from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class TextChunkingError(Exception):
    """Custom exception for text chunking errors"""
    pass


class EnterpriseTextChunker:
    """
    Production-grade text chunker optimized for SMB document processing.
    
    Uses RecursiveCharacterTextSplitter with intelligent defaults:
    - chunk_size=1000: Optimal for most LLM context windows
    - chunk_overlap=200: Preserves context across chunks (20% overlap)
    - Smart separators: Prioritizes semantic boundaries (paragraphs > sentences > words)
    
    Benefits:
    - Maintains document coherence across chunks
    - Preserves metadata from original documents
    - Handles various document types intelligently
    - Provides comprehensive chunk validation
    """
    
    def __init__(
        self, 
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
        keep_separator: bool = True
    ):
        """
        Initialize the text chunker with production-optimized settings.
        
        Args:
            chunk_size: Maximum characters per chunk (default: 1000)
            chunk_overlap: Characters to overlap between chunks (default: 200) 
            separators: Custom separators list (default: intelligent hierarchy)
            keep_separator: Whether to preserve separators in chunks (default: True)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Use intelligent separator hierarchy if none provided
        if separators is None:
            # Priority: Paragraphs > Sentences > Words > Characters
            separators = [
                "\n\n",      # Double newline (paragraphs)
                "\n",        # Single newline (line breaks)
                ". ",        # Sentence endings
                "! ",        # Exclamations
                "? ",        # Questions
                "; ",        # Semicolons
                ", ",        # Commas
                " ",         # Spaces (words)
                ""           # Character-level (last resort)
            ]
        
        self.separators = separators  # Store for access
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            keep_separator=keep_separator,
            is_separator_regex=False,  # Use literal separators for reliability
            length_function=len        # Use character count
        )
        
        # Statistics tracking
        self.stats = {
            "total_documents_processed": 0,
            "total_chunks_created": 0,
            "average_chunk_size": 0,
            "min_chunk_size": float('inf'),
            "max_chunk_size": 0
        }
        
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split a list of documents into optimally-sized chunks.
        
        Args:
            documents: List of LangChain Document objects to chunk
            
        Returns:
            List of chunked Document objects with preserved metadata
            
        Raises:
            TextChunkingError: If chunking fails or produces invalid results
        """
        if not documents:
            raise TextChunkingError("No documents provided for chunking")
            
        try:
            # Split documents using the text splitter
            chunked_docs = self.text_splitter.split_documents(documents)
            
            if not chunked_docs:
                raise TextChunkingError("Text splitter produced no chunks")
            
            # Enhance metadata with chunk information
            enhanced_chunks = []
            for i, chunk in enumerate(chunked_docs):
                # Add chunk-specific metadata
                chunk.metadata = {
                    **chunk.metadata,  # Preserve original metadata
                    "chunk_id": i,
                    "chunk_size": len(chunk.page_content),
                    "chunking_method": "RecursiveCharacterTextSplitter",
                    "chunk_overlap": self.chunk_overlap,
                    "max_chunk_size": self.chunk_size
                }
                enhanced_chunks.append(chunk)
            
            # Update statistics
            self._update_stats(documents, enhanced_chunks)
            
            return enhanced_chunks
            
        except Exception as e:
            raise TextChunkingError(f"Failed to chunk documents: {str(e)}")
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Split raw text into Document chunks.
        
        Args:
            text: Raw text string to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of Document objects created from text chunks
        """
        if not text or not text.strip():
            raise TextChunkingError("No valid text provided for chunking")
            
        if metadata is None:
            metadata = {}
            
        try:
            # Create documents from text chunks
            text_chunks = self.text_splitter.split_text(text)
            
            documents = []
            for i, chunk in enumerate(text_chunks):
                doc_metadata = {
                    **metadata,
                    "chunk_id": i,
                    "chunk_size": len(chunk),
                    "chunking_method": "RecursiveCharacterTextSplitter",
                    "chunk_overlap": self.chunk_overlap,
                    "max_chunk_size": self.chunk_size,
                    "source_type": "raw_text"
                }
                
                documents.append(Document(
                    page_content=chunk,
                    metadata=doc_metadata
                ))
            
            return documents
            
        except Exception as e:
            raise TextChunkingError(f"Failed to chunk text: {str(e)}")
    
    def _update_stats(self, original_docs: List[Document], chunked_docs: List[Document]):
        """Update internal statistics after chunking."""
        self.stats["total_documents_processed"] += len(original_docs)
        new_chunks = len(chunked_docs)
        self.stats["total_chunks_created"] += new_chunks
        
        # Calculate chunk size statistics
        chunk_sizes = [len(doc.page_content) for doc in chunked_docs]
        
        if chunk_sizes:
            current_min = min(chunk_sizes)
            current_max = max(chunk_sizes)
            
            self.stats["min_chunk_size"] = min(self.stats["min_chunk_size"], current_min)
            self.stats["max_chunk_size"] = max(self.stats["max_chunk_size"], current_max)
            
            # Calculate running average
            total_chars = sum(chunk_sizes)
            total_chunks = self.stats["total_chunks_created"]
            self.stats["average_chunk_size"] = total_chars / total_chunks if total_chunks > 0 else 0
    
    def get_chunk_summary(self, chunks: List[Document]) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of chunks for validation.
        
        Args:
            chunks: List of chunked documents
            
        Returns:
            Dictionary with chunk statistics and metadata
        """
        if not chunks:
            return {"total_chunks": 0}
            
        chunk_sizes = [len(chunk.page_content) for chunk in chunks]
        total_chars = sum(chunk_sizes)
        
        # Analyze metadata distribution
        file_types = {}
        sources = {}
        
        for chunk in chunks:
            # Count file types
            file_type = chunk.metadata.get('file_type', 'unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # Count sources
            source = chunk.metadata.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        return {
            "total_chunks": len(chunks),
            "total_characters": total_chars,
            "average_chunk_size": total_chars // len(chunks) if chunks else 0,
            "min_chunk_size": min(chunk_sizes) if chunk_sizes else 0,
            "max_chunk_size": max(chunk_sizes) if chunk_sizes else 0,
            "chunk_size_distribution": {
                "small_chunks_(<500)": len([s for s in chunk_sizes if s < 500]),
                "medium_chunks_(500-800)": len([s for s in chunk_sizes if 500 <= s <= 800]),
                "large_chunks_(>800)": len([s for s in chunk_sizes if s > 800])
            },
            "file_types_chunked": file_types,
            "sources_chunked": len(sources),
            "chunking_config": {
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "separator_count": len(self.separators)
            }
        }
    
    def validate_chunks(self, chunks: List[Document]) -> Dict[str, Any]:
        """
        Validate that chunks meet quality standards.
        
        Args:
            chunks: List of chunks to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "chunk_count": len(chunks)
        }
        
        if not chunks:
            validation_results["is_valid"] = False
            validation_results["issues"].append("No chunks produced")
            return validation_results
        
        # Check for empty chunks
        empty_chunks = [i for i, chunk in enumerate(chunks) if not chunk.page_content.strip()]
        if empty_chunks:
            validation_results["issues"].append(f"Empty chunks found at indices: {empty_chunks}")
            validation_results["is_valid"] = False
        
        # Check for oversized chunks
        oversized_chunks = [
            i for i, chunk in enumerate(chunks) 
            if len(chunk.page_content) > self.chunk_size * 1.1  # Allow 10% tolerance
        ]
        if oversized_chunks:
            validation_results["warnings"].append(
                f"Chunks exceeding target size found at indices: {oversized_chunks}"
            )
        
        # Check for very small chunks (might indicate poor splitting)
        tiny_chunks = [i for i, chunk in enumerate(chunks) if len(chunk.page_content) < 50]
        if len(tiny_chunks) > len(chunks) * 0.1:  # More than 10% are tiny
            validation_results["warnings"].append(
                f"Many very small chunks detected ({len(tiny_chunks)} out of {len(chunks)})"
            )
        
        # Check metadata consistency
        chunks_missing_metadata = [
            i for i, chunk in enumerate(chunks) 
            if not chunk.metadata.get('chunk_id') is not None
        ]
        if chunks_missing_metadata:
            validation_results["issues"].append("Some chunks missing required metadata")
            validation_results["is_valid"] = False
        
        return validation_results
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        stats = self.stats.copy()
        
        # Fix infinity values for display
        if stats["min_chunk_size"] == float('inf'):
            stats["min_chunk_size"] = 0
            
        return stats