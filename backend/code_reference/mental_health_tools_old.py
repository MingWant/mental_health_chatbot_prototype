"""
心理健康自我關懷工具集
專門為學生提供心理健康支持和自我關懷策略
"""

import json
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re

class MentalHealthTools:
    """心理健康工具類"""
    
    def __init__(self):
        self.emotion_keywords = {
            "焦慮": ["焦慮", "緊張", "擔心", "不安", "恐懼", "panic", "anxiety"],
            "抑鬱": ["抑鬱", "憂鬱", "悲傷", "沮喪", "絕望", "depression", "sad"],
            "憤怒": ["憤怒", "生氣", "惱火", "煩躁", "angry", "mad", "irritated"],
            "壓力": ["壓力", "疲勞", "累", "stress", "tired", "exhausted"],
            "孤獨": ["孤獨", "寂寞", "孤立", "lonely", "isolated"],
            "快樂": ["快樂", "開心", "興奮", "happy", "joy", "excited"],
            "平靜": ["平靜", "放鬆", "安寧", "calm", "relaxed", "peaceful"]
        }
        
        self.coping_strategies = {
            "焦慮": [
                "深呼吸練習：慢慢吸氣4秒，屏住呼吸4秒，慢慢呼氣6秒",
                "5-4-3-2-1感官練習：找出5個你能看到的東西，4個能聽到的，3個能觸摸到的，2個能聞到的，1個能嘗到的",
                "漸進性肌肉放鬆：從腳趾開始，依次放鬆身體各部位",
                "寫下擔憂：把擔憂寫在紙上，然後問自己這些擔憂有多少是真的會發生"
            ],
            "抑鬱": [
                "建立日常規律：保持規律的作息時間",
                "小目標設定：每天設定一個小目標並完成它",
                "身體活動：即使是短暫的散步也能改善心情",
                "與人聯繫：與朋友或家人保持聯繫",
                "感恩練習：每天寫下3件感恩的事情"
            ],
            "憤怒": [
                "暫停反應：在回應前先數到10",
                "深呼吸：做幾次深呼吸來冷靜下來",
                "表達感受：用'我感覺...'的方式表達，而不是指責",
                "身體活動：運動是釋放憤怒的好方法",
                "寫下感受：把憤怒寫下來，然後撕掉"
            ],
            "壓力": [
                "時間管理：列出待辦事項，按重要性排序",
                "學會說不：不要承擔超出能力範圍的任務",
                "休息時間：每工作50分鐘休息10分鐘",
                "放鬆技巧：冥想、瑜伽或聽音樂",
                "尋求支持：與朋友、家人或輔導員談話"
            ],
            "孤獨": [
                "加入社團：參加學校的社團活動",
                "志願服務：幫助他人能帶來滿足感",
                "學習新技能：參加興趣班或工作坊",
                "線上社群：加入線上興趣小組",
                "寵物陪伴：考慮養寵物"
            ]
        }
        
        self.meditation_guides = {
            "初學者": {
                "呼吸冥想": {
                    "duration": "5-10分鐘",
                    "steps": [
                        "找一個安靜的地方坐下",
                        "閉上眼睛，專注於呼吸",
                        "數呼吸：吸氣時數1，呼氣時數2，直到10後重新開始",
                        "當思緒飄走時，溫柔地回到呼吸上"
                    ]
                },
                "身體掃描": {
                    "duration": "10-15分鐘",
                    "steps": [
                        "平躺或坐著，閉上眼睛",
                        "從腳趾開始，依次關注身體各部位",
                        "感受每個部位的感覺，不判斷好壞",
                        "放鬆緊張的部位"
                    ]
                }
            },
            "進階": {
                "愛心冥想": {
                    "duration": "15-20分鐘",
                    "steps": [
                        "閉上眼睛，想像溫暖的光",
                        "先對自己說：願我快樂，願我健康，願我平安",
                        "然後對親人說同樣的話",
                        "最後對所有人說：願所有人快樂，願所有人健康，願所有人平安"
                    ]
                },
                "正念行走": {
                    "duration": "20-30分鐘",
                    "steps": [
                        "選擇一個安靜的地方走路",
                        "專注於腳步的感覺",
                        "感受身體的移動",
                        "觀察周圍的環境，但不判斷"
                    ]
                }
            }
        }
        
        self.sleep_hygiene = [
            "保持規律的睡眠時間",
            "睡前1小時避免使用電子設備",
            "創造舒適的睡眠環境：安靜、黑暗、涼爽",
            "睡前避免咖啡因和酒精",
            "建立睡前儀式：讀書、聽音樂、泡澡",
            "如果20分鐘內無法入睡，起床做其他事情",
            "避免在床上做與睡眠無關的事情"
        ]
        
        self.study_wellness_tips = [
            "番茄工作法：25分鐘專注學習，5分鐘休息",
            "定期休息：每小時休息10分鐘",
            "保持水分：多喝水，避免過多咖啡因",
            "適當運動：學習間隙做些伸展運動",
            "營養均衡：保持健康的飲食習慣",
            "社交平衡：學習之餘也要與朋友交流",
            "尋求幫助：遇到困難時不要猶豫尋求幫助"
        ]

