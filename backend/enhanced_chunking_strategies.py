"""
Enhanced Chunking Strategies for RAG System
提供多種智能分塊方式，包括語義分塊、會話分塊、層次分塊等
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import jieba
from dataclasses import dataclass
from enum import Enum

class ChunkingStrategy(Enum):
    """分塊策略枚舉"""
    FIXED_LENGTH = "fixed_length"  # 固定長度分塊
    SEMANTIC = "semantic"          # 語義分塊（段落、句子）
    SESSION = "session"            # 會話分塊
    HIERARCHICAL = "hierarchical"  # 層次分塊
    ADAPTIVE = "adaptive"          # 自適應分塊

@dataclass
class ChunkConfig:
    """分塊配置"""
    strategy: ChunkingStrategy
    chunk_size: int = 200
    overlap: int = 30
    mode: str = "chars"  # chars, words, sentences, paragraphs
    preserve_boundaries: bool = True  # 是否保持邊界
    min_chunk_size: int = 50  # 最小分塊大小
    max_chunk_size: int = 1000  # 最大分塊大小

class EnhancedChunkingStrategies:
    """增強分塊策略類"""
    
    def __init__(self):
        # 中文標點符號
        self.chinese_punctuation = r'[。！？；：，、]'
        # 英文標點符號
        self.english_punctuation = r'[.!?;:,]'
        # 段落分隔符
        self.paragraph_separators = r'\n\s*\n'
        # 標題標記
        self.title_patterns = [
            r'^#{1,6}\s+',  # Markdown標題
            r'^第[一二三四五六七八九十\d]+[章節]\s*',  # 中文章節
            r'^\d+\.\d*\s+',  # 數字標題
            r'^[A-Z][A-Z\s]+$',  # 全大寫標題
        ]
    
    def chunk_text(self, text: str, config: ChunkConfig) -> List[Dict[str, Any]]:
        """根據策略分塊文本"""
        if config.strategy == ChunkingStrategy.FIXED_LENGTH:
            return self._fixed_length_chunking(text, config)
        elif config.strategy == ChunkingStrategy.SEMANTIC:
            return self._semantic_chunking(text, config)
        elif config.strategy == ChunkingStrategy.SESSION:
            return self._session_chunking(text, config)
        elif config.strategy == ChunkingStrategy.HIERARCHICAL:
            return self._hierarchical_chunking(text, config)
        elif config.strategy == ChunkingStrategy.ADAPTIVE:
            return self._adaptive_chunking(text, config)
        else:
            raise ValueError(f"Unsupported chunking strategy: {config.strategy}")
    
    def _fixed_length_chunking(self, text: str, config: ChunkConfig) -> List[Dict[str, Any]]:
        """固定長度分塊（原有實現的改進版）"""
        if config.mode == 'words':
            units = list(jieba.cut(text))
        else:
            units = list(text)
        
        chunks = []
        current_chunk = []
        current_measure = 0
        
        for i, unit in enumerate(units):
            current_chunk.append(unit)
            if config.mode == 'words':
                current_measure += 1
            else:
                current_measure += len(unit)
            
            if current_measure >= config.chunk_size:
                chunk_text = ''.join(current_chunk)
                chunks.append(self._create_chunk_metadata(
                    chunk_text, len(chunks), i - len(current_chunk) + 1, i, config
                ))
                
                # 處理重疊
                if config.overlap > 0:
                    overlap_units = current_chunk[-config.overlap:] if len(current_chunk) > config.overlap else current_chunk
                else:
                    overlap_units = []
                current_chunk = overlap_units
                current_measure = len(overlap_units) if config.mode == 'words' else sum(len(u) for u in overlap_units)
        
        # 處理最後一個分塊
        if current_chunk:
            chunk_text = ''.join(current_chunk)
            chunks.append(self._create_chunk_metadata(
                chunk_text, len(chunks), len(units) - len(current_chunk), len(units) - 1, config
            ))
        
        return chunks
    
    def _semantic_chunking(self, text: str, config: ChunkConfig) -> List[Dict[str, Any]]:
        """語義分塊：按段落、句子邊界分割"""
        chunks = []
        
        if config.mode == "paragraphs":
            # 按段落分塊
            paragraphs = re.split(self.paragraph_separators, text.strip())
            current_chunk = ""
            chunk_id = 0
            start_pos = 0
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                # 檢查是否需要分割
                if len(current_chunk) + len(para) > config.chunk_size and current_chunk:
                    chunks.append(self._create_chunk_metadata(
                        current_chunk.strip(), chunk_id, start_pos, start_pos + len(current_chunk), config,
                        chunk_type="paragraph"
                    ))
                    chunk_id += 1
                    start_pos += len(current_chunk)
                    current_chunk = para
                else:
                    current_chunk += "\n\n" + para if current_chunk else para
            
            # 處理最後一個分塊
            if current_chunk:
                chunks.append(self._create_chunk_metadata(
                    current_chunk.strip(), chunk_id, start_pos, start_pos + len(current_chunk), config,
                    chunk_type="paragraph"
                ))
        
        elif config.mode == "sentences":
            # 按句子分塊
            sentences = self._split_into_sentences(text)
            current_chunk = ""
            chunk_id = 0
            start_pos = 0
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # 檢查是否需要分割
                if len(current_chunk) + len(sentence) > config.chunk_size and current_chunk:
                    chunks.append(self._create_chunk_metadata(
                        current_chunk.strip(), chunk_id, start_pos, start_pos + len(current_chunk), config,
                        chunk_type="sentence"
                    ))
                    chunk_id += 1
                    start_pos += len(current_chunk)
                    current_chunk = sentence
                else:
                    current_chunk += " " + sentence if current_chunk else sentence
            
            # 處理最後一個分塊
            if current_chunk:
                chunks.append(self._create_chunk_metadata(
                    current_chunk.strip(), chunk_id, start_pos, start_pos + len(current_chunk), config,
                    chunk_type="sentence"
                ))
        
        else:
            # 混合模式：優先保持句子邊界，必要時按字符分割
            return self._hybrid_semantic_chunking(text, config)
        
        return chunks
    
    def _session_chunking(self, text: str, config: ChunkConfig) -> List[Dict[str, Any]]:
        """會話分塊：按對話、會議記錄等分割"""
        chunks = []
        
        # 識別會話模式
        session_patterns = [
            r'(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(.+?)(?=\d{1,2}:\d{2}|$)',  # 時間戳格式
            r'(Speaker\s+\d+:|主持人|發言人|用戶|系統):\s*(.+?)(?=Speaker\s+\d+:|主持人|發言人|用戶|系統|$)',  # 發言人格式
            r'(Q\d*:|問題\d*:|Question\s*\d*:)\s*(.+?)(?=Q\d*:|問題\d*:|Question\s*\d*:|$)',  # 問答格式
        ]
        
        sessions = []
        for pattern in session_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                sessions.append({
                    'content': match.group(0).strip(),
                    'start': match.start(),
                    'end': match.end(),
                    'type': 'session'
                })
        
        if not sessions:
            # 如果沒有識別到會話模式，回退到語義分塊
            return self._semantic_chunking(text, config)
        
        # 按會話分塊
        chunk_id = 0
        for session in sessions:
            session_text = session['content']
            
            # 如果會話太長，進一步分割
            if len(session_text) > config.max_chunk_size:
                sub_chunks = self._semantic_chunking(session_text, config)
                for sub_chunk in sub_chunks:
                    sub_chunk['chunk_type'] = 'session_sub'
                    sub_chunk['session_id'] = chunk_id
                    chunks.append(sub_chunk)
            else:
                chunks.append(self._create_chunk_metadata(
                    session_text, chunk_id, session['start'], session['end'], config,
                    chunk_type="session"
                ))
            
            chunk_id += 1
        
        return chunks
    
    def _hierarchical_chunking(self, text: str, config: ChunkConfig) -> List[Dict[str, Any]]:
        """層次分塊：按標題、章節結構分割"""
        chunks = []
        
        # 識別標題和層次結構
        lines = text.split('\n')
        current_section = ""
        current_level = 0
        chunk_id = 0
        start_pos = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # 檢查是否為標題
            is_title = False
            title_level = 0
            
            for pattern in self.title_patterns:
                if re.match(pattern, line):
                    is_title = True
                    title_level = len(re.match(pattern, line).group(0).strip())
                    break
            
            if is_title:
                # 保存當前章節
                if current_section and len(current_section.strip()) > config.min_chunk_size:
                    chunks.append(self._create_chunk_metadata(
                        current_section.strip(), chunk_id, start_pos, start_pos + len(current_section), config,
                        chunk_type="section", level=current_level
                    ))
                    chunk_id += 1
                    start_pos += len(current_section)
                
                # 開始新章節
                current_section = line + "\n"
                current_level = title_level
            else:
                # 添加到當前章節
                current_section += line + "\n"
                
                # 檢查章節是否過長
                if len(current_section) > config.chunk_size:
                    chunks.append(self._create_chunk_metadata(
                        current_section.strip(), chunk_id, start_pos, start_pos + len(current_section), config,
                        chunk_type="section", level=current_level
                    ))
                    chunk_id += 1
                    start_pos += len(current_section)
                    current_section = ""
        
        # 處理最後一個章節
        if current_section and len(current_section.strip()) > config.min_chunk_size:
            chunks.append(self._create_chunk_metadata(
                current_section.strip(), chunk_id, start_pos, start_pos + len(current_section), config,
                chunk_type="section", level=current_level
            ))
        
        return chunks
    
    def _adaptive_chunking(self, text: str, config: ChunkConfig) -> List[Dict[str, Any]]:
        """自適應分塊：根據內容類型選擇最佳分塊策略"""
        # 分析文本特徵
        text_features = self._analyze_text_features(text)
        
        # 根據特徵選擇策略
        if text_features['has_sessions']:
            return self._session_chunking(text, config)
        elif text_features['has_hierarchy']:
            return self._hierarchical_chunking(text, config)
        elif text_features['avg_paragraph_length'] > config.chunk_size:
            return self._semantic_chunking(text, ChunkConfig(
                strategy=ChunkingStrategy.SEMANTIC,
                chunk_size=config.chunk_size,
                overlap=config.overlap,
                mode="paragraphs"
            ))
        else:
            return self._semantic_chunking(text, ChunkConfig(
                strategy=ChunkingStrategy.SEMANTIC,
                chunk_size=config.chunk_size,
                overlap=config.overlap,
                mode="sentences"
            ))
    
    def _hybrid_semantic_chunking(self, text: str, config: ChunkConfig) -> List[Dict[str, Any]]:
        """混合語義分塊：結合句子邊界和字符限制"""
        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = ""
        chunk_id = 0
        start_pos = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 檢查添加句子後是否超長
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(potential_chunk) > config.chunk_size and current_chunk:
                # 當前分塊已滿，保存並開始新分塊
                chunks.append(self._create_chunk_metadata(
                    current_chunk.strip(), chunk_id, start_pos, start_pos + len(current_chunk), config,
                    chunk_type="hybrid"
                ))
                chunk_id += 1
                start_pos += len(current_chunk)
                
                # 如果單個句子就超過限制，強制分割
                if len(sentence) > config.chunk_size:
                    sub_chunks = self._fixed_length_chunking(sentence, config)
                    for sub_chunk in sub_chunks:
                        sub_chunk['chunk_type'] = 'hybrid_sub'
                        sub_chunk['parent_sentence'] = sentence[:50] + "..."
                        chunks.append(sub_chunk)
                    current_chunk = ""
                else:
                    current_chunk = sentence
            else:
                current_chunk = potential_chunk
        
        # 處理最後一個分塊
        if current_chunk:
            chunks.append(self._create_chunk_metadata(
                current_chunk.strip(), chunk_id, start_pos, start_pos + len(current_chunk), config,
                chunk_type="hybrid"
            ))
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """將文本分割為句子"""
        # 結合中英文標點符號
        sentence_endings = r'[。！？.!?]'
        sentences = re.split(sentence_endings, text)
        
        # 重新組合句子和標點符號
        result = []
        parts = re.split(sentence_endings, text)
        separators = re.findall(sentence_endings, text)
        
        for i, part in enumerate(parts):
            if part.strip():
                if i < len(separators):
                    result.append(part.strip() + separators[i])
                else:
                    result.append(part.strip())
        
        return [s.strip() for s in result if s.strip()]
    
    def _analyze_text_features(self, text: str) -> Dict[str, Any]:
        """分析文本特徵"""
        features = {
            'has_sessions': False,
            'has_hierarchy': False,
            'avg_paragraph_length': 0,
            'sentence_count': 0,
            'paragraph_count': 0
        }
        
        # 檢查會話模式
        session_patterns = [
            r'\d{1,2}:\d{2}(?::\d{2})?\s*-\s*',
            r'(Speaker\s+\d+|主持人|發言人|用戶|系統):\s*',
            r'(Q\d*:|問題\d*:|Question\s*\d*:)\s*'
        ]
        
        for pattern in session_patterns:
            if re.search(pattern, text):
                features['has_sessions'] = True
                break
        
        # 檢查層次結構
        for pattern in self.title_patterns:
            if re.search(pattern, text, re.MULTILINE):
                features['has_hierarchy'] = True
                break
        
        # 統計段落和句子
        paragraphs = re.split(self.paragraph_separators, text.strip())
        features['paragraph_count'] = len([p for p in paragraphs if p.strip()])
        
        sentences = self._split_into_sentences(text)
        features['sentence_count'] = len(sentences)
        
        if features['paragraph_count'] > 0:
            features['avg_paragraph_length'] = sum(len(p) for p in paragraphs if p.strip()) / features['paragraph_count']
        
        return features
    
    def _create_chunk_metadata(self, text: str, chunk_id: int, start_index: int, end_index: int, 
                             config: ChunkConfig, chunk_type: str = "default", **extra_metadata) -> Dict[str, Any]:
        """創建分塊元數據"""
        metadata = {
            "id": chunk_id,
            "text": text,
            "length": len(text),
            "word_count": len(list(jieba.cut(text))),
            "start_index": start_index,
            "end_index": end_index,
            "chunk_type": chunk_type,
            "strategy": config.strategy.value,
            "created_at": datetime.now().isoformat()
        }
        
        # 添加額外元數據
        metadata.update(extra_metadata)
        
        return metadata

# 使用示例
def demonstrate_chunking_strategies():
    """演示不同分塊策略"""
    
    sample_text = """
