"""
Test script for the EnterpriseDocumentLoader module

This script validates the document loader can handle all SMB file types
and provides comprehensive error handling and metadata extraction.
"""

from modules.document_loader import EnterpriseDocumentLoader

def test_document_loader():
    """Test the document loader with all file types."""
    
    print("=== Enterprise Document Loader Validation ===\n")
    
    # Initialize the loader
    loader = EnterpriseDocumentLoader()
    
    # Test 1: Single file loading (PDF)
    print("1. Testing PDF single file loading...")
    try:
        pdf_docs = loader.load_single_document("data/sample-business-report.pdf")
        print(f"   ✅ PDF loaded: {len(pdf_docs)} document(s)")
        print(f"   📄 Content preview: {pdf_docs[0].page_content[:100]}...")
        print(f"   📊 Metadata: {pdf_docs[0].metadata}")
    except Exception as e:
        print(f"   ❌ PDF loading failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Directory loading (all files)
    print("2. Testing directory loading (all supported files)...")
    try:
        all_docs = loader.load_directory("data")
        print(f"   ✅ Directory loaded: {len(all_docs)} total document(s)")
        
        # Show summary by file type
        summary = loader.get_document_summary(all_docs)
        print(f"   📊 Document Summary:")
        for key, value in summary.items():
            print(f"      {key}: {value}")
            
    except Exception as e:
        print(f"   ❌ Directory loading failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Individual file type validation
    file_tests = [
        ("data/business-memo.txt", "Text file"),
        ("data/stanley-cups.csv", "CSV file"),
        ("data/fake-email.eml", "Email file"),
        ("data/fake.docx", "Word document"),
        ("data/fake-power-point.pptx", "PowerPoint"),
    ]
    
    print("3. Testing individual file types...")
    for file_path, description in file_tests:
        try:
            docs = loader.load_single_document(file_path)
            file_type = loader.get_file_type(file_path)
            print(f"   ✅ {description} ({file_type}): {len(docs)} document(s)")
            
            # Show first document preview
            if docs:
                content_preview = docs[0].page_content[:80].replace('\n', ' ')
                print(f"      Preview: {content_preview}...")
                
        except Exception as e:
            print(f"   ❌ {description} failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 4: Error handling
    print("4. Testing error handling...")
    
    # Test unsupported file type
    try:
        loader.load_single_document("nonexistent.xyz")
        print("   ❌ Should have failed for unsupported file type")
    except Exception as e:
        print(f"   ✅ Correctly handled unsupported file: {e}")
    
    # Test non-existent file
    try:
        loader.load_single_document("nonexistent.pdf")
        print("   ❌ Should have failed for non-existent file")
    except Exception as e:
        print(f"   ✅ Correctly handled missing file: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 5: File type detection
    print("5. Testing file type detection...")
    test_files = [
        "data/sample-business-report.pdf",
        "data/business-memo.txt",
        "data/stanley-cups.csv",
        "data/fake-email.eml",
        "data/fake.docx",
        "data/fake-power-point.pptx"
    ]
    
    for file_path in test_files:
        file_type = loader.get_file_type(file_path)
        is_supported = loader.is_supported_file(file_path)
        print(f"   📁 {file_path}: {file_type} (Supported: {is_supported})")
    
    print("\n=== Document Loader Validation Complete ===")

if __name__ == "__main__":
    test_document_loader()