# 創建全局實例
mental_health_tools = MentalHealthTools()

async def assess_emotion_state(user_message: str) -> Dict[str, Any]:
    """
    評估用戶的情緒狀態
    """
    try:
        # 分析用戶消息中的情緒關鍵詞
        detected_emotions = []
        emotion_scores = {}
        
        for emotion, keywords in mental_health_tools.emotion_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in user_message.lower():
                    score += 1
            
            if score > 0:
                detected_emotions.append(emotion)
                emotion_scores[emotion] = score
        
        # 確定主要情緒
        primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0] if emotion_scores else "平靜"
        
        # 評估情緒強度
        total_score = sum(emotion_scores.values())
        if total_score >= 3:
            intensity = "高"
        elif total_score >= 1:
            intensity = "中"
        else:
            intensity = "低"
        
        return {
            "detected_emotions": detected_emotions,
            "primary_emotion": primary_emotion,
            "emotion_scores": emotion_scores,
            "intensity": intensity,
            "assessment_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"情緒評估失敗: {str(e)}",
            "primary_emotion": "未知",
            "intensity": "未知"
        }

async def get_coping_strategies(emotion: str, intensity: str = "中") -> Dict[str, Any]:
    """
    獲取針對特定情緒的應對策略
    """
    try:
        strategies = mental_health_tools.coping_strategies.get(emotion, [])
        
        # 根據強度調整建議
        if intensity == "高":
            priority_strategies = strategies[:2]  # 只提供前2個最有效的策略
            additional_note = "建議同時尋求專業心理健康支持"
        elif intensity == "中":
            priority_strategies = strategies[:3]  # 提供前3個策略
            additional_note = "這些策略可以幫助你緩解當前的情緒"
        else:
            priority_strategies = strategies[:4]  # 提供更多策略選擇
            additional_note = "這些策略可以幫助你保持心理健康"
        
        return {
            "emotion": emotion,
            "intensity": intensity,
            "strategies": priority_strategies,
            "additional_note": additional_note,
            "all_strategies": strategies,
            "generated_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"獲取應對策略失敗: {str(e)}",
            "strategies": ["深呼吸練習", "與朋友聊天", "聽音樂放鬆"],
            "additional_note": "如果情緒持續困擾，建議尋求專業幫助"
        }

async def get_meditation_guide(level: str = "初學者", type: str = "呼吸冥想") -> Dict[str, Any]:
    """
    獲取冥想指導
    """
    try:
        level_guides = mental_health_tools.meditation_guides.get(level, {})
        guide = level_guides.get(type, level_guides.get("呼吸冥想"))
        
        if not guide:
            return {
                "error": f"未找到{level}級別的{type}冥想指導",
                "available_types": list(level_guides.keys())
            }
        
        return {
            "level": level,
            "type": type,
            "duration": guide["duration"],
            "steps": guide["steps"],
            "tips": [
                "不要擔心做得完美，冥想是練習的過程",
                "如果思緒飄走，溫柔地回到練習上",
                "每天堅持練習，效果會逐漸顯現",
                "可以根據自己的情況調整練習時間"
            ],
            "generated_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"獲取冥想指導失敗: {str(e)}",
            "type": "呼吸冥想",
            "duration": "5-10分鐘",
            "steps": ["找個安靜地方坐下", "閉上眼睛", "專注於呼吸", "當思緒飄走時回到呼吸上"]
        }

async def get_sleep_advice() -> Dict[str, Any]:
    """
    獲取睡眠建議
    """
    try:
        return {
            "sleep_hygiene": mental_health_tools.sleep_hygiene,
            "additional_tips": [
                "建立固定的睡眠時間表",
                "避免在床上使用手機或電腦",
                "睡前可以聽輕音樂或白噪音",
                "如果失眠持續，考慮諮詢專業人士"
            ],
            "sleep_myths": [
                "睡前喝酒有助睡眠 - 事實：酒精會干擾睡眠質量",
                "週末補覺可以彌補平時的睡眠不足 - 事實：規律作息更重要",
                "躺在床上就能睡著 - 事實：需要放鬆身心"
            ],
            "generated_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"獲取睡眠建議失敗: {str(e)}",
            "sleep_hygiene": ["保持規律作息", "避免睡前使用電子設備", "創造舒適睡眠環境"]
        }

