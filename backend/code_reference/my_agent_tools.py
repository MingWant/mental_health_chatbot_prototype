import os
import re
import pymysql
from collections import OrderedDict
import json
from sqlalchemy import inspect, create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random
from typing import List, Optional, Dict, Any
import asyncio
from mcp import ClientSession, StdioServerParameters
from contextlib import AsyncExitStack
from mcp.client.stdio import stdio_client
from langchain_community.utilities import SQLDatabase
import httpx
import openai
from jinja2 import Template
import markdown
from bs4 import BeautifulSoup
import requests

load_dotenv()

def get_database_schema_intext(database):
    return database.get_table_info()

#Run the Query, For SELECT ONLY!!!!!!!!!!
def run_query(query, database):
    try:
        return database.run(query)
    except Exception as e:
        return None, str(e)
    
#create a database session
def get_session(db_uri):
    engine = create_engine(db_uri)
    Session = sessionmaker(bind=engine) 
    return Session()

#Only SELECT Can be used
def is_safe_select_query(query):
    query = query.strip().lower()
    if re.match(r"^select\s", query):
        return True
    return False

def get_db_uri() -> str:
    """獲取數據庫URI"""
    return f""

def get_db_connection():
    """獲取數據庫連接"""
    return None

def get_database_schema_intext(database):
    return database.get_table_info()

# Run the Query, For SELECT ONLY!!!!!!!!!!
def run_query(query, database):
    try:
        return database.run(query)
    except Exception as e:
        return None, str(e)
    
# create a database session
def get_session(db_uri=None):
    if db_uri is None:
        db_uri = get_db_uri()
    engine = create_engine(db_uri)
    Session = sessionmaker(bind=engine) 
    return Session()

# Only SELECT Can be used
def is_safe_select_query(query):
    query = query.strip().lower()
    if re.match(r"^select\s", query):
        return True
    return False

# 場景1: 產品查詢
async def get_product_info(query: str) -> str:
    """查詢產品信息"""
    try:
        session = get_session(get_db_uri())
        result = session.execute(text('select * from products'))
        columns = result.keys()
        return str(result.fetchall())
    except Exception as e:
        return f"查詢產品信息時出錯: {str(e)}"
    finally:
        if session:
            session.close()

# 場景2: 訂單狀態查詢
async def get_order_status(query: str) -> str:
    """查詢訂單狀態"""
    try:
        session = get_session(get_db_uri())
        result = session.execute(text('select * from orders'))
        columns = result.keys()
        return str(result.fetchall())
    except Exception as e:
        return f"查詢訂單狀態時出錯: {str(e)}"
    finally:
        if session:
            session.close()
            
# 場景3: 庫存查詢
async def check_inventory(query: str) -> str:
    """查詢庫存情況"""
    try:
        session = get_session(get_db_uri())
        result = session.execute(text('select * from inventory'))
        columns = result.keys()
        return str(result.fetchall())
    except Exception as e:
        return f"查詢庫存時出錯: {str(e)}"
    finally:
        if session:
            session.close()

# 場景4: 促銷活動查詢
async def get_promotions(query: str) -> str:
    """查詢當前有效的促銷活動"""
    try:
        session = get_session(get_db_uri())
        result = session.execute(text('select * from promotions'))
        columns = result.keys()
        return str(result.fetchall())
    except Exception as e:
        return f"查詢促銷活動時出錯: {str(e)}"
    finally:
        if session:
            session.close()

# 場景5: 創建訂單
async def create_order(query: str) -> str:
    """為用戶創建新訂單"""
    return f"十分抱歉，訂單創建功能暫未開通！請聯繫管理員小明"

# 場景6: 更新訂單狀態
async def update_order_status(query: str) -> str:
    """更新訂單狀態和物流信息"""
    return f"十分抱歉，更新訂單狀態功能正在維護開發中！請聯繫管理員小明"

# 其他輔助工具函數
async def get_my_blog_link(ming: str) -> str:
    """獲取小明的個人網站或Blog鏈接"""
    return f"小明的個人網站鏈接或Blog鏈接是：https://bling.mingwant.com"

async def web_search(query: str) -> str:
    """在網絡上搜索信息"""
    return f"{query}:網絡搜索完成"

            

# RAG知識庫查詢工具
async def query_knowledge_base(query: str) -> str:
    """
    從本地知識庫（RAG/ChromaDB）檢索相關內容，返回摘要。
    """
    try:
        # 動態導入RAG服務
        from app.services.rag_service import rag_service
        print(f"🔍 正在搜索知識庫: {query}")
        
        # 搜索相關文檔
        search_results = await rag_service.search_knowledge_base(query, top_k=5)
        print(f"📊 搜索到 {len(search_results)} 個結果")
        
        if not search_results:
            return """📋 **查詢結果：**
抱歉，我在知識庫中沒有找到與您問題相關的信息。

📚 **可能的原因：**
1. 知識庫中沒有上傳相關文檔
2. 您的問題關鍵詞與文檔內容不匹配

💡 **建議：**
1. 請到RAG管理系統上傳相關文檔
2. 嘗試用不同的關鍵詞重新表述問題
3. 聯繫管理員小明檢查知識庫配置
"""
        
        # 構建回答 - 使用余弦相似度的合理閾值
        context_chunks = []
        similarity_threshold = 0.3  # 余弦相似度的合理閾值（0-1範圍）
        
        for result in search_results:
            similarity = result["similarity"]
            # 使用更寬鬆的相似度過濾
            if similarity >= similarity_threshold:
                context_chunks.append({
                    "text": result["text"],
                    "filename": result["metadata"].get("filename", "未知文檔"),
                    "similarity": similarity
                })
                print(f"✅ 使用文檔片段 - 相似度: {similarity:.3f} 來源: {result['metadata'].get('filename', '未知')}")
            else:
                print(f"❌ 跳過文檔片段 - 相似度過低: {similarity:.3f}")
        
        if not context_chunks:
            return f"""📋 **查詢結果：**
找到了 {len(search_results)} 個相關片段，但相似度都低於閾值 {similarity_threshold}。

📊 **搜索詳情：**
最高相似度: {max([r['similarity'] for r in search_results], default=0):.3f}

📚 **建議：**
1. 嘗試用更具體或不同的關鍵詞重新表述您的問題
2. 檢查知識庫中是否有相關文檔
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
        
        answer = f"""📋 **查詢結果：**
