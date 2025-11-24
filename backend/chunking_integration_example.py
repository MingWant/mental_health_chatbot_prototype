"""
RAG系統分塊策略集成示例
展示如何將新的分塊策略整合到現有的心理健康RAG系統中
"""

import asyncio
import os
import uuid
import aiofiles
from datetime import datetime
from typing import List, Dict, Any, Optional
from enhanced_chunking_strategies import (
    EnhancedChunkingStrategies, 
    ChunkingStrategy, 
    ChunkConfig
)
from mental_health_rag_service import MentalHealthRAGService

class EnhancedMentalHealthRAGService(MentalHealthRAGService):
    """增強版心理健康RAG服務，支持多種分塊策略"""
    
    def __init__(self):
        super().__init__()
        self.chunking_strategies = EnhancedChunkingStrategies()
    
    async def upload_and_process_document_enhanced(
        self, 
        file_content: bytes, 
        filename: str, 
        *,
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
        chunk_size: int = 200,
        overlap: int = 30,
        mode: str = "sentences",
        custom_keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """使用增強分塊策略上傳和處理文檔"""
        
        # 生成唯一文檔ID
        doc_id = str(uuid.uuid4())
        
        # 保存文件
        file_path = os.path.join(self.upload_dir, f"{doc_id}_{filename}")
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        try:
            # 提取文本內容
            text_content = await self.doc_processor._extract_text(file_path, os.path.splitext(filename)[1].lower())

            # 結構友好的清理：保留換行與段落，以支援 hierarchical/session 分塊
            def _clean_text_preserve_structure(raw: str) -> str:
                # Normalize newlines
                raw = raw.replace('\r\n', '\n').replace('\r', '\n')
                # Collapse excessive spaces within lines but keep line breaks
                lines = [
                    ' '.join(line.strip().split()) for line in raw.split('\n')
                ]
                # Remove consecutive more than 2 empty lines
                normalized = []
                empty_run = 0
                for line in lines:
                    if line == '':
                        empty_run += 1
                        if empty_run <= 2:
                            normalized.append('')
                    else:
                        empty_run = 0
                        normalized.append(line)
                return '\n'.join(normalized).strip()

            cleaned_text = _clean_text_preserve_structure(text_content)
            
            # 分類內容
            categories = self.doc_processor._classify_content(cleaned_text, custom_keywords=custom_keywords)
            
            # 使用增強分塊策略
            config = ChunkConfig(
                strategy=chunking_strategy,
                chunk_size=chunk_size,
                overlap=overlap,
                mode=mode
            )
            
            chunks = self.chunking_strategies.chunk_text(cleaned_text, config)
            
            # 準備元數據
            metadata = {
                "filename": filename,
                "extension": os.path.splitext(filename)[1].lower(),
                "categories": categories,
                "doc_id": doc_id,
                "chunking_strategy": chunking_strategy.value,
                "chunking_strategy": chunking_strategy.value,
                "chunk_size": chunk_size,
                "overlap": overlap,
                "mode": mode
            }
            
            # 添加到向量數據庫
            success = await self.vector_db.add_document(
                doc_id=doc_id,
                chunks=chunks,
                metadata=metadata
            )
            
            if success:
                # 刪除臨時文件
                os.remove(file_path)
                
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "filename": filename,
                    "categories": categories,
                    "chunk_count": len(chunks),
                    "chunking_strategy": chunking_strategy.value,
                    "processed_at": datetime.now().isoformat(),
                    "message": f"文檔使用 {chunking_strategy.value} 策略成功處理",
                    "chunk_details": {
                        "avg_length": sum(chunk['length'] for chunk in chunks) / len(chunks) if chunks else 0,
                        "chunk_types": list(set(chunk.get('chunk_type', 'default') for chunk in chunks)),
                        "strategy_used": chunking_strategy.value
                    }
                }
            else:
                os.remove(file_path)
                return {
                    "success": False,
                    "message": "向量化處理失敗"
                }
                
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            return {
                "success": False,
                "message": f"文檔處理失敗: {str(e)}"
            }

