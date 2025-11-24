"""
實際集成示例：將增強分塊策略整合到現有RAG系統
"""

import asyncio
import os
from typing import Dict, Any
from enhanced_chunking_strategies import ChunkingStrategy, ChunkConfig
from mental_health_rag_service import MentalHealthRAGService

class IntegratedMentalHealthRAG:
    """整合了增強分塊策略的心理健康RAG系統"""
    
    def __init__(self):
        self.rag_service = MentalHealthRAGService()
        self.chunking_strategies = None
        
        # 嘗試導入增強分塊策略
        try:
            from enhanced_chunking_strategies import EnhancedChunkingStrategies
            self.chunking_strategies = EnhancedChunkingStrategies()
            print("✅ 增強分塊策略已加載")
        except ImportError as e:
            print(f"⚠️ 增強分塊策略加載失敗: {e}")
            print("將使用原有的固定長度分塊")
    
    async def process_document_with_strategy(
        self, 
        file_path: str, 
        filename: str,
        strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
        **kwargs
    ) -> Dict[str, Any]:
        """使用指定策略處理文檔"""
        
        if not self.chunking_strategies:
            # 回退到原有方法
            return await self._fallback_processing(file_path, filename, **kwargs)
        
        try:
            # 讀取文件內容
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # 提取文本
            text_content = await self.rag_service.doc_processor._extract_text(
                file_path, os.path.splitext(filename)[1].lower()
            )
            cleaned_text = self.rag_service.doc_processor._clean_text(text_content)
            
            # 分類內容
            categories = self.rag_service.doc_processor._classify_content(
                cleaned_text, kwargs.get('custom_keywords')
            )
            
            # 使用增強分塊策略
            config = ChunkConfig(
                strategy=strategy,
                chunk_size=kwargs.get('chunk_size', 200),
                overlap=kwargs.get('overlap', 30),
                mode=kwargs.get('mode', 'sentences')
            )
            
            chunks = self.chunking_strategies.chunk_text(cleaned_text, config)
            
            return {
                "success": True,
                "filename": filename,
                "strategy_used": strategy.value,
                "categories": categories,
                "chunk_count": len(chunks),
                "chunks": chunks,
                "statistics": {
                    "avg_length": sum(chunk['length'] for chunk in chunks) / len(chunks) if chunks else 0,
                    "chunk_types": list(set(chunk.get('chunk_type', 'default') for chunk in chunks)),
                    "total_text_length": len(cleaned_text)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "strategy_attempted": strategy.value
            }
    
    async def _fallback_processing(self, file_path: str, filename: str, **kwargs) -> Dict[str, Any]:
        """回退到原有處理方法"""
        try:
            result = await self.rag_service.doc_processor.process_file(
                file_path, filename,
                chunk_size=kwargs.get('chunk_size', 200),
                overlap=kwargs.get('overlap', 30),
                mode=kwargs.get('mode', 'chars'),
                custom_keywords=kwargs.get('custom_keywords')
            )
            result["strategy_used"] = "fixed_length_fallback"
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "strategy_attempted": "fixed_length_fallback"
            }

async def demonstrate_integration():
    """演示整合效果"""
    
    print("🚀 開始RAG系統分塊策略整合演示...\n")
    
    # 創建整合RAG系統
    integrated_rag = IntegratedMentalHealthRAG()
    
    # 創建測試文檔
    test_content = """
# 學生心理健康指南

## 第一章：認識情緒

情緒是我們對外界刺激的自然反應。學會識別和管理情緒是心理健康的重要技能。

### 1.1 常見情緒類型

**焦慮情緒**：當面臨考試、演講或重要決策時，我們可能會感到焦慮。這是正常的反應，但如果持續時間過長或影響日常生活，就需要關注。

**抑鬱情緒**：長時間感到悲傷、失去興趣或希望，可能是抑鬱的徵兆。需要及時尋求專業幫助。

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
    
    # 保存測試文檔
    test_file_path = "backend/test_mental_health_guide.txt"
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("📄 測試文檔已創建")
    
    # 測試不同分塊策略
    strategies_to_test = [
        (ChunkingStrategy.FIXED_LENGTH, "固定長度分塊"),
        (ChunkingStrategy.SEMANTIC, "語義分塊"),
        (ChunkingStrategy.HIERARCHICAL, "層次分塊"),
        (ChunkingStrategy.ADAPTIVE, "自適應分塊")
    ]
    
    results = {}
    
    for strategy, description in strategies_to_test:
        print(f"\n🔍 測試 {description}...")
        
        result = await integrated_rag.process_document_with_strategy(
            test_file_path,
            "test_mental_health_guide.txt",
            strategy=strategy,
            chunk_size=200,
            overlap=30,
            mode="sentences" if strategy == ChunkingStrategy.SEMANTIC else "chars"
        )
        
        results[strategy.value] = result
        
        if result["success"]:
            print(f"✅ {description} 成功")
            print(f"   - 分塊數量: {result['chunk_count']}")
            print(f"   - 平均長度: {result['statistics']['avg_length']:.1f} 字符")
            print(f"   - 分塊類型: {result['statistics']['chunk_types']}")
            print(f"   - 識別類別: {', '.join(result['categories'][:3])}...")
        else:
            print(f"❌ {description} 失敗: {result.get('error', '未知錯誤')}")
    
    # 比較結果
    print("\n📊 分塊策略比較結果:")
    print("=" * 80)
    print(f"{'策略':<15} {'分塊數':<8} {'平均長度':<10} {'分塊類型':<20} {'狀態':<8}")
    print("-" * 80)
    
    for strategy_name, result in results.items():
        if result["success"]:
            chunk_types = ', '.join(result['statistics']['chunk_types'][:2])
            if len(result['statistics']['chunk_types']) > 2:
                chunk_types += "..."
            print(f"{strategy_name:<15} {result['chunk_count']:<8} "
                  f"{result['statistics']['avg_length']:<10.1f} "
                  f"{chunk_types:<20} {'✅':<8}")
        else:
            print(f"{strategy_name:<15} {'N/A':<8} {'N/A':<10} {'N/A':<20} {'❌':<8}")
    
    # 清理測試文件
    if os.path.exists(test_file_path):
        os.remove(test_file_path)
        print(f"\n🧹 測試文件已清理")
    
    print("\n🎉 整合演示完成！")
    
    return results

async def demonstrate_session_chunking():
    """演示會話分塊的特殊應用"""
    
    print("\n🎤 會話分塊演示:")
    print("=" * 50)
    
    # 模擬心理諮詢記錄
    session_text = """
