"""
Enterprise RAG System - Streamlit Interface

User-friendly web interface for querying business documents using the
enterprise RAG pipeline with local Llama 3.1 and ChromaDB.

Author: Enterprise RAG Pipeline
Usage: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import our enterprise query pipeline
from query import EnterpriseQueryPipeline, QueryPipelineError


# Page configuration
st.set_page_config(
    page_title="Enterprise RAG System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .source-card {
        background-color: #f8f9fa;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    .success-response {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-response {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_pipeline():
    """Initialize the RAG pipeline with caching for performance."""
    try:
        pipeline = EnterpriseQueryPipeline(
            collection_name="smb_documents",
            storage_path="./chroma_db",
            model_name="llama3.1:8b-instruct-q4_K_M",
            top_k_results=5,
            max_context_length=2000
        )
        pipeline.initialize_components()
        return pipeline, None
    except Exception as e:
        return None, str(e)


def display_header():
    """Display the main header and description."""
    st.markdown('<div class="main-header">🔍 Enterprise RAG System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Query your business documents with AI-powered semantic search</div>', unsafe_allow_html=True)
    
    # System status indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Status", "🟢 Online", delta="System Ready")
    with col2:
        st.metric("Model", "Llama 3.1 8B", delta="Local AI")
    with col3:
        st.metric("Documents", "14 chunks", delta="SMB Data")
    with col4:
        st.metric("Privacy", "100% Local", delta="No Cloud")


def display_sidebar():
    """Display sidebar with system information and controls."""
    st.sidebar.header("🛠️ System Controls")
    
    # Query parameters
    st.sidebar.subheader("Query Parameters")
    top_k = st.sidebar.slider("Number of sources to retrieve", 1, 10, 5)
    max_context = st.sidebar.slider("Max context length", 500, 4000, 2000)
    
    # System information
    st.sidebar.subheader("📊 System Information")
    st.sidebar.info("""
    **Technology Stack:**
    - **LLM:** Llama 3.1 8B (Ollama)
    - **Embeddings:** SentenceTransformers
    - **Vector DB:** ChromaDB
    - **Interface:** Streamlit
    
    **Features:**
    - 100% Local Processing
    - Source Attribution
    - Real-time Query Analysis
    - Enterprise Security
    """)
    
    # Example queries
    st.sidebar.subheader("💡 Example Queries")
    example_queries = [
        "Who won the most Stanley Cups?",
        "What technology updates are mentioned in the business documents?",
        "Based on the available data, which team has the best performance?",
        "What are the main points from the business memo?",
        "Show me information about client onboarding plans"
    ]
    
    for query in example_queries:
        if st.sidebar.button(f"📝 {query[:30]}...", key=f"example_{hash(query)}"):
            st.session_state.example_query = query
    
    return top_k, max_context


def format_response_display(result: Dict[str, Any]):
    """Format and display the query response."""
    if result.get('success'):
        # Success response
        st.markdown('<div class="success-response">', unsafe_allow_html=True)
        st.markdown("### 🤖 AI Response")
        st.write(result['response'])
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Performance metrics
        perf = result['performance']
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Time", f"{perf['total_time']}s")
        with col2:
            st.metric("Retrieval", f"{perf['retrieval_time']}s")
        with col3:
            st.metric("Generation", f"{perf['generation_time']}s")
        with col4:
            st.metric("Sources Found", len(result['sources']))
        
        # Sources section
        if result['sources']:
            st.markdown("### 📚 Sources & Citations")
            for i, source in enumerate(result['sources'], 1):
                with st.expander(f"📄 Source {i}: {source['filename']} (Confidence: {source['confidence_score']:.3f})"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write("**Content Preview:**")
                        st.write(source['content_preview'])
                    with col2:
                        st.write("**Metadata:**")
                        st.write(f"**File:** {source['filename']}")
                        st.write(f"**Chunk ID:** {source['chunk_id']}")
                        st.write(f"**Confidence:** {source['confidence_score']:.3f}")
                        st.write(f"**Distance:** {source['similarity_distance']:.3f}")
        
        # Context information
        with st.expander("🔍 Context Details"):
            st.write("**Context Used by AI:**")
            st.code(result['context_used'], language="text")
            
            retrieval_stats = result['retrieval_stats']
            st.write("**Retrieval Statistics:**")
            st.json(retrieval_stats)
    
    else:
        # Error response
        st.markdown('<div class="error-response">', unsafe_allow_html=True)
        st.markdown("### ❌ Error")
        st.error(f"Query failed: {result.get('error', 'Unknown error')}")
        st.markdown('</div>', unsafe_allow_html=True)


def display_query_history():
    """Display query history if available."""
    if 'query_history' in st.session_state and st.session_state.query_history:
        st.markdown("### 📜 Query History")
        
        # Create a DataFrame for better display
        history_data = []
        for entry in st.session_state.query_history[-5:]:  # Show last 5 queries
            history_data.append({
                "Time": entry['timestamp'][:19],  # Truncate timestamp
                "Query": entry['query'][:50] + "..." if len(entry['query']) > 50 else entry['query'],
                "Status": "✅ Success" if entry['success'] else "❌ Failed",
                "Response Time": f"{entry.get('performance', {}).get('total_time', 'N/A')}s"
            })
        
        if history_data:
            df = pd.DataFrame(history_data)
            st.dataframe(df, use_container_width=True)


def main():
    """Main application function."""
    # Initialize session state
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'example_query' not in st.session_state:
        st.session_state.example_query = ""
    
    # Display header
    display_header()
    
    # Display sidebar and get parameters
    top_k, max_context = display_sidebar()
    
    # Initialize pipeline
    with st.spinner("🔄 Initializing RAG Pipeline..."):
        pipeline, error = initialize_pipeline()
    
    if error:
        st.error(f"❌ Failed to initialize pipeline: {error}")
        st.stop()
    else:
        st.success("✅ Pipeline initialized successfully!")
    
    # Main query interface
    st.markdown("### 💬 Ask Your Question")
    
    # Check for example query
    default_query = st.session_state.example_query if st.session_state.example_query else ""
    if st.session_state.example_query:
        st.session_state.example_query = ""  # Clear after use
    
    # Query input
    query = st.text_area(
        "Enter your question about the business documents:",
        value=default_query,
        height=100,
        placeholder="e.g., Who won the most Stanley Cups? or What technology updates are mentioned?"
    )
    
    # Query button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍 Search Documents", type="primary", use_container_width=True):
            if query.strip():
                with st.spinner("🧠 Processing your query..."):
                    # Update pipeline parameters
                    pipeline.top_k_results = top_k
                    pipeline.max_context_length = max_context
                    
                    # Process query
                    start_time = time.time()
                    result = pipeline.process_query(query.strip())
                    processing_time = time.time() - start_time
                    
                    # Add to history
                    st.session_state.query_history.append(result)
                    
                    # Display results
                    format_response_display(result)
                    
                    # Show processing time
                    st.info(f"⏱️ Query processed in {processing_time:.2f} seconds")
            else:
                st.warning("⚠️ Please enter a question to search.")
    
    # Query history
    if st.session_state.query_history:
        st.markdown("---")
        display_query_history()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: 2rem;">
        <p>🔒 <strong>Enterprise RAG System</strong> - 100% Local Processing | No Data Leaves Your Machine</p>
        <p>Built with Llama 3.1, ChromaDB, and SentenceTransformers</p>
    </div>
    """, unsafe_allow_html=True)


