"""
增強版RAG API
提供多種分塊策略的API端點
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime
import json

from enhanced_chunking_strategies import ChunkingStrategy, ChunkConfig
from chunking_integration_example import EnhancedMentalHealthRAGService

app = FastAPI(title="Enhanced Mental Health RAG API", version="1.0.0")

# 初始化增強RAG服務
enhanced_rag_service = EnhancedMentalHealthRAGService()

@app.post("/api/upload-document-enhanced")
async def upload_document_enhanced(
    file: UploadFile = File(...),
    chunking_strategy: str = Query("semantic", description="分塊策略: fixed_length, semantic, session, hierarchical, adaptive"),
    chunk_size: int = Query(200, description="分塊大小"),
    overlap: int = Query(30, description="重疊大小"),
    mode: str = Query("sentences", description="分塊模式: chars, words, sentences, paragraphs"),
    custom_keywords: Optional[str] = Query(None, description="自定義關鍵詞，用逗號分隔")
):
    """
    使用增強分塊策略上傳文檔
    """
    try:
        # 驗證分塊策略
        try:
            strategy = ChunkingStrategy(chunking_strategy)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"無效的分塊策略: {chunking_strategy}. 可用策略: {[s.value for s in ChunkingStrategy]}"
            )
        
        # 解析自定義關鍵詞
        keywords = None
        if custom_keywords:
            keywords = [kw.strip() for kw in custom_keywords.split(',') if kw.strip()]
        
        # 讀取文件內容
        file_content = await file.read()
        
        # 處理文檔
        result = await enhanced_rag_service.upload_and_process_document_enhanced(
            file_content=file_content,
            filename=file.filename,
            chunking_strategy=strategy,
            chunk_size=chunk_size,
            overlap=overlap,
            mode=mode,
            custom_keywords=keywords
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文檔處理失敗: {str(e)}")

@app.get("/api/chunking-strategies")
async def get_chunking_strategies():
    """
    獲取可用的分塊策略信息
    """
    strategies_info = {
        "fixed_length": {
            "name": "固定長度分塊",
            "description": "按固定字符數或詞數分割文本",
            "適用場景": ["一般文檔", "結構化文本"],
            "優點": ["簡單快速", "可預測"],
            "缺點": ["可能破壞語義完整性"]
        },
        "semantic": {
            "name": "語義分塊",
            "description": "按段落、句子邊界分割，保持語義完整性",
            "適用場景": ["文章", "報告", "學術論文"],
            "優點": ["保持語義完整", "提高檢索質量"],
            "缺點": ["分塊大小不均勻"]
        },
        "session": {
            "name": "會話分塊",
            "description": "按對話、會議記錄等會話結構分割",
            "適用場景": ["會議記錄", "聊天記錄", "訪談記錄"],
            "優點": ["保持會話完整性", "便於理解上下文"],
            "缺點": ["需要識別會話模式"]
        },
        "hierarchical": {
            "name": "層次分塊",
            "description": "按標題、章節等層次結構分割",
            "適用場景": ["書籍", "手冊", "技術文檔"],
            "優點": ["保持結構完整", "便於導航"],
            "缺點": ["依賴文檔結構"]
        },
        "adaptive": {
            "name": "自適應分塊",
            "description": "根據文本特徵自動選擇最佳分塊策略",
            "適用場景": ["混合類型文檔", "未知格式"],
            "優點": ["智能選擇", "適應性強"],
            "缺點": ["複雜度較高"]
        }
    }
    
    return JSONResponse(content={
        "strategies": strategies_info,
        "recommendations": {
            "心理健康文檔": "semantic",
            "會議記錄": "session", 
            "技術手冊": "hierarchical",
            "混合文檔": "adaptive",
            "一般文檔": "fixed_length"
        }
    })

@app.post("/api/test-chunking")
async def test_chunking_strategy(
    text: str,
    chunking_strategy: str = Query("semantic"),
    chunk_size: int = Query(200),
    overlap: int = Query(30),
    mode: str = Query("sentences")
):
    """
    測試分塊策略，返回分塊結果
    """
    try:
        # 驗證分塊策略
        try:
            strategy = ChunkingStrategy(chunking_strategy)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"無效的分塊策略: {chunking_strategy}"
            )
        
        # 創建分塊配置
        config = ChunkConfig(
            strategy=strategy,
            chunk_size=chunk_size,
            overlap=overlap,
            mode=mode
        )
        
        # 執行分塊
        chunks = enhanced_rag_service.chunking_strategies.chunk_text(text, config)
        
        # 準備結果
        result = {
            "input_text_length": len(text),
            "chunking_strategy": chunking_strategy,
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分塊測試失敗: {str(e)}")

@app.get("/api/search-enhanced")
async def search_enhanced(
    query: str,
    top_k: int = Query(5, description="返回結果數量"),
    category_filter: Optional[str] = Query(None, description="類別過濾器")
):
    """
    使用增強RAG服務搜索知識庫
    """
    try:
        results = await enhanced_rag_service.search_knowledge_base(
            query=query,
            top_k=top_k,
            category_filter=category_filter
        )
        
        return JSONResponse(content={
            "query": query,
            "results_count": len(results),
            "results": results,
            "search_time": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失敗: {str(e)}")

@app.get("/api/documents")
async def get_documents():
    """
    獲取所有文檔信息
    """
    try:
        documents = await enhanced_rag_service.get_all_documents()
        return JSONResponse(content={
            "documents": documents,
            "total_count": len(documents)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取文檔失敗: {str(e)}")

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """
    刪除指定文檔
    """
    try:
        success = await enhanced_rag_service.delete_document(doc_id)
        if success:
            return JSONResponse(content={"message": "文檔刪除成功"})
        else:
            raise HTTPException(status_code=404, detail="文檔不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除文檔失敗: {str(e)}")

@app.get("/api/documents/{doc_id}/chunks")
async def get_document_chunks(doc_id: str):
    """
    獲取指定文檔的分塊信息
    """
    try:
        chunks = await enhanced_rag_service.get_document_chunks(doc_id)
        return JSONResponse(content={
            "doc_id": doc_id,
            "chunks": chunks,
            "chunk_count": len(chunks)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取分塊失敗: {str(e)}")

@app.get("/api/health")
async def health_check():
    """
    健康檢查端點
    """
    return JSONResponse(content={
        "status": "healthy",
        "service": "Enhanced Mental Health RAG API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
