"""
Test script for the EnterpriseTextChunker module

This script validates text chunking functionality with various document types
and ensures chunks meet quality standards for RAG applications.
"""

from modules.text_chunker import EnterpriseTextChunker
from modules.document_loader import EnterpriseDocumentLoader

def test_text_chunker():
    """Test the text chunker with various document types and scenarios."""
    
    print("=== Enterprise Text Chunker Validation ===\n")
    
    # Initialize chunker with production settings
    chunker = EnterpriseTextChunker(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    # Initialize document loader to get test documents
    loader = EnterpriseDocumentLoader()
    
    print(f"Chunker Configuration:")
    print(f"  Chunk Size: {chunker.chunk_size}")
    print(f"  Overlap: {chunker.chunk_overlap}")
    print(f"  Separators: {len(chunker.separators)} levels")
    print("\n" + "="*50 + "\n")
    
    # Test 1: Simple text chunking
    print("1. Testing raw text chunking...")
    sample_text = """
    This is a comprehensive business report about quarterly performance. 
    
    Our company has seen significant growth in the past quarter with revenue increasing by 15%.
    
    Key achievements include:
    - New product launches in three markets
    - Customer satisfaction scores improved by 8%
    - Operational efficiency gains of 12%
    
    Looking forward, we anticipate continued growth based on market trends and our strategic initiatives. 
    The next quarter will focus on expanding our digital capabilities and enhancing customer experience.
    
    Financial Performance:
    Total Revenue: $2.4M (up 15% from last quarter)
    Net Profit: $480K (up 18% from last quarter)
    Operating Expenses: $1.92M (down 3% from last quarter)
    
    Market Analysis:
    Our primary market shows strong demand for our core products. Competition remains fierce, 
    but our unique value proposition and customer service excellence continue to differentiate us.
    """
    
    try:
        text_chunks = chunker.chunk_text(sample_text, metadata={"source": "sample_report", "type": "business_report"})
        print(f"   ✅ Text chunked into {len(text_chunks)} chunks")
        
        # Show first chunk
        if text_chunks:
            first_chunk = text_chunks[0]
            print(f"   📄 First chunk ({len(first_chunk.page_content)} chars):")
            print(f"      {first_chunk.page_content[:150]}...")
            print(f"   📊 Metadata: {first_chunk.metadata}")
            
    except Exception as e:
        print(f"   ❌ Text chunking failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Document chunking with various file types
    print("2. Testing document chunking with multiple file types...")
    try:
        # Load various document types
        test_docs = []
        
        # Load business memo (should be chunked due to length)
        memo_docs = loader.load_single_document("data/business-memo.txt")
        test_docs.extend(memo_docs)
        
        # Load PDF document
        pdf_docs = loader.load_single_document("data/sample-business-report.pdf") 
        test_docs.extend(pdf_docs)
        
        print(f"   📁 Loaded {len(test_docs)} documents for chunking")
        
        # Chunk the documents
        all_chunks = chunker.chunk_documents(test_docs)
        print(f"   ✅ Created {len(all_chunks)} chunks from {len(test_docs)} documents")
        
        # Get comprehensive summary
        summary = chunker.get_chunk_summary(all_chunks)
        print(f"   📊 Chunk Summary:")
        for key, value in summary.items():
            if isinstance(value, dict):
                print(f"      {key}:")
                for sub_key, sub_value in value.items():
                    print(f"        {sub_key}: {sub_value}")
            else:
                print(f"      {key}: {value}")
                
    except Exception as e:
        print(f"   ❌ Document chunking failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Chunk validation
    print("3. Testing chunk validation...")
    try:
        validation_results = chunker.validate_chunks(all_chunks)
        print(f"   📋 Validation Results:")
        print(f"      Valid: {validation_results['is_valid']}")
        print(f"      Chunk Count: {validation_results['chunk_count']}")
        
        if validation_results['issues']:
            print(f"      Issues: {validation_results['issues']}")
        else:
            print(f"      Issues: None")
            
        if validation_results['warnings']:
            print(f"      Warnings: {validation_results['warnings']}")
        else:
            print(f"      Warnings: None")
            
    except Exception as e:
        print(f"   ❌ Validation failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 4: Edge cases and error handling
    print("4. Testing edge cases and error handling...")
    
    # Test empty text
    try:
        chunker.chunk_text("")
        print("   ❌ Should have failed for empty text")
    except Exception as e:
        print(f"   ✅ Correctly handled empty text: {type(e).__name__}")
    
    # Test empty document list
    try:
        chunker.chunk_documents([])
        print("   ❌ Should have failed for empty document list")
    except Exception as e:
        print(f"   ✅ Correctly handled empty documents: {type(e).__name__}")
    
    # Test very long text (should chunk appropriately)
    try:
        long_text = "This is a very long sentence. " * 100  # 3000+ characters
        long_chunks = chunker.chunk_text(long_text)
        print(f"   ✅ Long text chunked into {len(long_chunks)} chunks")
        print(f"      Largest chunk: {max(len(c.page_content) for c in long_chunks)} chars")
    except Exception as e:
        print(f"   ❌ Long text chunking failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 5: Processing statistics
    print("5. Testing processing statistics...")
    try:
        stats = chunker.get_processing_stats()
        print(f"   📈 Processing Statistics:")
        for key, value in stats.items():
            print(f"      {key}: {value}")
    except Exception as e:
        print(f"   ❌ Statistics retrieval failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 6: Custom chunking configuration
    print("6. Testing custom chunking configuration...")
    try:
        # Create chunker with smaller chunks for testing
        small_chunker = EnterpriseTextChunker(
            chunk_size=200,
            chunk_overlap=50
        )
        
        test_text = "This is a paragraph. This is another paragraph with more content to test chunking behavior."
        small_chunks = small_chunker.chunk_text(test_text)
        
        print(f"   ✅ Small chunker created {len(small_chunks)} chunks")
        print(f"   📏 Chunk sizes: {[len(c.page_content) for c in small_chunks]}")
        
    except Exception as e:
        print(f"   ❌ Custom chunking failed: {e}")
    
    print("\n=== Text Chunker Validation Complete ===")

if __name__ == "__main__":
    test_text_chunker()