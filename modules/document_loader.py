"""
Enterprise-Grade Document Loader Module

Handles all SMB document types with automatic file type detection and appropriate loader selection.
Follows production architecture principles: modular, swappable, and maintainable.

Author: Enterprise RAG Pipeline
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    UnstructuredPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader,
    TextLoader,
    CSVLoader, 
    UnstructuredEmailLoader
)


class DocumentLoaderError(Exception):
    """Custom exception for document loading errors"""
    pass


class EnterpriseDocumentLoader:
    """
    Production-grade document loader supporting all common SMB file formats.
    
    Supported formats:
    - PDF (.pdf): Reports, contracts, technical documents
    - Word (.docx): Policies, proposals, meeting minutes
    - PowerPoint (.pptx): Training materials, presentations  
    - Text (.txt): Memos, notes, plain documentation
    - CSV (.csv): Customer data, inventory, financial records
    - Email (.eml): Communications, decisions, project updates
    """
    
    # File type mapping to appropriate loaders
    LOADER_MAPPING = {
        '.pdf': UnstructuredPDFLoader,
        '.docx': UnstructuredWordDocumentLoader,
        '.pptx': UnstructuredPowerPointLoader,
        '.txt': TextLoader,
        '.csv': CSVLoader,
        '.eml': UnstructuredEmailLoader
    }
    
    def __init__(self):
        """Initialize the document loader with supported file types."""
        self.supported_extensions = set(self.LOADER_MAPPING.keys())
        
    def is_supported_file(self, file_path: str) -> bool:
        """Check if file type is supported."""
        extension = Path(file_path).suffix.lower()
        return extension in self.supported_extensions
        
    def get_file_type(self, file_path: str) -> str:
        """Get the file extension/type."""
        return Path(file_path).suffix.lower()
        
    def load_single_document(self, file_path: str) -> List[Document]:
        """
        Load a single document using the appropriate loader.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of LangChain Document objects
            
        Raises:
            DocumentLoaderError: If file type not supported or loading fails
        """
        if not os.path.exists(file_path):
            raise DocumentLoaderError(f"File not found: {file_path}")
            
        extension = self.get_file_type(file_path)
        
        if not self.is_supported_file(file_path):
            raise DocumentLoaderError(
                f"Unsupported file type: {extension}. "
                f"Supported types: {', '.join(self.supported_extensions)}"
            )
            
        loader_class = self.LOADER_MAPPING[extension]
        
        try:
            loader = loader_class(file_path)
            documents = loader.load()
            
            if not documents:
                raise DocumentLoaderError(f"No content loaded from {file_path}")
                
            # Add file type metadata
            for doc in documents:
                doc.metadata['file_type'] = extension
                doc.metadata['original_filename'] = Path(file_path).name
                
            return documents
            
        except Exception as e:
            raise DocumentLoaderError(f"Failed to load {file_path}: {str(e)}")
            
    def load_directory(self, directory_path: str) -> List[Document]:
        """
        Load all supported documents from a directory.
        
        Args:
            directory_path: Path to directory containing documents
            
        Returns:
            List of all loaded LangChain Document objects
        """
        if not os.path.exists(directory_path):
            raise DocumentLoaderError(f"Directory not found: {directory_path}")
            
        all_documents = []
        loaded_files = []
        skipped_files = []
        
        for file_path in Path(directory_path).iterdir():
            if file_path.is_file() and self.is_supported_file(str(file_path)):
                try:
                    documents = self.load_single_document(str(file_path))
                    all_documents.extend(documents)
                    loaded_files.append(str(file_path))
                except DocumentLoaderError as e:
                    skipped_files.append(f"{file_path}: {str(e)}")
                    
        print(f"Document loading summary:")
        print(f"  ✅ Successfully loaded: {len(loaded_files)} files")
        print(f"  ❌ Skipped/Failed: {len(skipped_files)} files")
        print(f"  📄 Total documents: {len(all_documents)}")
        
        if skipped_files:
            print(f"  Errors:")
            for error in skipped_files:
                print(f"    - {error}")
                
        return all_documents
        
    def get_document_summary(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Generate a summary of loaded documents for validation.
        
        Args:
            documents: List of loaded documents
            
        Returns:
            Dictionary with document statistics
        """
        if not documents:
            return {"total_documents": 0}
            
        file_types = {}
        total_chars = 0
        
        for doc in documents:
            file_type = doc.metadata.get('file_type', 'unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1
            total_chars += len(doc.page_content)
            
        return {
            "total_documents": len(documents),
            "file_types": file_types,
            "total_characters": total_chars,
            "average_doc_length": total_chars // len(documents) if documents else 0
        }