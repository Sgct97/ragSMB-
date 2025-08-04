"""
Test script for the EnterpriseEmbeddingGenerator module

This script validates embedding generation functionality using SentenceTransformers
with all-MiniLM-L6-v2 model for optimal RAG performance.
"""

from modules.embedding_generator import EnterpriseEmbeddingGenerator
from modules.text_chunker import EnterpriseTextChunker
from modules.document_loader import EnterpriseDocumentLoader
import numpy as np

def test_embedding_generator():
    """Test the embedding generator with various scenarios and document types."""
    
    print("=== Enterprise Embedding Generator Validation ===\n")
    
    # Initialize embedding generator
    try:
        embedder = EnterpriseEmbeddingGenerator(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            normalize_embeddings=True,
            batch_size=16
        )
        print(f"Model Information:")
        model_info = embedder.get_model_info()
        for key, value in model_info.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"❌ Failed to initialize embedding generator: {e}")
        return
    
    print("\n" + "="*50 + "\n")
    
    # Test 1: Simple text embedding
    print("1. Testing simple text embedding...")
    try:
        sample_texts = [
            "This is a business document about quarterly results.",
            "Our company performance has improved significantly this quarter.",
            "The financial metrics show strong growth trends.",
            "Customer satisfaction scores have increased by 15%."
        ]
        
        embeddings = embedder.generate_embeddings(sample_texts, show_progress=False)
        print(f"   ✅ Generated embeddings for {len(sample_texts)} texts")
        print(f"   📐 Embedding shape: {embeddings.shape}")
        print(f"   📊 Embedding summary:")
        
        summary = embedder.get_embedding_summary(embeddings)
        for key, value in summary.items():
            if isinstance(value, dict):
                print(f"      {key}:")
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, float):
                        print(f"        {sub_key}: {sub_value:.4f}")
                    else:
                        print(f"        {sub_key}: {sub_value}")
            else:
                print(f"      {key}: {value}")
        
    except Exception as e:
        print(f"   ❌ Simple text embedding failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Document embedding with chunked documents
    print("2. Testing document embedding with chunked documents...")
    try:
        # Load and chunk documents first
        loader = EnterpriseDocumentLoader()
        chunker = EnterpriseTextChunker(chunk_size=500, chunk_overlap=100)  # Smaller chunks for testing
        
        # Load business memo
        memo_docs = loader.load_single_document("data/business-memo.txt")
        memo_chunks = chunker.chunk_documents(memo_docs)
        print(f"   📄 Loaded and chunked business memo: {len(memo_chunks)} chunks")
        
        # Generate embeddings for document chunks
        embedded_docs = embedder.embed_documents(memo_chunks, show_progress=False)
        print(f"   ✅ Generated embeddings for {len(embedded_docs)} document chunks")
        
        # Show first embedded document details
        if embedded_docs:
            first_doc = embedded_docs[0]
            print(f"   📋 First embedded document:")
            print(f"      Content length: {len(first_doc['content'])} chars")
            print(f"      Content preview: {first_doc['content'][:100]}...")
            print(f"      Embedding shape: {np.array(first_doc['embedding']).shape}")
            print(f"      Metadata keys: {list(first_doc['metadata'].keys())}")
        
    except Exception as e:
        print(f"   ❌ Document embedding failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Query embedding and similarity search
    print("3. Testing query embedding and similarity search...")
    try:
        # Generate query embedding
        query = "What are the budget projections for Q1 2025?"
        query_embedding = embedder.generate_query_embedding(query)
        print(f"   ✅ Generated query embedding")
        print(f"   🔍 Query: '{query}'")
        print(f"   📐 Query embedding shape: {query_embedding.shape}")
        
        # Find most similar documents
        if 'embedded_docs' in locals():
            doc_embeddings = [np.array(doc['embedding_array']) for doc in embedded_docs]
            similar_docs = embedder.find_most_similar(
                query_embedding, 
                doc_embeddings, 
                top_k=3
            )
            
            print(f"   🎯 Top 3 most similar documents:")
            for i, result in enumerate(similar_docs):
                doc_idx = result['index']
                similarity = result['similarity']
                content_preview = embedded_docs[doc_idx]['content'][:100]
                print(f"      {i+1}. Similarity: {similarity:.4f}")
                print(f"         Content: {content_preview}...")
        
    except Exception as e:
        print(f"   ❌ Query embedding and similarity search failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 4: Embedding validation
    print("4. Testing embedding validation...")
    try:
        validation_results = embedder.validate_embeddings(embeddings)
        print(f"   📋 Validation Results:")
        print(f"      Valid: {validation_results['is_valid']}")
        print(f"      Embedding Count: {validation_results['embedding_count']}")
        
        if validation_results['issues']:
            print(f"      Issues: {validation_results['issues']}")
        else:
            print(f"      Issues: None")
            
        if validation_results['warnings']:
            print(f"      Warnings: {validation_results['warnings']}")
        else:
            print(f"      Warnings: None")
            
    except Exception as e:
        print(f"   ❌ Embedding validation failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 5: Similarity calculations
    print("5. Testing similarity calculations...")
    try:
        # Test similarity between different texts
        text1 = "The company's revenue increased this quarter."
        text2 = "Quarterly revenue showed significant growth."
        text3 = "The weather is nice today."
        
        emb1 = embedder.generate_query_embedding(text1)
        emb2 = embedder.generate_query_embedding(text2)
        emb3 = embedder.generate_query_embedding(text3)
        
        sim_related = embedder.calculate_similarity(emb1, emb2)
        sim_unrelated = embedder.calculate_similarity(emb1, emb3)
        
        print(f"   📊 Similarity Tests:")
        print(f"      Text 1: '{text1}'")
        print(f"      Text 2: '{text2}'")
        print(f"      Text 3: '{text3}'")
        print(f"      Similarity (1-2): {sim_related:.4f} (should be high)")
        print(f"      Similarity (1-3): {sim_unrelated:.4f} (should be low)")
        
        if sim_related > sim_unrelated:
            print(f"   ✅ Similarity test passed: Related texts more similar")
        else:
            print(f"   ⚠️ Similarity test warning: Expected related texts to be more similar")
        
    except Exception as e:
        print(f"   ❌ Similarity calculation failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 6: Edge cases and error handling
    print("6. Testing edge cases and error handling...")
    
    # Test empty text list
    try:
        embedder.generate_embeddings([])
        print("   ❌ Should have failed for empty text list")
    except Exception as e:
        print(f"   ✅ Correctly handled empty text list: {type(e).__name__}")
    
    # Test empty query
    try:
        embedder.generate_query_embedding("")
        print("   ❌ Should have failed for empty query")
    except Exception as e:
        print(f"   ✅ Correctly handled empty query: {type(e).__name__}")
    
    # Test very long text (should be truncated)
    try:
        long_text = "This is a very long text. " * 200  # Much longer than 256 tokens
        long_embedding = embedder.generate_query_embedding(long_text)
        print(f"   ✅ Long text handled: embedding shape {long_embedding.shape}")
    except Exception as e:
        print(f"   ❌ Long text handling failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 7: Processing statistics
    print("7. Testing processing statistics...")
    try:
        stats = embedder.get_processing_stats()
        print(f"   📈 Processing Statistics:")
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"      {key}: {value:.4f}")
            else:
                print(f"      {key}: {value}")
    except Exception as e:
        print(f"   ❌ Statistics retrieval failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 8: Batch processing efficiency
    print("8. Testing batch processing efficiency...")
    try:
        # Generate embeddings for varying batch sizes
        test_texts = [f"This is test sentence number {i}." for i in range(50)]
        
        import time
        
        # Test with default batch size
        start_time = time.time()
        batch_embeddings = embedder.generate_embeddings(test_texts, show_progress=False)
        batch_time = time.time() - start_time
        
        print(f"   ⚡ Batch Processing Results:")
        print(f"      Texts processed: {len(test_texts)}")
        print(f"      Batch size: {embedder.batch_size}")
        print(f"      Processing time: {batch_time:.2f}s")
        print(f"      Rate: {len(test_texts)/batch_time:.1f} texts/second")
        print(f"      Embedding shape: {batch_embeddings.shape}")
        
    except Exception as e:
        print(f"   ❌ Batch processing test failed: {e}")
    
    print("\n=== Embedding Generator Validation Complete ===")

if __name__ == "__main__":
    test_embedding_generator()