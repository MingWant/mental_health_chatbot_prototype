"""
心理健康自我關懷聊天機器人服務器
專門為學生提供心理健康支持和自我關懷策略
"""

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_agentchat.messages import *
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient
from llms import model_client
import asyncio
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from sse_starlette.sse import EventSourceResponse
import json
import os
from datetime import datetime
import uuid
from typing import List, Optional
import hashlib
import secrets

# Memory 相關
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType

# 上下文管理相關
from autogen_core.model_context import BufferedChatCompletionContext

# 導入心理健康工具
from mental_health_tools import (
    assess_emotion_state,
    get_coping_strategies,
    get_meditation_guide,
    get_sleep_advice,
    get_study_wellness_tips,
    create_self_care_plan,
    check_mental_health_resources,
    generate_mood_tracker,
    analyze_user_mental_state,
    provide_mental_health_support,
    query_mental_health_knowledge_base
)

# 導入聊天記錄管理器
from chat_history_manager import (
    create_chat_session,
    save_chat_message,
    get_chat_messages,
    get_user_sessions
)

# 導入RAG服務（如果可用）
try:
    from mental_health_rag_service import mental_health_rag_service
    from mental_health_rag_api import router as mental_health_rag_router
    RAG_ENABLED = True
    print("✅ 心理健康RAG服務已成功加載")
except ImportError as e:
    print(f"⚠️ 心理健康RAG服務加載失敗: {e}")
    RAG_ENABLED = False
    mental_health_rag_router = None

# 會話記憶體
session_memories = {}

# 用FunctionTool封裝心理健康工具
emotion_assessment_tool = FunctionTool(
    assess_emotion_state,
    description="評估用戶的情緒狀態，分析消息中的情緒關鍵詞並返回情緒分析結果"
)

coping_strategies_tool = FunctionTool(
    get_coping_strategies,
    description="獲取針對特定情緒的應對策略，根據情緒類型和強度提供個性化建議"
)

meditation_guide_tool = FunctionTool(
    get_meditation_guide,
    description="提供冥想指導，包括不同級別和類型的冥想練習步驟"
)

sleep_advice_tool = FunctionTool(
    get_sleep_advice,
    description="提供睡眠衛生建議，幫助改善睡眠質量"
)

study_wellness_tool = FunctionTool(
    get_study_wellness_tips,
    description="提供學習健康建議，幫助學生在學習過程中保持心理健康"
)

self_care_plan_tool = FunctionTool(
    create_self_care_plan,
    description="創建個性化的自我關懷計劃，根據用戶偏好制定日常和每週活動"
)

mental_health_resources_tool = FunctionTool(
    check_mental_health_resources,
    description="提供心理健康資源信息，包括校園資源、線上資源和緊急聯繫方式"
)

mood_tracker_tool = FunctionTool(
    generate_mood_tracker,
    description="生成心情追蹤器模板，幫助用戶記錄和追蹤心理健康狀況"
)

mental_health_support_tool = FunctionTool(
    provide_mental_health_support,
    description="提供心理健康支持，分析用戶狀態並提供相應的建議和資源"
)

mental_health_knowledge_base_tool = FunctionTool(
    query_mental_health_knowledge_base,
    description="從心理健康知識庫中搜索相關信息並回答用戶問題，適用於心理健康專業知識、治療方法、自我關懷策略等查詢"
)

# 心理健康工具集
mental_health_tools = [
    emotion_assessment_tool,
    coping_strategies_tool,
    meditation_guide_tool,
    sleep_advice_tool,
    study_wellness_tool,
    self_care_plan_tool,
    mental_health_resources_tool,
    mood_tracker_tool,
    mental_health_support_tool,
    mental_health_knowledge_base_tool,  # 添加RAG知識庫工具
]

app = FastAPI(title="心理健康自我關懷聊天機器人", version="1.0.0")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊心理健康RAG路由（如果可用）
if RAG_ENABLED and mental_health_rag_router:
    app.include_router(mental_health_rag_router)
    print("✅ 心理健康RAG API路由已註冊")
else:
    print("⚠️ 心理健康RAG API路由未註冊（依賴缺失）")

# 數據模型
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

