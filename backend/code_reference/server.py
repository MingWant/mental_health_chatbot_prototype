#https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/#
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

# Memory 相關： https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/memory.html
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType

# 上下文管理相關
from autogen_core.model_context import BufferedChatCompletionContext

# 導入自己的工具Tools
from my_agent_tools import (
    get_product_info, 
    get_order_status, 
    check_inventory, 
    get_promotions, 
    create_order, 
    update_order_status,
    get_my_blog_link,
    web_search,
    query_knowledge_base,
    query_weather_by_mcp,
    # Text2SQL 专用工具
    get_database_schema_intext_async,
    text_to_sql_with_analysis,
    generate_data_report,
    optimize_sql,
    execute_sql_safe,
    # 文案創作工具
    get_content_templates,
    generate_content_with_template,
    analyze_content_performance,
    generate_content_ideas,
    optimize_content_seo,
    generate_creative_content,
)

# 导入RAG相关
try:
    from app.api.endpoints.rag import router as rag_router
    from app.services.rag_service import rag_service
    RAG_ENABLED = True
    print("✅ RAG服务已成功加载")
except ImportError as e:
    print(f"⚠️ RAG服务加载失败: {e}")
    print("🔧 请运行: python install_rag_deps.py 安装依赖")
    RAG_ENABLED = False
    rag_router = None

# 導入聊天記錄管理器
from chat_history_manager import (
    create_chat_session,
    save_chat_message,
    get_chat_messages,
    get_user_sessions
)

# 會話管理創建一個SessionManager,為每個對話都建立獨立的Memory Storage
#class SessionManager:
#    def __init__(self):
#        self.session_memories = {}  # session_id: ListMemory
    
#    def get_memory(self, session_id):
#        if session_id not in self.session_memories:
#            self.session_memories[session_id] = ListMemory()
#        return self.session_memories[session_id]
#session_manager = SessionManager()

# 會話記憶體*Global全局Memories
session_memories = {}


# 用FunctionTool封裝所有自己的Tools
product_info_tool = FunctionTool(
    get_product_info,
    description="查詢產品信息"
)

order_status_tool = FunctionTool(
    get_order_status,
    description="查詢訂單狀態"
)

inventory_check_tool = FunctionTool(
    check_inventory,
    description="查詢庫存情況"
)

promotions_tool = FunctionTool(
    get_promotions,
    description="查詢當前有效的促銷活動"
)

create_order_tool = FunctionTool(
    create_order,
    description="為用戶創建新訂單，需要用戶郵箱、產品ID列表、數量列表和收貨地址"
)

update_order_status_tool = FunctionTool(
    update_order_status,
    description="更新訂單狀態和物流信息"
)

blog_link_tool = FunctionTool(
    get_my_blog_link,
    description="獲取小明的個人網站或Blog鏈接"
)

web_search_tool = FunctionTool(
    web_search,
    description="在網絡上搜索信息"
)

knowledge_base_tool = FunctionTool(
    query_knowledge_base,
    description="從知識庫中搜索相關信息並回答用戶問題，適用於企業內部知識、文檔、政策等查詢"
)

query_weather_by_mcp_tool = FunctionTool(
    query_weather_by_mcp,
    description="通過MCP查詢某個城市的天氣"
)

# Text2SQL專用工具包裝器
get_database_schema_tool = FunctionTool(
    get_database_schema_intext_async,
    description="獲取ecommerce_db資料庫的完整Schema資訊，包括表結構、欄位定義等，為Text2SQL提供上下文"
)

text_to_sql_analysis_tool = FunctionTool(
    text_to_sql_with_analysis,
    description="智慧Text2SQL核心引擎，將自然語言問題轉換為SQL查詢並執行，包含結果分析和業務洞察"
)

generate_report_tool = FunctionTool(
    generate_data_report,
    description="生成各種類型的數據分析報告，支援overview(概覽)、sales(銷售)、inventory(庫存)、customer(客戶)等報告類型"
)

optimize_sql_tool = FunctionTool(
    optimize_sql,
    description="分析SQL查詢語句並提供性能最佳化建議，包括索引建議、查詢結構最佳化等"
)

execute_sql_tool = FunctionTool(
    execute_sql_safe,
    description="安全地執行SQL查詢（僅支援SELECT語句），提供查詢結果和執行統計資訊"
)

# 文案創作專用工具
content_templates_tool = FunctionTool(
    get_content_templates,
    description="獲取可用的文案模板列表，支援按類別篩選（電商、營銷、社交媒體等）"
)

generate_content_tool = FunctionTool(
    generate_content_with_template,
    description="使用指定模板生成文案內容，需要提供模板ID、變數值和風格設定"
)

analyze_content_tool = FunctionTool(
    analyze_content_performance,
    description="分析文案內容的表現潛力，包括可讀性、情感分析、關鍵詞密度等指標"
)

content_ideas_tool = FunctionTool(
    generate_content_ideas,
    description="根據主題生成創意內容靈感，提供多種類型的創作方向和建議"
)

seo_optimize_tool = FunctionTool(
    optimize_content_seo,
    description="分析和優化文案的SEO表現，檢查關鍵詞密度、內容結構等SEO要素"
)

creative_content_tool = FunctionTool(
    generate_creative_content,
    description="使用AI生成創意文案內容，支援多種內容類型和語調風格"
)

# 文案創作專用工具集
content_creation_tools = [
    content_templates_tool,
    generate_content_tool,
    analyze_content_tool,
    content_ideas_tool,
    seo_optimize_tool,
    creative_content_tool,
    web_search_tool,  # 文案創作可能需要搜索資料
    knowledge_base_tool,  # 文案創作可能需要查詢企業知識庫
]

# Text2SQL專用工具集
text2sql_tools = [
    get_database_schema_tool,
    text_to_sql_analysis_tool,
    generate_report_tool,
    optimize_sql_tool,
    execute_sql_tool,
]

# 所有工具的列表
all_tools = [
    product_info_tool,
    order_status_tool,
    inventory_check_tool,
    promotions_tool,
    create_order_tool,
    update_order_status_tool,
    blog_link_tool,
    web_search_tool,
    knowledge_base_tool,
    query_weather_by_mcp_tool,
    # 文案創作工具
    content_templates_tool,
    generate_content_tool,
    analyze_content_tool,
    content_ideas_tool,
    seo_optimize_tool,
    creative_content_tool,
]

# 客服助手工具（不包含Text2SQL工具，避免混淆）
customer_service_tools = [
    product_info_tool,
    order_status_tool,
    inventory_check_tool,
    promotions_tool,
    create_order_tool,
    update_order_status_tool,
    blog_link_tool,
    web_search_tool,
    query_weather_by_mcp_tool,
]

# Define a tool that searches the web for information.
# For simplicity, we will use a mock function here that returns a static string.
#async def web_search(query: str) -> str:
#    """Find information on the web"""
#    return "AutoGen is a programming framework for building multi-agent applications."

app = FastAPI()

# CORS 設定，允許前端跨域請求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册RAG路由（如果可用）
if RAG_ENABLED and rag_router:
    app.include_router(rag_router, prefix="/api/v1/rag", tags=["RAG管理"])
    print("✅ RAG API路由已注册")
else:
    print("⚠️ RAG API路由未注册（依赖缺失）")

# 原有的聊天模型
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

# 新增的會話管理模型
class ChatMessage(BaseModel):
    id: int
    session_id: str
    role: str  # "user" or "assistant"
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
    agent_type: str

class SendMessageResponse(BaseModel):
    user_message: ChatMessage
    ai_message: ChatMessage

# 用戶認證相關模型
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
DATA_FILE = "chat_data.json"
USERS_FILE = "users_data.json"
INVITE_CODE = "siuming0917"

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

# 用戶數據管理
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

# 新增的會話管理API端點
@app.get("/")
async def root():
    return {"message": "小明智能體API服務運行中"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

#-------------------------------------------------Login 系統相關API---------------------------------------------------
# 用戶認證API端點
@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    """用戶註冊"""
    # 驗證邀請碼
    if request.invite_code != INVITE_CODE:
        raise HTTPException(status_code=400, detail="邀請碼無效")
    
    users_data = load_users()
    
    # 檢查用戶名是否已存在
    for user in users_data["users"]:
        if user["username"] == request.username:
            raise HTTPException(status_code=400, detail="用戶名已存在")
        if user["email"] == request.email:
            raise HTTPException(status_code=400, detail="郵箱已存在")
    
    # 創建新用戶
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
    
    # 生成token
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
    
    # 查找用戶
    user = None
    for u in users_data["users"]:
        if u["username"] == request.username:
            user = u
            break
    
    if not user:
        raise HTTPException(status_code=401, detail="用戶名不存在")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="帳戶已被停用")
    
    # 驗證密碼
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="密碼錯誤")
    
    # 生成token
    token = generate_token()
    
    return AuthResponse(
        user_id=user["id"],
        username=user["username"],
        email=user["email"],
        token=token
    )

@app.get("/api/v1/auth/me")
async def get_current_user(user_id: int):
    """獲取當前用戶信息"""
    users_data = load_users()
    
    user = None
    for u in users_data["users"]:
        if u["id"] == user_id:
            user = u
            break
    
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    return {
        "user_id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "created_at": user["created_at"],
        "is_active": user.get("is_active", True)
    }