async def get_study_wellness_tips() -> Dict[str, Any]:
    """
    獲取學習健康建議
    """
    try:
        return {
            "study_tips": mental_health_tools.study_wellness_tips,
            "stress_management": [
                "設定合理的學習目標",
                "學會時間管理",
                "保持學習與休息的平衡",
                "不要害怕尋求幫助"
            ],
            "motivation_boosters": [
                "慶祝小成就",
                "與同學組成學習小組",
                "設定獎勵機制",
                "記住學習的意義和目標"
            ],
            "generated_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"獲取學習健康建議失敗: {str(e)}",
            "study_tips": ["保持規律作息", "適當休息", "尋求幫助"]
        }

async def create_self_care_plan(user_preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    創建個性化的自我關懷計劃
    """
    try:
        plan = {
            "daily_routine": [],
            "weekly_activities": [],
            "emergency_coping": [],
            "progress_tracking": [],
            "created_time": datetime.now().isoformat()
        }
        
        # 根據用戶偏好創建日常計劃
        if user_preferences.get("meditation", False):
            plan["daily_routine"].append({
                "activity": "冥想練習",
                "duration": "10-15分鐘",
                "time": "早晨或睡前",
                "description": "幫助放鬆心情，提高專注力"
            })
        
        if user_preferences.get("exercise", False):
            plan["daily_routine"].append({
                "activity": "運動",
                "duration": "30分鐘",
                "time": "下午或傍晚",
                "description": "釋放壓力，改善心情"
            })
        
        if user_preferences.get("journaling", False):
            plan["daily_routine"].append({
                "activity": "寫日記",
                "duration": "10-15分鐘",
                "time": "晚上",
                "description": "記錄感受，反思一天"
            })
        
        # 每週活動
        plan["weekly_activities"] = [
            {
                "activity": "與朋友聚會",
                "frequency": "每週1-2次",
                "description": "保持社交聯繫"
            },
            {
                "activity": "戶外活動",
                "frequency": "每週1次",
                "description": "接觸自然，放鬆身心"
            },
            {
                "activity": "學習新技能",
                "frequency": "每週1次",
                "description": "保持學習熱情"
            }
        ]
        
        # 緊急應對策略
        plan["emergency_coping"] = [
            "深呼吸練習",
            "打電話給朋友或家人",
            "聽喜歡的音樂",
            "出去散步",
            "寫下感受"
        ]
        
        # 進度追蹤
        plan["progress_tracking"] = [
            "每天記錄心情（1-10分）",
            "記錄完成的自我關懷活動",
            "每週回顧和調整計劃",
            "慶祝進步和成就"
        ]
        
        return plan
    except Exception as e:
        return {
            "error": f"創建自我關懷計劃失敗: {str(e)}",
            "daily_routine": [{"activity": "深呼吸練習", "duration": "5分鐘", "time": "任何時候"}],
            "emergency_coping": ["深呼吸", "打電話給朋友", "出去散步"]
        }

async def check_mental_health_resources() -> Dict[str, Any]:
    """
    檢查心理健康資源
    """
    try:
        return {
            "campus_resources": [
                {
                    "name": "學校心理諮詢中心",
                    "description": "提供免費的心理諮詢服務",
                    "contact": "請查詢學校官網或學生事務處",
                    "availability": "工作日 9:00-17:00"
                },
                {
                    "name": "學生健康服務",
                    "description": "提供身心健康相關服務",
                    "contact": "請查詢學校官網",
                    "availability": "工作日 8:00-18:00"
                }
            ],
            "online_resources": [
                {
                    "name": "心理健康熱線",
                    "description": "24小時心理健康支持熱線",
                    "contact": "請查詢當地心理健康熱線",
                    "availability": "24/7"
                },
                {
                    "name": "線上心理諮詢平台",
                    "description": "提供線上心理諮詢服務",
                    "contact": "請查詢可靠的線上平台",
                    "availability": "預約制"
                }
            ],
            "self_help_resources": [
                {
                    "name": "正念冥想APP",
                    "description": "提供冥想和放鬆練習",
                    "examples": ["Headspace", "Calm", "Insight Timer"]
                },
                {
                    "name": "心理健康書籍",
                    "description": "推薦的心理健康相關書籍",
                    "examples": ["《正念的奇蹟》", "《情緒的智慧》", "《自我關懷的力量》"]
                }
            ],
            "emergency_contacts": [
                {
                    "name": "緊急心理熱線",
                    "description": "24小時緊急心理支持",
                    "contact": "請查詢當地緊急心理熱線"
                },
                {
                    "name": "自殺預防熱線",
                    "description": "自殺預防和危機干預",
                    "contact": "請查詢當地自殺預防熱線"
                }
            ],
            "generated_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"獲取心理健康資源失敗: {str(e)}",
            "campus_resources": ["請聯繫學校心理諮詢中心"],
            "emergency_contacts": ["請查詢當地心理健康熱線"]
        }

async def generate_mood_tracker() -> Dict[str, Any]:
    """
    生成心情追蹤器
    """
    try:
        return {
            "tracking_template": {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "mood_scale": "1-10 (1=非常糟糕, 10=非常棒)",
                "energy_level": "1-10 (1=非常疲勞, 10=精力充沛)",
                "sleep_quality": "1-10 (1=很差, 10=很好)",
                "stress_level": "1-10 (1=無壓力, 10=極度壓力)",
                "activities": "今天做了什麼",
                "gratitude": "今天感恩的事情",
                "challenges": "遇到的挑戰",
                "coping_strategies": "使用的應對策略"
            },
            "weekly_summary": {
                "average_mood": "計算一週平均心情",
                "mood_trend": "心情變化趨勢",
                "most_helpful_activities": "最有幫助的活動",
                "areas_for_improvement": "需要改善的方面"
            },
            "tips": [
                "每天固定時間記錄心情",
                "不要判斷自己的感受，只是觀察",
                "定期回顧和總結",
                "與信任的人分享你的觀察"
            ],
            "generated_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"生成心情追蹤器失敗: {str(e)}",
            "tracking_template": {"date": "", "mood": "1-10", "notes": ""}
        }

# 便捷函數
async def analyze_user_mental_state(user_message: str) -> str:
    """
    分析用戶心理健康狀態並提供建議
    """
    try:
        # 評估情緒狀態
        emotion_assessment = await assess_emotion_state(user_message)
        
        # 獲取應對策略
        coping_strategies = await get_coping_strategies(
            emotion_assessment["primary_emotion"], 
            emotion_assessment["intensity"]
        )
        
        # 構建回應
        response = f"""
🧠 **心理健康狀態分析**

📊 **情緒評估：**
- 主要情緒：{emotion_assessment['primary_emotion']}
- 情緒強度：{emotion_assessment['intensity']}
- 檢測到的情緒：{', '.join(emotion_assessment['detected_emotions']) if emotion_assessment['detected_emotions'] else '平靜'}

💡 **建議的應對策略：**
"""
        
        for i, strategy in enumerate(coping_strategies["strategies"], 1):
            response += f"{i}. {strategy}\n"
        
        response += f"""
📝 **額外建議：**
{coping_strategies['additional_note']}

🌱 **自我關懷提醒：**
- 你的感受是正常的，每個人都有情緒起伏
- 給自己一些時間和空間來處理這些感受
- 如果需要，不要猶豫尋求專業幫助
"""
        
        return response
        
    except Exception as e:
        return f"分析過程中出現錯誤：{str(e)}"

async def query_mental_health_knowledge_base(query: str) -> str:
    """
    從心理健康知識庫（RAG）檢索相關內容，返回專業建議。
    """
    try:
        # 動態導入心理健康RAG服務
        from mental_health_rag_service import mental_health_rag_service
        print(f"🔍 正在搜索心理健康知識庫: {query}")
        
        # 搜索相關文檔
        search_results = await mental_health_rag_service.search_knowledge_base(query, top_k=5)
        print(f"📊 搜索到 {len(search_results)} 個結果")
        
        if not search_results:
            return """📋 **知識庫查詢結果：**
抱歉，我在心理健康知識庫中沒有找到與您問題相關的信息。

📚 **可能的原因：**
1. 知識庫中沒有上傳相關的心理健康文檔
2. 您的問題關鍵詞與文檔內容不匹配

💡 **建議：**
1. 請到心理健康RAG管理系統上傳相關文檔
2. 嘗試用不同的關鍵詞重新表述問題
3. 聯繫管理員檢查知識庫配置
"""
        
        # 構建回答 - 使用餘弦相似度的合理閾值
        context_chunks = []
        similarity_threshold = 0.3  # 餘弦相似度的合理閾值（0-1範圍）
        
        for result in search_results:
            similarity = result["similarity"]
            # 使用更寬鬆的相似度過濾
            if similarity >= similarity_threshold:
                context_chunks.append({
                    "text": result["text"],
                    "filename": result["metadata"].get("filename", "未知文檔"),
                    "categories": result["metadata"].get("categories", []),
                    "similarity": similarity
                })
                print(f"✅ 使用文檔片段 - 相似度: {similarity:.3f} 來源: {result['metadata'].get('filename', '未知')}")
            else:
                print(f"❌ 跳過文檔片段 - 相似度過低: {similarity:.3f}")
        
        if not context_chunks:
            return f"""📋 **知識庫查詢結果：**
找到了 {len(search_results)} 個相關片段，但相似度都低於閾值 {similarity_threshold}。

📊 **搜索詳情：**
最高相似度: {max([r['similarity'] for r in search_results], default=0):.3f}

📚 **建議：**
1. 嘗試用更具體或不同的關鍵詞重新表述您的問題
2. 檢查知識庫中是否有相關的心理健康文檔
3. 考慮上傳更多相關文檔到知識庫"""
        
        # 構建上下文回答
        context_text = "\n\n".join([chunk["text"] for chunk in context_chunks])
        
        # 構建帶有來源信息的回答
        sources = list(set([chunk["filename"] for chunk in context_chunks]))
        sources_text = "、".join(sources)
        
        # 按相似度排序，優先顯示最相關的內容
        context_chunks.sort(key=lambda x: x["similarity"], reverse=True)
        context_text = "\n\n".join([chunk["text"] for chunk in context_chunks])
        
        # 計算平均相似度
        avg_similarity = sum([chunk["similarity"] for chunk in context_chunks]) / len(context_chunks)
        
        # 獲取文檔類別
        all_categories = []
        for chunk in context_chunks:
            all_categories.extend(chunk["categories"])
        unique_categories = list(set(all_categories))
        categories_text = "、".join(unique_categories) if unique_categories else "一般心理健康"
        
        answer = f"""📋 **心理健康知識庫查詢結果：**
基於心理健康知識庫中的相關信息，我為您找到以下專業建議：

{context_text}

📚 **信息來源：**
{sources_text}

🏷️ **相關類別：**
{categories_text}

📊 **檢索統計：**
- 使用了 {len(context_chunks)} 個文檔片段（共搜索到 {len(search_results)} 個）
- 平均相似度：{avg_similarity:.3f}"""
        
        if len(context_chunks) < len(search_results):
            answer += f"\n\n💡 **提示：**\n還有 {len(search_results) - len(context_chunks)} 個相關度較低的片段，如需更詳細的內容，請進一步細化您的問題。"
        
        return answer
        
    except ImportError as e:
        return f"""📋 **系統錯誤：**
心理健康知識庫服務暫時不可用。

📚 **錯誤詳情：**
{str(e)}

💡 **解決方案：**
1. 請確保已安裝心理健康RAG相關依賴
2. 重新啟動後端服務
3. 聯繫管理員檢查系統配置"""
    except Exception as e:
        return f"""📋 **查詢錯誤：**
查詢心理健康知識庫時出現錯誤。

📚 **錯誤詳情：**
{str(e)}

💡 **建議：**
1. 請稍後再試
2. 檢查心理健康RAG管理系統是否正常運行
3. 聯繫管理員進行技術支持"""

async def provide_mental_health_support(user_message: str) -> str:
    """
    提供心理健康支持
    """
    try:
        # 檢查是否包含緊急關鍵詞
        emergency_keywords = ["自殺", "死亡", "結束", "痛苦", "絕望", "suicide", "die", "end", "pain", "hopeless"]
        has_emergency = any(keyword in user_message.lower() for keyword in emergency_keywords)
        
        if has_emergency:
            return """
🚨 **緊急支持**

我注意到你的消息包含一些令人擔憂的內容。請記住：

💙 **你並不孤單**
- 你的生命是寶貴的
- 有人關心你，願意幫助你
- 這些困難是暫時的，會過去的

📞 **立即尋求幫助**
- 聯繫信任的朋友或家人
- 撥打心理健康熱線
- 尋求專業心理健康服務
- 如果情況緊急，請撥打緊急電話

🌟 **記住**
- 你的感受是有效的
- 尋求幫助是勇敢的表現
- 專業人士可以幫助你度過這個困難時期
"""
        
        # 一般心理健康支持
        return await analyze_user_mental_state(user_message)
        
    except Exception as e:
        return f"提供支持時出現錯誤：{str(e)}"
