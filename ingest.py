"""
Enterprise RAG Ingestion Pipeline

Main orchestrator script that coordinates all modules to create a complete
document ingestion and vector storage pipeline for SMB documents.

Author: Enterprise RAG Pipeline
Usage: python ingest.py [--data-dir data] [--collection-name smb_documents]
"""

import os
import argparse
import time
from datetime import datetime
from typing import Dict, Any, List

from modules.document_loader import EnterpriseDocumentLoader
from modules.text_chunker import EnterpriseTextChunker  
from modules.embedding_generator import EnterpriseEmbeddingGenerator
from modules.vector_storage import EnterpriseVectorStorage


class IngestionPipelineError(Exception):
    """Custom exception for ingestion pipeline errors"""
    pass


class EnterpriseIngestionPipeline:
    """
    Production-grade document ingestion pipeline for SMB RAG applications.
    
    This orchestrator coordinates all components to:
    1. Load documents from multiple file types (PDF, DOCX, PPTX, TXT, CSV, EML)
    2. Chunk documents intelligently with semantic boundaries
    3. Generate high-quality embeddings using SentenceTransformers
    4. Store in ChromaDB vector database for similarity search
    
    Features:
    - Modular architecture with swappable components
    - Comprehensive error handling and recovery
    - Performance monitoring and statistics
    - Production-ready configuration
    - Batch processing for efficiency
    """
    
    def __init__(
        self,
        data_directory: str = "data",
        collection_name: str = "smb_documents",
        storage_path: str = "./chroma_db",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        batch_size: int = 32
    ):
        """
        Initialize the ingestion pipeline with production settings.
        
        Args:
            data_directory: Directory containing documents to ingest
            collection_name: Name for the vector database collection
            storage_path: Path for ChromaDB persistent storage
            chunk_size: Maximum characters per chunk
            chunk_overlap: Character overlap between chunks
            batch_size: Batch size for embedding generation
        """
        self.data_directory = data_directory
        self.collection_name = collection_name
        self.storage_path = storage_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.batch_size = batch_size
        
        # Initialize components
        print("=== Initializing Enterprise RAG Ingestion Pipeline ===\n")
        
        try:
            print("1. Initializing Document Loader...")
            self.document_loader = EnterpriseDocumentLoader()
            print("   ✅ Document Loader ready")
            
            print("\n2. Initializing Text Chunker...")
            self.text_chunker = EnterpriseTextChunker(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            print(f"   ✅ Text Chunker ready (size: {chunk_size}, overlap: {chunk_overlap})")
            
            print("\n3. Initializing Embedding Generator...")
            self.embedding_generator = EnterpriseEmbeddingGenerator(
                batch_size=batch_size,
                normalize_embeddings=True
            )
            print(f"   ✅ Embedding Generator ready (batch size: {batch_size})")
            
            print("\n4. Initializing Vector Storage...")
            self.vector_storage = EnterpriseVectorStorage(
                storage_path=storage_path,
                collection_name=collection_name,
                distance_metric="cosine",
                batch_size=batch_size
            )
            print(f"   ✅ Vector Storage ready (collection: {collection_name})")
            
        except Exception as e:
            raise IngestionPipelineError(f"Failed to initialize pipeline components: {str(e)}")
        
        # Pipeline statistics
        self.stats = {
            "start_time": None,
            "end_time": None,
            "total_processing_time": 0.0,
            "files_processed": 0,
            "documents_loaded": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "documents_stored": 0,
            "errors_encountered": 0,
            "pipeline_stages": {}
        }
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Execute the complete ingestion pipeline.
        
        Returns:
            Dictionary with comprehensive pipeline results
        """
        print(f"\n=== Starting Full Pipeline Execution ===\n")
        print(f"Data Directory: {self.data_directory}")
        print(f"Collection: {self.collection_name}")
        print(f"Processing Parameters:")
        print(f"  Chunk Size: {self.chunk_size}")
        print(f"  Chunk Overlap: {self.chunk_overlap}")
        print(f"  Batch Size: {self.batch_size}")
        print()
        
        self.stats["start_time"] = datetime.now()
        overall_start_time = time.time()
        
        try:
            # Stage 1: Document Loading
            print("STAGE 1: Document Loading")
            print("-" * 30)
            stage_start_time = time.time()
            
            documents = self._load_documents()
            
            stage_time = time.time() - stage_start_time
            self.stats["pipeline_stages"]["document_loading"] = {
                "duration": stage_time,
                "documents_loaded": len(documents),
                "success": True
            }
            
            print(f"✅ Stage 1 Complete ({stage_time:.2f}s)")
            print(f"   Documents loaded: {len(documents)}\n")
            
            # Stage 2: Text Chunking
            print("STAGE 2: Text Chunking")
            print("-" * 30)
            stage_start_time = time.time()
            
            chunks = self._chunk_documents(documents)
            
            stage_time = time.time() - stage_start_time
            self.stats["pipeline_stages"]["text_chunking"] = {
                "duration": stage_time,
                "chunks_created": len(chunks),
                "success": True
            }
            
            print(f"✅ Stage 2 Complete ({stage_time:.2f}s)")
            print(f"   Chunks created: {len(chunks)}\n")
            
            # Stage 3: Embedding Generation
            print("STAGE 3: Embedding Generation")
            print("-" * 30)
            stage_start_time = time.time()
            
            embedded_docs = self._generate_embeddings(chunks)
            
            stage_time = time.time() - stage_start_time
            self.stats["pipeline_stages"]["embedding_generation"] = {
                "duration": stage_time,
                "embeddings_generated": len(embedded_docs),
                "success": True
            }
            
            print(f"✅ Stage 3 Complete ({stage_time:.2f}s)")
            print(f"   Embeddings generated: {len(embedded_docs)}\n")
            
            # Stage 4: Vector Storage
            print("STAGE 4: Vector Storage")
            print("-" * 30)
            stage_start_time = time.time()
            
            storage_result = self._store_vectors(embedded_docs)
            
            stage_time = time.time() - stage_start_time
            self.stats["pipeline_stages"]["vector_storage"] = {
                "duration": stage_time,
                "documents_stored": storage_result["documents_added"],
                "success": True
            }
            
            print(f"✅ Stage 4 Complete ({stage_time:.2f}s)")
            print(f"   Documents stored: {storage_result['documents_added']}\n")
            
            # Calculate final statistics
            total_time = time.time() - overall_start_time
            self.stats["end_time"] = datetime.now()
            self.stats["total_processing_time"] = total_time
            self.stats["documents_loaded"] = len(documents)
            self.stats["chunks_created"] = len(chunks)
            self.stats["embeddings_generated"] = len(embedded_docs)
            self.stats["documents_stored"] = storage_result["documents_added"]
            
            # Pipeline completion summary
            print("=== Pipeline Execution Complete ===")
            self._print_pipeline_summary()
            
            return {
                "success": True,
                "statistics": self.stats,
                "collection_info": self.vector_storage.get_collection_info()
            }
            
        except Exception as e:
            self.stats["errors_encountered"] += 1
            self.stats["end_time"] = datetime.now()
            
            print(f"❌ Pipeline failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "statistics": self.stats
            }
    
    def _load_documents(self) -> List:
        """Load all supported documents from the data directory."""
        print(f"Loading documents from: {self.data_directory}")
        
        if not os.path.exists(self.data_directory):
            raise IngestionPipelineError(f"Data directory not found: {self.data_directory}")
        
        documents = self.document_loader.load_directory(self.data_directory)
        
        if not documents:
            raise IngestionPipelineError(f"No documents found in {self.data_directory}")
        
        # Get document summary
        doc_summary = self.document_loader.get_document_summary(documents)
        print(f"Document Summary:")
        for key, value in doc_summary.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
        
        return documents
    
    def _chunk_documents(self, documents: List) -> List:
        """Chunk documents into optimal sizes for embeddings."""
        print(f"Chunking {len(documents)} documents...")
        
        chunks = self.text_chunker.chunk_documents(documents)
        
        if not chunks:
            raise IngestionPipelineError("No chunks created from documents")
        
        # Validate chunks
        validation_result = self.text_chunker.validate_chunks(chunks)
        if not validation_result["is_valid"]:
            print(f"⚠️ Chunk validation warnings: {validation_result['issues']}")
        
        # Get chunk summary
        chunk_summary = self.text_chunker.get_chunk_summary(chunks)
        print(f"Chunk Summary:")
        for key, value in chunk_summary.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
        
        return chunks
    
    def _generate_embeddings(self, chunks: List) -> List:
        """Generate embeddings for document chunks."""
        print(f"Generating embeddings for {len(chunks)} chunks...")
        
        embedded_docs = self.embedding_generator.embed_documents(
            chunks, 
            show_progress=True
        )
        
        if not embedded_docs:
            raise IngestionPipelineError("No embeddings generated")
        
        # Validate embeddings
        embeddings_array = [doc["embedding_array"] for doc in embedded_docs]
        import numpy as np
        embeddings_np = np.array([emb for emb in embeddings_array])
        
        validation_result = self.embedding_generator.validate_embeddings(embeddings_np)
        if not validation_result["is_valid"]:
            print(f"⚠️ Embedding validation issues: {validation_result['issues']}")
        
        # Get embedding summary
        embedding_summary = self.embedding_generator.get_embedding_summary(embeddings_np)
        print(f"Embedding Summary:")
        for key, value in embedding_summary.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, float):
                        print(f"    {sub_key}: {sub_value:.4f}")
                    else:
                        print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
        
        return embedded_docs
    
    def _store_vectors(self, embedded_docs: List) -> Dict[str, Any]:
        """Store embeddings in the vector database."""
        print(f"Storing {len(embedded_docs)} embedded documents in vector database...")
        
        storage_result = self.vector_storage.add_documents(embedded_docs)
        
        if not storage_result["success"]:
            raise IngestionPipelineError("Failed to store documents in vector database")
        
        print(f"Storage Results:")
        for key, value in storage_result.items():
            print(f"  {key}: {value}")
        
        return storage_result
    
    def _print_pipeline_summary(self):
        """Print comprehensive pipeline execution summary."""
        print(f"\n📊 PIPELINE EXECUTION SUMMARY")
        print(f"=" * 50)
        print(f"🕐 Total Processing Time: {self.stats['total_processing_time']:.2f} seconds")
        print(f"📄 Documents Processed: {self.stats['documents_loaded']}")
        print(f"📝 Chunks Created: {self.stats['chunks_created']}")
        print(f"🧠 Embeddings Generated: {self.stats['embeddings_generated']}")  
        print(f"💾 Documents Stored: {self.stats['documents_stored']}")
        print(f"❌ Errors Encountered: {self.stats['errors_encountered']}")
        
        print(f"\n⏱️ STAGE TIMING BREAKDOWN:")
        for stage, info in self.stats["pipeline_stages"].items():
            print(f"  {stage.replace('_', ' ').title()}: {info['duration']:.2f}s")
        
        print(f"\n🎯 PERFORMANCE METRICS:")
        if self.stats['total_processing_time'] > 0:
            docs_per_sec = self.stats['documents_loaded'] / self.stats['total_processing_time']
            chunks_per_sec = self.stats['chunks_created'] / self.stats['total_processing_time']
            embeddings_per_sec = self.stats['embeddings_generated'] / self.stats['total_processing_time']
            
            print(f"  Documents/second: {docs_per_sec:.2f}")
            print(f"  Chunks/second: {chunks_per_sec:.2f}")
            print(f"  Embeddings/second: {embeddings_per_sec:.2f}")
        
        # Get vector storage info
        collection_info = self.vector_storage.get_collection_info()
        print(f"\n💽 STORAGE INFORMATION:")
        print(f"  Collection: {collection_info['collection_name']}")
        print(f"  Total Documents: {collection_info['document_count']}")
        print(f"  Storage Size: {collection_info['storage_size_mb']:.2f} MB")


def main():
    """Main entry point for the ingestion pipeline."""
    parser = argparse.ArgumentParser(
        description="Enterprise RAG Ingestion Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ingest.py                           # Use default settings
  python ingest.py --data-dir ./documents    # Custom data directory  
  python ingest.py --collection-name legal_docs --chunk-size 500
        """
    )
    
    parser.add_argument(
        "--data-dir", 
        default="data",
        help="Directory containing documents to ingest (default: data)"
    )
    
    parser.add_argument(
        "--collection-name",
        default="smb_documents", 
        help="Name for the vector database collection (default: smb_documents)"
    )
    
    parser.add_argument(
        "--storage-path",
        default="./chroma_db",
        help="Path for ChromaDB persistent storage (default: ./chroma_db)"
    )
    
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Maximum characters per chunk (default: 1000)"
    )
    
    parser.add_argument(
        "--chunk-overlap", 
        type=int,
        default=200,
        help="Character overlap between chunks (default: 200)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int, 
        default=32,
        help="Batch size for processing (default: 32)"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize and run pipeline
        pipeline = EnterpriseIngestionPipeline(
            data_directory=args.data_dir,
            collection_name=args.collection_name,
            storage_path=args.storage_path,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            batch_size=args.batch_size
        )
        
        # Execute full pipeline
        result = pipeline.run_full_pipeline()
        
        if result["success"]:
            print(f"\n🎉 PIPELINE COMPLETED SUCCESSFULLY!")
            exit(0)
        else:
            print(f"\n💥 PIPELINE FAILED: {result['error']}")
            exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Pipeline interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()