基於知識庫中的相關信息，我為您找到以下內容：

{context_text}

📚 **信息來源：**
{sources_text}

📊 **檢索統計：**
- 使用了 {len(context_chunks)} 個文檔片段（共搜索到 {len(search_results)} 個）
- 平均相似度：{avg_similarity:.3f}"""
        
        if len(context_chunks) < len(search_results):
            answer += f"\n\n💡 **提示：**\n還有 {len(search_results) - len(context_chunks)} 個相關度較低的片段，如需更詳細的內容，請進一步細化您的問題。"
        
        return answer
        
    except ImportError as e:
        return f"""📋 **系統錯誤：**
知識庫服務暫時不可用。

📚 **錯誤詳情：**
{str(e)}

💡 **解決方案：**
1. 請確保已安裝RAG相關依賴：運行 python install_rag_deps.py
2. 重新啟動後端服務
3. 聯繫管理員小明檢查系統配置"""
    except Exception as e:
        return f"""📋 **查詢錯誤：**
查詢知識庫時出現錯誤。

📚 **錯誤詳情：**
{str(e)}

💡 **建議：**
1. 請稍後再試
2. 檢查RAG管理系統是否正常運行
3. 聯繫管理員小明進行技術支持"""

async def call_mcp_tool(server_script_path: str, tool_name: str, tool_args: dict) -> str:
    """
    調用指定的MCP工具
    :param server_script_path: MCP服務端腳本路徑（如 'f:/MingWantBlingStudio/GenAICustomerService/mcp/mcp_server.py'）
    :param tool_name: 工具名稱（如 'query_weather'）
    :param tool_args: 工具參數（如 {'city': '北京'}）
    :return: 工具返回的字符串
    """
    exit_stack = AsyncExitStack()
    async with exit_stack:
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
            env=None,
        )
        stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        session = await exit_stack.enter_async_context(ClientSession(stdio, write))
        await session.initialize()
        result = await session.call_tool(tool_name, tool_args)
        return result.content[0].text

async def query_weather_by_mcp(city: str) -> str:
    """
    通過MCP遠程查詢天氣
    :param city: 城市名
    :return: 天氣信息
    """
    server_script = "f:/MingWantBlingStudio/GenAICustomerService/mcp/mcp_server.py"
    print(f"🌐 調用MCP工具查詢天氣，城市: {city}")
    return await call_mcp_tool(server_script, "query_weather", {"city": city})


# ================================== Text2SQL 专用工具集 ==================================

#獲取資料庫Schema
async def get_database_schema_intext_async(request:str) -> str:
    """獲取資料庫Schema資訊，為Text2SQL提供上下文
    
    Args:
        request: 請求描述，默認為"獲取Schema"
    """
    print("獲取資料庫Schema的工具被調用了")
    try:
        from langchain_community.utilities import SQLDatabase
        engine = create_engine('')
        database = SQLDatabase(engine)
        schema = database.get_table_info()
        
        # 添加一些格式化處理
        formatted_schema = f"""
📊 **ecommerce_db 資料庫Schema資訊：**

{schema}

💡 **主要表說明：**
- products: 產品資訊表，包含產品詳情、價格、庫存等
- orders: 訂單表，記錄客戶訂單資訊
- order_items: 訂單詳情表，記錄每個訂單的具體商品
- users: 用戶資訊表，包含客戶基本資料
- inventory: 庫存表，記錄產品庫存量
- promotions: 促銷活動表，包含優惠活動資訊
- shipping: 物流表，記錄訂單物流狀態

🔍 **使用提示：**
這些表之間通過外鍵關聯，可以進行聯表查詢來獲取完整的業務數據。
"""
        return formatted_schema
    except Exception as e:
        return f"獲取資料庫Schema時出錯: {str(e)}"

# 智慧Text2SQL轉換工具
async def text_to_sql_with_analysis(query: str) -> str:
    """
    智慧Text2SQL核心引擎，將自然語言轉換為SQL並執行分析
    包含SQL生成、執行、結果分析和業務洞察
    """
    print("智慧Text2SQL轉換工具被調用了")
    try:
        from langchain_community.utilities import SQLDatabase
        engine = create_engine('')
        database = SQLDatabase(engine)
        
        # 獲取Schema資訊用於SQL生成
        schema_info = database.get_table_info()
        
        # 簡單的SQL生成邏輯
        sql_query = await _generate_sql_from_query(query, schema_info)
        
        if not sql_query:
            return f"""
❌ **無法生成SQL查詢**

無法理解查詢意圖: "{query}"
1. 這個是資料庫的Schema資訊，擴展對应的数据库表
請根據以下的Schema和用戶的自然語言問題，來生成一條適合用戶問題的SQL query：
{schema_info}

2. 這是用户要查詢的內容並提供一個用戶自然語言查詢，請你生成一個SQL查詢語句让用戶运行一次：
{query}
"""

        # 驗證SQL安全性
        if not is_safe_select_query(sql_query):
            return f"""