# Advanced features sidebar
def display_advanced_sidebar():
    """Display advanced system monitoring and controls."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 Advanced Controls")
    
    # Clear history button
    if st.sidebar.button("🗑️ Clear Query History"):
        st.session_state.query_history = []
        st.experimental_rerun()
    
    # Export functionality
    if st.sidebar.button("📊 Export Query History"):
        if st.session_state.query_history:
            history_json = json.dumps(st.session_state.query_history, indent=2)
            st.sidebar.download_button(
                label="📥 Download JSON",
                data=history_json,
                file_name=f"rag_query_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # System statistics
    if st.sidebar.button("📊 Show System Stats"):
        if st.session_state.query_history:
            successful_queries = sum(1 for q in st.session_state.query_history if q.get('success'))
            total_queries = len(st.session_state.query_history)
            avg_response_time = sum(
                q.get('performance', {}).get('total_time', 0) 
                for q in st.session_state.query_history if q.get('success')
            ) / max(1, successful_queries)
            
            st.sidebar.metric("Success Rate", f"{(successful_queries/total_queries)*100:.1f}%")
            st.sidebar.metric("Avg Response Time", f"{avg_response_time:.2f}s")
            st.sidebar.metric("Total Queries", total_queries)


if __name__ == "__main__":
    # Add advanced sidebar features
    display_advanced_sidebar()
    
    # Run main application
    main()