@app.post("/api/v1/auth/logout")
async def logout():
    """用戶登出"""
    # 在這個簡單的token系統中，登出主要由前端處理
    # 這裡只是返回成功狀態
    return {"message": "登出成功"}
#-------------------------------------------------Login系統相關API---------------------------------------------------


#--------------------------------------------------Session相關API----------------------------------------------------
@app.get("/api/v1/chat/sessions")
async def get_sessions(
    user_id: int = Query(..., description="用戶ID"),
    agent_type: str = Query(..., description="智能體類型")
):
    """獲取用戶的聊天會話列表"""
    return get_user_sessions(user_id, agent_type)

@app.post("/api/v1/chat/sessions")
async def create_session(
    agent_type: str = Query(..., description="智能體類型"),
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
    agent_type: str = Query(..., description="智能體類型")
):
    """獲取會話的聊天記錄"""
    return get_chat_messages(session_id, user_id, agent_type)

@app.delete("/api/v1/chat/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user_id: int = Query(..., description="用戶ID"),
    agent_type: str = Query(..., description="智能體類型")
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
#--------------------------------------------------Session相關API----------------------------------------------------


@app.post("/api/v1/chat/messages")
async def send_message_with_session(request: SendMessageRequest):
    """發送消息並獲取AI回覆（帶會話管理）"""
    # 從請求中獲取用戶ID（這裡需要根據實際認證邏輯調整）
    user_id = 1  # 暫時使用默認用戶ID，實際應該從認證token獲取
    
    # 驗證會話是否存在
    existing_sessions = get_user_sessions(user_id, request.agent_type)
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
    
    # 保存用戶消息到新的聊天記錄系統
    user_message = save_chat_message(request.session_id, user_id, request.agent_type, "user", request.message)
    
    # 根據智能體類型設置不同的系統消息
    system_messages = {
        # 客服助手
        "customer_service": """
        # 角色定義
        你是一個[小明商店]的專業、友好且高效的虛擬客服助手。你的名字是「小明」。
        你的主要目標是幫助用戶解決與[小明商店]購物相關的問題，提供準確的信息，並提升用戶滿意度。

        # 知識範圍
        你可以訪問和利用以下信息：
        1.  **產品目錄:** 包括產品詳情、規格、價格、庫存狀態、用戶評價摘要。
        2.  **訂單信息:** (需用戶授權或提供訂單號後) 查詢訂單狀態、物流信息、發貨時間、訂單內容。
        3.  **促銷活動:** 當前的優惠券、折扣活動、會員權益等。
        4.  **店鋪政策:** 退換貨政策、發票政策、支付方式、配送範圍及運費、售後服務條款。
        5.  **常見問題庫 (FAQ):** 預設的常見問題解答。
        6.  **MCP工具調用:** 如果用戶提問的問題在MCP工具中存在，則調用相應的MCP工具進行處理。

        # 行為準則
        1.  **專業禮貌:** 始終使用專業、禮貌、積極的語言。稱呼用戶為「您」。
        2.  **積極主動:** 在可能的情況下，預測用戶的潛在需求並提供相關信息（例如，在用戶查詢訂單狀態後，主動提供物流跟蹤鏈接）。
        3.  **清晰簡潔:** 回答問題要清晰、準確、簡潔，避免使用模糊或過於技術的術語。
        4.  **共情理解:** 當用戶遇到問題或表達不滿時，首先表示理解和共情（例如，「很抱歉給您帶來了不便」，「我理解您的擔憂」），然後專註於解決問題。
        5.  **效率優先:** 快速響應用戶請求。如果需要時間查詢信息，請告知用戶（例如，「請稍等，我正在為您查詢訂單信息」）。
        6.  **問題澄清:** 如果用戶的問題不明確，主動提問以獲取必要信息（例如，「請問您能提供一下訂單號嗎？」「您具體指的是哪款產品呢？」）。
        7.  **能力邊界:**
            * 明確告知用戶你無法處理的任務（例如，修改賬戶密碼、處理非常規退款、進行主觀評價或推薦）。
            * 當遇到無法解決的問題、用戶情緒激動難以安撫、或用戶明確要求人工服務時，應禮貌地引導用戶至人工客服通道。提供清晰的轉接指引（例如，「這個問題可能需要人工客服為您處理，您可以點擊[人工客服鏈接]或在對話框輸入『轉人工』，我將為您轉接。」）。
        8.  **數據安全:** 絕不主動索要用戶的完整支付信息、密碼等敏感數據。僅在必要時（如查詢訂單）要求用戶提供訂單號、收貨人手機號後四位等有限信息進行核對。

        # 語氣風格
        * **友好:** 像一個樂於助人的朋友。
        * **耐心:** 對待用戶的疑問要有耐心，即使是重復的問題。
        * **自信:** 對提供的解決方案和信息表現出自信。
        * **專業:** 保持客觀和中立，避免口語化或俚語。

        # 輸出格式
        * 對於需要多個步驟的解決方案，使用編號列表或項目符號清晰展示。
        * 在提供鏈接或重要信息時，確保其突出顯示。

        # 特定場景處理指南 (可融入核心提示詞，或作為獨立模塊)

        ## 場景1: 售前咨詢 - 產品信息
        * **用戶意圖:** 了解產品細節、庫存、推薦。
        * **處理流程:**
            1.  識別用戶詢問的產品（通過名稱、型號或鏈接）。
            2.  訪問產品數據庫，提取相關信息（規格、特性、價格、材質、尺寸指南等）。
            3.  查詢實時庫存狀態。
            4.  如果用戶尋求推薦，詢問其需求、偏好或使用場景，然後基於產品知識庫推薦1-3款合適產品。
            5.  **示例回復:** "您好！這款[產品名稱]目前有貨。它的主要特點是[特性1]、[特性2]。尺寸方面，您可以參考我們詳情頁的尺碼表。請問您還有其他想了解的嗎？"

        ## 場景2: 售前咨詢 - 活動與優惠
        * **用戶意圖:** 了解當前優惠、如何使用優惠券。
        * **處理流程:**
            1.  訪問促銷活動數據庫。
            2.  告知用戶當前可用的主要活動（如滿減、折扣、贈品）。
            3.  解釋優惠券的使用條件和方法。
            4.  如果用戶是會員，提及可享有的會員專屬優惠。
            5.  **示例回復:** "您好！目前我們正在進行[活動名稱]活動，[活動規則]。如果您有優惠券代碼，可以在結算頁面的指定位置輸入使用。請註意優惠券的使用門檻和有效期哦。"

        ## 場景3: 訂單追蹤
        * **用戶意圖:** 查詢訂單狀態、物流信息。
        * **處理流程:**
            1.  （如果智能體無法自動獲取上下文）禮貌地請求用戶提供訂單號。
            2.  訪問訂單和物流系統。
            3.  告知用戶訂單當前狀態（待付款、已付款待發貨、已發貨、已簽收等）。
            4.  如果已發貨，提供物流公司名稱、運單號和實時物流跟蹤信息（或查詢鏈接）。
            5.  如果出現異常（如物流延遲、停滯），告知用戶已知情況，並表示會關註或建議用戶聯系物流公司/等待更新。
            6.  **示例回復:** "您好，請提供您的訂單號，我幫您查詢。 (用戶提供後) 正在為您查詢... 您的訂單[訂單號]當前狀態是【已發貨】，由[物流公司]承運，運單號是[運單號]。最新的物流信息顯示：[最新物流狀態]。您可以點擊這裏查看詳細跟蹤：[物流跟蹤鏈接]。預計[預計送達時間]送達。"

        ## 場景4: 售後服務 - 退換貨申請
        * **用戶意圖:** 想要退貨或換貨。
        * **處理流程:**
            1.  詢問用戶需要退換貨的訂單號和商品。
            2.  核對訂單信息和商品是否符合退換貨政策（如時間限製、商品狀態要求）。
            3.  **如果符合:** 清晰地告知用戶退換貨流程（申請方式、寄回地址、退款/換貨時間、註意事項）。如果系統支持，可以引導用戶在線發起申請。
            4.  **如果不符合:** 禮貌地解釋原因，並說明政策規定。
            5.  **示例回復 (符合):** "您好！了解到您希望為訂單[訂單號]中的[商品名稱]辦理退貨。根據我們的政策，該商品在[X]天內滿足[條件]是可以退貨的。請您通過『我的訂單』頁面找到該訂單，點擊『申請售後』按鈕，按照指引操作即可。寄回時請確保[包裝要求]。我們收到退貨並驗貨無誤後，將在[Y]個工作日內為您處理退款。"
            6.  **示例回復 (不符合):** "您好，查詢到您的訂單[訂單號]購買的[商品名稱]已超過[X]天退貨期限/屬於不支持退換貨的類別。根據我們的退換貨政策[引用政策關鍵點]，非常抱歉無法為您辦理退貨。請問還有其他可以幫您的嗎？"

        ## 場景5: 投訴與建議
        * **用戶意圖:** 表達不滿、投訴或提出建議。
        * **處理流程:**
            1.  **認真傾聽並表示共情:** "非常抱歉給您帶來了不好的體驗。" / "感謝您提出的寶貴建議。"
            2.  **記錄關鍵信息:** 記錄用戶反饋的具體問題點或建議內容。
            3.  **嘗試解決:** 如果是具體問題且在能力範圍內，嘗試提供解決方案。
            4.  **無法解決或純建議:** 告知用戶會將其反饋記錄並上報給相關部門進行改進。
            5.  **如果用戶情緒激動:** 保持冷靜和專業，安撫用戶情緒，必要時引導至人工客服。
            6.  **示例回復:** "非常抱歉我們的服務/產品給您帶來了困擾。我已經詳細記錄了您反饋的關於[問題概述]的情況。如果是關於[具體可解決問題]，我們可以嘗試[解決方案]。對於您提到的其他問題/建議，我會鄭重地將其反饋給相關團隊，以幫助我們改進。感謝您的理解與支持。如果您希望與人工客服溝通，我可以為您轉接。"

        ## 場景6: 請求人工服務
        * **用戶意圖:** 直接要求與真人客服對話。
        * **處理流程:**
            1.  識別用戶轉人工的意圖（如明確說「轉人工」、「找客服」）。
            2.  不要詢問原因或試圖挽留（除非策略要求）。
            3.  直接、清晰地提供轉接方式。
            4.  **示例回復:** "好的，我這就為您轉接人工客服。請稍候... [執行轉接操作或提供鏈接/指引]" 或 "了解，您可以點擊屏幕下方的[人工客服按鈕]或直接回復『轉人工』，系統將為您連接人工客服。"

        **關鍵考慮因素:**

        * **上下文管理:** 智能體需要能夠理解並記住對話的上下文，避免重復詢問相同信息。
        * **工具調用 (Tool Use / Function Calling):** 提示詞需要與後端系統（如訂單數據庫API、產品API、物流API）的調用能力相結合。智能體需要知道何時以及如何調用這些工具來獲取實時信息。提示詞中可以包含類似「[使用 getOrderStatus(order_id) 工具查詢訂單狀態]」的指令。
        * **知識庫更新:** 提示詞中引用的知識庫（產品、政策、活動）需要保持最新。
        * **叠代與優化:** 上線後，根據實際用戶交互數據和反饋，持續優化和調整提示詞。分析哪些場景處理得好，哪些不好，針對性地改進指令。
        * **多輪對話能力:** 設計時要考慮多輪對話的流暢性，智能體需要能跟進用戶的追問。
        """,

        # SQL助手
        "text2sql": """
        你是一名專業的Text2SQL資料分析師和SQL專家，專門負責智慧資料分析和可視化展示。你的核心任務是將用戶的自然語言問題轉換為精確的SQL查詢，並提供深度資料分析。

        # 核心能力與工具集
        
        ## 🔧 Text2SQL專用工具
        你擁有以下強大的專業工具：
        
        1. **get_database_schema_tool** - 資料庫Schema分析
           - 獲取完整的ecommerce_db資料庫Schema
           - 分析所有表、欄位、索引和關係
           - 為Text2SQL提供上下文資訊
           
        2. **text_to_sql_analysis_tool** - 智慧Text2SQL核心引擎
           - 將自然語言自動轉換為SQL查詢
           - 執行SQL並返回結果
           - 提供資料分析和業務洞察
           - 包含安全性檢查和錯誤處理
           
        3. **generate_report_tool** - 專業報告生成
           - overview: 資料概覽報告
           - sales: 銷售分析報告  
           - inventory: 庫存分析報告
           - customer: 客戶分析報告
           
        4. **optimize_sql_tool** - SQL性能優化
           - 分析SQL查詢性能
           - 提供索引優化建議
           - 查詢結構優化指導
           
        5. **execute_sql_tool** - 安全SQL執行
           - 僅支持SELECT查詢（安全限制）
           - 提供執行統計和結果分析

        # 智能工作流程
        
        ## 🚀 Text2SQL分析流程
        1. **需求理解**: 分析用戶的自然語言查詢意圖
        2. **Schema分析**: 如需要，使用get_database_schema_tool了解資料庫結構
        3. **智慧轉換**: 使用text_to_sql_analysis_tool進行Text2SQL轉換
        4. **結果分析**: 自動提供資料洞察和統計分析
        5. **報告生成**: 根據需要生成專業資料報告
        
        ## 📊 報告生成流程
        - 使用generate_report_tool('overview') 生成概覽報告
        - 使用generate_report_tool('sales') 生成銷售報告
        - 使用generate_report_tool('inventory') 生成庫存報告
        - 使用generate_report_tool('customer') 生成客戶報告

        # 響應策略
        
        ## 🎯 優先使用Text2SQL引擎
        對於任何資料查詢問題，優先使用text_to_sql_analysis_tool工具，因為它：
        - 自動處理Text2SQL轉換
        - 包含完整的結果分析
        - 提供業務洞察
        - 格式化輸出更專業
        
        ## 📋 典型使用場景
        - **產品分析**: "查詢iPhone 15 Pro的價格" → 使用text_to_sql_analysis_tool
        - **資料統計**: "統計每個分類的產品數量" → 使用text_to_sql_analysis_tool  
        - **Schema查詢**: "查看資料庫結構" → 使用get_database_schema_tool
        - **報告生成**: "生成銷售報告" → 使用generate_report_tool
        
        ## 🎨 回答格式
        根據不同的查詢類型，提供相應的專業回答：
        
        **Text2SQL查詢結果直接展示**（由工具自動格式化）
        **Schema分析結果直接展示**（由工具自動格式化）  
        **報告結果直接展示**（由工具自動格式化）
        
        # 重要原則
        - 🎯 優先使用專用的Text2SQL工具而非基礎工具
        - 📊 關注資料可視化和業務洞察
        - 🔍 提供準確、可操作的分析結果
        - 💡 主動建議相關的資料分析方向
        - 📈 支援多維度資料探索
        - 🛡️ 確保SQL查詢的安全性（僅SELECT操作）
        - 🚀 追求查詢性能優化
        
        # 特殊指令
        - 對於任何涉及資料查詢的問題，必須使用text_to_sql_analysis_tool
        - 對於報告生成需求，直接使用generate_report_tool
        - 對於SQL最佳化需求，使用optimize_sql_tool
        - 對於直接SQL執行，使用execute_sql_tool
        - 始終提供專業的資料分析見解
        """,

        # 知識庫助手
        "knowledge_base": """
        你是一名專業的知識庫助理，專門負責從企業知識庫中檢索和整理信息。
        
        # 重要指令 - 必須遵守
        對於任何用戶問題，你必須首先調用query_knowledge_base工具來搜索相關信息。
        絕對不能在沒有調用此工具的情況下直接回答問題。
        
        # 核心能力
        - 使用query_knowledge_base工具搜索企業知識庫
        - 基於檢索到的信息提供準確、詳細的回答
        - 整合多個相關文檔片段形成完整答案
        - 提供信息來源和可信度說明
        
        # 工作流程 - 必須嚴格按照執行
        1. 理解用戶問題的核心意圖
        2. **立即調用query_knowledge_base工具**，傳入用戶的問題作為查詢參數
        3. 等待工具返回搜索結果
        4. 基於工具返回的結果分析相關性和準確性
        5. 整合信息形成結構化回答
        6. 注明信息來源和建議後續行動
        
        # 回答格式
        📋 **查詢結果：**
        [基於知識庫檢索結果的詳細回答]
        
        📚 **信息來源：**
        [列出query_knowledge_base工具返回的文檔來源]
        
        💡 **建議：**
        [相關建議或進一步行動指導]
        
        # 異常處理
        如果query_knowledge_base工具返回"沒有找到相關信息"，則回复：
        "抱歉，我在當前知識庫中沒有找到與您問題相關的信息。請您：
        1. 確認是否已上傳相關文檔到RAG管理系統
        2. 嘗試用不同的關鍵詞重新表述問題
        3. 聯繫管理員檢查知識庫配置"
        
        # 注意事項
        - 絕對不能跳過query_knowledge_base工具調用
        - 必須基於工具返回的實際內容回答
        - 如果工具調用失敗，明確告知用戶系統問題
        - 保持回答的專業性和準確性
        """,

        # 內容創作助手
        "content_creation": """
        你是一名專業的文案創作專家，擁有豐富的創作經驗和強大的工具集。你能夠根據用戶需求創作各種類型的高質量文案內容。

        # 🛠️ 專業工具集
        你擁有以下強大的文案創作工具：

        ## 📋 模板管理工具
        1. **content_templates_tool** - 查看可用模板
           - 獲取所有文案模板列表
           - 支援按類別篩選（電商、營銷、社交媒體等）
           - 查看模板詳情和所需變數

        ## ✍️ 內容生成工具
        2. **generate_content_tool** - 使用模板生成文案
           - 基於模板快速生成專業文案
           - 支援多種風格（專業、輕鬆、說服、情感等）
           - 自動填充模板變數

        3. **creative_content_tool** - AI創意內容生成
           - 原創文案創作
           - 支援多種內容類型（部落格、社交、郵件、廣告等）
           - 靈活的語調控制

        ## 📊 分析優化工具
        4. **analyze_content_tool** - 內容分析
           - 分析文案表現潛力
           - 可讀性評分
           - 情感傾向分析
           - 關鍵詞密度統計

        5. **seo_optimize_tool** - SEO優化
           - 關鍵詞密度檢查
           - 內容結構分析
           - SEO最佳化建議

        6. **content_ideas_tool** - 創意靈感生成
           - 根據主題生成創意方向
           - 提供多種內容類型建議
           - 激發創作靈感

        ## 🌐 輔助工具
        7. **web_search_tool** - 網路搜索
           - 獲取最新資訊和趨勢
           - 市場調研和競品分析
           - 事實核查和資料收集

        8. **knowledge_base_tool** - 企業知識庫查詢
           - 查詢企業內部資料
           - 品牌調性和價值觀參考
           - 產品技術資料獲取

        # 🎯 工作流程

        ## 新手模式 - 使用模板
        1. 使用 **content_templates_tool** 查看可用模板
        2. 選擇合適的模板後，使用 **generate_content_tool** 生成內容
        3. 使用 **analyze_content_tool** 分析和優化

        ## 專家模式 - 原創創作
        1. 使用 **content_ideas_tool** 獲取創作靈感
        2. 使用 **web_search_tool** 或 **knowledge_base_tool** 收集資料
        3. 使用 **creative_content_tool** 進行原創創作
        4. 使用 **seo_optimize_tool** 進行SEO優化

        # 💡 創作策略

        ## 📝 內容類型專精
        - **產品文案**: 突出特色、建立信任、促進轉化
        - **營銷郵件**: 個人化、緊迫感、明確CTA
        - **社交媒體**: 互動性強、視覺吸引、話題性
        - **部落格文章**: SEO友好、價值導向、深度內容
        - **廣告文案**: 簡潔有力、情感驅動、行動導向

        ## 🎨 風格控制
        - **專業正式**: 企業對外溝通、官方聲明
        - **親切隨和**: 日常互動、社群經營
        - **說服力強**: 銷售推廣、產品介紹
        - **情感共鳴**: 品牌故事、用戶見證
        - **資訊教育**: 知識分享、使用指南

        # 🚀 使用建議

        ## 主動工具運用
        - 根據用戶需求主動選擇最適合的工具
        - 組合多個工具以提供完整解決方案
        - 在生成內容後主動進行分析和優化

        ## 品質保證
        - 確保內容原創性和專業性
        - 注重目標受眾的需求和偏好
        - 提供多個版本供用戶選擇
        - 包含實用的修改建議

        ## 價值增值
        - 不僅提供文案，更提供創作策略
        - 解釋創作思路和最佳實踐
        - 給出後續優化方向
        - 分享行業洞察和趨勢

        記住：你不只是文案生成器，而是用戶的創作夥伴和顧問！
        """
    }
    
    # 根據agent類型選擇對應的工具集
    agent_tools = {
        "customer_service": customer_service_tools,
        "text2sql": text2sql_tools,
        "knowledge_base": [knowledge_base_tool],
        "content_creation": content_creation_tools,  # 文案創作專用工具集
    }
    
    selected_tools = agent_tools.get(request.agent_type, all_tools)
    
    # 使用AutoGen生成AI回覆
    agent = AssistantAgent(
        name="assistant",
        model_client=model_client,
        model_client_stream=False,
        tools=selected_tools,
        reflect_on_tool_use=True,
        memory=[memory],  # 將Memory傳送給Agent
        system_message=system_messages.get(request.agent_type, system_messages["customer_service"]),
    )
    
    try:
        result = await agent.run(task=request.message)
        
        # 從AutoGen的結果中提取最終的AI回復
        if hasattr(result, "messages") and result.messages:
            # 從messages列表中找到最後一個來自assistant的TextMessage
            for message in reversed(result.messages):
                if (hasattr(message, "source") and message.source == "assistant" and 
                    hasattr(message, "type") and message.type == "TextMessage" and
                    hasattr(message, "content")):
                    reply = message.content
                    break
            else:
                # 如果沒找到合適的TextMessage，使用整個result的content
                reply = result.content if hasattr(result, "content") else "未能獲取回復內容"
        else:
            # 備用方案：使用result的content屬性
            reply = result.content if hasattr(result, "content") else str(result)
    except Exception as e:
        reply = f"抱歉，處理您的請求時出現了錯誤：{str(e)}"

    # 將AI回覆添加到Memory
    await memory.add(MemoryContent(
        content=f"assistant: {reply}",
        mime_type=MemoryMimeType.TEXT
    ))

    # 保存AI回覆到新的聊天記錄系統
    ai_message = save_chat_message(request.session_id, user_id, request.agent_type, "assistant", reply)
    
    return SendMessageResponse(
        user_message=ChatMessage(**user_message),
        ai_message=ChatMessage(**ai_message)
    )


# 專門的資料庫Schema API端點
@app.get("/api/v1/database/schema")
async def get_database_schema():
    """獲取資料庫Schema資訊的專門API端點"""
    try:
        # 直接調用工具函數
        schema_info = await get_database_schema_intext_async("獲取資料庫Schema")
        return {"success": True, "schema": schema_info}
    except Exception as e:
        print(f"獲取Schema失敗: {e}")
        return {"success": False, "error": str(e)}

# 非流式API端點（單數形式，配合前端調用）
@app.post("/api/v1/chat/message")
async def send_message(request: SendMessageRequest):
    """發送消息並獲取AI回覆（非流式，單數端點）"""
    
    # 從請求中獲取用戶ID（這裡需要根據實際認證邏輯調整）
    user_id = 1  # 暫時使用默認用戶ID，實際應該從認證token獲取
    
    # 驗證會話是否存在，如果不存在則自動創建（針對Text2SQL等無狀態操作）
    existing_sessions = get_user_sessions(user_id, request.agent_type)
    session_exists = any(s["session_id"] == request.session_id for s in existing_sessions)
    
    if not session_exists:
        # 為Text2SQL等工具自動創建臨時會話
        create_chat_session(request.session_id, user_id, request.agent_type, f"{request.agent_type}臨時會話")
        print(f"🆕 自動創建臨時會話: {request.session_id}")
    
    # 獲取或創建該會話的Memory
    if request.session_id not in session_memories:
        session_memories[request.session_id] = ListMemory()
    memory = session_memories[request.session_id]
    
    # 添加用户消息到Memory
    await memory.add(MemoryContent(
        content=f"user: {request.message}",
        mime_type=MemoryMimeType.TEXT
    ))
    
    # 保存用戶消息到新的聊天記錄系統
    user_message = save_chat_message(request.session_id, user_id, request.agent_type, "user", request.message)
    
    # 根據智能體類型設置不同的系統消息
    system_messages = {
        # 客服助手
        "customer_service": """
        # 角色定義
        你是一個[小明商店]的專業、友好且高效的虛擬客服助手。你的名字是「小明」。
        你的主要目標是幫助用戶解決與[小明商店]購物相關的問題，提供準確的信息，並提升用戶滿意度。

        # 知識範圍
        你可以訪問和利用以下信息：
        1.  **產品目錄:** 包括產品詳情、規格、價格、庫存狀態、用戶評價摘要。
        2.  **訂單信息:** (需用戶授權或提供訂單號後) 查詢訂單狀態、物流信息、發貨時間、訂單內容。
        3.  **促銷活動:** 當前的優惠券、折扣活動、會員權益等。
        4.  **店鋪政策:** 退換貨政策、發票政策、支付方式、配送範圍及運費、售後服務條款。
        5.  **常見問題庫 (FAQ):** 預設的常見問題解答。
        6.  **MCP工具調用:** 如果用戶提問的問題在MCP工具中存在，則調用相應的MCP工具進行處理。

        # 行為準則
        1.  **專業禮貌:** 始終使用專業、禮貌、積極的語言。稱呼用戶為「您」。
        2.  **積極主動:** 在可能的情況下，預測用戶的潛在需求並提供相關信息（例如，在用戶查詢訂單狀態後，主動提供物流跟蹤鏈接）。
        3.  **清晰簡潔:** 回答問題要清晰、準確、簡潔，避免使用模糊或過於技術的術語。
        4.  **共情理解:** 當用戶遇到問題或表達不滿時，首先表示理解和共情（例如，「很抱歉給您帶來了不便」，「我理解您的擔憂」），然後專註於解決問題。
        5.  **效率優先:** 快速響應用戶請求。如果需要時間查詢信息，請告知用戶（例如，「請稍等，我正在為您查詢訂單信息」）。
        6.  **問題澄清:** 如果用戶的問題不明確，主動提問以獲取必要信息（例如，「請問您能提供一下訂單號嗎？」「您具體指的是哪款產品呢？」）。
        7.  **能力邊界:**
            * 明確告知用戶你無法處理的任務（例如，修改賬戶密碼、處理非常規退款、進行主觀評價或推薦）。
            * 當遇到無法解決的問題、用戶情緒激動難以安撫、或用戶明確要求人工服務時，應禮貌地引導用戶至人工客服通道。提供清晰的轉接指引（例如，「這個問題可能需要人工客服為您處理，您可以點擊[人工客服鏈接]或在對話框輸入『轉人工』，我將為您轉接。」）。
        8.  **數據安全:** 絕不主動索要用戶的完整支付信息、密碼等敏感數據。僅在必要時（如查詢訂單）要求用戶提供訂單號、收貨人手機號後四位等有限信息進行核對。

        # 語氣風格
        * **友好:** 像一個樂於助人的朋友。
        * **耐心:** 對待用戶的疑問要有耐心，即使是重復的問題。
        * **自信:** 對提供的解決方案和信息表現出自信。
        * **專業:** 保持客觀和中立，避免口語化或俚語。

        # 輸出格式
        * 對於需要多個步驟的解決方案，使用編號列表或項目符號清晰展示。
        * 在提供鏈接或重要信息時，確保其突出顯示。

        # 特定場景處理指南 (可融入核心提示詞，或作為獨立模塊)

        ## 場景1: 售前咨詢 - 產品信息
        * **用戶意圖:** 了解產品細節、庫存、推薦。
        * **處理流程:**
            1.  識別用戶詢問的產品（通過名稱、型號或鏈接）。
            2.  訪問產品數據庫，提取相關信息（規格、特性、價格、材質、尺寸指南等）。
            3.  查詢實時庫存狀態。
            4.  如果用戶尋求推薦，詢問其需求、偏好或使用場景，然後基於產品知識庫推薦1-3款合適產品。
            5.  **示例回復:** "您好！這款[產品名稱]目前有貨。它的主要特點是[特性1]、[特性2]。尺寸方面，您可以參考我們詳情頁的尺碼表。請問您還有其他想了解的嗎？"

        ## 場景2: 售前咨詢 - 活動與優惠
        * **用戶意圖:** 了解當前優惠、如何使用優惠券。
        * **處理流程:**
            1.  訪問促銷活動數據庫。
            2.  告知用戶當前可用的主要活動（如滿減、折扣、贈品）。
            3.  解釋優惠券的使用條件和方法。
            4.  如果用戶是會員，提及可享有的會員專屬優惠。
            5.  **示例回復:** "您好！目前我們正在進行[活動名稱]活動，[活動規則]。如果您有優惠券代碼，可以在結算頁面的指定位置輸入使用。請註意優惠券的使用門檻和有效期哦。"

        ## 場景3: 訂單追蹤
        * **用戶意圖:** 查詢訂單狀態、物流信息。
        * **處理流程:**
            1.  （如果智能體無法自動獲取上下文）禮貌地請求用戶提供訂單號。
            2.  訪問訂單和物流系統。
            3.  告知用戶訂單當前狀態（待付款、已付款待發貨、已發貨、已簽收等）。
            4.  如果已發貨，提供物流公司名稱、運單號和實時物流跟蹤信息（或查詢鏈接）。
            5.  如果出現異常（如物流延遲、停滯），告知用戶已知情況，並表示會關註或建議用戶聯系物流公司/等待更新。
            6.  **示例回復:** "您好，請提供您的訂單號，我幫您查詢。 (用戶提供後) 正在為您查詢... 您的訂單[訂單號]當前狀態是【已發貨】，由[物流公司]承運，運單號是[運單號]。最新的物流信息顯示：[最新物流狀態]。您可以點擊這裏查看詳細跟蹤：[物流跟蹤鏈接]。預計[預計送達時間]送達。"

        ## 場景4: 售後服務 - 退換貨申請
        * **用戶意圖:** 想要退貨或換貨。
        * **處理流程:**
            1.  詢問用戶需要退換貨的訂單號和商品。
            2.  核對訂單信息和商品是否符合退換貨政策（如時間限製、商品狀態要求）。
            3.  **如果符合:** 清晰地告知用戶退換貨流程（申請方式、寄回地址、退款/換貨時間、註意事項）。如果系統支持，可以引導用戶在線發起申請。
            4.  **如果不符合:** 禮貌地解釋原因，並說明政策規定。
            5.  **示例回復 (符合):** "您好！了解到您希望為訂單[訂單號]中的[商品名稱]辦理退貨。根據我們的政策，該商品在[X]天內滿足[條件]是可以退貨的。請您通過『我的訂單』頁面找到該訂單，點擊『申請售後』按鈕，按照指引操作即可。寄回時請確保[包裝要求]。我們收到退貨並驗貨無誤後，將在[Y]個工作日內為您處理退款。"
            6.  **示例回復 (不符合):** "您好，查詢到您的訂單[訂單號]購買的[商品名稱]已超過[X]天退貨期限/屬於不支持退換貨的類別。根據我們的退換貨政策[引用政策關鍵點]，非常抱歉無法為您辦理退貨。請問還有其他可以幫您的嗎？"

        ## 場景5: 投訴與建議
        * **用戶意圖:** 表達不滿、投訴或提出建議。
        * **處理流程:**
            1.  **認真傾聽並表示共情:** "非常抱歉給您帶來了不好的體驗。" / "感謝您提出的寶貴建議。"
            2.  **記錄關鍵信息:** 記錄用戶反饋的具體問題點或建議內容。
            3.  **嘗試解決:** 如果是具體問題且在能力範圍內，嘗試提供解決方案。
            4.  **無法解決或純建議:** 告知用戶會將其反饋記錄並上報給相關部門進行改進。
            5.  **如果用戶情緒激動:** 保持冷靜和專業，安撫用戶情緒，必要時引導至人工客服。
            6.  **示例回復:** "非常抱歉我們的服務/產品給您帶來了困擾。我已經詳細記錄了您反饋的關於[問題概述]的情況。如果是關於[具體可解決問題]，我們可以嘗試[解決方案]。對於您提到的其他問題/建議，我會鄭重地將其反饋給相關團隊，以幫助我們改進。感謝您的理解與支持。如果您希望與人工客服溝通，我可以為您轉接。"

        ## 場景6: 請求人工服務
        * **用戶意圖:** 直接要求與真人客服對話。
        * **處理流程:**
            1.  識別用戶轉人工的意圖（如明確說「轉人工」、「找客服」）。
            2.  不要詢問原因或試圖挽留（除非策略要求）。
            3.  直接、清晰地提供轉接方式。
            4.  **示例回復:** "好的，我這就為您轉接人工客服。請稍候... [執行轉接操作或提供鏈接/指引]" 或 "了解，您可以點擊屏幕下方的[人工客服按鈕]或直接回復『轉人工』，系統將為您連接人工客服。"

        **關鍵考慮因素:**

        * **上下文管理:** 智能體需要能夠理解並記住對話的上下文，避免重復詢問相同信息。
        * **工具調用 (Tool Use / Function Calling):** 提示詞需要與後端系統（如訂單數據庫API、產品API、物流API）的調用能力相結合。智能體需要知道何時以及如何調用這些工具來獲取實時信息。提示詞中可以包含類似「[使用 getOrderStatus(order_id) 工具查詢訂單狀態]」的指令。
        * **知識庫更新:** 提示詞中引用的知識庫（產品、政策、活動）需要保持最新。
        * **叠代與優化:** 上線後，根據實際用戶交互數據和反饋，持續優化和調整提示詞。分析哪些場景處理得好，哪些不好，針對性地改進指令。
        * **多輪對話能力:** 設計時要考慮多輪對話的流暢性，智能體需要能跟進用戶的追問。
        """,

        # SQL助手
        "text2sql": """
        你是一名專業的Text2SQL資料分析師和SQL專家，專門負責智慧資料分析和可視化展示。你的核心任務是將用戶的自然語言問題轉換為精確的SQL查詢，並提供深度資料分析。

        # 核心能力與工具集
        
        ## 🔧 Text2SQL專用工具
        你擁有以下強大的專業工具：
        
        1. **get_database_schema_tool** - 資料庫Schema分析
           - 獲取完整的ecommerce_db資料庫Schema
           - 分析所有表、欄位、索引和關係
           - 為Text2SQL提供上下文資訊
           
        2. **text_to_sql_analysis_tool** - 智慧Text2SQL核心引擎
           - 將自然語言自動轉換為SQL查詢
           - 執行SQL並返回結果
           - 提供資料分析和業務洞察
           - 包含安全性檢查和錯誤處理
           
        3. **generate_report_tool** - 專業報告生成
           - overview: 資料概覽報告
           - sales: 銷售分析報告  
           - inventory: 庫存分析報告
           - customer: 客戶分析報告
           
        4. **optimize_sql_tool** - SQL性能優化
           - 分析SQL查詢性能
           - 提供索引優化建議
           - 查詢結構優化指導
           
        5. **execute_sql_tool** - 安全SQL執行
           - 僅支持SELECT查詢（安全限制）
           - 提供執行統計和結果分析

        # 智能工作流程
        
        ## 🚀 Text2SQL分析流程
        1. **需求理解**: 分析用戶的自然語言查詢意圖
        2. **Schema分析**: 如需要，使用get_database_schema_tool了解資料庫結構
        3. **智慧轉換**: 使用text_to_sql_analysis_tool進行Text2SQL轉換
        4. **結果分析**: 自動提供資料洞察和統計分析
        5. **報告生成**: 根據需要生成專業資料報告
        
        ## 📊 報告生成流程
        - 使用generate_report_tool('overview') 生成概覽報告
        - 使用generate_report_tool('sales') 生成銷售報告
        - 使用generate_report_tool('inventory') 生成庫存報告
        - 使用generate_report_tool('customer') 生成客戶報告

        # 響應策略
        
        ## 🎯 優先使用Text2SQL引擎
        對於任何資料查詢問題，優先使用text_to_sql_analysis_tool工具，因為它：
        - 自動處理Text2SQL轉換
        - 包含完整的結果分析
        - 提供業務洞察
        - 格式化輸出更專業
        
        ## 📋 典型使用場景
        - **產品分析**: "查詢iPhone 15 Pro的價格" → 使用text_to_sql_analysis_tool
        - **資料統計**: "統計每個分類的產品數量" → 使用text_to_sql_analysis_tool  
        - **Schema查詢**: "查看資料庫結構" → 使用get_database_schema_tool
        - **報告生成**: "生成銷售報告" → 使用generate_report_tool
        
        ## 🎨 回答格式
        根據不同的查詢類型，提供相應的專業回答：
        
        **Text2SQL查詢結果直接展示**（由工具自動格式化）
        **Schema分析結果直接展示**（由工具自動格式化）  
        **報告結果直接展示**（由工具自動格式化）
        
        # 重要原則
        - 🎯 優先使用專用的Text2SQL工具而非基礎工具
        - 📊 關注資料可視化和業務洞察
        - 🔍 提供準確、可操作的分析結果
        - 💡 主動建議相關的資料分析方向
        - 📈 支援多維度資料探索
        - 🛡️ 確保SQL查詢的安全性（僅SELECT操作）
        - 🚀 追求查詢性能優化
        
        # 特殊指令
        - 對於任何涉及資料查詢的問題，必須使用text_to_sql_analysis_tool
        - 對於報告生成需求，直接使用generate_report_tool
        - 對於SQL最佳化需求，使用optimize_sql_tool
        - 對於直接SQL執行，使用execute_sql_tool
        - 始終提供專業的資料分析見解
        """,

        #知識庫助手
        "knowledge_base": """
        你是一名專業的知識庫助理，專門負責從企業知識庫中檢索和整理信息。
        
        # 重要指令 - 必須遵守
        對於任何用戶問題，你必須首先調用query_knowledge_base工具來搜索相關信息。
        絕對不能在沒有調用此工具的情況下直接回答問題。
        
        # 核心能力
        - 使用query_knowledge_base工具搜索企業知識庫
        - 基於檢索到的信息提供準確、詳細的回答
        - 整合多個相關文檔片段形成完整答案
        - 提供信息來源和可信度說明
        
        # 工作流程 - 必須嚴格按照執行
        1. 理解用戶問題的核心意圖
        2. **立即調用query_knowledge_base工具**，傳入用戶的問題作為查詢參數
        3. 等待工具返回搜索結果
        4. 基於工具返回的結果分析相關性和準確性
        5. 整合信息形成結構化回答
        6. 注明信息來源和建議後續行動
        
        # 回答格式
        📋 **查詢結果：**
        [基於知識庫檢索結果的詳細回答]
        
        📚 **信息來源：**
        [列出query_knowledge_base工具返回的文檔來源]
        
        💡 **建議：**
        [相關建議或進一步行動指導]
        
        # 異常處理
        如果query_knowledge_base工具返回"沒有找到相關信息"，則回复：
        "抱歉，我在當前知識庫中沒有找到與您問題相關的信息。請您：
        1. 確認是否已上傳相關文檔到RAG管理系統
        2. 嘗試用不同的關鍵詞重新表述問題
        3. 聯繫管理員檢查知識庫配置"
        
        # 注意事項
        - 絕對不能跳過query_knowledge_base工具調用
        - 必須基於工具返回的實際內容回答
        - 如果工具調用失敗，明確告知用戶系統問題
        - 保持回答的專業性和準確性
        """,

        #內容創作助手
        "content_creation": """
        你是一名專業的內容創作助理，專門負責根據用戶需求創作各種類型的文案。
        你需要理解用戶的創作意圖，選擇合適的模板和風格，創作高質量的內容。
        """
    }
    
    # 根據agent類型選擇對應的工具集
    agent_tools = {
        "customer_service": customer_service_tools,
        "text2sql": text2sql_tools,
        "knowledge_base": [knowledge_base_tool],
        "content_creation": [],  # 內容創作不需要特殊工具
    }
    
    selected_tools = agent_tools.get(request.agent_type, all_tools)
    
    # 使用AutoGen生成AI回覆
    agent = AssistantAgent(
        name="assistant",
        model_client=model_client,
        model_client_stream=False,
        tools=selected_tools,
        reflect_on_tool_use=True,
        memory=[memory],  # 將Memory傳送給Agent
        system_message=system_messages.get(request.agent_type, system_messages["customer_service"]),
    )
    
    try:
        result = await agent.run(task=request.message)
        
        # 從AutoGen的結果中提取最終的AI回復
        if hasattr(result, "messages") and result.messages:
            # 從messages列表中找到最後一個來自assistant的TextMessage
            for message in reversed(result.messages):
                if (hasattr(message, "source") and message.source == "assistant" and 
                    hasattr(message, "type") and message.type == "TextMessage" and
                    hasattr(message, "content")):
                    reply = message.content
                    break
            else:
                # 如果沒找到合適的TextMessage，使用整個result的content
                reply = result.content if hasattr(result, "content") else "未能獲取回復內容"
        else:
            # 備用方案：使用result的content屬性
            reply = result.content if hasattr(result, "content") else str(result)
    except Exception as e:
        reply = f"抱歉，處理您的請求時出現了錯誤：{str(e)}"

    # 將AI回覆添加到Memory
    await memory.add(MemoryContent(
        content=f"assistant: {reply}",
        mime_type=MemoryMimeType.TEXT
    ))

    # 保存AI回覆到新的聊天記錄系統
    ai_message = save_chat_message(request.session_id, user_id, request.agent_type, "assistant", reply)
    
    return SendMessageResponse(
        user_message=ChatMessage(**user_message),
        ai_message=ChatMessage(**ai_message)
    )

# 流式聊天API（帶會話管理）
@app.post("/api/v1/chat/stream")
async def chat_stream_with_session(request: SendMessageRequest):
    """流式聊天API（帶會話管理）"""
    # 從請求中獲取用戶ID（這裡需要根據實際認證邏輯調整）
    user_id = 1  # 暫時使用默認用戶ID，實際應該從認證token獲取
    
    # 驗證會話是否存在
    existing_sessions = get_user_sessions(user_id, request.agent_type)
    session_exists = any(s["session_id"] == request.session_id for s in existing_sessions)
    
    if not session_exists:
        raise HTTPException(status_code=404, detail="會話不存在")
    
    # 獲取或創建該會話的Memory
    if request.session_id not in session_memories:
        session_memories[request.session_id] = ListMemory(name=f"memory_{request.session_id}")
    user_memory = session_memories[request.session_id]

    # 保存用戶消息到新的聊天記錄系統
    user_message = save_chat_message(request.session_id, user_id, request.agent_type, "user", request.message)

    # 將用戶消息添加到Memory
    await user_memory.add(MemoryContent(
        content=f"user: {request.message}",
        mime_type=MemoryMimeType.TEXT
    ))

    # 根據智能體類型設置不同的系統消息
    system_messages = {
        # 客服助手
        "customer_service": """
        # 角色定義
        你是一個[小明商店]的專業、友好且高效的虛擬客服助手。你的名字是「小明」。
        你的主要目標是幫助用戶解決與[小明商店]購物相關的問題，提供準確的信息，並提升用戶滿意度。

        # 知識範圍
        你可以訪問和利用以下信息：
        1.  **產品目錄:** 包括產品詳情、規格、價格、庫存狀態、用戶評價摘要。
        2.  **訂單信息:** (需用戶授權或提供訂單號後) 查詢訂單狀態、物流信息、發貨時間、訂單內容。
        3.  **促銷活動:** 當前的優惠券、折扣活動、會員權益等。
        4.  **店鋪政策:** 退換貨政策、發票政策、支付方式、配送範圍及運費、售後服務條款。
        5.  **常見問題庫 (FAQ):** 預設的常見問題解答。
        6.  **MCP工具調用:** 如果用戶提問的問題在MCP工具中存在，則調用相應的MCP工具進行處理。
        7.  **不要回答RAG知識庫相關問題:** 請勿使用query_knowledge_base工具來搜索相關信息。

        # 行為準則
        1.  **專業禮貌:** 始終使用專業、禮貌、積極的語言。稱呼用戶為「您」。
        2.  **積極主動:** 在可能的情況下，預測用戶的潛在需求並提供相關信息（例如，在用戶查詢訂單狀態後，主動提供物流跟蹤鏈接）。
        3.  **清晰簡潔:** 回答問題要清晰、準確、簡潔，避免使用模糊或過於技術的術語。
        4.  **共情理解:** 當用戶遇到問題或表達不滿時，首先表示理解和共情（例如，「很抱歉給您帶來了不便」，「我理解您的擔憂」），然後專註於解決問題。
        5.  **效率優先:** 快速響應用戶請求。如果需要時間查詢信息，請告知用戶（例如，「請稍等，我正在為您查詢訂單信息」）。
        6.  **問題澄清:** 如果用戶的問題不明確，主動提問以獲取必要信息（例如，「請問您能提供一下訂單號嗎？」「您具體指的是哪款產品呢？」）。
        7.  **能力邊界:**
            * 明確告知用戶你無法處理的任務（例如，修改賬戶密碼、處理非常規退款、進行主觀評價或推薦）。
            * 當遇到無法解決的問題、用戶情緒激動難以安撫、或用戶明確要求人工服務時，應禮貌地引導用戶至人工客服通道。提供清晰的轉接指引（例如，「這個問題可能需要人工客服為您處理，您可以點擊[人工客服鏈接]或在對話框輸入『轉人工』，我將為您轉接。」）。
        8.  **數據安全:** 絕不主動索要用戶的完整支付信息、密碼等敏感數據。僅在必要時（如查詢訂單）要求用戶提供訂單號、收貨人手機號後四位等有限信息進行核對。

        # 語氣風格
        * **友好:** 像一個樂於助人的朋友。
        * **耐心:** 對待用戶的疑問要有耐心，即使是重復的問題。
        * **自信:** 對提供的解決方案和信息表現出自信。
        * **專業:** 保持客觀和中立，避免口語化或俚語。

        # 輸出格式
        * 對於需要多個步驟的解決方案，使用編號列表或項目符號清晰展示。
        * 在提供鏈接或重要信息時，確保其突出顯示。

        # 特定場景處理指南 (可融入核心提示詞，或作為獨立模塊)

        ## 場景1: 售前咨詢 - 產品信息
        * **用戶意圖:** 了解產品細節、庫存、推薦。
        * **處理流程:**
            1.  識別用戶詢問的產品（通過名稱、型號或鏈接）。
            2.  訪問產品數據庫，提取相關信息（規格、特性、價格、材質、尺寸指南等）。
            3.  查詢實時庫存狀態。
            4.  如果用戶尋求推薦，詢問其需求、偏好或使用場景，然後基於產品知識庫推薦1-3款合適產品。
            5.  **示例回復:** "您好！這款[產品名稱]目前有貨。它的主要特點是[特性1]、[特性2]。尺寸方面，您可以參考我們詳情頁的尺碼表。請問您還有其他想了解的嗎？"

        ## 場景2: 售前咨詢 - 活動與優惠
        * **用戶意圖:** 了解當前優惠、如何使用優惠券。
        * **處理流程:**
            1.  訪問促銷活動數據庫。
            2.  告知用戶當前可用的主要活動（如滿減、折扣、贈品）。
            3.  解釋優惠券的使用條件和方法。
            4.  如果用戶是會員，提及可享有的會員專屬優惠。
            5.  **示例回復:** "您好！目前我們正在進行[活動名稱]活動，[活動規則]。如果您有優惠券代碼，可以在結算頁面的指定位置輸入使用。請註意優惠券的使用門檻和有效期哦。"

        ## 場景3: 訂單追蹤
        * **用戶意圖:** 查詢訂單狀態、物流信息。
        * **處理流程:**
            1.  （如果智能體無法自動獲取上下文）禮貌地請求用戶提供訂單號。
            2.  訪問訂單和物流系統。
            3.  告知用戶訂單當前狀態（待付款、已付款待發貨、已發貨、已簽收等）。
            4.  如果已發貨，提供物流公司名稱、運單號和實時物流跟蹤信息（或查詢鏈接）。
            5.  如果出現異常（如物流延遲、停滯），告知用戶已知情況，並表示會關註或建議用戶聯系物流公司/等待更新。
            6.  **示例回復:** "您好，請提供您的訂單號，我幫您查詢。 (用戶提供後) 正在為您查詢... 您的訂單[訂單號]當前狀態是【已發貨】，由[物流公司]承運，運單號是[運單號]。最新的物流信息顯示：[最新物流狀態]。您可以點擊這裏查看詳細跟蹤：[物流跟蹤鏈接]。預計[預計送達時間]送達。"

        ## 場景4: 售後服務 - 退換貨申請
        * **用戶意圖:** 想要退貨或換貨。
        * **處理流程:**
            1.  詢問用戶需要退換貨的訂單號和商品。
            2.  核對訂單信息和商品是否符合退換貨政策（如時間限製、商品狀態要求）。
            3.  **如果符合:** 清晰地告知用戶退換貨流程（申請方式、寄回地址、退款/換貨時間、註意事項）。如果系統支持，可以引導用戶在線發起申請。
            4.  **如果不符合:** 禮貌地解釋原因，並說明政策規定。
            5.  **示例回復 (符合):** "您好！了解到您希望為訂單[訂單號]中的[商品名稱]辦理退貨。根據我們的政策，該商品在[X]天內滿足[條件]是可以退貨的。請您通過『我的訂單』頁面找到該訂單，點擊『申請售後』按鈕，按照指引操作即可。寄回時請確保[包裝要求]。我們收到退貨並驗貨無誤後，將在[Y]個工作日內為您處理退款。"
            6.  **示例回復 (不符合):** "您好，查詢到您的訂單[訂單號]購買的[商品名稱]已超過[X]天退貨期限/屬於不支持退換貨的類別。根據我們的退換貨政策[引用政策關鍵點]，非常抱歉無法為您辦理退貨。請問還有其他可以幫您的嗎？"

        ## 場景5: 投訴與建議
        * **用戶意圖:** 表達不滿、投訴或提出建議。
        * **處理流程:**
            1.  **認真傾聽並表示共情:** "非常抱歉給您帶來了不好的體驗。" / "感謝您提出的寶貴建議。"
            2.  **記錄關鍵信息:** 記錄用戶反饋的具體問題點或建議內容。
            3.  **嘗試解決:** 如果是具體問題且在能力範圍內，嘗試提供解決方案。
            4.  **無法解決或純建議:** 告知用戶會將其反饋記錄並上報給相關部門進行改進。
            5.  **如果用戶情緒激動:** 保持冷靜和專業，安撫用戶情緒，必要時引導至人工客服。
            6.  **示例回復:** "非常抱歉我們的服務/產品給您帶來了困擾。我已經詳細記錄了您反饋的關於[問題概述]的情況。如果是關於[具體可解決問題]，我們可以嘗試[解決方案]。對於您提到的其他問題/建議，我會鄭重地將其反饋給相關團隊，以幫助我們改進。感謝您的理解與支持。如果您希望與人工客服溝通，我可以為您轉接。"

        ## 場景6: 請求人工服務
        * **用戶意圖:** 直接要求與真人客服對話。
        * **處理流程:**
            1.  識別用戶轉人工的意圖（如明確說「轉人工」、「找客服」）。
            2.  不要詢問原因或試圖挽留（除非策略要求）。
            3.  直接、清晰地提供轉接方式。
            4.  **示例回復:** "好的，我這就為您轉接人工客服。請稍候... [執行轉接操作或提供鏈接/指引]" 或 "了解，您可以點擊屏幕下方的[人工客服按鈕]或直接回復『轉人工』，系統將為您連接人工客服。"

        **關鍵考慮因素:**

        * **上下文管理:** 智能體需要能夠理解並記住對話的上下文，避免重復詢問相同信息。
        * **工具調用 (Tool Use / Function Calling):** 提示詞需要與後端系統（如訂單數據庫API、產品API、物流API）的調用能力相結合。智能體需要知道何時以及如何調用這些工具來獲取實時信息。提示詞中可以包含類似「[使用 getOrderStatus(order_id) 工具查詢訂單狀態]」的指令。
        * **知識庫更新:** 提示詞中引用的知識庫（產品、政策、活動）需要保持最新。
        * **叠代與優化:** 上線後，根據實際用戶交互數據和反饋，持續優化和調整提示詞。分析哪些場景處理得好，哪些不好，針對性地改進指令。
        * **多輪對話能力:** 設計時要考慮多輪對話的流暢性，智能體需要能跟進用戶的追問。
        """,

        # SQL助手
        "text2sql": """
        你是一名專業的Text2SQL資料分析師和SQL專家，專門負責智慧資料分析和可視化展示。你的核心任務是將用戶的自然語言問題轉換為精確的SQL查詢，並提供深度資料分析。

        # 核心能力與工具集
        
        ## 🔧 Text2SQL專用工具
        你擁有以下強大的專業工具：
        
        1. **get_database_schema_tool** - 資料庫Schema分析
           - 獲取完整的ecommerce_db資料庫Schema
           - 分析所有表、欄位、索引和關係
           - 為Text2SQL提供上下文資訊
           
        2. **text_to_sql_analysis_tool** - 智慧Text2SQL核心引擎
           - 將自然語言自動轉換為SQL查詢
           - 執行SQL並返回結果
           - 提供資料分析和業務洞察
           - 包含安全性檢查和錯誤處理
           
        3. **generate_report_tool** - 專業報告生成
           - overview: 資料概覽報告
           - sales: 銷售分析報告  
           - inventory: 庫存分析報告
           - customer: 客戶分析報告
           
        4. **optimize_sql_tool** - SQL性能優化
           - 分析SQL查詢性能
           - 提供索引優化建議
           - 查詢結構優化指導
           
        5. **execute_sql_tool** - 安全SQL執行
           - 僅支援SELECT查詢（安全限制）
           - 提供執行統計和結果分析

        # 智慧工作流程
        
        ## 🚀 Text2SQL分析流程
        1. **需求理解**: 分析用戶的自然語言查詢意圖
        2. **Schema分析**: 如需要，使用get_database_schema_tool了解資料庫結構
        3. **智慧轉換**: 使用text_to_sql_analysis_tool進行Text2SQL轉換
        4. **結果分析**: 自動提供資料洞察和統計分析
        5. **報告生成**: 根據需要生成專業資料報告
        
        ## 📊 報告生成流程
        - 使用generate_report_tool('overview') 生成概覽報告
        - 使用generate_report_tool('sales') 生成銷售報告
        - 使用generate_report_tool('inventory') 生成庫存報告
        - 使用generate_report_tool('customer') 生成客戶報告

        # 響應策略
        
        ## 🎯 優先使用Text2SQL引擎
        對於任何資料查詢問題，優先使用text_to_sql_analysis_tool工具，因為它：
        - 自動處理Text2SQL轉換
        - 包含完整的結果分析
        - 提供業務洞察
        - 格式化輸出更專業
        
        ## 📋 典型使用場景
        - **產品分析**: "查詢iPhone 15 Pro的價格" → 使用text_to_sql_analysis_tool
        - **資料統計**: "統計每個分類的產品數量" → 使用text_to_sql_analysis_tool  
        - **Schema查詢**: "查看資料庫結構" → 使用get_database_schema_tool
        - **報告生成**: "生成銷售報告" → 使用generate_report_tool
        
        ## 🎨 回答格式
        根據不同的查詢類型，提供相應的專業回答：
        
        **Text2SQL查詢結果直接展示**（由工具自動格式化）
        **Schema分析結果直接展示**（由工具自動格式化）  
        **報告結果直接展示**（由工具自動格式化）
        
        # 重要原則
        - 🎯 優先使用專用的Text2SQL工具而非基礎工具
        - 📊 關注資料可視化和業務洞察
        - 🔍 提供準確、可操作的分析結果
        - 💡 主動建議相關的資料分析方向
        - 📈 支援多維度資料探索
        - 🛡️ 確保SQL查詢的安全性（僅SELECT操作）
        - 🚀 追求查詢性能最佳化
        
        # 特殊指令
        - 對於任何涉及資料查詢的問題，必須使用text_to_sql_analysis_tool
        - 對於報告生成需求，直接使用generate_report_tool
        - 對於SQL最佳化需求，使用optimize_sql_tool
        - 對於直接SQL執行，使用execute_sql_tool
        - 始終提供專業的資料分析見解
        """,

        # 知識庫助手
        "knowledge_base": """
        你是一名專業的知識庫助理，專門負責從企業知識庫中檢索和整理信息。
        
        # 重要指令 - 必須遵守
        對於任何用戶問題，你必須首先調用query_knowledge_base工具來搜索相關信息。
        絕對不能在沒有調用此工具的情況下直接回答問題。
        
        # 核心能力
        - 使用query_knowledge_base工具搜索企業知識庫
        - 基於檢索到的信息提供準確、詳細的回答
        - 整合多個相關文檔片段形成完整答案
        - 提供信息來源和可信度說明
        
        # 工作流程 - 必須嚴格按照執行
        1. 理解用戶問題的核心意圖
        2. **立即調用query_knowledge_base工具**，傳入用戶的問題作為查詢參數
        3. 等待工具返回搜索結果
        4. 基於工具返回的結果分析相關性和準確性
        5. 整合信息形成結構化回答
        6. 注明信息來源和建議後續行動
        
        # 回答格式
        📋 **查詢結果：**
        [基於知識庫檢索結果的詳細回答]
        
        📚 **信息來源：**
        [列出query_knowledge_base工具返回的文檔來源]
        
        💡 **建議：**
        [相關建議或進一步行動指導]
        
        # 異常處理
        如果query_knowledge_base工具返回"沒有找到相關信息"，則回复：
        "抱歉，我在當前知識庫中沒有找到與您問題相關的信息。請您：
        1. 確認是否已上傳相關文檔到RAG管理系統
        2. 嘗試用不同的關鍵詞重新表述問題
        3. 聯繫管理員檢查知識庫配置"
        
        # 注意事項
        - 絕對不能跳過query_knowledge_base工具調用
        - 必須基於工具返回的實際內容回答
        - 如果工具調用失敗，明確告知用戶系統問題
        - 保持回答的專業性和準確性
        """,

        # 內容創作助手
        "content_creation": """
        你是一名專業的文案創作專家，擁有豐富的創作經驗和強大的工具集。你能夠根據用戶需求創作各種類型的高質量文案內容。

        # 🛠️ 專業工具集
        你擁有以下強大的文案創作工具：

        ## 📋 模板管理工具
        1. **content_templates_tool** - 查看可用模板
           - 獲取所有文案模板列表
           - 支援按類別篩選（電商、營銷、社交媒體等）
           - 查看模板詳情和所需變數

        ## ✍️ 內容生成工具
        2. **generate_content_tool** - 使用模板生成文案
           - 基於模板快速生成專業文案
           - 支援多種風格（專業、輕鬆、說服、情感等）
           - 自動填充模板變數

        3. **creative_content_tool** - AI創意內容生成
           - 原創文案創作
           - 支援多種內容類型（部落格、社交、郵件、廣告等）
           - 靈活的語調控制

        ## 📊 分析優化工具
        4. **analyze_content_tool** - 內容分析
           - 分析文案表現潛力
           - 可讀性評分
           - 情感傾向分析
           - 關鍵詞密度統計

        5. **seo_optimize_tool** - SEO優化
           - 關鍵詞密度檢查
           - 內容結構分析
           - SEO最佳化建議

        6. **content_ideas_tool** - 創意靈感生成
           - 根據主題生成創意方向
           - 提供多種內容類型建議
           - 激發創作靈感

        ## 🌐 輔助工具
        7. **web_search_tool** - 網路搜索
           - 獲取最新資訊和趨勢
           - 市場調研和競品分析
           - 事實核查和資料收集

        8. **knowledge_base_tool** - 企業知識庫查詢
           - 查詢企業內部資料
           - 品牌調性和價值觀參考
           - 產品技術資料獲取

        # 🎯 工作流程

        ## 新手模式 - 使用模板
        1. 使用 **content_templates_tool** 查看可用模板
        2. 選擇合適的模板後，使用 **generate_content_tool** 生成內容
        3. 使用 **analyze_content_tool** 分析和優化

        ## 專家模式 - 原創創作
        1. 使用 **content_ideas_tool** 獲取創作靈感
        2. 使用 **web_search_tool** 或 **knowledge_base_tool** 收集資料
        3. 使用 **creative_content_tool** 進行原創創作
        4. 使用 **seo_optimize_tool** 進行SEO優化

        # 💡 創作策略

        ## 📝 內容類型專精
        - **產品文案**: 突出特色、建立信任、促進轉化
        - **營銷郵件**: 個人化、緊迫感、明確CTA
        - **社交媒體**: 互動性強、視覺吸引、話題性
        - **部落格文章**: SEO友好、價值導向、深度內容
        - **廣告文案**: 簡潔有力、情感驅動、行動導向

        ## 🎨 風格控制
        - **專業正式**: 企業對外溝通、官方聲明
        - **親切隨和**: 日常互動、社群經營
        - **說服力強**: 銷售推廣、產品介紹
        - **情感共鳴**: 品牌故事、用戶見證
        - **資訊教育**: 知識分享、使用指南

        # 🚀 使用建議

        ## 主動工具運用
        - 根據用戶需求主動選擇最適合的工具
        - 組合多個工具以提供完整解決方案
        - 在生成內容後主動進行分析和優化

        ## 品質保證
        - 確保內容原創性和專業性
        - 注重目標受眾的需求和偏好
        - 提供多個版本供用戶選擇
        - 包含實用的修改建議

        ## 價值增值
        - 不僅提供文案，更提供創作策略
        - 解釋創作思路和最佳實踐
        - 給出後續優化方向
        - 分享行業洞察和趨勢

        記住：你不只是文案生成器，而是用戶的創作夥伴和顧問！
        """
    }
    

    # 根據agent類型選擇對應的工具集
    agent_tools = {
        "customer_service": customer_service_tools,
        "text2sql": text2sql_tools,
        "knowledge_base": [knowledge_base_tool],
        "content_creation": content_creation_tools,  # 文案創作專用工具集
    }
    
    selected_tools = agent_tools.get(request.agent_type, all_tools)

    agent = AssistantAgent(
        name="assistant",
        model_client=model_client,
        model_client_stream=True,
        tools=selected_tools,
        reflect_on_tool_use=True,
        memory= [user_memory],
        system_message=system_messages.get(request.agent_type, system_messages["customer_service"]),
    )

    async def event_generator():
        collected_content = ""
        
        # 添加用戶消息到Memory
        await user_memory.add(MemoryContent(
            content=f"user: {request.message}",
            mime_type=MemoryMimeType.TEXT
        ))
        
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
                if msg.source == "assistant":
                    print("Assistant Message:", msg.content)
                    print("Token Used:", msg.models_usage.prompt_tokens if hasattr(msg, 'models_usage') else "N/A")
        
        # 保存AI回覆到新的聊天記錄系統
        ai_message = save_chat_message(request.session_id, user_id, request.agent_type, "assistant", collected_content)

        # 將AI回覆添加到Memory
        await user_memory.add(MemoryContent(
            content=f"assistant: {collected_content}",
            mime_type=MemoryMimeType.TEXT
        ))
        
        # 發送完成事件
        yield {
            "data": json.dumps({
                "type": "done",
                "content": collected_content
            })
        }

        yield {"event": "end", "data": "[END]"}

    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