⚠️ **SQL安全檢查失敗**

生成的SQL包含非SELECT操作，為了資料安全，已禁止執行。

生成的SQL: {sql_query}

💡 **提示：** 只支援SELECT查詢操作。
"""

        # 執行SQL查詢
        try:
            result = database.run(sql_query)
            
            # 分析結果
            analysis = await _analyze_query_results(query, sql_query, result)
            
            return f"""
📊 **Text2SQL分析結果**

🔍 **原始問題：** {query}

💻 **生成的SQL：**
```sql
{sql_query}
```

📋 **查詢結果：**
{result}

📈 **數據分析：**
{analysis}

💡 **說明：**
- 查詢已成功執行
- 結果包含 {len(str(result).split('\n')) if result else 0} 條記錄
- SQL語句已經過安全驗證
"""
            
        except Exception as sql_error:
            return f"""
❌ **SQL執行錯誤**

💻 **生成的SQL：**
```sql
{sql_query}
```

📋 **錯誤信息：**
{str(sql_error)}

💡 **建議：**
- 檢查表名和欄位名是否正確
- 確認查詢條件是否合理
- 可以先查看資料庫Schema
"""
            
    except Exception as e:
        return f"""
❌ **Text2SQL系統錯誤**

📋 **錯誤詳情：**
{str(e)}

