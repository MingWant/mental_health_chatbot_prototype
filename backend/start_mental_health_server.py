#!/usr/bin/env python3
"""
Mental Health Self-care Chatbot - Startup Script
"""

import uvicorn
import os
import sys
from pathlib import Path

def main():
    """Main entry point"""
    print("🧠 Starting Mental Health Self-care Chatbot...")
    
    # 檢查依賴
    check_dependencies()
    
    # 創建必要的目錄
    create_directories()
    
    # 啟動服務器
    start_server()

def check_dependencies():
    """Check required dependencies"""
    print("📋 Checking dependencies...")
    
    required_modules = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "autogen_agentchat",
        "autogen_core",
        "autogen_ext",
        "chromadb",
        "sentence_transformers",
        "aiofiles",
        "jieba"
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n⚠️ Missing the following dependency modules: {', '.join(missing_modules)}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ Dependency check completed")

def create_directories():
    """Create required directories"""
    print("📁 Creating required directories...")
    
    directories = [
        "chat_history",
        "mental_health_uploads",
        "mental_health_chroma_db",
        "exports"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Ensured directory exists: {directory}")

def start_server():
    """Start the server"""
    print("🚀 Starting Mental Health Chatbot server...")
    
    # 配置
    host = "0.0.0.0"
    port = 8001
    reload = True
    
    print(f"📍 Server URL: http://{host}:{port}")
    print("📚 API Docs: http://localhost:8001/docs")
    print("🔧 Health Check: http://localhost:8001/health")
    print("\n🎯 Features:")
    print("- Emotion assessment and analysis")
    print("- Personalized coping strategies")
    print("- Meditation guidance")
    print("- Sleep advice")
    print("- Study wellness tips")
    print("- Self-care plan")
    print("- Mental health resources")
    print("- Mood tracking")
    print("- RAG知識庫支持")
    
    print("\n💡 使用提示:")
    print("- 按 Ctrl+C 停止服務器")
    print("- 查看日誌了解詳細運行狀態")
    print("- 訪問 /docs 查看API文檔")
    
    try:
        uvicorn.run(
            "mental_health_server:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
