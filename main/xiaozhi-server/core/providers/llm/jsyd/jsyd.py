import json
# # from config.logger import setup_logging
import requests
from core.providers.llm.base import LLMProviderBase
from core.utils.util import check_model_key
from typing import Generator, Dict, Any, List, Optional

TAG = __name__
# from loguru import logger

from loguru import logger

class LLMProvider(LLMProviderBase):
    def __init__(self, config: Dict[str, Any]) -> None:
        self.api_key = config["api_key"]
        self.base_url = config.get("base_url")
        self.detail = config.get("detail", False)
        #TODO 这块相当于只存在本地，无法分布式使用，需要修改
        self.session_conversation_map = {}  # 存储session_id和conversation_id的映射
        model_key_msg = check_model_key("jsyd", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)

    def response(self, session_id: str, dialogue: List[Dict[str, Any]], **kwargs) -> Generator[str, None, None]:
        try:
            # 取最后一条用户消息
            last_msg = next(m for m in reversed(dialogue) if m["role"] == "user")
            conversation_id = self.session_conversation_map.get(session_id)
            #system_msg = next(m for m in reversed(dialogue) if m["role"] == "system")

            # 发起流式请求
            payload = {
                "question": {
                    "question": last_msg["content"],
                    "system_prompt": '你叫小为助手，你主要功能是陪聊',
                },
                "user_id": session_id,
            }
            
            # 只有当session_id不为None且不为空时才添加conversation_id
            if conversation_id is not None and conversation_id != "":
                payload["conversation_id"] = conversation_id
            logger.bind(tag=TAG).info(f"payload:{payload}")
            with requests.post(
                f"{self.base_url}/api/coze/chat",
                headers={"supplierKey": f"{self.api_key}", "Content-Type": "application/json"},
                json=payload,
                stream=True,
            ) as r:
                for line in r.iter_lines():
                    if line:
                        try:
                            if line.startswith(b"data: "):
                                if line[6:].decode("utf-8") == "[DONE]":
                                    break

                                data = json.loads(line[6:])
                                #{'code': '200', 'content': '正在进行联网查询，请稍后。', 'conversationId': '', 'status': 'processing'}
                                logger.bind(tag=TAG).info(f"data:{data}")
                                if "code" in data and data["code"] == '200':
                                    if "status" in data and data["status"] == 'done':
                                        conversation_id = data["conversationId"]
                                        self.session_conversation_map[session_id] = (
                                            conversation_id  # 更新映射
                                        )
                                    else:
                                        if (
                                                data
                                                and "content" in data
                                                and data["content"] is not None
                                        ):
                                            content = data["content"]
                                            logger.bind(tag=TAG).info(f"content:{content}")
                                            if "<think>" in content:
                                                continue
                                            if "</think>" in content:
                                                continue
                                            yield content
                        except json.JSONDecodeError as e:
                            continue
                        except Exception as e:
                            continue

        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in response generation: {e}")
            yield "【服务响应异常】"

    def response_with_functions(self, session_id: str, dialogue: List[Dict[str, Any]], functions: Optional[List[Dict[str, Any]]] = None) -> None:
        logger.bind(tag=TAG).error(
            f"fastgpt暂未实现完整的工具调用（function call），建议使用其他意图识别"
        )


if __name__ == '__main__':
    # 测试配置
    api_key = "SUPPsYnAfcM6kK6y87jwtaUg"
    base_url = "http://www.xiaobantoy.com:8019"  # 添加协议前缀
    
    # 创建配置字典
    config = {
        "api_key": api_key,
        "base_url": base_url,
        "detail": False
    }
    
    # 创建LLMProvider实例
    provider = LLMProvider(config)
    
    # 模拟对话历史
    dialogue = [
        {"role": "system", "content": "你是苏晓伴"},
        {"role": "assistant", "content": "你好！有什么我可以帮你的吗？"},
        {"role": "user", "content": "你能告诉我今天的天气怎么样吗？"}
    ]
    
    # 调用response方法进行测试
    print("开始测试response方法:")
    try:
        for response_chunk in provider.response("test_session_123", dialogue):
            print(response_chunk, end="", flush=True)
        print("\n测试完成")
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