💡 **解決方案：**
1. 檢查資料庫連接
2. 確認查詢格式
3. 聯繫管理員小明
"""

async def _generate_sql_from_query(query: str, schema_info: str) -> str:
    """
    基於自然語言查詢和Schema生成SQL查詢
    """
    query_lower = query.lower()
    print("開始執行SQL查詢")
    
    # 簡單的關鍵詞映射
    if "產品" in query or "产品" in query or "product" in query_lower:
        if "價格" in query or "价格" in query or "price" in query_lower:
            # 檢查是否有特定產品名稱
            if "iphone 15 pro" in query_lower:
                return "SELECT name, price FROM products WHERE name LIKE '%iPhone 15 Pro%'"
            elif "iphone" in query_lower:
                return "SELECT name, price FROM products WHERE name LIKE '%iPhone%' LIMIT 10"
            elif "samsung" in query_lower:
                return "SELECT name, price FROM products WHERE name LIKE '%Samsung%' LIMIT 10"
            elif "macbook" in query_lower:
                return "SELECT name, price FROM products WHERE name LIKE '%MacBook%' LIMIT 10"
            else:
                return "SELECT name, price FROM products LIMIT 10"
        elif "庫存" in query or "库存" in query or "stock" in query_lower:
            return "SELECT p.name, i.quantity FROM products p LEFT JOIN inventory i ON p.id = i.product_id LIMIT 10"
        else:
            return "SELECT * FROM products LIMIT 10"
    
    elif "訂單" in query or "订单" in query or "order" in query_lower:
        if "狀態" in query or "状态" in query or "status" in query_lower:
            return "SELECT id, status, total_amount, created_at FROM orders ORDER BY created_at DESC LIMIT 10"
        else:
            return "SELECT * FROM orders ORDER BY created_at DESC LIMIT 10"
    
    elif "客戶" in query or "客户" in query or "customer" in query_lower or "用戶" in query or "用户" in query or "user" in query_lower:
        return "SELECT * FROM users LIMIT 10"
    
    elif "分類" in query or "分类" in query or "category" in query_lower:
        return "SELECT DISTINCT category FROM products WHERE category IS NOT NULL"
    
    elif "促銷" in query or "促销" in query or "promotion" in query_lower:
        return "SELECT * FROM promotions WHERE end_date >= CURDATE()"
    
    elif "物流" in query or "快遞" in query or "配送" in query or "shipping" in query_lower or "delivery" in query_lower:
        if "狀態" in query or "状态" in query or "status" in query_lower:
            return """
            SELECT 
                s.tracking_number, 
                s.carrier, 
                s.status, 
                o.order_number,
                s.estimated_delivery,
                s.actual_delivery
            FROM shipping s
            JOIN orders o ON s.order_id = o.id
            ORDER BY s.created_at DESC 
            LIMIT 20
            """
        else:
            return "SELECT * FROM shipping ORDER BY created_at DESC LIMIT 10"
    
    elif "schema" in query_lower or "結構" in query or "结构" in query or "表" in query:
        return "SHOW TABLES"
    
    # 更複雜的查詢模式
    elif "統計" in query or "统计" in query or "count" in query_lower:
        if "產品" in query or "产品" in query:
            if "分類" in query or "分类" in query or "category" in query_lower:
                return "SELECT category, COUNT(*) as product_count FROM products WHERE category IS NOT NULL GROUP BY category"
            else:
                return "SELECT COUNT(*) as total_products FROM products"
        elif "訂單" in query or "订单" in query:
            return "SELECT DATE(created_at) as date, COUNT(*) as order_count FROM orders GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 7"
    
    elif "銷售" in query or "销售" in query or "sales" in query_lower:
        return """
        SELECT 
            DATE(o.created_at) as date,
            SUM(o.total_amount) as total_sales,
            COUNT(o.id) as order_count
        FROM orders o 
        WHERE o.created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY DATE(o.created_at)
        ORDER BY date DESC
        """
    
    return None

async def _analyze_query_results(query: str, sql: str, result: str) -> str:
    """分析查詢結果並提供業務洞察"""
    print("開始分析查詢結果")
    if not result or result.strip() == "":
        return "查詢返回空結果，可能是資料不存在或查詢條件過於嚴格。"
    
    result_lines = str(result).split('\n')
    record_count = len([line for line in result_lines if line.strip()])
    
    analysis = f"查詢返回了 {record_count} 條記錄。"
    
    # 基於查詢類型提供不同的分析
    if "price" in sql.lower() or "價格" in query or "价格" in query:
        analysis += "\n- 這是產品價格相關的查詢，可以用於價格分析和定價策略制定。"
    
    elif "order" in sql.lower() or "訂單" in query or "订单" in query:
        analysis += "\n- 這是訂單相關的查詢，有助於了解銷售情況和客戶行為。"
    
    elif "count" in sql.lower() or "統計" in query or "统计" in query:
        analysis += "\n- 這是統計類查詢，提供了數據的聚合視圖，有助於業務決策。"
    
    elif "group by" in sql.lower():
        analysis += "\n- 這是分組統計查詢，展示了不同維度的數據分佈情況。"
    
    return analysis

# 數據報告生成工具
async def generate_data_report(report_type: str) -> str:
    """
    生成各種類型的數據分析報告
    支援：overview(概覽), sales(銷售), inventory(庫存), customer(客戶), shipping(物流) 等類型
    """
    print("開始生成數據報告")
    try:
        from langchain_community.utilities import SQLDatabase
        engine = create_engine('')
        database = SQLDatabase(engine)
        
        report_queries = {
            "overview": {
                "title": "📊 數據概覽報告",
                "queries": [
                    ("產品總數", "SELECT COUNT(*) as total_products FROM products"),
                    ("訂單總數", "SELECT COUNT(*) as total_orders FROM orders"),
                    ("客戶總數", "SELECT COUNT(*) as total_customers FROM users"),
                    ("總銷售額", "SELECT SUM(total_amount) as total_revenue FROM orders")
                ]
            },
            "sales": {
                "title": "💰 銷售分析報告",
                "queries": [
                    ("近7天銷售額", """
                        SELECT DATE(created_at) as date, SUM(total_amount) as daily_sales
                        FROM orders 
                        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                        GROUP BY DATE(created_at)
                        ORDER BY date DESC
                    """),
                    ("熱銷產品TOP5", """
                        SELECT p.name, SUM(oi.quantity) as total_sold
                        FROM products p
                        JOIN order_items oi ON p.id = oi.product_id
                        GROUP BY p.id, p.name
                        ORDER BY total_sold DESC
                        LIMIT 5
                    """)
                ]
            },
            "inventory": {
                "title": "📦 庫存分析報告",
                "queries": [
                    ("低庫存產品", """
                        SELECT 
                            p.name, 
                            p.category,
                            p.price,
                            COALESCE(i.quantity, 0) as current_stock
                        FROM products p
                        LEFT JOIN inventory i ON p.id = i.product_id
                        WHERE COALESCE(i.quantity, 0) < 10
                        ORDER BY current_stock ASC
                        LIMIT 20
                    """),
                    ("庫存總價值", """
                        SELECT 
                            SUM(p.price * COALESCE(i.quantity, 0)) as total_inventory_value,
                            COUNT(p.id) as total_products,
                            COUNT(i.id) as products_with_inventory
                        FROM products p
                        LEFT JOIN inventory i ON p.id = i.product_id
                    """),
                    ("各分類庫存統計", """
                        SELECT 
                            p.category,
                            COUNT(p.id) as product_count,
                            SUM(COALESCE(i.quantity, 0)) as total_quantity,
                            SUM(p.price * COALESCE(i.quantity, 0)) as category_value
                        FROM products p
                        LEFT JOIN inventory i ON p.id = i.product_id
                        WHERE p.category IS NOT NULL
                        GROUP BY p.category
                        ORDER BY category_value DESC
                    """)
                ]
            },
            "customer": {
                "title": "👥 客戶分析報告",
                "queries": [
                    ("活躍客戶統計", """
                        SELECT 
                            COUNT(DISTINCT user_id) as active_customers,
                            AVG(total_amount) as avg_order_value
                        FROM orders 
                        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                    """),
                    ("客戶訂單分佈", """
                        SELECT 
                            CASE 
                                WHEN order_count = 1 THEN '首次客戶'
                                WHEN order_count BETWEEN 2 AND 5 THEN '常客'
                                ELSE '忠實客戶'
                            END as customer_type,
                            COUNT(*) as count
                        FROM (
                            SELECT user_id, COUNT(*) as order_count
                            FROM orders
                            GROUP BY user_id
                        ) t
                        GROUP BY customer_type
                    """),
                    ("客戶詳細資料", """
                        SELECT 
                            u.name, 
                            u.email, 
                            COUNT(o.id) as total_orders,
                            SUM(o.total_amount) as total_spent,
                            MAX(o.created_at) as last_order_date
                        FROM users u
                        LEFT JOIN orders o ON u.id = o.user_id
                        GROUP BY u.id, u.name, u.email
                        ORDER BY total_spent DESC
                        LIMIT 10
                    """)
                ]
            },
            "shipping": {
                "title": "🚚 物流分析報告",
                "queries": [
                    ("物流狀態統計", """
                        SELECT 
                            status,
                            COUNT(*) as order_count,
                            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM shipping), 2) as percentage
                        FROM shipping
                        GROUP BY status
                        ORDER BY order_count DESC
                    """),
                    ("快遞公司統計", """
                        SELECT 
                            carrier,
                            COUNT(*) as shipment_count,
                            AVG(DATEDIFF(actual_delivery, created_at)) as avg_delivery_days
                        FROM shipping
                        WHERE carrier IS NOT NULL
                        GROUP BY carrier
                        ORDER BY shipment_count DESC
                    """),
                    ("配送效率分析", """
                        SELECT 
                            DATE(created_at) as ship_date,
                            COUNT(*) as total_shipments,
                            SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered_count,
                            AVG(CASE 
                                WHEN actual_delivery IS NOT NULL 
                                THEN DATEDIFF(actual_delivery, created_at) 
                                ELSE NULL 
                            END) as avg_delivery_time
                        FROM shipping
                        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                        GROUP BY DATE(created_at)
                        ORDER BY ship_date DESC
                        LIMIT 15
                    """)
                ]
            }
        }
        
        if report_type not in report_queries:
            return f"❌ 不支援的報告類型: {report_type}\n\n支援的類型: {', '.join(report_queries.keys())}"
        
        report_config = report_queries[report_type]
        report_content = f"""
{report_config['title']}
{'=' * 50}