# 心理健康指南

## 第一章：情緒管理

情緒管理是心理健康的重要組成部分。當我們感到焦慮時，可以嘗試深呼吸練習。

### 1.1 焦慮處理技巧

深呼吸練習：吸氣4秒，屏氣4秒，呼氣6秒。這個技巧可以幫助我們在緊張時刻保持冷靜。

## 第二章：壓力管理

現代生活中，壓力無處不在。學會管理壓力對我們的整體健康至關重要。

### 2.1 時間管理

制定合理的時間表，優先處理重要任務，避免拖延。
"""
    
    chunking_strategies = EnhancedChunkingStrategies()
    
    # 測試不同策略
    strategies = [
        ChunkingStrategy.FIXED_LENGTH,
        ChunkingStrategy.SEMANTIC,
        ChunkingStrategy.HIERARCHICAL,
        ChunkingStrategy.ADAPTIVE
    ]
    
    config = ChunkConfig(
        strategy=ChunkingStrategy.SEMANTIC,
        chunk_size=200,
        overlap=30,
        mode="sentences"
    )
    
    for strategy in strategies:
        config.strategy = strategy
        chunks = chunking_strategies.chunk_text(sample_text, config)
        
        print(f"\n=== {strategy.value.upper()} CHUNKING ===")
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i}: {chunk['text'][:100]}...")
            print(f"Type: {chunk.get('chunk_type', 'default')}, Length: {chunk['length']}")

if __name__ == "__main__":
    demonstrate_chunking_strategies()