心理諮詢記錄
日期: 2024-01-15
諮詢師: 張心理師
來訪者: 學生A

14:00 - 張心理師: 你好，今天感覺怎麼樣？

14:01 - 學生A: 我最近壓力很大，考試快到了，感覺很焦慮。

14:02 - 張心理師: 我理解你的感受。考試焦慮是很常見的。能具體說說你的焦慮表現嗎？

14:03 - 學生A: 主要是睡不好，注意力不集中，有時候會心慌。

14:04 - 張心理師: 這些都是焦慮的典型症狀。我們來討論一些應對策略。

Q1: 你平時有什麼放鬆的方法嗎？

14:05 - 學生A: 我喜歡聽音樂，但最近連音樂都聽不進去。

14:06 - 張心理師: 我們可以嘗試一些更主動的放鬆技巧，比如深呼吸練習。

14:07 - 學生A: 深呼吸？我試過，但感覺沒什麼用。

14:08 - 張心理師: 深呼吸需要正確的方法。讓我教你一個4-4-6呼吸法...

14:10 - 學生A: 這樣做嗎？(示範呼吸)

14:11 - 張心理師: 很好！記住要慢慢來，不要急。我們下次見面時再討論其他技巧。
"""
    
    integrated_rag = IntegratedMentalHealthRAG()
    
    # 保存會話文檔
    session_file_path = "backend/test_session.txt"
    with open(session_file_path, 'w', encoding='utf-8') as f:
        f.write(session_text)
    
    print("📝 會話文檔已創建")
    
    # 測試會話分塊
    result = await integrated_rag.process_document_with_strategy(
        session_file_path,
        "test_session.txt",
        strategy=ChunkingStrategy.SESSION,
        chunk_size=300,
        overlap=50
    )
    
    if result["success"]:
        print(f"✅ 會話分塊成功")
        print(f"   - 分塊數量: {result['chunk_count']}")
        print(f"   - 分塊類型: {result['statistics']['chunk_types']}")
        
        print("\n📋 會話分塊內容預覽:")
        for i, chunk in enumerate(result['chunks'][:3]):
            print(f"\n會話分塊 {i+1}:")
            print(f"類型: {chunk.get('chunk_type', 'unknown')}")
            print(f"內容: {chunk['text'][:100]}...")
    else:
        print(f"❌ 會話分塊失敗: {result.get('error', '未知錯誤')}")
    
    # 清理文件
    if os.path.exists(session_file_path):
        os.remove(session_file_path)
        print(f"\n🧹 會話測試文件已清理")

async def main():
    """主函數"""
    try:
        # 基本整合演示
        await demonstrate_integration()
        
        # 會話分塊演示
        await demonstrate_session_chunking()
        
        print("\n🎯 總結:")
        print("1. 語義分塊最適合心理健康文檔，保持內容完整性")
        print("2. 層次分塊適合結構化文檔，如指南和手冊")
        print("3. 會話分塊適合諮詢記錄和對話文檔")
        print("4. 自適應分塊可以智能選擇最佳策略")
        print("5. 固定長度分塊作為備用方案，簡單可靠")
        
    except Exception as e:
        print(f"❌ 演示過程中出現錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(main())