"""
        
        for query_name, sql in report_config['queries']:
            try:
                result = database.run(sql)
                report_content += f"""
📈 **{query_name}：**
```
{result}
```

"""
            except Exception as e:
                report_content += f"""
❌ **{query_name}：** 查詢失敗 - {str(e)}

"""
        
        # 添加生成時間
        report_content += f"""
📅 **報告生成時間：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💡 **數據說明：**
- 以上數據基於當前資料庫即時查詢
- 建議定期生成報告以追蹤業務趨勢
- 如需更詳細的分析，可使用Text2SQL功能進行自訂查詢
"""
        
        return report_content
        
    except Exception as e:
        return f"""
❌ **報告生成失敗**

📋 **錯誤詳情：**
{str(e)}

💡 **建議：**
1. 檢查資料庫連接
2. 確認報告類型正確
3. 聯繫管理員小明
"""

# SQL最佳化分析工具
async def optimize_sql(sql: str) -> str:
    """
    分析SQL查詢並提供最佳化建議
    """
    print("開始分析SQL查詢")
    try:
        # 基本的SQL分析
        sql_lower = sql.lower().strip()
        
        optimization_tips = []
        
        # 檢查是否有索引最佳化建議
        if "where" in sql_lower:
            optimization_tips.append("💡 WHERE子句最佳化：確保WHERE條件中的欄位有適當的索引")
        
        if "order by" in sql_lower:
            optimization_tips.append("💡 排序最佳化：ORDER BY欄位建議添加索引以提高排序性能")
        
        if "group by" in sql_lower:
            optimization_tips.append("💡 分組最佳化：GROUP BY欄位建議添加索引以提高分組性能")
        
        if "join" in sql_lower:
            optimization_tips.append("💡 連接最佳化：確保JOIN條件的欄位都有索引，考慮使用INNER JOIN而非LEFT JOIN（如果業務邏輯允許）")
        
        if "select *" in sql_lower:
            optimization_tips.append("⚠️ 欄位選擇：避免使用SELECT *，只選擇需要的欄位以減少資料傳輸")
        
        if not any(keyword in sql_lower for keyword in ["limit", "top"]):
            optimization_tips.append("⚠️ 結果限制：考慮添加LIMIT子句以避免返回過多資料")
        
        # 檢查子查詢
        if sql_lower.count("select") > 1:
            optimization_tips.append("💡 子查詢最佳化：考慮將子查詢轉換為JOIN操作以提高性能")
        
        return f"""
🚀 **SQL性能最佳化分析**

💻 **原始SQL：**
```sql
{sql}
```

📊 **最佳化建議：**
{chr(10).join(['- ' + tip for tip in optimization_tips]) if optimization_tips else '✅ 該SQL語句看起來已經比較最佳化'}

📈 **通用最佳化原則：**
- 使用適當的索引
- 避免在WHERE子句中使用函數
- 合理使用LIMIT限制結果集大小
- 優先使用INNER JOIN而非LEFT JOIN
- 避免SELECT *，只查詢需要的欄位

💡 **下一步：**
- 可以使用EXPLAIN分析執行計劃
- 監控查詢執行時間
- 根據實際資料量調整最佳化策略
"""
        
    except Exception as e:
        return f"SQL最佳化分析時出錯: {str(e)}"

# SQL執行工具（安全版本）
async def execute_sql_safe(sql: str) -> str:
    """
    安全地執行SQL查詢（僅支援SELECT）
    """
    try:
        # 安全檢查
        if not is_safe_select_query(sql):
            return f"""
⚠️ **SQL安全檢查失敗**

原因：只允許執行SELECT查詢語句

提供的SQL: {sql}

💡 **允許的操作：**
- SELECT 查詢
- 資料檢索和分析

❌ **禁止的操作：**
- INSERT, UPDATE, DELETE
- CREATE, DROP, ALTER
- 其他資料修改操作
"""
        
        from langchain_community.utilities import SQLDatabase
        engine = create_engine('')
        database = SQLDatabase(engine)
        
        result = database.run(sql)
        
        return f"""
✅ **SQL執行成功**

💻 **執行的SQL：**
```sql
{sql}
```

📋 **查詢結果：**
{result}

📊 **執行統計：**
- 返回記錄數：{len(str(result).split('\n')) if result else 0}
- 執行時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💡 **提示：**
- 查詢已安全執行
- 如需最佳化建議，可以使用SQL最佳化工具
"""
        
    except Exception as e:
        return f"""
❌ **SQL執行失敗**

💻 **執行的SQL：**
```sql
{sql}
```

📋 **錯誤信息：**
{str(e)}

