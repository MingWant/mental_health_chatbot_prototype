from autogen_ext.models.openai import OpenAIChatCompletionClient

def _setup_model_client():
    model_config = {
        "model": "claude-sonnet-4-20250514",
        "api_key": "",
        "base_url": "",
        #接口/请求地址： https://xiaoai.plus
        #接口/请求地址： https://xiaoai.plus/v1
        #路由请求地址： https://xiaoai.plus/v1/chat/completions
        "model_info": {
            "vision":False,
            "function_calling": True,
            "json_output": True,
            "family": "unknown", #可以是ModelFamily.GPT4, ModelFamily.R1等
            "structured_output": True,
            "multiple_system_messages": True,  # 支持多个系统消息（Memory功能需要）
            #"max_tokens": 1024,
            #"temperature": 0.7,
        },
    }
    return OpenAIChatCompletionClient(**model_config)

#單利設計模式（只創建一次）
model_client = _setup_model_client()