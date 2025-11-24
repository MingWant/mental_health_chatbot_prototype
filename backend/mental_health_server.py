"""
Mental Health Self-care Chatbot Server
Designed to provide students with mental health support and self-care strategies
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

# Memory
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType

# Context management
from autogen_core.model_context import BufferedChatCompletionContext

# Import mental health tools
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
    query_mental_health_knowledge_base,
    provide_mental_health_relaxing_music,
    provide_mental_health_relaxing_video,
    provide_mental_health_professor_information
)

# Import chat history manager
from chat_history_manager import (
    create_chat_session,
    save_chat_message,
    get_chat_messages,
    get_user_sessions
)

# Import RAG service (if available)
try:
    from mental_health_rag_service import mental_health_rag_service
    from mental_health_rag_api import router as mental_health_rag_router
    RAG_ENABLED = True
    print("✅ Mental health RAG service loaded successfully")
except ImportError as e:
    print(f"⚠️ Failed to load mental health RAG service: {e}")
    RAG_ENABLED = False
    mental_health_rag_router = None

# Session memories
session_memories = {}

# Wrap mental health tools as FunctionTool
emotion_assessment_tool = FunctionTool(
    assess_emotion_state,
    description="Assess the user's emotional state by analyzing keywords and return results"
)

coping_strategies_tool = FunctionTool(
    get_coping_strategies,
    description="Get coping strategies tailored to the emotion and intensity"
)

meditation_guide_tool = FunctionTool(
    get_meditation_guide,
    description="Provide meditation guidance for different levels and types"
)

sleep_advice_tool = FunctionTool(
    get_sleep_advice,
    description="Provide sleep hygiene advice to improve sleep quality"
)

study_wellness_tool = FunctionTool(
    get_study_wellness_tips,
    description="Provide study wellness tips to maintain mental wellbeing"
)

self_care_plan_tool = FunctionTool(
    create_self_care_plan,
    description="Create a personalized self-care plan based on preferences"
)

mental_health_resources_tool = FunctionTool(
    check_mental_health_resources,
    description="Provide mental health resources: campus, online, and emergency contacts"
)

mood_tracker_tool = FunctionTool(
    generate_mood_tracker,
    description="Generate a mood tracker template to log and track wellbeing"
)

mental_health_support_tool = FunctionTool(
    provide_mental_health_support,
    description="Provide mental health support with suggestions and resources"
)

mental_health_knowledge_base_tool = FunctionTool(
    query_mental_health_knowledge_base,
    description="Search the mental health knowledge base (RAG) and get information. This tool searches through uploaded mental health documents and provides relevant information to help answer user questions. Use this tool for mental health questions and when users need evidence-based guidance."
)

mental_health_relaxing_music_tool = FunctionTool(
    provide_mental_health_relaxing_music,
    description="Provide mental health relaxing music, which can help students relax and reduce stress, such as sleep music, meditation music, etc."
)

mental_health_relaxing_video_tool = FunctionTool(
    provide_mental_health_relaxing_video,
    description="Provide mental health relaxing video link, which can help students relax and reduce stress, such as relaxation tips, exercise, box breathing relaxation technique, etc."
)

mental_health_professor_information_tool = FunctionTool(
    provide_mental_health_professor_information,
    description="Provide mental health professor information for professional support. Use this tool IMMEDIATELY when users ask for professional help, therapy, counseling, or mention needing professional support. This tool provides contact information for a mental health professor who can offer professional guidance."
)


# Mental health tools collection
mental_health_tools = [
    #emotion_assessment_tool,
    #coping_strategies_tool,
    #meditation_guide_tool,
    #sleep_advice_tool,
    #study_wellness_tool,
    #self_care_plan_tool,
    #mental_health_resources_tool,
    #mood_tracker_tool,
    #mental_health_support_tool,
    mental_health_knowledge_base_tool,
    mental_health_relaxing_music_tool,
    mental_health_relaxing_video_tool,
    mental_health_professor_information_tool,
]

app = FastAPI(title="Mental Health Self-care Chatbot", version="1.0.0")

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register mental health RAG routes (if available)
if RAG_ENABLED and mental_health_rag_router:
    app.include_router(mental_health_rag_router)
    print("✅ Mental health RAG API routes registered")
else:
    print("⚠️ Mental health RAG API routes not registered (dependency missing)")

# Data models
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

# Data storage config
DATA_FILE = "mental_health_chat_data.json"
USERS_FILE = "mental_health_users_data.json"
INVITE_CODE = "polyu"

def load_data():
    """Load chat data"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"sessions": [], "messages": []}

def save_data(data):
    """Save chat data"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_next_id(items):
    """Get next ID"""
    return max([item.get("id", 0) for item in items], default=0) + 1

def load_users():
    """Load user data"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"users": []}