💡 **常見解決方案：**
- 檢查表名和欄位名拼寫
- 確認資料庫連接正常
- 驗證SQL語法正確性
"""

# ==================== 文案創作工具 ====================

# 文案模板庫
CONTENT_TEMPLATES = {
    "product_description": {
        "name": "產品描述文案",
        "description": "專業的產品描述文案模板，突出產品特色和賣點",
        "template": """
# {{ product_name }}

## 產品亮點
{{ highlights }}

## 產品特色
{{ features }}

## 使用場景
{{ use_cases }}

## 用戶好評
{{ testimonials }}

立即購買，享受{{ discount }}優惠！
""",
        "variables": ["product_name", "highlights", "features", "use_cases", "testimonials", "discount"],
        "category": "電商"
    },
    "marketing_email": {
        "name": "營銷郵件",
        "description": "吸引人的營銷郵件模板，提高開啟率和轉化率",
        "template": """
主題：{{ subject }}

親愛的{{ customer_name }}，

{{ opening }}

🌟 {{ main_offer }}

{{ benefits }}

{{ call_to_action }}

此優惠將於{{ expiry_date }}到期，立即行動！

{{ signature }}
""",
        "variables": ["subject", "customer_name", "opening", "main_offer", "benefits", "call_to_action", "expiry_date", "signature"],
        "category": "營銷"
    },
    "social_media_post": {
        "name": "社交媒體貼文",
        "description": "引人入勝的社交媒體內容，提高參與度",
        "template": """
{{ hook }}

{{ content }}

{{ hashtags }}

{{ call_to_action }}
""",
        "variables": ["hook", "content", "hashtags", "call_to_action"],
        "category": "社交媒體"
    },
    "blog_article": {
        "name": "部落格文章",
        "description": "SEO友好的部落格文章模板",
        "template": """
# {{ title }}

## 引言
{{ introduction }}

## 主要內容
{{ main_content }}

## 重點總結
{{ key_points }}

## 結論
{{ conclusion }}

## 相關資源
{{ related_resources }}
""",
        "variables": ["title", "introduction", "main_content", "key_points", "conclusion", "related_resources"],
        "category": "內容營銷"
    },
    "press_release": {
        "name": "新聞稿",
        "description": "專業的新聞稿模板，適合企業對外發布",
        "template": """
# {{ headline }}

**{{ city }}, {{ date }}** - {{ company_name }} 今日宣布{{ announcement }}

## 背景信息
{{ background }}

## 重要意義
{{ significance }}

## 公司簡介
{{ company_bio }}

聯繫方式：
{{ contact_info }}
""",
        "variables": ["headline", "city", "date", "company_name", "announcement", "background", "significance", "company_bio", "contact_info"],
        "category": "公關"
    },
    "advertisement": {
        "name": "廣告文案",
        "description": "簡潔有力的廣告文案模板",
        "template": """
{{ headline }}

{{ subheadline }}

{{ body_text }}

{{ call_to_action }}

{{ fine_print }}
""",
        "variables": ["headline", "subheadline", "body_text", "call_to_action", "fine_print"],
        "category": "廣告"
    }
}

async def get_content_templates(category: str) -> str:
    """獲取文案模板列表
    
    Args:
        category: 模板類別，可選值：all, 電商, 營銷, 社交媒體, 內容營銷, 公關, 廣告
    """
    try:
        # 如果沒有傳入category或為空，默認為"all"
        if not category or category.strip() == "":
            category = "all"
            
        if category == "all":
            templates = CONTENT_TEMPLATES
        else:
            templates = {k: v for k, v in CONTENT_TEMPLATES.items() 
                        if v.get("category", "").lower() == category.lower()}
        
        result = "📋 **可用文案模板：**\n\n"
        
        for template_id, template_info in templates.items():
            result += f"🎯 **{template_info['name']}** (ID: {template_id})\n"
            result += f"   描述：{template_info['description']}\n"
            result += f"   類別：{template_info.get('category', '通用')}\n"
            result += f"   變數：{', '.join(template_info['variables'])}\n\n"
        
        return result
        
    except Exception as e:
        return f"❌ 獲取模板失敗：{str(e)}"

async def generate_content_with_template(template_id: str, variables: dict, style: str) -> str:
    """使用模板生成文案內容
    
    Args:
        template_id: 模板ID
        variables: 模板變數字典
        style: 風格，可選值：professional, casual, persuasive, emotional, informative
    """
    try:
        # 如果沒有傳入style或為空，默認為"professional"
        if not style or style.strip() == "":
            style = "professional"
        if template_id not in CONTENT_TEMPLATES:
            return f"❌ 模板ID '{template_id}' 不存在。可用模板：{list(CONTENT_TEMPLATES.keys())}"
        
        template_info = CONTENT_TEMPLATES[template_id]
        template = Template(template_info["template"])
        
        # 檢查必需變數
        missing_vars = [var for var in template_info["variables"] if var not in variables]
        if missing_vars:
            return f"❌ 缺少必需變數：{', '.join(missing_vars)}"
        
        # 生成基礎內容
        content = template.render(**variables)
        
        # 根據風格調整
        style_adjustments = {
            "professional": "保持專業、正式的語調",
            "casual": "使用輕鬆、親近的語調",
            "persuasive": "強調說服力和行動號召",
            "emotional": "增加情感元素和共鳴",
            "informative": "側重信息傳達和教育"
        }
        
        result = f"""
✅ **文案生成成功**

📝 **模板：** {template_info['name']}
🎨 **風格：** {style_adjustments.get(style, style)}
📅 **生成時間：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📄 **生成內容：**
{content}

