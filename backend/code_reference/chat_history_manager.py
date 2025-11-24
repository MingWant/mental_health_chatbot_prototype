import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

class ChatHistoryManager:
    """聊天記錄管理器 - 按session_id和user_id分別保存到不同JSON文件"""
    
    def __init__(self, base_dir: str = "chat_history"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # 創建agent_type子目錄
        self.agent_types = [
            "customer_service",
            "text2sql", 
            "knowledge_base",
            "content_creation"
        ]
        
        for agent_type in self.agent_types:
            agent_dir = self.base_dir / agent_type
            agent_dir.mkdir(exist_ok=True)
    
    def _get_chat_file_path(self, session_id: str, user_id: int, agent_type: str) -> Path:
        """獲取聊天記錄文件路徑"""
        # 格式: chat_history/{agent_type}/{user_id}_{session_id}.json
        filename = f"{user_id}_{session_id}.json"
        return self.base_dir / agent_type / filename
    
    def _get_session_file_path(self, user_id: int, agent_type: str) -> Path:
        """獲取會話列表文件路徑"""
        # 格式: chat_history/{agent_type}/sessions_{user_id}.json
        filename = f"sessions_{user_id}.json"
        return self.base_dir / agent_type / filename
    
    def create_session(self, session_id: str, user_id: int, agent_type: str, title: Optional[str] = None) -> Dict[str, Any]:
        """創建新的聊天會話"""
        session_data = {
            "id": self._get_next_session_id(user_id, agent_type),
            "session_id": session_id,
            "user_id": user_id,
            "agent_type": agent_type,
            "title": title or f"{agent_type}會話",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # 保存到對應的會話文件
        sessions = self._load_sessions(user_id, agent_type)
        sessions.append(session_data)
        self._save_sessions(user_id, agent_type, sessions)
        
        print(f"✅ 創建會話: {session_id} (用戶: {user_id}, 類型: {agent_type})")
        return session_data
    
    def get_sessions(self, user_id: int, agent_type: str) -> List[Dict[str, Any]]:
        """獲取用戶的聊天會話列表"""
        return self._load_sessions(user_id, agent_type)
    
    def get_messages(self, session_id: str, user_id: int, agent_type: str) -> List[Dict[str, Any]]:
        """獲取會話的聊天記錄"""
        chat_file = self._get_chat_file_path(session_id, user_id, agent_type)
        
        if not chat_file.exists():
            return []
        
        try:
            with open(chat_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("messages", [])
        except Exception as e:
            print(f"❌ 讀取聊天記錄失敗: {e}")
            return []
    
    def save_message(self, session_id: str, user_id: int, agent_type: str, 
                    role: str, content: str, message_id: Optional[int] = None) -> Dict[str, Any]:
        """保存聊天消息"""
        chat_file = self._get_chat_file_path(session_id, user_id, agent_type)
        
        # 創建聊天記錄目錄（如果不存在）
        chat_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 載入現有聊天記錄
        if chat_file.exists():
            try:
                with open(chat_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                data = {"session_id": session_id, "user_id": user_id, "agent_type": agent_type, "messages": []}
        else:
            data = {"session_id": session_id, "user_id": user_id, "agent_type": agent_type, "messages": []}
        
        # 生成消息ID
        if message_id is None:
            message_id = self._get_next_message_id(data.get("messages", []))
        
        # 創建消息對象
        message = {
            "id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": datetime.now().isoformat()
        }
        
        # 添加消息到聊天記錄
        data["messages"].append(message)
        
        # 保存聊天記錄
        try:
            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存聊天記錄失敗: {e}")
            return message
        
        # 更新會話時間
        self._update_session_time(session_id, user_id, agent_type)
        
        print(f"💾 保存消息: {role} -> {session_id} (用戶: {user_id})")
        return message
    
    def save_user_message(self, session_id: str, user_id: int, agent_type: str, content: str) -> Dict[str, Any]:
        """保存用戶消息"""
        return self.save_message(session_id, user_id, agent_type, "user", content)
    
    def save_ai_message(self, session_id: str, user_id: int, agent_type: str, content: str) -> Dict[str, Any]:
        """保存AI回覆消息"""
        return self.save_message(session_id, user_id, agent_type, "assistant", content)
    
    def _load_sessions(self, user_id: int, agent_type: str) -> List[Dict[str, Any]]:
        """載入會話列表"""
        session_file = self._get_session_file_path(user_id, agent_type)
        
        if not session_file.exists():
            return []
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("sessions", [])
        except Exception as e:
            print(f"❌ 讀取會話列表失敗: {e}")
            return []
    
    def _save_sessions(self, user_id: int, agent_type: str, sessions: List[Dict[str, Any]]):
        """保存會話列表"""
        session_file = self._get_session_file_path(user_id, agent_type)
        
        # 創建目錄（如果不存在）
        session_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "user_id": user_id,
            "agent_type": agent_type,
            "sessions": sessions
        }
        
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存會話列表失敗: {e}")
    
    def _update_session_time(self, session_id: str, user_id: int, agent_type: str):
        """更新會話時間"""
        sessions = self._load_sessions(user_id, agent_type)
        
        for session in sessions:
            if session["session_id"] == session_id:
                session["updated_at"] = datetime.now().isoformat()
                self._save_sessions(user_id, agent_type, sessions)
                break
    
    def _get_next_session_id(self, user_id: int, agent_type: str) -> int:
        """獲取下一個會話ID"""
        sessions = self._load_sessions(user_id, agent_type)
        if not sessions:
            return 1
        return max(session.get("id", 0) for session in sessions) + 1
    
    def _get_next_message_id(self, messages: List[Dict[str, Any]]) -> int:
        """獲取下一個消息ID"""
        if not messages:
            return 1
        return max(message.get("id", 0) for message in messages) + 1
    
    def delete_session(self, session_id: str, user_id: int, agent_type: str) -> bool:
        """刪除會話及其聊天記錄"""
        try:
            # 刪除聊天記錄文件
            chat_file = self._get_chat_file_path(session_id, user_id, agent_type)
            if chat_file.exists():
                chat_file.unlink()
                print(f"🗑️ 刪除聊天記錄: {session_id}")
            
            # 從會話列表中移除
            sessions = self._load_sessions(user_id, agent_type)
            sessions = [s for s in sessions if s["session_id"] != session_id]
            self._save_sessions(user_id, agent_type, sessions)
            
            print(f"✅ 刪除會話: {session_id}")
            return True
        except Exception as e:
            print(f"❌ 刪除會話失敗: {e}")
            return False
    
    def get_chat_stats(self, user_id: int, agent_type: str) -> Dict[str, Any]:
        """獲取聊天統計信息"""
        sessions = self._load_sessions(user_id, agent_type)
        total_messages = 0
        
        for session in sessions:
            messages = self.get_messages(session["session_id"], user_id, agent_type)
            total_messages += len(messages)
        
        return {
            "total_sessions": len(sessions),
            "total_messages": total_messages,
            "agent_type": agent_type,
            "user_id": user_id
        }
    
    def cleanup_old_sessions(self, user_id: int, agent_type: str, days: int = 30):
        """清理舊會話（可選功能）"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        sessions = self._load_sessions(user_id, agent_type)
        
        sessions_to_remove = []
        for session in sessions:
            try:
                session_date = datetime.fromisoformat(session["updated_at"])
                if session_date < cutoff_date:
                    sessions_to_remove.append(session["session_id"])
            except:
                continue
        
        for session_id in sessions_to_remove:
            self.delete_session(session_id, user_id, agent_type)
        
        print(f"🧹 清理了 {len(sessions_to_remove)} 個舊會話")
    
    def export_chat_history(self, session_id: str, user_id: int, agent_type: str, 
                           export_dir: str = "exports") -> Optional[str]:
        """導出聊天記錄"""
        export_path = Path(export_dir)
        export_path.mkdir(exist_ok=True)
        
        messages = self.get_messages(session_id, user_id, agent_type)
        if not messages:
            return None
        
        # 創建導出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_export_{user_id}_{session_id}_{timestamp}.json"
        export_file = export_path / filename
        
        export_data = {
            "export_info": {
                "exported_at": datetime.now().isoformat(),
                "session_id": session_id,
                "user_id": user_id,
                "agent_type": agent_type,
                "total_messages": len(messages)
            },
            "messages": messages
        }
        
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            print(f"📤 導出聊天記錄: {export_file}")
            return str(export_file)
        except Exception as e:
            print(f"❌ 導出聊天記錄失敗: {e}")
            return None

# 創建全局實例
chat_history_manager = ChatHistoryManager()

# 便捷函數
def create_chat_session(session_id: str, user_id: int, agent_type: str, title: Optional[str] = None):
    """創建聊天會話"""
    return chat_history_manager.create_session(session_id, user_id, agent_type, title)

def save_chat_message(session_id: str, user_id: int, agent_type: str, role: str, content: str):
    """保存聊天消息"""
    return chat_history_manager.save_message(session_id, user_id, agent_type, role, content)

def get_chat_messages(session_id: str, user_id: int, agent_type: str):
    """獲取聊天記錄"""
    return chat_history_manager.get_messages(session_id, user_id, agent_type)

def get_user_sessions(user_id: int, agent_type: str):
    """獲取用戶會話列表"""
    return chat_history_manager.get_sessions(user_id, agent_type)



