"""
測試前端與後端RAG分塊策略集成
"""

import asyncio
import requests
import json
from typing import Dict, Any

class RAGIntegrationTester:
    """RAG系統集成測試器"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1/mental-health-rag"
    
    async def test_chunking_strategies_api(self) -> Dict[str, Any]:
        """測試分塊策略API"""
        print("🧪 測試分塊策略API...")
        
        try:
            # 測試獲取分塊策略信息
            response = requests.get(f"{self.api_url}/chunking-strategies")
            if response.status_code == 200:
                strategies = response.json()
                print(f"✅ 成功獲取 {len(strategies['strategies'])} 種分塊策略")
                return {"success": True, "strategies": strategies}
            else:
                print(f"❌ 獲取分塊策略失敗: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ 分塊策略API測試失敗: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_chunking_preview(self) -> Dict[str, Any]:
        """測試分塊預覽功能"""
        print("🧪 測試分塊預覽功能...")
        
        test_text = """
# 心理健康指南

## 第一章：情緒管理

情緒管理是心理健康的重要組成部分。當我們感到焦慮時，可以嘗試深呼吸練習。

### 1.1 焦慮處理技巧

深呼吸練習：吸氣4秒，屏氣4秒，呼氣6秒。這個技巧可以幫助我們在緊張時刻保持冷靜。

## 第二章：壓力管理

現代生活中，壓力無處不在。學會管理壓力對我們的整體健康至關重要。
"""
        
        strategies_to_test = ["semantic", "hierarchical", "adaptive"]
        results = {}
        
        for strategy in strategies_to_test:
            try:
                payload = {
                    "text": test_text,
                    "chunking_strategy": strategy,
                    "chunk_size": 200,
                    "overlap": 30,
                    "mode": "sentences"
                }
                
                response = requests.post(
                    f"{self.api_url}/test-chunking",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    results[strategy] = {
                        "success": True,
                        "chunk_count": result.get("chunk_count", 0),
                        "avg_length": result.get("statistics", {}).get("avg_chunk_length", 0),
                        "chunk_types": result.get("statistics", {}).get("chunk_types", [])
                    }
                    print(f"✅ {strategy} 策略測試成功: {result.get('chunk_count', 0)} 個分塊")
                else:
                    results[strategy] = {"success": False, "error": f"HTTP {response.status_code}"}
                    print(f"❌ {strategy} 策略測試失敗: {response.status_code}")
                    
            except Exception as e:
                results[strategy] = {"success": False, "error": str(e)}
                print(f"❌ {strategy} 策略測試異常: {e}")
        
        return {"success": True, "results": results}
    
    async def test_health_check(self) -> Dict[str, Any]:
        """測試健康檢查"""
        print("🧪 測試健康檢查...")
        
        try:
            response = requests.get(f"{self.api_url}/health")
            if response.status_code == 200:
                health = response.json()
                print(f"✅ 健康檢查通過: {health.get('status', 'unknown')}")
                return {"success": True, "health": health}
            else:
                print(f"❌ 健康檢查失敗: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ 健康檢查異常: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_document_upload_simulation(self) -> Dict[str, Any]:
        """模擬文檔上傳測試"""
        print("🧪 模擬文檔上傳測試...")
        
        # 創建測試文檔內容
        test_content = """
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
"""
        
        # 保存測試文檔
        test_file_path = "test_mental_health_guide.txt"
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        try:
            # 模擬上傳請求
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test_guide.txt', f, 'text/plain')}
                data = {
                    'chunking_strategy': 'semantic',
                    'chunk_size': '200',
                    'overlap': '30',
                    'mode': 'sentences',
                    'custom_keywords': '焦慮, 壓力, 情緒管理'
                }
                
                response = requests.post(f"{self.api_url}/upload", files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 文檔上傳測試成功")
                    print(f"   策略: {result.get('used_params', {}).get('chunking_strategy', 'unknown')}")
                    print(f"   分塊數: {result.get('data', {}).get('chunk_count', 0)}")
                    return {"success": True, "result": result}
                else:
                    print(f"❌ 文檔上傳測試失敗: {response.status_code}")
                    print(f"   響應: {response.text}")
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            print(f"❌ 文檔上傳測試異常: {e}")
            return {"success": False, "error": str(e)}
        finally:
            # 清理測試文件
            import os
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """運行所有測試"""
        print("🚀 開始RAG系統集成測試...\n")
        
        results = {}
        
        # 健康檢查
        results["health"] = await self.test_health_check()
        print()
        
        # 分塊策略API測試
        results["strategies"] = await self.test_chunking_strategies_api()
        print()
        
        # 分塊預覽測試
        results["preview"] = await self.test_chunking_preview()
        print()
        
        # 文檔上傳模擬測試
        results["upload"] = await self.test_document_upload_simulation()
        print()
        
        # 統計結果
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result.get("success", False))
        
        print("📊 測試結果統計:")
        print(f"   總測試數: {total_tests}")
        print(f"   通過測試: {passed_tests}")
        print(f"   失敗測試: {total_tests - passed_tests}")
        print(f"   成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 所有測試通過！RAG系統集成成功！")
        else:
            print(f"\n⚠️ 有 {total_tests - passed_tests} 個測試失敗，請檢查相關功能")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "results": results
        }

async def main():
    """主函數"""
    tester = RAGIntegrationTester()
    
    try:
        results = await tester.run_all_tests()
        
        # 保存測試結果
        with open("integration_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 測試結果已保存到 integration_test_results.json")
        
    except Exception as e:
        print(f"❌ 測試過程中出現錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(main())
