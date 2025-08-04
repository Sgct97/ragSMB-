from langchain_community.document_loaders import UnstructuredPowerPointLoader

# The path to our test file
pptx_file_path = "data/fake-power-point.pptx"

print(f"--- Loading PowerPoint file: {pptx_file_path} ---")

# Create the loader
loader = UnstructuredPowerPointLoader(pptx_file_path)

# Load the documents
docs = loader.load()

# --- Validation ---
if not docs:
    print("!!! Test Failed: No documents were loaded.")
else:
    print(f"+++ Test Passed: Successfully loaded {len(docs)} document(s).")
    # Print the content of the first few elements to verify
    for i, doc in enumerate(docs[:2]): # Limit to first 2 elements for brevity
        print(f"\n--- Document {i+1} Content (first 200 chars) ---")
        print(doc.page_content[:200])
        print("\n--- Document Metadata ---")
        print(doc.metadata)

print("\n--- Test Complete ---") 