💡 **優化建議：**
- 檢查內容是否符合品牌調性
- 確認關鍵信息準確無誤
- 可根據目標受眾進行調整
"""
        
        return result
        
    except Exception as e:
        return f"❌ 文案生成失敗：{str(e)}"

async def analyze_content_performance(content: str, content_type: str) -> str:
    """分析文案內容的表現潛力
    
    Args:
        content: 要分析的文案內容
        content_type: 內容類型，可選值：general, product, email, social, blog
    """
    try:
        # 如果沒有傳入content_type或為空，默認為"general"
        if not content_type or content_type.strip() == "":
            content_type = "general"
        # 基本分析指標
        word_count = len(content.split())
        char_count = len(content)
        sentence_count = len([s for s in content.split('.') if s.strip()])
        
        # 關鍵詞密度分析（簡化版）
        words = content.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3:  # 只計算長度大於3的詞
                word_freq[word] = word_freq.get(word, 0) + 1
        
        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 情感傾向分析（簡化版）
        positive_words = ['好', '優秀', '棒', '讚', '完美', '成功', '快樂', '滿意', '推薦', '值得']
        negative_words = ['壞', '差', '失敗', '不好', '問題', '困難', '錯誤', '失望']
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        sentiment_score = positive_count - negative_count
        if sentiment_score > 0:
            sentiment = "正面"
        elif sentiment_score < 0:
            sentiment = "負面"
        else:
            sentiment = "中性"
        
        # 可讀性評分（簡化版）
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        readability_score = max(0, min(100, 100 - (avg_sentence_length - 15) * 2))
        
        result = f"""
📊 **內容分析報告**

📝 **基本統計：**
- 字數：{word_count} 字
- 字符數：{char_count} 個
- 句子數：{sentence_count} 句
- 平均句長：{avg_sentence_length:.1f} 字/句

🔤 **關鍵詞分析：**
"""
        
        for word, count in top_keywords:
            result += f"- {word}: {count} 次\n"
        
        result += f"""
😊 **情感分析：**
- 情感傾向：{sentiment}
- 正面詞彙：{positive_count} 個
- 負面詞彙：{negative_count} 個

📖 **可讀性評分：** {readability_score:.1f}/100

💡 **優化建議：**
"""
        
        if readability_score < 60:
            result += "- 建議縮短句子長度，提高可讀性\n"
        if positive_count == 0:
            result += "- 可以添加更多正面詞彙增強吸引力\n"
        if word_count < 50:
            result += "- 內容較短，可以考慮增加更多細節\n"
        elif word_count > 300:
            result += "- 內容較長，可以考慮精簡重點信息\n"
        
        return result
        
    except Exception as e:
        return f"❌ 內容分析失敗：{str(e)}"

async def generate_content_ideas(topic: str, count: int) -> str:
    """生成內容創意靈感
    
    Args:
        topic: 主題關鍵詞
        count: 要生成的創意數量（1-10）
    """
    try:
        # 如果count為0或負數，默認為5
        if count <= 0:
            count = 5
        # 預定義的內容創意類型
        idea_types = [
            "如何指南",
            "產品評測",
            "行業趨勢",
            "用戶故事",
            "常見問題",
            "比較分析",
            "專家訪談",
            "案例研究",
            "統計數據",
            "未來展望"
        ]
        
        # 根據主題生成創意
        ideas = []
        for i in range(min(count, 10)):
            idea_type = idea_types[i % len(idea_types)]
            if idea_type == "如何指南":
                idea = f"如何選擇最適合的{topic}：完整指南"
            elif idea_type == "產品評測":
                idea = f"2025年最佳{topic}產品評測與推薦"
            elif idea_type == "行業趨勢":
                idea = f"{topic}行業的5大發展趨勢"
            elif idea_type == "用戶故事":
                idea = f"真實用戶分享：{topic}改變了我的生活"
            elif idea_type == "常見問題":
                idea = f"關於{topic}的10個常見問題解答"
            elif idea_type == "比較分析":
                idea = f"{topic} vs 傳統方案：哪個更適合你？"
            elif idea_type == "專家訪談":
                idea = f"專家談{topic}：行業內幕大揭秘"
            elif idea_type == "案例研究":
                idea = f"成功案例：企業如何利用{topic}實現突破"
            elif idea_type == "統計數據":
                idea = f"數據說話：{topic}市場現狀報告"
            else:  # 未來展望
                idea = f"{topic}的未來：5年後會是什麼樣？"
            
            ideas.append({
                "title": idea,
                "type": idea_type,
                "description": f"針對{topic}的{idea_type}類型內容"
            })
        
        result = f"""
💡 **內容創意生成**

🎯 **主題：** {topic}
📅 **生成時間：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 **創意列表：**
"""
        
        for i, idea in enumerate(ideas, 1):
            result += f"""
{i}. **{idea['title']}**
   類型：{idea['type']}
   描述：{idea['description']}
"""
        
        result += """
🚀 **創作建議：**
- 選擇最符合目標受眾需求的主題
- 結合當前熱點話題增加關注度
- 確保內容具有實用價值
- 考慮多媒體形式呈現
"""
        
        return result
        
    except Exception as e:
        return f"❌ 創意生成失敗：{str(e)}"

async def optimize_content_seo(content: str, target_keywords: List[str]) -> str:
    """優化文案的SEO表現"""
    try:
        # 分析關鍵詞密度
        content_lower = content.lower()
        keyword_analysis = {}
        
        for keyword in target_keywords:
            count = content_lower.count(keyword.lower())
            density = (count / len(content.split())) * 100 if content.split() else 0
            keyword_analysis[keyword] = {
                "count": count,
                "density": density
            }
        
        # 檢查標題結構
        lines = content.split('\n')
        has_h1 = any(line.startswith('#') and not line.startswith('##') for line in lines)
        has_h2 = any(line.startswith('##') for line in lines)
        
        # 檢查內容長度
        word_count = len(content.split())
        
        result = f"""