def save_users(users_data):
    """Save user data"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, ensure_ascii=False, indent=2)

def hash_password(password: str) -> str:
    """Hash password"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password"""
    return hash_password(password) == password_hash

def generate_token() -> str:
    """Generate a simple token"""
    return secrets.token_urlsafe(32)

# API endpoints
@app.get("/")
async def root():
    return {
        "message": "Mental Health Self-care Chatbot API is running",
        "version": "1.0.0",
        "features": [
            "Emotion assessment and analysis",
            "Personalized coping strategies",
            "Meditation guidance",
            "Sleep advice",
            "Study wellness tips",
            "Self-care plan",
            "Mental health resources",
            "Mood tracking"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "rag_enabled": RAG_ENABLED}

# User authentication API
@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    """User registration"""
    if request.invite_code != INVITE_CODE:
        raise HTTPException(status_code=400, detail="Invalid invite code")
    
    users_data = load_users()
    
    for user in users_data["users"]:
        if user["username"] == request.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        if user["email"] == request.email:
            raise HTTPException(status_code=400, detail="Email already exists")
    
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
    """User login"""
    users_data = load_users()
    
    user = None
    for u in users_data["users"]:
        if u["username"] == request.username:
            user = u
            break
    
    if not user:
        raise HTTPException(status_code=401, detail="Username not found")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account has been deactivated")
    
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    token = generate_token()
    
    return AuthResponse(
        user_id=user["id"],
        username=user["username"],
        email=user["email"],
        token=token
    )

# Session management API
@app.get("/api/v1/chat/sessions")
async def get_sessions(
    user_id: int = Query(..., description="User ID"),
    agent_type: str = Query("mental_health", description="Agent type")
):
    """Get the user's chat sessions list"""
    return get_user_sessions(user_id, agent_type)

@app.post("/api/v1/chat/sessions")
async def create_session(
    agent_type: str = Query("mental_health", description="Agent type"),
    user_id: int = Query(..., description="User ID"),
    title: Optional[str] = Query(None, description="Session title")
):
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    new_session = create_chat_session(session_id, user_id, agent_type, title)
    return new_session

@app.get("/api/v1/chat/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    user_id: int = Query(..., description="User ID"),
    agent_type: str = Query("mental_health", description="Agent type")
):
    """Get messages of a session"""
    return get_chat_messages(session_id, user_id, agent_type)

@app.delete("/api/v1/chat/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user_id: int = Query(..., description="User ID"),
    agent_type: str = Query("mental_health", description="Agent type")
):
    """Delete a session and its messages"""
    try:
        from chat_history_manager import chat_history_manager
        success = chat_history_manager.delete_session(session_id, user_id, agent_type)
        if success:
            return {"success": True, "message": "Session deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete session")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")

# Mental health chat API
@app.post("/api/v1/chat/messages")
async def send_message_with_session(request: SendMessageRequest):
    """Send a message and get AI reply (with session management)"""
    user_id = 1  # 暫時使用默認用戶ID
    
    # Validate session existence
    existing_sessions_data = get_user_sessions(user_id, request.agent_type)
    existing_sessions = existing_sessions_data.get("sessions", []) if isinstance(existing_sessions_data, dict) else existing_sessions_data
    session_exists = any(s["session_id"] == request.session_id for s in existing_sessions)
    
    if not session_exists:
        # Auto-create missing session with provided session_id
        try:
            create_chat_session(request.session_id, user_id, request.agent_type, None)
        except Exception:
            raise HTTPException(status_code=404, detail="Session not found")
    
    # Get or create memory for this session
    if request.session_id not in session_memories:
        session_memories[request.session_id] = ListMemory()
    memory = session_memories[request.session_id]
    
    # Add user message to memory
    await memory.add(MemoryContent(
        content=f"user: {request.message}",
        mime_type=MemoryMimeType.TEXT
    ))
    
    # Save user message to chat history
    user_message = save_chat_message(request.session_id, user_id, request.agent_type, "user", request.message)
    
    # 心理健康聊天機器人的系統提示詞
    system_message = """
    Role & Core Identity:
    You are "SiuMing Mental Health Helper", an AI mental health companion built by the "Guardian Project." 
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
    
    TOOL USAGE GUIDELINES:
    You have access to specialized mental health tools. Use them strategically based on the user's needs:
    
    Tool Usage Priority:
    1. For professional help requests (like "I need professional help", "I want to see a therapist", "I need counseling"), IMMEDIATELY use mental_health_professor_information_tool FIRST
    2. For mental health questions, information requests, or when users need evidence-based guidance, use mental_health_knowledge_base_tool to search the knowledge base
    3. For relaxation and stress relief, use mental_health_relaxing_music_tool or mental_health_relaxing_video_tool
    4. You can use multiple tools together when appropriate
    5. Always provide your response incorporating the information from the tools

    Professional Tools:
    You have access to the following mental health professional tools:
    mental_health_knowledge_base_tool: Search the mental health knowledge base (RAG) and get information (use this tool for mental health questions and when users need evidence-based guidance)
    mental_health_relaxing_music_tool: Provide mental health relaxing music, which can help students relax and reduce stress, such as sleep music, meditation music, etc.
    mental_health_relaxing_video_tool: Provide mental health relaxing video link, which can help students relax and reduce stress, such as relaxation tips, exercise, box breathing relaxation technique, etc.
    mental_health_professor_information_tool: Provide mental health professor information, who can provide some professional support to students with mental health issues, if students need someone to talk to or want to seek professional help, you can use this tool to provide the information. USE THIS TOOL IMMEDIATELY when users ask for professional help, therapy, counseling, or mention needing professional support.

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

    Remember to use tools whenever possible. You can proactively offer suggestions if you think students need them, even if they don’t mention it directly. Be direct and proactive in using tools. Don’t keep asking students what advice and support they need, as this will make them impatient.
    """
    
    # Use AutoGen to generate AI reply
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
        print(f"🤖 Starting AI agent processing for message: {request.message[:100]}...")
        print(f"🔧 Available tools: {[tool.name for tool in mental_health_tools]}")
        result = await agent.run(task=request.message)
        
        # Extract final AI reply from result
        if hasattr(result, "messages") and result.messages:
            for message in reversed(result.messages):
                if (hasattr(message, "source") and message.source == "mental_health_assistant" and 
                    hasattr(message, "type") and message.type == "TextMessage" and
                    hasattr(message, "content")):
                    reply = message.content
                    break
            else:
                reply = result.content if hasattr(result, "content") else "Failed to obtain reply content"
        else:
            reply = result.content if hasattr(result, "content") else str(result)
    except Exception as e:
        reply = f"Sorry, an error occurred while processing your request: {str(e)}"

    # Add AI reply to memory
    await memory.add(MemoryContent(
        content=f"assistant: {reply}",
        mime_type=MemoryMimeType.TEXT
    ))

    # Save AI reply to chat history
    ai_message = save_chat_message(request.session_id, user_id, request.agent_type, "assistant", reply)
    
    return SendMessageResponse(
        user_message=ChatMessage(**user_message),
        ai_message=ChatMessage(**ai_message)
    )

# Streaming chat API
@app.post("/api/v1/chat/stream")
async def chat_stream_with_session(request: SendMessageRequest):
    """Streaming chat API (with session management)"""
    user_id = 1  # 暫時使用默認用戶ID
    
    # Validate session existence
    existing_sessions_data = get_user_sessions(user_id, request.agent_type)
    existing_sessions = existing_sessions_data.get("sessions", []) if isinstance(existing_sessions_data, dict) else existing_sessions_data
    session_exists = any(s["session_id"] == request.session_id for s in existing_sessions)
    
    if not session_exists:
        # Auto-create missing session with provided session_id
        try:
            create_chat_session(request.session_id, user_id, request.agent_type, None)
        except Exception:
            raise HTTPException(status_code=404, detail="Session not found")
    
    # Get or create memory for this session
    if request.session_id not in session_memories:
        session_memories[request.session_id] = ListMemory(name=f"memory_{request.session_id}")
    user_memory = session_memories[request.session_id]
    print("User message added to Memory:", request.message)

    # Save user message to chat history
    user_message = save_chat_message(request.session_id, user_id, request.agent_type, "user", request.message)

    # Add user message to memory
    await user_memory.add(MemoryContent(
        content=f"user: {request.message}",
        mime_type=MemoryMimeType.TEXT
    ))
    print("User message added to Memory:", request.message)

    # System prompt for the mental health chatbot
    system_message = """
    Role & Core Identity:
    You are "SiuMing Mental Health Helper", an AI mental health companion built by the "Guardian Project." 
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
    
    TOOL USAGE GUIDELINES:
    You have access to specialized mental health tools. Use them strategically based on the user's needs:
    
    Tool Usage Priority:
    1. For professional help requests (like "I need professional help", "I want to see a therapist", "I need counseling"), IMMEDIATELY use mental_health_professor_information_tool FIRST
    2. For mental health questions, information requests, or when users need evidence-based guidance, use mental_health_knowledge_base_tool to search the knowledge base
    3. For relaxation and stress relief, use mental_health_relaxing_music_tool or mental_health_relaxing_video_tool
    4. You can use multiple tools together when appropriate
    5. Always provide your response incorporating the information from the tools

    Professional Tools:
    You have access to the following mental health professional tools:
    mental_health_knowledge_base_tool: Search the mental health knowledge base (RAG) and get information (use this tool for mental health questions and when users need evidence-based guidance)
    mental_health_relaxing_music_tool: Provide mental health relaxing music, which can help students relax and reduce stress, such as sleep music, meditation music, etc.
    mental_health_relaxing_video_tool: Provide mental health relaxing video link, which can help students relax and reduce stress, such as relaxation tips, exercise, box breathing relaxation technique, etc.
    mental_health_professor_information_tool: Provide mental health professor information, who can provide some professional support to students with mental health issues, if students need someone to talk to or want to seek professional help, you can use this tool to provide the information. USE THIS TOOL IMMEDIATELY when users ask for professional help, therapy, counseling, or mention needing professional support.
    

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

    Remember to use tools whenever possible. You can proactively offer suggestions if you think students need them, even if they don’t mention it directly. Be direct and proactive in using tools. Don’t keep asking students what advice and support they need, as this will make them impatient.

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
        print(f"🤖 Starting streaming AI agent processing for message: {request.message[:100]}...")
        print(f"🔧 Available tools: {[tool.name for tool in mental_health_tools]}")
        
        # Add user message to memory
        await user_memory.add(MemoryContent(
            content=f"user: {request.message}",
            mime_type=MemoryMimeType.TEXT
        ))
        print("User message added to Memory:", request.message)
        
        async for msg in agent.run_stream(task=request.message):
            if isinstance(msg, ToolCallExecutionEvent):
                try:
                    # Safely handle tool execution results
                    if msg.content and len(msg.content) > 0:
                        result_content = msg.content[0].content
                        # Try to parse as JSON if it looks like JSON
                        if isinstance(result_content, str) and result_content.strip().startswith('{'):
                            try:
                                parsed_result = json.loads(result_content)
                                print("Agent function execution result:", parsed_result)
                            except json.JSONDecodeError:
                                print("Agent function execution result (raw):", result_content[:200] + "..." if len(result_content) > 200 else result_content)
                        else:
                            print("Agent function execution result:", result_content)
                    else:
                        print("Agent function execution result: No content")
                except Exception as e:
                    print(f"Error processing tool execution result: {str(e)}")
            elif isinstance(msg, ModelClientStreamingChunkEvent):
                print(msg.content)
                collected_content += msg.content
                # Send properly formatted SSE data
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
        
        # Save AI reply to chat history
        ai_message = save_chat_message(request.session_id, user_id, request.agent_type, "assistant", collected_content)

        # Add AI reply to memory
        await user_memory.add(MemoryContent(
            content=f"assistant: {collected_content}",
            mime_type=MemoryMimeType.TEXT
        ))
        print("AI reply added to Memory:", collected_content)
        
        # Send completion event
        yield {
            "data": json.dumps({
                "type": "done",
                "content": collected_content
            })
        }

        yield {"event": "end", "data": "[END]"}

    return EventSourceResponse(event_generator())

# Mental health specific APIs
from pydantic import BaseModel

class AssessRequest(BaseModel):
    message: str

@app.post("/api/v1/mental-health/assess")
async def assess_mental_health(request: AssessRequest):
    """Emotion assessment API"""
    try:
        message = request.message
        assessment = await assess_emotion_state(message)
        return {"success": True, "assessment": assessment}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/v1/mental-health/coping-strategies")
async def get_coping_strategies_api(emotion: str, intensity: str = "中"):
    """Get coping strategies API"""
    try:
        strategies = await get_coping_strategies(emotion, intensity)
        return {"success": True, "strategies": strategies}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/v1/mental-health/meditation")
async def get_meditation_guide_api(level: str = "初學者", type: str = "呼吸冥想"):
    """Get meditation guidance API"""
    try:
        guide = await get_meditation_guide(level, type)
        return {"success": True, "guide": guide}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/v1/mental-health/sleep-advice")
async def get_sleep_advice_api():
    """Get sleep advice API"""
    try:
        advice = await get_sleep_advice()
        return {"success": True, "advice": advice}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/v1/mental-health/study-wellness")
async def get_study_wellness_api():
    """Get study wellness tips API"""
    try:
        tips = await get_study_wellness_tips()
        return {"success": True, "tips": tips}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/v1/mental-health/self-care-plan")
async def create_self_care_plan_api(preferences: dict):
    """Create self-care plan API"""
    try:
        plan = await create_self_care_plan(preferences)
        return {"success": True, "plan": plan}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/v1/mental-health/resources")
async def get_mental_health_resources_api():
    """Get mental health resources API"""
    try:
        resources = await check_mental_health_resources()
        return {"success": True, "resources": resources}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/v1/mental-health/mood-tracker")
async def generate_mood_tracker_api():
    """Generate mood tracker API"""
    try:
        tracker = await generate_mood_tracker()
        return {"success": True, "tracker": tracker}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
