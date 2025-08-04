"""
Enterprise RAG Query Pipeline

Main query processing script that handles user questions by:
1. Converting queries to embeddings
2. Retrieving relevant document chunks from ChromaDB
3. Generating contextual responses using local Llama 3.1
4. Providing source citations and confidence scores

Author: Enterprise RAG Pipeline
Usage: python query.py "Your question here"
"""

import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from modules.embedding_generator import EnterpriseEmbeddingGenerator
from modules.vector_storage import EnterpriseVectorStorage


class QueryPipelineError(Exception):
    """Custom exception for query pipeline errors"""
    pass


class EnterpriseQueryPipeline:
    """
    Production-grade RAG query pipeline for SMB applications.
    
    This orchestrator coordinates all components to:
    1. Convert user queries to embeddings using SentenceTransformers
    2. Retrieve relevant document chunks via similarity search
    3. Assemble context from retrieved chunks
    4. Generate responses using local Llama 3.1 via Ollama
    5. Format responses with source citations and confidence scores
    
    Features:
    - 100% local processing (no external API calls)
    - Context-only responses (no LLM knowledge fallback)
    - Source citation with confidence scoring
    - Performance monitoring and statistics
    - Production-ready error handling
    """
    
    def __init__(
        self,
        collection_name: str = "smb_documents",
        storage_path: str = "./chroma_db",
        model_name: str = "llama3.1:8b-instruct-q4_K_M",
        ollama_host: str = "http://localhost:11434",
        top_k_results: int = 5,
        max_context_length: int = 2000
    ):
        """
        Initialize the query pipeline with production configurations.
        
        Args:
            collection_name: ChromaDB collection name
            storage_path: Path to ChromaDB storage
            model_name: Ollama model name
            ollama_host: Ollama server URL
            top_k_results: Number of chunks to retrieve
            max_context_length: Maximum context characters for LLM
        """
        self.collection_name = collection_name
        self.storage_path = storage_path
        self.model_name = model_name
        self.ollama_host = ollama_host
        self.top_k_results = top_k_results
        self.max_context_length = max_context_length
        
        # Initialize components
        self.embedding_generator = None
        self.vector_storage = None
        
        # Statistics tracking
        self.stats = {
            "queries_processed": 0,
            "total_query_time": 0.0,
            "avg_retrieval_time": 0.0,
            "avg_generation_time": 0.0,
            "successful_queries": 0,
            "failed_queries": 0
        }
    
    def initialize_components(self) -> None:
        """Initialize all pipeline components."""
        try:
            print("🔧 Initializing RAG Query Pipeline...")
            
            # Initialize embedding generator
            print("1. Initializing Embedding Generator...")
            self.embedding_generator = EnterpriseEmbeddingGenerator(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                normalize_embeddings=True,
                batch_size=32
            )
            print(f"   ✅ Embedding Generator ready")
            
            # Initialize vector storage
            print("2. Initializing Vector Storage...")
            self.vector_storage = EnterpriseVectorStorage(
                storage_path=self.storage_path,
                collection_name=self.collection_name,
                distance_metric="cosine"
            )
            print(f"   ✅ Vector Storage ready (collection: {self.collection_name})")
            
            # Test Ollama connection
            print("3. Testing Ollama Connection...")
            self._test_ollama_connection()
            print(f"   ✅ Ollama ready (model: {self.model_name})")
            
            print("🎉 All components initialized successfully!\n")
            
        except Exception as e:
            raise QueryPipelineError(f"Component initialization failed: {str(e)}")
    
    def _test_ollama_connection(self) -> None:
        """Test connection to Ollama server."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            response.raise_for_status()
            
            # Check if our model is available
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            
            if self.model_name not in model_names:
                raise QueryPipelineError(f"Model {self.model_name} not found. Available: {model_names}")
                
        except requests.exceptions.RequestException as e:
            raise QueryPipelineError(f"Cannot connect to Ollama at {self.ollama_host}: {str(e)}")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query through the complete RAG pipeline.
        
        Args:
            query: User question/query string
            
        Returns:
            Dictionary containing response, sources, metadata, and statistics
        """
        start_time = time.time()
        
        try:
            # Validate query
            if not query or not query.strip():
                raise QueryPipelineError("Empty query provided")
            
            query = query.strip()
            print(f"🔍 Processing query: '{query}'\n")
            
            # Step 1: Generate query embedding
            embedding_start = time.time()
            print("📐 Step 1: Generating query embedding...")
            query_embedding = self.embedding_generator.generate_query_embedding(query)
            embedding_time = time.time() - embedding_start
            print(f"   ✅ Query embedded ({embedding_time:.3f}s)")
            
            # Step 2: Retrieve relevant chunks
            retrieval_start = time.time()
            print("🔎 Step 2: Retrieving relevant chunks...")
            retrieved_chunks = self.vector_storage.similarity_search(
                query_embedding=query_embedding,
                top_k=self.top_k_results,
                include_distances=True
            )
            retrieval_time = time.time() - retrieval_start
            print(f"   ✅ Retrieved {len(retrieved_chunks)} chunks ({retrieval_time:.3f}s)")
            
            # Step 3: Assemble context
            print("📄 Step 3: Assembling context...")
            context_info = self._assemble_context(retrieved_chunks)
            print(f"   ✅ Context assembled ({len(context_info['context'])} chars)")
            
            # Step 4: Generate response
            generation_start = time.time()
            print("🤖 Step 4: Generating response...")
            response = self._generate_response(query, context_info['context'])
            generation_time = time.time() - generation_start
            print(f"   ✅ Response generated ({generation_time:.3f}s)")
            
            # Calculate total time
            total_time = time.time() - start_time
            
            # Update statistics
            self._update_statistics(total_time, retrieval_time, generation_time, success=True)
            
            # Format final result
            result = {
                "query": query,
                "response": response,
                "sources": context_info['sources'],
                "context_used": context_info['context'][:200] + "..." if len(context_info['context']) > 200 else context_info['context'],
                "retrieval_stats": {
                    "chunks_found": len(retrieved_chunks),
                    "top_similarity_score": retrieved_chunks[0].get('distance', 0) if retrieved_chunks else 0,
                    "context_length": len(context_info['context'])
                },
                "performance": {
                    "total_time": round(total_time, 3),
                    "embedding_time": round(embedding_time, 3),
                    "retrieval_time": round(retrieval_time, 3),
                    "generation_time": round(generation_time, 3)
                },
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
            print(f"\n✅ Query processed successfully in {total_time:.3f}s")
            return result
            
        except Exception as e:
            total_time = time.time() - start_time
            self._update_statistics(total_time, 0, 0, success=False)
            
            error_result = {
                "query": query,
                "response": None,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "success": False
            }
            
            print(f"\n❌ Query processing failed: {str(e)}")
            return error_result
    
    def _assemble_context(self, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assemble context from retrieved chunks with source tracking.
        
        Args:
            retrieved_chunks: List of retrieved document chunks with metadata
            
        Returns:
            Dictionary with assembled context and source information
        """
        context_parts = []
        sources = []
        total_length = 0
        
        for i, chunk in enumerate(retrieved_chunks):
            # Extract chunk information
            content = chunk.get('content', '')  # Fixed: use 'content' key
            metadata = chunk.get('metadata', {})
            distance = chunk.get('distance', 1.0)
            
            # Calculate confidence score (1 - distance for cosine similarity)
            confidence = max(0, 1 - distance)
            
            # Check if adding this chunk would exceed context limit
            if total_length + len(content) > self.max_context_length:
                # Truncate content to fit within limit
                remaining_space = self.max_context_length - total_length
                if remaining_space > 100:  # Only add if meaningful content can fit
                    content = content[:remaining_space] + "..."
                else:
                    break
            
            # Add to context
            context_parts.append(f"[Source {i+1}]: {content}")
            total_length += len(content)
            
            # Track source information
            source_info = {
                "source_id": i + 1,
                "filename": metadata.get('source', 'Unknown'),
                "chunk_id": metadata.get('chunk_id', f'chunk_{i}'),
                "confidence_score": round(confidence, 3),
                "similarity_distance": round(distance, 3),
                "content_preview": content[:100] + "..." if len(content) > 100 else content
            }
            sources.append(source_info)
        
        # Combine all context parts
        full_context = "\n\n".join(context_parts)
        
        return {
            "context": full_context,
            "sources": sources,
            "total_chunks_used": len(context_parts),
            "context_length": len(full_context)
        }
    
    def _generate_response(self, query: str, context: str) -> str:
        """
        Generate response using local Ollama with strict context-only instruction.
        
        Args:
            query: Original user query
            context: Assembled context from retrieved chunks
            
        Returns:
            Generated response string
        """
        # Create prompt with principle-based role definition
        prompt = f"""You are a DOCUMENT ANALYST, not a general knowledge assistant.

ROLE & SCOPE:
- Your job: Analyze and compare data from the provided documents
- Your scope: ONLY the documents given to you
- Your confidence: When you find relevant data, analyze it confidently

KEY PRINCIPLE:
Users asking questions expect analysis of YOUR DOCUMENT SET, not universal knowledge.
When they ask "who/what/which is most/best/highest/won the most", they want you to 
analyze the data you have and find the maximum/optimum within that dataset.

You are NOT expected to know universal facts.
You ARE expected to analyze the information you have been given.

INSTRUCTIONS:
1. Examine ALL the data in the context below
2. For comparative questions, analyze and compare the values you see
3. Answer confidently when the data supports a clear conclusion
4. If truly no relevant data exists, then say you cannot find the information
5. Always cite sources [Source N] for your findings

DOCUMENT DATA:
{context}

USER QUESTION: {query}

ANALYSIS & ANSWER:"""
        
        try:
            # Make request to Ollama
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for factual responses
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract generated text
            generated_text = result.get('response', '').strip()
            
            if not generated_text:
                return "I apologize, but I was unable to generate a response based on the provided context."
            
            return generated_text
            
        except requests.exceptions.RequestException as e:
            raise QueryPipelineError(f"Failed to generate response via Ollama: {str(e)}")
    
    def _update_statistics(self, total_time: float, retrieval_time: float, generation_time: float, success: bool) -> None:
        """Update pipeline performance statistics."""
        self.stats["queries_processed"] += 1
        self.stats["total_query_time"] += total_time
        
        if success:
            self.stats["successful_queries"] += 1
            self.stats["avg_retrieval_time"] = (
                (self.stats["avg_retrieval_time"] * (self.stats["successful_queries"] - 1) + retrieval_time) / 
                self.stats["successful_queries"]
            )
            self.stats["avg_generation_time"] = (
                (self.stats["avg_generation_time"] * (self.stats["successful_queries"] - 1) + generation_time) / 
                self.stats["successful_queries"]
            )
        else:
            self.stats["failed_queries"] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current pipeline performance statistics."""
        if self.stats["queries_processed"] > 0:
            avg_total_time = self.stats["total_query_time"] / self.stats["queries_processed"]
        else:
            avg_total_time = 0.0
        
        return {
            **self.stats,
            "avg_total_time": round(avg_total_time, 3),
            "success_rate": round(
                (self.stats["successful_queries"] / max(1, self.stats["queries_processed"])) * 100, 1
            )
        }


def main():
    """Main CLI interface for the query pipeline."""
    parser = argparse.ArgumentParser(
        description="Enterprise RAG Query Pipeline - Ask questions about your documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python query.py "What are the Q1 2025 budget projections?"
  python query.py "Who won the most Stanley Cups?" --top-k 3
  python query.py "What are the client onboarding plans?" --collection mydata
        """
    )
    
    parser.add_argument(
        "query",
        help="Your question about the documents"
    )
    
    parser.add_argument(
        "--collection-name",
        default="smb_documents",
        help="ChromaDB collection name (default: smb_documents)"
    )
    
    parser.add_argument(
        "--storage-path",
        default="./chroma_db",
        help="Path to ChromaDB storage (default: ./chroma_db)"
    )
    
    parser.add_argument(
        "--model-name",
        default="llama3.1:8b-instruct-q4_K_M",
        help="Ollama model name (default: llama3.1:8b-instruct-q4_K_M)"
    )
    
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of relevant chunks to retrieve (default: 5)"
    )
    
    parser.add_argument(
        "--max-context",
        type=int,
        default=2000,
        help="Maximum context length for LLM (default: 2000)"
    )
    
    parser.add_argument(
        "--show-stats",
        action="store_true",
        help="Show performance statistics after query"
    )
    
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize pipeline
        pipeline = EnterpriseQueryPipeline(
            collection_name=args.collection_name,
            storage_path=args.storage_path,
            model_name=args.model_name,
            top_k_results=args.top_k,
            max_context_length=args.max_context
        )
        
        # Initialize components
        pipeline.initialize_components()
        
        # Process query
        result = pipeline.process_query(args.query)
        
        if args.json_output:
            # JSON output for programmatic use
            print(json.dumps(result, indent=2))
        else:
            # Human-readable output
            print("=" * 80)
            print("🎯 RAG QUERY RESULTS")
            print("=" * 80)
            print(f"📝 Question: {result['query']}")
            print(f"🤖 Response: {result['response']}")
            
            if result.get('success'):
                print(f"\n📚 Sources Used ({len(result['sources'])}):")
                for source in result['sources']:
                    print(f"  • {source['filename']} (confidence: {source['confidence_score']:.3f})")
                    print(f"    Preview: {source['content_preview']}")
                
                print(f"\n⚡ Performance:")
                perf = result['performance']
                print(f"  • Total time: {perf['total_time']}s")
                print(f"  • Retrieval: {perf['retrieval_time']}s")
                print(f"  • Generation: {perf['generation_time']}s")
                
                if args.show_stats:
                    print(f"\n📊 Pipeline Statistics:")
                    stats = pipeline.get_statistics()
                    print(f"  • Success rate: {stats['success_rate']}%")
                    print(f"  • Avg response time: {stats['avg_total_time']}s")
            else:
                print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
        
        exit(0 if result.get('success') else 1)
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Query interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()