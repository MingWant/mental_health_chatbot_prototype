"""
Mental Health RAG Management API
Provides mental health knowledge base management functionality
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body, Form
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from pydantic import BaseModel

# Import mental health RAG service
try:
    from mental_health_rag_service import mental_health_rag_service
    RAG_ENABLED = True
except ImportError as e:
    print(f"⚠️ Mental health RAG service loading failed: {e}")
    RAG_ENABLED = False

router = APIRouter(prefix="/api/v1/mental-health-rag", tags=["Mental Health RAG Management"])

# Pydantic models for request/response
class ChunkingTestRequest(BaseModel):
    text: str
    chunking_strategy: str = "semantic"
    chunk_size: int = 200
    overlap: int = 30
    mode: str = "sentences"

@router.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy" if RAG_ENABLED else "unavailable",
        "rag_enabled": RAG_ENABLED,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    chunking_strategy: str = Form("semantic"),  # 'fixed_length' | 'semantic' | 'session' | 'hierarchical' | 'adaptive'
    chunk_size: int = Form(200),
    overlap: int = Form(30),
    mode: str = Form("sentences"),  # 'chars' | 'words' | 'sentences' | 'paragraphs'
    custom_keywords: Optional[str] = Form(None)  # JSON array string or comma-separated
):
    """Upload mental health document"""
    if not RAG_ENABLED:
        raise HTTPException(status_code=503, detail="Mental health RAG service unavailable")
    
    try:
        print(f"📥 RAG Upload Params -> chunking_strategy={chunking_strategy}, chunk_size={chunk_size}, overlap={overlap}, mode={mode}, custom_keywords={custom_keywords}")
        # Check file type
        allowed_extensions = {'.txt', '.pdf', '.docx', '.xlsx', '.md'}
        file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        
        if f'.{file_extension}' not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format: {file_extension}. Supported formats: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        file_content = await file.read()

        # Parse custom keywords
        user_keywords: Optional[List[str]] = None
        if custom_keywords:
            try:
                parsed = json.loads(custom_keywords)
                if isinstance(parsed, list):
                    user_keywords = [str(x).strip() for x in parsed if str(x).strip()]
                else:
                    user_keywords = [s.strip() for s in str(custom_keywords).split(',') if s.strip()]
            except Exception:
                user_keywords = [s.strip() for s in str(custom_keywords).split(',') if s.strip()]
        
        # Process document (with user parameters)
        # 嘗試使用增強分塊策略
        try:
            from enhanced_chunking_strategies import ChunkingStrategy
            from chunking_integration_example import EnhancedMentalHealthRAGService
            
            enhanced_rag = EnhancedMentalHealthRAGService()
            strategy_enum = ChunkingStrategy(chunking_strategy)
            
            result = await enhanced_rag.upload_and_process_document_enhanced(
                file_content,
                file.filename,
                chunking_strategy=strategy_enum,
                chunk_size=chunk_size,
                overlap=overlap,
                mode=mode,
                custom_keywords=user_keywords
            )
        except Exception as e:
            print(f"⚠️ Enhanced chunking failed: {e}")
            print(f"⚠️ Error type: {type(e).__name__}")
            print(f"⚠️ Falling back to basic chunking strategy")
            # 回退到原有方法
            try:
                result = await mental_health_rag_service.upload_and_process_document(
                    file_content,
                    file.filename,
                    chunk_size=chunk_size,
                    overlap=overlap,
                    mode=mode,
                    custom_keywords=user_keywords
                )
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                raise HTTPException(status_code=500, detail=f"Both enhanced and basic chunking failed: {str(e)}")
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Document uploaded successfully",
                    "data": result,
                    "used_params": {
                        "chunking_strategy": chunking_strategy,
                        "chunk_size": chunk_size,
                        "overlap": overlap,
                        "mode": mode,
                        "custom_keywords": user_keywords or []
                    }
                }
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")

@router.get("/search")
async def search_knowledge_base(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(5, description="Number of results to return"),
    category_filter: Optional[str] = Query(None, description="Category filter")
):
    """Search mental health knowledge base"""
    if not RAG_ENABLED:
        raise HTTPException(status_code=503, detail="Mental health RAG service unavailable")
    
    try:
        results = await mental_health_rag_service.search_knowledge_base(query, top_k, category_filter)
        
        return {
            "success": True,
            "query": query,
            "top_k": top_k,
            "category_filter": category_filter,
            "results_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/search-by-category")
async def search_by_category(
    category: str = Query(..., description="Search category"),
    top_k: int = Query(10, description="Number of results to return")
):
    """Search mental health documents by category"""
    if not RAG_ENABLED:
        raise HTTPException(status_code=503, detail="Mental health RAG service unavailable")
    
    try:
        results = await mental_health_rag_service.search_by_category(category, top_k)
        
        return {
            "success": True,
            "category": category,
            "top_k": top_k,
            "results_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Category search failed: {str(e)}")

@router.get("/documents")
async def get_all_documents():
    """Get all document list"""
    if not RAG_ENABLED:
        raise HTTPException(status_code=503, detail="Mental health RAG service unavailable")
    
    try:
        documents = await mental_health_rag_service.get_all_documents()
        
        return {
            "success": True,
            "documents_count": len(documents),
            "documents": documents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document list: {str(e)}")

@router.get("/documents/{doc_id}")
async def get_document_chunks(doc_id: str):
    """Get detailed document content"""
    if not RAG_ENABLED:
        raise HTTPException(status_code=503, detail="Mental health RAG service unavailable")
    
    try:
        chunks = await mental_health_rag_service.get_document_chunks(doc_id)
        
        return {
            "success": True,
            "doc_id": doc_id,
            "chunks_count": len(chunks),
            "chunks": chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document content: {str(e)}")

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete document"""
    if not RAG_ENABLED:
        raise HTTPException(status_code=503, detail="Mental health RAG service unavailable")
    
    try:
        success = await mental_health_rag_service.delete_document(doc_id)
        
        if success:
            return {
                "success": True,
                "message": f"Document {doc_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.get("/categories")
async def get_available_categories():
    """Get available document categories"""
    if not RAG_ENABLED:
        raise HTTPException(status_code=503, detail="Mental health RAG service unavailable")
    
    try:
        categories = await mental_health_rag_service.get_available_categories()
        
        return {
            "success": True,
            "categories_count": len(categories),
            "categories": categories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get category list: {str(e)}")

@router.post("/generate-response")
async def generate_mental_health_response(
    query: str = Query(..., description="User question"),
    context_chunks: List[dict] = Body(..., description="Context chunks")
):
    """Generate mental health response"""
    if not RAG_ENABLED:
        raise HTTPException(status_code=503, detail="Mental health RAG service unavailable")
    
    try:
        response = await mental_health_rag_service.generate_mental_health_response(query, context_chunks)
        
        return {
            "success": True,
            "query": query,
            "context_chunks_count": len(context_chunks),
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")

@router.get("/stats")
async def get_rag_stats():
    """Get RAG system statistics"""
    if not RAG_ENABLED:
        raise HTTPException(status_code=503, detail="Mental health RAG service unavailable")
    
    try:
        documents = await mental_health_rag_service.get_all_documents()
        categories = await mental_health_rag_service.get_available_categories()
        
        # Count documents by category
        category_stats = {}
        for doc in documents:
            for category in doc.get("categories", []):
                category_stats[category] = category_stats.get(category, 0) + 1
        
        total_chunks = sum(doc.get("total_chunks", 0) for doc in documents)
        
        return {
            "success": True,
            "stats": {
                "total_documents": len(documents),
                "total_chunks": total_chunks,
                "available_categories": len(categories),
                "category_distribution": category_stats,
                "categories": categories
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.post("/test-chunking")
async def test_chunking_strategy(request: ChunkingTestRequest):
    """Test chunking strategy with sample text"""
    if not RAG_ENABLED:
        raise HTTPException(status_code=503, detail="Mental health RAG service unavailable")
    
    try:
        # 嘗試使用增強分塊策略
        try:
            from enhanced_chunking_strategies import ChunkingStrategy, ChunkConfig, EnhancedChunkingStrategies
            
            chunking_strategies = EnhancedChunkingStrategies()
            strategy_enum = ChunkingStrategy(request.chunking_strategy)
            
            config = ChunkConfig(
                strategy=strategy_enum,
                chunk_size=request.chunk_size,
                overlap=request.overlap,
                mode=request.mode
            )
            
            chunks = chunking_strategies.chunk_text(request.text, config)
            
            # 準備結果
            result = {
                "input_text_length": len(request.text),
                "chunking_strategy": request.chunking_strategy,
                "chunk_count": len(chunks),
                "chunks": []
            }
            
            for i, chunk in enumerate(chunks):
                result["chunks"].append({
                    "id": chunk["id"],
                    "text": chunk["text"],
                    "length": chunk["length"],
                    "word_count": chunk["word_count"],
                    "chunk_type": chunk.get("chunk_type", "default"),
                    "start_index": chunk["start_index"],
                    "end_index": chunk["end_index"]
                })
            
            # 添加統計信息
            result["statistics"] = {
                "avg_chunk_length": sum(chunk["length"] for chunk in chunks) / len(chunks) if chunks else 0,
                "min_chunk_length": min(chunk["length"] for chunk in chunks) if chunks else 0,
                "max_chunk_length": max(chunk["length"] for chunk in chunks) if chunks else 0,
                "chunk_types": list(set(chunk.get("chunk_type", "default") for chunk in chunks))
            }
            
            return JSONResponse(content=result)
            
        except (ImportError, ValueError) as e:
            print(f"⚠️ Enhanced chunking not available, falling back to basic: {e}")
            # 回退到基本分塊測試
            return JSONResponse(content={
                "error": "Enhanced chunking not available",
                "fallback_message": "Please use the basic chunking strategy",
                "available_strategies": ["fixed_length"]
            })
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chunking test failed: {str(e)}")

@router.get("/chunking-strategies")
async def get_chunking_strategies():
    """Get available chunking strategies information (English)"""
    strategies_info = {
        "fixed_length": {
            "name": "Fixed-length chunking",
            "description": "Split by a fixed number of characters or words",
            "use_cases": ["Generic documents", "Structured text"],
            "pros": ["Simple and fast", "Predictable size"],
            "cons": ["May break semantic boundaries"]
        },
        "semantic": {
            "name": "Semantic chunking",
            "description": "Split by paragraph or sentence boundaries to preserve semantics",
            "use_cases": ["Articles", "Reports", "Academic papers"],
            "pros": ["Better retrieval quality", "Keeps meaning intact"],
            "cons": ["Uneven chunk sizes"]
        },
        "session": {
            "name": "Session chunking",
            "description": "Split by dialogue/meeting/session turns",
            "use_cases": ["Meeting notes", "Chat logs", "Interviews"],
            "pros": ["Keeps conversation context", "Easy to follow"],
            "cons": ["Requires session pattern detection"]
        },
        "hierarchical": {
            "name": "Hierarchical chunking",
            "description": "Split by headings/chapters/sections",
            "use_cases": ["Books", "Manuals", "Technical docs"],
            "pros": ["Preserves structure", "Good navigation"],
            "cons": ["Depends on heading quality"]
        },
        "adaptive": {
            "name": "Adaptive chunking",
            "description": "Choose the best strategy based on text features",
            "use_cases": ["Mixed-type documents", "Unknown formats"],
            "pros": ["Smart selection", "Flexible"],
            "cons": ["More complex"]
        }
    }

    return JSONResponse(content={
        "strategies": strategies_info,
        "recommendations": {
            "Mental health guides": "semantic",
            "Meeting transcripts": "session",
            "Technical manuals": "hierarchical",
            "Mixed documents": "adaptive",
            "Generic text": "fixed_length"
        }
    })