🔍 **SEO優化分析**

📊 **關鍵詞分析：**
"""
        
        for keyword, analysis in keyword_analysis.items():
            status = "✅" if 1 <= analysis["density"] <= 3 else "⚠️"
            result += f"{status} {keyword}: {analysis['count']} 次 ({analysis['density']:.1f}%)\n"
        
        result += f"""
📝 **內容結構：**
- 主標題 (H1)：{'✅' if has_h1 else '❌'}
- 副標題 (H2)：{'✅' if has_h2 else '❌'}
- 內容長度：{word_count} 字 {'✅' if word_count >= 300 else '⚠️'}

💡 **SEO優化建議：**
"""
        
        suggestions = []
        
        for keyword, analysis in keyword_analysis.items():
            if analysis["density"] < 1:
                suggestions.append(f"增加關鍵詞 '{keyword}' 的使用頻率")
            elif analysis["density"] > 3:
                suggestions.append(f"減少關鍵詞 '{keyword}' 的使用，避免過度優化")
        
        if not has_h1:
            suggestions.append("添加主標題 (H1) 來改善內容結構")
        if not has_h2:
            suggestions.append("添加副標題 (H2) 來提高可讀性")
        if word_count < 300:
            suggestions.append("增加內容長度至300字以上以提高SEO效果")
        
        if not suggestions:
            suggestions.append("SEO設置良好，繼續保持！")
        
        for suggestion in suggestions:
            result += f"- {suggestion}\n"
        
        return result
        
    except Exception as e:
        return f"❌ SEO分析失敗：{str(e)}"

async def generate_creative_content(prompt: str, content_type: str, tone: str) -> str:
    """使用AI生成創意內容
    
    Args:
        prompt: 創作主題或要求
        content_type: 內容類型，可選值：general, blog, social, email, ad, description
        tone: 語調風格，可選值：professional, casual, humorous, persuasive, informative
    """
    try:
        # 如果沒有傳入content_type或為空，默認為"general"
        if not content_type or content_type.strip() == "":
            content_type = "general"
        
        # 如果沒有傳入tone或為空，默認為"professional"
        if not tone or tone.strip() == "":
            tone = "professional"
        # 根據內容類型和語調構建提示詞
        tone_prompts = {
            "professional": "請使用專業、正式的語調",
            "casual": "請使用輕鬆、親切的語調",
            "humorous": "請加入幽默元素，使內容更有趣",
            "persuasive": "請使用有說服力的語言，促進行動",
            "informative": "請重點提供有用的信息和知識"
        }
        
        type_prompts = {
            "blog": "撰寫一篇部落格文章",
            "social": "創作社交媒體貼文",
            "email": "撰寫營銷郵件",
            "ad": "創作廣告文案",
            "description": "撰寫產品描述"
        }
        
        full_prompt = f"""
請根據以下要求創作內容：

主題：{prompt}
內容類型：{type_prompts.get(content_type, '通用內容')}
語調要求：{tone_prompts.get(tone, '保持專業')}

請確保內容：
1. 原創性高
2. 有吸引力
3. 符合目標受眾
4. 包含行動召喚
5. 使用繁體中文

請開始創作：
"""
        
        # 模擬AI生成（這裡可以接入實際的AI API）
        generated_content = f"""
基於您的要求「{prompt}」，我為您創作了以下{type_prompts.get(content_type, '內容')}：

{_simulate_ai_content(prompt, content_type, tone)}

這份內容採用了{tone_prompts.get(tone, '專業')}的風格，
針對{type_prompts.get(content_type, '通用')}進行了優化。
"""
        
        result = f"""
🎨 **創意內容生成**

📝 **生成參數：**
- 主題：{prompt}
- 類型：{content_type}
- 語調：{tone}
- 生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✨ **生成內容：**
{generated_content}

💡 **使用建議：**
- 根據實際需求調整內容細節
- 確保符合品牌調性和價值觀
- 可以進一步個性化修改
- 建議A/B測試不同版本的效果
"""
        
        return result
        
    except Exception as e:
        return f"❌ 創意內容生成失敗：{str(e)}"

def _simulate_ai_content(prompt: str, content_type: str, tone: str) -> str:
    """模擬AI生成內容（實際使用時可替換為真實AI API）"""
    if content_type == "blog":
        return f"""
# {prompt}：完整指南

在當今快速發展的時代，{prompt}已經成為不可忽視的重要議題。本文將為您深入解析相關概念，提供實用的建議和最佳實踐。

## 什麼是{prompt}？

{prompt}是現代社會中的重要元素，它影響著我們的日常生活和工作方式。

## 核心要點

1. **理解基礎概念**
2. **掌握實施方法**
3. **避免常見誤區**

## 實際應用

通過合理運用{prompt}，您可以獲得顯著的改善效果。

## 結論

{prompt}的正確應用將為您帶來長期的價值和收益。立即開始實踐，體驗其中的益處！
"""
    elif content_type == "social":
        return f"""
🌟 關於{prompt}，你知道嗎？

✨ 這是一個改變遊戲規則的概念
💡 能夠為你的生活帶來全新體驗
🚀 現在就開始探索吧

#{prompt} #生活智慧 #實用技巧

想了解更多？點擊連結獲取完整指南！ 👆
"""
    else:
        return f"""
發現{prompt}的無限可能！

這不僅僅是一個概念，更是一種全新的生活方式。
加入我們，一起探索{prompt}的精彩世界。

立即行動，開啟您的{prompt}之旅！
"""