async def demonstrate_chunking_comparison():
    """演示不同分塊策略的比較"""
    
    # 示例文本
    sample_text = """
# 學生心理健康指南

## 第一章：認識情緒

情緒是我們對外界刺激的自然反應。學會識別和管理情緒是心理健康的重要技能。

### 1.1 常見情緒類型

**焦慮情緒**：當面臨考試、演講或重要決策時，我們可能會感到焦慮。這是正常的反應。

**抑鬱情緒**：長時間感到悲傷、失去興趣或希望，可能是抑鬱的徵兆。

**憤怒情緒**：當事情不如預期時，我們可能會感到憤怒。學會表達憤怒而不傷害他人很重要。

## 第二章：壓力管理技巧

### 2.1 深呼吸練習

深呼吸是簡單有效的壓力管理技巧：
1. 找一個安靜的地方坐下
2. 閉上眼睛，專注於呼吸
3. 吸氣4秒，屏氣4秒，呼氣6秒
4. 重複5-10次

### 2.2 時間管理

良好的時間管理可以減少壓力：
- 制定每日計劃
- 優先處理重要任務
- 學會說"不"
- 給自己留出休息時間

## 第三章：尋求幫助

當自我調節無法解決問題時，尋求專業幫助是明智的選擇。

### 3.1 校園資源

大多數學校都提供心理健康服務：
- 心理諮詢中心
- 學生健康服務
- 同輩支持小組

### 3.2 何時尋求幫助

如果出現以下情況，建議尋求專業幫助：
- 情緒持續低落超過兩週
- 影響日常學習和生活
- 有自傷或傷害他人的想法
- 睡眠或飲食習慣發生重大變化
"""
    
    # 創建增強RAG服務
    enhanced_rag = EnhancedMentalHealthRAGService()
    
    # 測試不同分塊策略
    strategies_to_test = [
        (ChunkingStrategy.FIXED_LENGTH, "固定長度分塊"),
        (ChunkingStrategy.SEMANTIC, "語義分塊（句子）"),
        (ChunkingStrategy.HIERARCHICAL, "層次分塊"),
        (ChunkingStrategy.ADAPTIVE, "自適應分塊")
    ]
    
    print("=== RAG系統分塊策略比較演示 ===\n")
    
    for strategy, description in strategies_to_test:
        print(f"📋 {description}")
        print("-" * 50)
        
        # 創建分塊配置
        config = ChunkConfig(
            strategy=strategy,
            chunk_size=200,
            overlap=30,
            mode="sentences" if strategy == ChunkingStrategy.SEMANTIC else "chars"
        )
        
        # 執行分塊
        chunks = enhanced_rag.chunking_strategies.chunk_text(sample_text, config)
        
        # 顯示結果
        print(f"總分塊數: {len(chunks)}")
        print(f"平均分塊長度: {sum(chunk['length'] for chunk in chunks) / len(chunks):.1f} 字符")
        print(f"分塊類型: {list(set(chunk.get('chunk_type', 'default') for chunk in chunks))}")
        
        # 顯示前3個分塊的內容
        print("\n前3個分塊內容:")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n分塊 {i+1} ({chunk.get('chunk_type', 'default')}):")
            print(f"長度: {chunk['length']} 字符")
            print(f"內容: {chunk['text'][:100]}...")
        
        print("\n" + "="*60 + "\n")

async def demonstrate_session_chunking():
    """演示會話分塊的特殊用法"""
    
    # 模擬會話記錄
    session_text = """
會議記錄 - 心理健康研討會
時間: 2024-01-15 14:00-16:00

主持人: 大家好，歡迎參加今天的心理健康研討會。我們今天的主題是"學生壓力管理"。

Speaker 1: 我想分享一些關於考試焦慮的經驗。當我面臨重要考試時，我會感到非常緊張。

Speaker 2: 我也有類似的經歷。我發現深呼吸練習對我很有幫助。

主持人: 很好的分享。讓我們討論一些具體的應對策略。

Q1: 如何區分正常的考試緊張和需要專業幫助的焦慮？

Speaker 1: 我認為關鍵是看這種情緒是否影響了日常功能。如果無法正常學習或生活，就應該尋求幫助。

Speaker 2: 我同意。持續時間也很重要。如果焦慮持續超過兩週，建議尋求專業幫助。

主持人: 謝謝大家的分享。讓我們繼續討論其他話題。
"""
    
    print("=== 會話分塊演示 ===\n")
    
    enhanced_rag = EnhancedMentalHealthRAGService()
    
    config = ChunkConfig(
        strategy=ChunkingStrategy.SESSION,
        chunk_size=300,
        overlap=50,
        mode="session"
    )
    
    chunks = enhanced_rag.chunking_strategies.chunk_text(session_text, config)
    
    print(f"會話分塊結果: {len(chunks)} 個分塊")
    
    for i, chunk in enumerate(chunks):
        print(f"\n會話分塊 {i+1}:")
        print(f"類型: {chunk.get('chunk_type', 'unknown')}")
        print(f"長度: {chunk['length']} 字符")
        print(f"內容: {chunk['text'][:150]}...")

async def main():
    """主函數：運行所有演示"""
    print("🚀 開始RAG系統分塊策略演示...\n")
    
    # 比較不同分塊策略
    await demonstrate_chunking_comparison()
    
    # 演示會話分塊
    await demonstrate_session_chunking()
    
    print("✅ 演示完成！")

if __name__ == "__main__":
    asyncio.run(main())
