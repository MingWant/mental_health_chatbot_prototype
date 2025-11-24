# RAG系統分塊策略指南

## 概述

本指南介紹了RAG（Retrieval-Augmented Generation）系統中除了固定長度分塊之外的多種智能分塊策略，特別針對心理健康文檔的處理需求。

## 分塊策略對比

### 1. 固定長度分塊 (Fixed Length Chunking)

**特點：**
- 按固定字符數或詞數分割文本
- 簡單快速，結果可預測
- 可能破壞語義完整性

**適用場景：**
- 一般文檔處理
- 結構化文本
- 需要統一分塊大小的場景

**示例：**
```python
config = ChunkConfig(
    strategy=ChunkingStrategy.FIXED_LENGTH,
    chunk_size=200,
    overlap=30,
    mode="chars"
)
```

### 2. 語義分塊 (Semantic Chunking)

**特點：**
- 按段落、句子邊界分割
- 保持語義完整性
- 提高檢索質量

**適用場景：**
- 文章、報告
- 學術論文
- 心理健康指南

**模式：**
- `paragraphs`: 按段落分塊
- `sentences`: 按句子分塊
- `hybrid`: 混合模式

**示例：**
```python
config = ChunkConfig(
    strategy=ChunkingStrategy.SEMANTIC,
    chunk_size=200,
    overlap=30,
    mode="sentences"
)
```

### 3. 會話分塊 (Session Chunking)

**特點：**
- 按對話、會議記錄等會話結構分割
- 保持會話完整性
- 便於理解上下文

**適用場景：**
- 會議記錄
- 聊天記錄
- 訪談記錄
- 心理諮詢記錄

**識別模式：**
- 時間戳格式：`14:30 - 發言內容`
- 發言人格式：`Speaker 1: 發言內容`
- 問答格式：`Q1: 問題內容`

**示例：**
```python
config = ChunkConfig(
    strategy=ChunkingStrategy.SESSION,
    chunk_size=300,
    overlap=50,
    mode="session"
)
```

### 4. 層次分塊 (Hierarchical Chunking)

**特點：**
- 按標題、章節等層次結構分割
- 保持文檔結構完整
- 便於導航和理解

**適用場景：**
- 書籍、手冊
- 技術文檔
- 心理健康指南
- 教學材料

**識別模式：**
- Markdown標題：`# 標題`
- 中文章節：`第一章 標題`
- 數字標題：`1.1 標題`
- 全大寫標題：`CHAPTER ONE`

**示例：**
```python
config = ChunkConfig(
    strategy=ChunkingStrategy.HIERARCHICAL,
    chunk_size=250,
    overlap=40,
    mode="hierarchical"
)
```

### 5. 自適應分塊 (Adaptive Chunking)

**特點：**
- 根據文本特徵自動選擇最佳分塊策略
- 智能適應不同文檔類型
- 綜合多種策略的優點

**適用場景：**
- 混合類型文檔
- 未知格式文檔
- 批量處理多樣化文檔

**決策邏輯：**
1. 檢測會話模式 → 使用會話分塊
2. 檢測層次結構 → 使用層次分塊
3. 段落較長 → 使用段落分塊
4. 其他情況 → 使用句子分塊

**示例：**
```python
config = ChunkConfig(
    strategy=ChunkingStrategy.ADAPTIVE,
    chunk_size=200,
    overlap=30,
    mode="adaptive"
)
```

## 使用建議

### 心理健康文檔分塊建議

| 文檔類型 | 推薦策略 | 理由 |
|---------|---------|------|
| 心理健康指南 | 層次分塊 | 保持章節結構完整 |
| 諮詢記錄 | 會話分塊 | 保持對話完整性 |
| 研究論文 | 語義分塊 | 保持段落邏輯 |
| 混合文檔 | 自適應分塊 | 自動選擇最佳策略 |
| 一般文檔 | 固定長度分塊 | 簡單快速 |

### 參數調優建議

**分塊大小 (chunk_size)：**
- 200-300字符：適合一般檢索
- 400-500字符：適合詳細分析
- 100-150字符：適合精確匹配

**重疊大小 (overlap)：**
- 10-20%：一般情況
- 30-40%：重要文檔
- 50%+：關鍵信息文檔

**分塊模式 (mode)：**
- `sentences`：保持句子完整性
- `paragraphs`：保持段落完整性
- `chars`：精確控制大小
- `words`：考慮詞邊界

## API使用示例

### 1. 上傳文檔並使用語義分塊

```bash
curl -X POST "http://localhost:8001/api/upload-document-enhanced" \
  -F "file=@mental_health_guide.pdf" \
  -F "chunking_strategy=semantic" \
  -F "chunk_size=250" \
  -F "overlap=40" \
  -F "mode=sentences"
```

### 2. 測試分塊策略

```bash
curl -X POST "http://localhost:8001/api/test-chunking" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "這是一段測試文本...",
    "chunking_strategy": "hierarchical",
    "chunk_size": 200,
    "overlap": 30,
    "mode": "hierarchical"
  }'
```

### 3. 搜索知識庫

```bash
curl "http://localhost:8001/api/search-enhanced?query=焦慮處理&top_k=5"
```

## 性能比較

| 策略 | 處理速度 | 檢索質量 | 語義完整性 | 適用性 |
|------|---------|---------|-----------|--------|
| 固定長度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| 語義分塊 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 會話分塊 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 層次分塊 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 自適應分塊 | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 最佳實踐

### 1. 文檔預處理
- 清理格式和特殊字符
- 識別文檔結構
- 提取關鍵信息

### 2. 策略選擇
- 根據文檔類型選擇策略
- 考慮檢索需求
- 平衡性能和質量

### 3. 參數調優
- 從默認參數開始
- 根據效果調整
- 記錄最佳配置

### 4. 質量評估
- 檢查分塊邊界
- 評估檢索效果
- 監控用戶反饋

## 故障排除

### 常見問題

**Q: 分塊後檢索效果不佳？**
A: 嘗試調整分塊大小或使用語義分塊策略

**Q: 處理速度太慢？**
A: 考慮使用固定長度分塊或減少重疊大小

**Q: 會話分塊無法識別模式？**
A: 檢查文檔格式，可能需要預處理或使用其他策略

**Q: 層次分塊破壞了結構？**
A: 檢查標題識別模式，可能需要自定義正則表達式

## 未來發展

### 計劃中的功能
- 多語言分塊支持
- 自定義分塊規則
- 分塊質量評估
- 動態參數調整

### 研究方向
- 基於深度學習的分塊
- 語義相似性分塊
- 多模態文檔分塊
- 實時分塊優化

## 結論

選擇合適的分塊策略對RAG系統的性能至關重要。對於心理健康文檔，建議：

1. **優先使用語義分塊**：保持內容的語義完整性
2. **考慮文檔結構**：根據文檔類型選擇策略
3. **持續優化**：根據使用效果調整參數
4. **監控質量**：定期評估分塊和檢索效果

通過合理使用這些分塊策略，可以顯著提升RAG系統在心理健康領域的應用效果。