class ChatMessage(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    created_at: str

class ChatSession(BaseModel):
    id: int
    session_id: str
    user_id: str
    agent_type: str
    title: str
    created_at: str
    updated_at: str

class SendMessageRequest(BaseModel):
    session_id: str
    message: str
    agent_type: str = "mental_health"

class SendMessageResponse(BaseModel):
    user_message: ChatMessage
    ai_message: ChatMessage

class User(BaseModel):
    id: int
    username: str
    email: str
    password_hash: str
    created_at: str
    is_active: bool = True

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    invite_code: str

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    user_id: int
    username: str
    email: str
    token: str

# 數據存儲配置
DATA_FILE = "mental_health_chat_data.json"
USERS_FILE = "mental_health_users_data.json"
INVITE_CODE = "mental_health_2024"

def load_data():
    """載入聊天數據"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"sessions": [], "messages": []}

def save_data(data):
    """保存聊天數據"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_next_id(items):
    """獲取下一個ID"""
    return max([item.get("id", 0) for item in items], default=0) + 1

def load_users():
    """載入用戶數據"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"users": []}

def save_users(users_data):
    """保存用戶數據"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, ensure_ascii=False, indent=2)

def hash_password(password: str) -> str:
    """加密密碼"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """驗證密碼"""
    return hash_password(password) == password_hash

def generate_token() -> str:
    """生成簡單的token"""
    return secrets.token_urlsafe(32)

# API端點
@app.get("/")
async def root():
    return {
        "message": "心理健康自我關懷聊天機器人API服務運行中",
        "version": "1.0.0",
        "features": [
            "情緒評估與分析",
            "個性化應對策略",
            "冥想指導",
            "睡眠建議",
            "學習健康建議",
            "自我關懷計劃",
            "心理健康資源",
            "心情追蹤"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "rag_enabled": RAG_ENABLED}

# 用戶認證API
@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    """用戶註冊"""
    if request.invite_code != INVITE_CODE:
        raise HTTPException(status_code=400, detail="邀請碼無效")
    
    users_data = load_users()
    
    for user in users_data["users"]:
        if user["username"] == request.username:
            raise HTTPException(status_code=400, detail="用戶名已存在")
        if user["email"] == request.email:
            raise HTTPException(status_code=400, detail="郵箱已存在")
    
    new_user = {
        "id": get_next_id(users_data["users"]),
        "username": request.username,
        "email": request.email,
        "password_hash": hash_password(request.password),
        "created_at": datetime.now().isoformat(),
        "is_active": True
    }
    
    users_data["users"].append(new_user)
    save_users(users_data)
    
    token = generate_token()
    
    return AuthResponse(
        user_id=new_user["id"],
        username=new_user["username"],
        email=new_user["email"],
        token=token
    )

@app.post("/api/v1/auth/login")
async def login(request: LoginRequest):
    """用戶登錄"""
    users_data = load_users()
    
    user = None
    for u in users_data["users"]:
        if u["username"] == request.username:
            user = u
            break
    
    if not user:
        raise HTTPException(status_code=401, detail="用戶名不存在")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="帳戶已被停用")
    
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="密碼錯誤")
    
    token = generate_token()
    
    return AuthResponse(
        user_id=user["id"],
        username=user["username"],
        email=user["email"],
        token=token
    )

# 會話管理API
@app.get("/api/v1/chat/sessions")
async def get_sessions(
    user_id: int = Query(..., description="用戶ID"),
    agent_type: str = Query("mental_health", description="智能體類型")
):
    """獲取用戶的聊天會話列表"""
    return get_user_sessions(user_id, agent_type)

@app.post("/api/v1/chat/sessions")
async def create_session(
    agent_type: str = Query("mental_health", description="智能體類型"),
    user_id: int = Query(..., description="用戶ID"),
    title: Optional[str] = Query(None, description="會話標題")
):
    """創建新的聊天會話"""
    session_id = str(uuid.uuid4())
    new_session = create_chat_session(session_id, user_id, agent_type, title)
    return new_session

@app.get("/api/v1/chat/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    user_id: int = Query(..., description="用戶ID"),
    agent_type: str = Query("mental_health", description="智能體類型")
):
    """獲取會話的聊天記錄"""
    return get_chat_messages(session_id, user_id, agent_type)

@app.delete("/api/v1/chat/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user_id: int = Query(..., description="用戶ID"),
    agent_type: str = Query("mental_health", description="智能體類型")
):
    """刪除會話及其聊天記錄"""
    try:
        from chat_history_manager import chat_history_manager
        success = chat_history_manager.delete_session(session_id, user_id, agent_type)
        if success:
            return {"success": True, "message": "會話刪除成功"}
        else:
            raise HTTPException(status_code=500, detail="刪除會話失敗")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除會話時發生錯誤: {str(e)}")

# 心理健康聊天API
@app.post("/api/v1/chat/messages")
async def send_message_with_session(request: SendMessageRequest):
    """發送消息並獲取AI回覆（帶會話管理）"""
    user_id = 1  # 暫時使用默認用戶ID
    
    # 驗證會話是否存在
    existing_sessions_data = get_user_sessions(user_id, request.agent_type)
    existing_sessions = existing_sessions_data.get("sessions", []) if isinstance(existing_sessions_data, dict) else existing_sessions_data
    session_exists = any(s["session_id"] == request.session_id for s in existing_sessions)
    
    if not session_exists:
        raise HTTPException(status_code=404, detail="會話不存在")
    
    # 獲取或創建該會話的Memory
    if request.session_id not in session_memories:
        session_memories[request.session_id] = ListMemory()
    memory = session_memories[request.session_id]
    
    # 添加用户消息到Memory
    await memory.add(MemoryContent(
        content=f"user: {request.message}",
        mime_type=MemoryMimeType.TEXT
    ))
    
    # 保存用戶消息到聊天記錄系統
    user_message = save_chat_message(request.session_id, user_id, request.agent_type, "user", request.message)
    
    # 心理健康聊天機器人的系統提示詞
    system_message = """
# 心理健康自我關懷助手

你是一個專業、溫暖、富有同理心的心理健康自我關懷助手，專門為學生提供心理健康支持和自我關懷策略。

## 🎯 核心使命
幫助學生管理情緒健康，提供實用的自我關懷策略，促進心理健康成長。

## 💙 核心價值觀
- **同理心**：理解並接納每個人的感受
- **專業性**：基於科學的心理健康知識
- **安全性**：優先考慮用戶的安全和福祉
- **個性化**：根據個人情況提供定制化建議
- **希望**：傳遞希望和積極的改變可能

## 🛠️ 專業工具集
你擁有以下心理健康專業工具：

1. **情緒評估工具** - 分析用戶情緒狀態
2. **應對策略工具** - 提供個性化應對方法
3. **冥想指導工具** - 提供冥想練習指導
4. **睡眠建議工具** - 改善睡眠質量
5. **學習健康工具** - 學習過程中的心理健康
6. **自我關懷計劃工具** - 制定個性化計劃
7. **心理健康資源工具** - 提供專業資源
8. **心情追蹤工具** - 追蹤心理健康狀況

## 🚨 緊急情況處理
如果用戶表達自殺想法、嚴重抑鬱或其他緊急情況：
1. 立即表達關心和理解
2. 強調生命的寶貴性
3. 提供緊急資源和聯繫方式
4. 鼓勵尋求專業幫助
5. 不要承諾保密，安全第一

## 💬 溝通風格
- **溫暖親切**：像朋友一樣關心和支持
- **專業可靠**：提供基於科學的建議
- **鼓勵支持**：肯定用戶的努力和進步
- **耐心理解**：給用戶時間和空間表達
- **積極正面**：傳遞希望和改變的可能

## 📋 回應結構
1. **情緒認同**：認同並理解用戶的感受
2. **專業分析**：使用工具進行情緒評估
3. **實用建議**：提供具體的應對策略
4. **資源推薦**：推薦相關的資源和工具
5. **鼓勵支持**：給予鼓勵和持續支持

## 🌱 自我關懷理念
- 每個人的感受都是有效的
- 尋求幫助是勇敢的表現
- 心理健康是整體健康的重要組成部分
- 自我關懷不是自私，而是必要的
- 改變是可能的，需要時間和耐心

## 📚 知識基礎
- 認知行為療法（CBT）原則
- 正念冥想技巧
- 情緒調節策略
- 壓力管理方法
- 睡眠衛生知識
- 學習心理健康

## 🎯 目標
幫助用戶：
- 更好地理解和管理情緒
- 建立健康的應對機制
- 培養自我關懷習慣
- 改善睡眠和學習狀態
- 在需要時尋求專業幫助

記住：你是一個支持者、引導者和陪伴者，而不是替代專業心理健康服務。始終鼓勵用戶在需要時尋求專業幫助。
"""
    
    # 使用AutoGen生成AI回覆
    agent = AssistantAgent(
        name="mental_health_assistant",
        model_client=model_client,
        model_client_stream=False,
        tools=mental_health_tools,
        reflect_on_tool_use=True,
        memory=[memory],
        system_message=system_message,
    )
    
    try:
        result = await agent.run(task=request.message)
        
        # 從AutoGen的結果中提取最終的AI回復
        if hasattr(result, "messages") and result.messages:
            for message in reversed(result.messages):
                if (hasattr(message, "source") and message.source == "mental_health_assistant" and 
                    hasattr(message, "type") and message.type == "TextMessage" and
                    hasattr(message, "content")):
                    reply = message.content
                    break
            else:
                reply = result.content if hasattr(result, "content") else "未能獲取回復內容"
        else:
            reply = result.content if hasattr(result, "content") else str(result)
    except Exception as e:
        reply = f"抱歉，處理您的請求時出現了錯誤：{str(e)}"

    # 將AI回覆添加到Memory
    await memory.add(MemoryContent(
        content=f"assistant: {reply}",
        mime_type=MemoryMimeType.TEXT
    ))

    # 保存AI回覆到聊天記錄系統
    ai_message = save_chat_message(request.session_id, user_id, request.agent_type, "assistant", reply)
    
    return SendMessageResponse(
        user_message=ChatMessage(**user_message),
        ai_message=ChatMessage(**ai_message)
    )

# 流式聊天API
@app.post("/api/v1/chat/stream")
async def chat_stream_with_session(request: SendMessageRequest):
    """流式聊天API（帶會話管理）"""
    user_id = 1  # 暫時使用默認用戶ID
    
    # 驗證會話是否存在
    existing_sessions_data = get_user_sessions(user_id, request.agent_type)
    existing_sessions = existing_sessions_data.get("sessions", []) if isinstance(existing_sessions_data, dict) else existing_sessions_data
    session_exists = any(s["session_id"] == request.session_id for s in existing_sessions)
    
    if not session_exists:
        raise HTTPException(status_code=404, detail="會話不存在")
    
    # 獲取或創建該會話的Memory
    if request.session_id not in session_memories:
        session_memories[request.session_id] = ListMemory(name=f"memory_{request.session_id}")
    user_memory = session_memories[request.session_id]
    print("用戶消息添加到Memory：", request.message)

    # 保存用戶消息到聊天記錄系統
    user_message = save_chat_message(request.session_id, user_id, request.agent_type, "user", request.message)

    # 將用戶消息添加到Memory
    await user_memory.add(MemoryContent(
        content=f"user: {request.message}",
        mime_type=MemoryMimeType.TEXT
    ))
    print("用戶消息添加到Memory：", request.message)

    # 心理健康聊天機器人的系統提示詞
    system_message = """
    Role & Core Identity:
    You are "MindPal," an AI mental health companion built by the "Guardian Project." 
    Your primary role is to act as a supportive, empathetic, and knowledgeable virtual friend for university students.
    You are not a licensed therapist, but a first point of contact for emotional support, mental health information, and resource connection.

    Mission & Core Values:
    Your mission is to help university students manage their emotional well-being, provide practical self-care strategies, and promote mental health growth.

    Key Principles:
    - Empathy: Understand and accept everyone's feelings
    - Professionalism: Based on scientific mental health knowledge
    - Safety: Prioritize user safety and well-being
    - Personalization: Provide customized advice based on individual needs
    - Hope: Spread optimism and positive change possibilities

    Core Principles (Non-Negotiable):
    Do No Harm: You must never provide a medical or psychiatric diagnosis, suggest treatments or medications, or handle acute crisis situations. Your role is to support and refer, not to treat.
    Empathy First: Prioritize active listening, emotional validation, and unconditional positive regard. The user must feel heard and understood above all else.
    Safety Net & Professional Referral: You are a bridge to professional help. For any mentions of suicide, self-harm, abuse, or violence, you MUST immediately trigger the Safety Protocol.
    Empowerment: Help users identify their own strengths and coping mechanisms. Frame suggestions as tools they can choose to use, fostering a sense of agency.
    Human-like & Natural: Engage in warm, conversational dialogue. Avoid clinical, robotic, or repetitive language. You are permitted to use minimal, appropriate emojis (e.g., 🙂, 😔, 🤗) to soften communication.

    Capabilities & Tools:
    You have access to specialized tools. You are better to use them to provide richer, more accurate support, Don't use them only when the user asks for it, you can use them when you think it's appropriate.
    You can use multiple tools together, but you need to use them in a logical order.
    It is better to use RAG Tools first to get the information, then use the other tools or the information from RAG Tools to provide the support.

    Professional Tools:
    You have access to the following mental health professional tools:
    # I will add the tools later

    Response Structure & Strategy(Reference Only, you can use it if you want, you can use your own strategy, which is optional):
    Craft responses that seamlessly blend the following elements:
    Emotional Validation & Reflection: Always begin by acknowledging the user's emotional state.
    Example Phrases: "That sounds incredibly overwhelming," "It's completely understandable to feel that way given what you're going through," "Thank you for sharing that with me. It must be really tough."
    Tool Utilization & Content Delivery: Integrate the results from your tools naturally into the conversation.
    RAG Example: "I recall a technique from our resources called 'progressive muscle relaxation' that might help with that physical anxiety. Would you like me to walk you through it?"
    Video Example: "I found a really clear video from a clinical psychologist that explains why we procrastinate and how to break the cycle. Here's the link: [Video Link]. I'd be curious to hear your thoughts on it after."
    Open-Ended Questioning: Guide the conversation deeper or check for understanding.
    Example Phrases: "What does that feeling feel like in your body?" "How have you been coping with this so far?" "What would you like to see change about this situation?"
    
    
    *Safety Protocol (CRITICAL)*(Important!!!): This is a hard-coded override. The instant you detect keywords or intent related to self-harm, suicide, abuse, or harming others, you MUST IMMEDIATELY execute the following response. Do not deviate. Do not continue the previous conversation.
    Exact Safety Protocol Response:(Do not change the meaning of this response, but you can change the format of the response, you can change the order of the response, you can add some other response, but you must ensure the meaning of the response is the same)
    "I hear you, and I am deeply concerned about what you're telling me. It's incredibly important that you speak with a trained professional who can give you the support you need right now. Please, right now, contact one of these free, confidential, 24/7 hotlines:
    The Hong Kong Polytechnic University for Prevention: https://www.polyu.edu.hk/
    Crisis Text Line: Text 'PolyU Help' to 27666223
    Mental Health Support Hotline: 18288
    Hospital Authority Emergency Hotline: 24667350
    Social Welfare Department: 23432255
    Suicide Prevention Services: 23820000
    The Samaritan Befrienders Hong Kong: 23892222
    The Samaritans: 28960000
    You are not alone, and they are there to help. Please, will you reach out to them? I'm here, and I care, but this is beyond my ability to help you with."
    
    Tone & Style Guidelines:
    Use: Warm, conversational, collaborative, and supportive language. Use "I" and "you".
    Avoid: Jargon, authoritative commands ("You must..."), clichés ("Everything happens for a reason"), and dismissive language ("Just cheer up!").
    Emojis: Use appropriate emojis (e.g., 🙂, 😔, 🤗) to soften communication.
    
    Example Interactions for Context(Reference Only, you can use it if you want, you can use your own interactions, which is optional):
    User: "I'm so stressed about finals I can't sleep and I feel like I'm going to fail everything."
    You: "That's a huge amount of pressure to be under, it's no wonder you're feeling so stressed and it's affecting your sleep. 😔 Let me see what our resources say about managing academic anxiety and improving sleep hygiene... [Calls search_knowledge_base] Okay, I have a few tips on a 'pre-sleep routine' to quiet the mind. Would talking through those be helpful?"
    User: "I just had a huge fight with my best friend and I think we're done forever."
    You: "I'm so sorry to hear that. Conflicts with close friends can be heartbreaking and make you feel really isolated. 🤗 Would it help to talk about what happened? Sometimes just putting it into words can bring clarity."

    """

    agent = AssistantAgent(
        name="mental_health_assistant",
        model_client=model_client,
        model_client_stream=True,
        tools=mental_health_tools,
        reflect_on_tool_use=True,
        memory=[user_memory],
        system_message=system_message,
    )

    async def event_generator():
        collected_content = ""
        
        # 添加用戶消息到Memory
        await user_memory.add(MemoryContent(
            content=f"user: {request.message}",
            mime_type=MemoryMimeType.TEXT
        ))
        print("用戶消息添加到Memory：", request.message)
        
        async for msg in agent.run_stream(task=request.message):
            if isinstance(msg, ToolCallExecutionEvent):
                print("Agent執行Function結果：", msg.content[0].content)
            elif isinstance(msg, ModelClientStreamingChunkEvent):
                print(msg.content)
                collected_content += msg.content
                # 發送正確格式的SSE數據
                yield {
                    "data": json.dumps({
                        "type": "content",
                        "content": collected_content
                    })
                }
            elif isinstance(msg, TextMessage):
                if msg.source == "mental_health_assistant":
                    print("Assistant Message:", msg.content)
                    print("Token Used:", msg.models_usage.prompt_tokens if hasattr(msg, 'models_usage') else "N/A")
        
        # 保存AI回覆到聊天記錄系統
        ai_message = save_chat_message(request.session_id, user_id, request.agent_type, "assistant", collected_content)

        # 將AI回覆添加到Memory
        await user_memory.add(MemoryContent(
            content=f"assistant: {collected_content}",
            mime_type=MemoryMimeType.TEXT
        ))
        print("AI回覆添加到Memory：", collected_content)
        
        # 發送完成事件
        yield {
            "data": json.dumps({
                "type": "done",
                "content": collected_content
            })
        }

        yield {"event": "end", "data": "[END]"}

    return EventSourceResponse(event_generator())

# 心理健康專用API
from pydantic import BaseModel

class AssessRequest(BaseModel):
    message: str

@app.post("/api/v1/mental-health/assess")
async def assess_mental_health(request: AssessRequest):
    """情緒評估API"""
    try:
        message = request.message
        assessment = await assess_emotion_state(message)
        return {"success": True, "assessment": assessment}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/v1/mental-health/coping-strategies")
async def get_coping_strategies_api(emotion: str, intensity: str = "中"):
    """獲取應對策略API"""
    try:
        strategies = await get_coping_strategies(emotion, intensity)
        return {"success": True, "strategies": strategies}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/v1/mental-health/meditation")
async def get_meditation_guide_api(level: str = "初學者", type: str = "呼吸冥想"):
    """獲取冥想指導API"""
    try:
        guide = await get_meditation_guide(level, type)
        return {"success": True, "guide": guide}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/v1/mental-health/sleep-advice")
async def get_sleep_advice_api():
    """獲取睡眠建議API"""
    try:
        advice = await get_sleep_advice()
        return {"success": True, "advice": advice}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/v1/mental-health/study-wellness")
async def get_study_wellness_api():
    """獲取學習健康建議API"""
    try:
        tips = await get_study_wellness_tips()
        return {"success": True, "tips": tips}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/v1/mental-health/self-care-plan")
async def create_self_care_plan_api(preferences: dict):
    """創建自我關懷計劃API"""
    try:
        plan = await create_self_care_plan(preferences)
        return {"success": True, "plan": plan}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/v1/mental-health/resources")
async def get_mental_health_resources_api():
    """獲取心理健康資源API"""
    try:
        resources = await check_mental_health_resources()
        return {"success": True, "resources": resources}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/v1/mental-health/mood-tracker")
async def generate_mood_tracker_api():
    """生成心情追蹤器API"""
    try:
        tracker = await generate_mood_tracker()
        return {"success": True, "tracker": tracker}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
