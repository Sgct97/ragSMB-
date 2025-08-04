"""
Test script for the EnterpriseVectorStorage module

This script validates ChromaDB vector storage functionality including
document storage, similarity search, and production features.
"""

from modules.vector_storage import EnterpriseVectorStorage
from modules.embedding_generator import EnterpriseEmbeddingGenerator
from modules.text_chunker import EnterpriseTextChunker
from modules.document_loader import EnterpriseDocumentLoader
import numpy as np
import os
import shutil

def test_vector_storage():
    """Test the vector storage with various scenarios and document types."""
    
    print("=== Enterprise Vector Storage Validation ===\n")
    
    # Clean up any existing test database
    test_db_path = "./test_chroma_db"
    if os.path.exists(test_db_path):
        shutil.rmtree(test_db_path)
    
    # Initialize vector storage
    try:
        vector_store = EnterpriseVectorStorage(
            storage_path=test_db_path,
            collection_name="test_smb_documents",
            distance_metric="cosine",
            batch_size=10
        )
        
        print(f"Collection Information:")
        collection_info = vector_store.get_collection_info()
        for key, value in collection_info.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"❌ Failed to initialize vector storage: {e}")
        return
    
    print("\n" + "="*50 + "\n")
    
    # Test 1: Prepare sample embedded documents
    print("1. Preparing sample embedded documents...")
    try:
        # Initialize components for creating embedded documents
        loader = EnterpriseDocumentLoader()
        chunker = EnterpriseTextChunker(chunk_size=300, chunk_overlap=50)  # Smaller chunks for testing
        embedder = EnterpriseEmbeddingGenerator(batch_size=8)
        
        # Load and process business memo
        memo_docs = loader.load_single_document("data/business-memo.txt")
        memo_chunks = chunker.chunk_documents(memo_docs)
        embedded_docs = embedder.embed_documents(memo_chunks, show_progress=False)
        
        print(f"   ✅ Prepared {len(embedded_docs)} embedded documents")
        print(f"   📄 First document preview: {embedded_docs[0]['content'][:100]}...")
        print(f"   📐 Embedding shape: {np.array(embedded_docs[0]['embedding']).shape}")
        
    except Exception as e:
        print(f"   ❌ Failed to prepare embedded documents: {e}")
        return
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Add documents to vector storage
    print("2. Testing document storage...")
    try:
        storage_result = vector_store.add_documents(embedded_docs)
        print(f"   ✅ Storage completed successfully")
        print(f"   📊 Storage Results:")
        for key, value in storage_result.items():
            print(f"      {key}: {value}")
        
        # Verify storage
        updated_info = vector_store.get_collection_info()
        print(f"   📈 Updated document count: {updated_info['document_count']}")
        
    except Exception as e:
        print(f"   ❌ Document storage failed: {e}")
        return
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Similarity search with embedding
    print("3. Testing similarity search with embeddings...")
    try:
        # Create a query embedding for budget-related content
        query = "What are the budget projections and financial metrics?"
        query_embedding = embedder.generate_query_embedding(query)
        
        print(f"   🔍 Query: '{query}'")
        print(f"   📐 Query embedding shape: {query_embedding.shape}")
        
        # Perform similarity search
        search_results = vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=3,
            include_distances=True
        )
        
        print(f"   ✅ Similarity search completed: {len(search_results)} results")
        
        # Display results
        for i, result in enumerate(search_results):
            print(f"   {i+1}. Similarity: {result.get('similarity', 'N/A'):.4f}")
            print(f"      Content: {result['content'][:100]}...")
            print(f"      Metadata: {result['metadata'].get('original_filename', 'N/A')}")
        
    except Exception as e:
        print(f"   ❌ Similarity search failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 4: Document retrieval by ID
    print("4. Testing document retrieval by ID...")
    try:
        # Get first document's ID from search results
        if search_results:
            doc_id = search_results[0]['id']
            retrieved_doc = vector_store.get_document_by_id(doc_id)
            
            if retrieved_doc:
                print(f"   ✅ Document retrieved successfully")
                print(f"   📄 Document ID: {retrieved_doc['id']}")
                print(f"   📝 Content preview: {retrieved_doc['content'][:100]}...")
            else:
                print(f"   ❌ Document not found for ID: {doc_id}")
        else:
            print(f"   ⚠️ No search results available for ID test")
            
    except Exception as e:
        print(f"   ❌ Document retrieval failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 5: Metadata filtering
    print("5. Testing metadata filtering...")
    try:
        # Search with metadata filter
        metadata_filter = {"file_type": ".txt"}
        filtered_results = vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=5,
            metadata_filter=metadata_filter,
            include_distances=True
        )
        
        print(f"   ✅ Filtered search completed: {len(filtered_results)} results")
        print(f"   🔍 Filter: {metadata_filter}")
        
        # Verify all results match the filter
        for result in filtered_results:
            file_type = result['metadata'].get('file_type', 'Unknown')
            print(f"      File type: {file_type}, Similarity: {result.get('similarity', 'N/A'):.4f}")
        
    except Exception as e:
        print(f"   ❌ Metadata filtering failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 6: Batch operations and performance
    print("6. Testing batch operations...")
    try:
        # Create additional sample documents for batch testing
        additional_docs = []
        for i in range(5):
            sample_content = f"This is additional test document number {i+1} for batch processing validation."
            sample_embedding = embedder.generate_query_embedding(sample_content)
            
            additional_doc = {
                "content": sample_content,
                "metadata": {
                    "doc_type": "test_document",
                    "doc_number": i+1,
                    "batch_test": True
                },
                "embedding": sample_embedding.tolist(),
                "embedding_array": sample_embedding
            }
            additional_docs.append(additional_doc)
        
        # Add batch to storage
        batch_result = vector_store.add_documents(additional_docs, batch_size=3)
        print(f"   ✅ Batch operation completed")
        print(f"   📊 Batch Results:")
        for key, value in batch_result.items():
            print(f"      {key}: {value}")
        
    except Exception as e:
        print(f"   ❌ Batch operations failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 7: Storage statistics and monitoring
    print("7. Testing statistics and monitoring...")
    try:
        stats = vector_store.get_processing_stats()
        print(f"   📈 Processing Statistics:")
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"      {key}:")
                for sub_key, sub_value in value.items():
                    print(f"        {sub_key}: {sub_value}")
            else:
                print(f"      {key}: {value}")
        
    except Exception as e:
        print(f"   ❌ Statistics retrieval failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 8: Backup functionality
    print("8. Testing backup functionality...")
    try:
        backup_path = "./test_backup"
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)
        
        backup_result = vector_store.backup_collection(backup_path)
        print(f"   ✅ Backup completed successfully")
        print(f"   📊 Backup Results:")
        for key, value in backup_result.items():
            print(f"      {key}: {value}")
        
        # Verify backup exists
        if os.path.exists(backup_path):
            print(f"   ✅ Backup files verified at: {backup_path}")
        else:
            print(f"   ❌ Backup files not found")
        
    except Exception as e:
        print(f"   ❌ Backup functionality failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 9: Error handling and edge cases
    print("9. Testing error handling and edge cases...")
    
    # Test empty document list
    try:
        vector_store.add_documents([])
        print("   ❌ Should have failed for empty document list")
    except Exception as e:
        print(f"   ✅ Correctly handled empty documents: {type(e).__name__}")
    
    # Test invalid query embedding
    try:
        vector_store.similarity_search(np.array([]))
        print("   ❌ Should have failed for empty query embedding")
    except Exception as e:
        print(f"   ✅ Correctly handled empty query embedding: {type(e).__name__}")
    
    # Test non-existent document ID
    try:
        result = vector_store.get_document_by_id("non_existent_id")
        if result is None:
            print(f"   ✅ Correctly returned None for non-existent ID")
        else:
            print(f"   ❌ Should have returned None for non-existent ID")
    except Exception as e:
        print(f"   ⚠️ Non-existent ID test raised exception: {type(e).__name__}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 10: Persistence verification
    print("10. Testing persistence verification...")
    try:
        # Store original count
        original_count = vector_store.collection.count()
        
        # Create new vector store instance with same path
        vector_store2 = EnterpriseVectorStorage(
            storage_path=test_db_path,
            collection_name="test_smb_documents",
            distance_metric="cosine"
        )
        
        # Verify count matches
        persistent_count = vector_store2.collection.count()
        
        if persistent_count == original_count:
            print(f"   ✅ Persistence verified: {persistent_count} documents persisted")
        else:
            print(f"   ❌ Persistence issue: expected {original_count}, got {persistent_count}")
        
    except Exception as e:
        print(f"   ❌ Persistence verification failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Cleanup
    print("11. Cleanup test databases...")
    try:
        if os.path.exists(test_db_path):
            shutil.rmtree(test_db_path)
            print("   ✅ Test database cleaned up")
            
        if os.path.exists("./test_backup"):
            shutil.rmtree("./test_backup")
            print("   ✅ Test backup cleaned up")
            
    except Exception as e:
        print(f"   ⚠️ Cleanup warning: {e}")
    
    print("\n=== Vector Storage Validation Complete ===")

if __name__ == "__main__":
    test_vector_storage()