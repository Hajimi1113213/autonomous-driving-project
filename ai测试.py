"""
@File    : digital_employee_deployment.py
@Author  : [李彦超/0122202930922]
@Date    : 2026-03-14
@Desc    : 基于大语言模型 (LLM) 的数字自动化办公助手部署脚本。
           本模块封装了对 MiniMax API 的底层调用，并通过 Feishu Webhook
           实现了系统状态与模型推理结果的自动化推送，具备网络重试与异常接管机制。
"""

import json
import time
import logging
import requests
from typing import Optional, Dict, Any

# ==========================================
# 1. 全局配置与日志初始化
# ==========================================
# 配置标准日志输出格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
)
logger = logging.getLogger("DigitalEmployeeSystem")

# 系统环境变量配置 (实际生产环境中应从 .env 或 Vault 读取)
SYS_CONFIG = {
    "MINIMAX_API_KEY": "YOUR_API_KEY_HERE",
    "FEISHU_WEBHOOK": "YOUR_FEISHU_WEBHOOK_HERE",
    "LLM_MODEL_VERSION": "abab6.5s-chat",
    "MAX_RETRIES": 3,
    "RETRY_DELAY": 2.0
}


# ==========================================
# 2. 核心业务类定义
# ==========================================
class LLMEngine:
    """大语言模型推理引擎驱动类"""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.minimax.chat/v1/text/chatcompletion_v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def request_reasoning(self, prompt: str) -> Optional[str]:
        """
        向 LLM 发起推理请求，包含异常捕获与指数退避重试机制。

        :param prompt: 输入的系统提示词或用户问题
        :return: 模型生成的文本内容，若最终失败则返回 None
        """
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "name": "user", "content": prompt}]
        }

        for attempt in range(1, SYS_CONFIG["MAX_RETRIES"] + 1):
            try:
                logger.info(f"正在建立 LLM 推理连接 (尝试 {attempt}/{SYS_CONFIG['MAX_RETRIES']})...")
                response = requests.post(
                    self.endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=15
                )
                response.raise_for_status()
                res_data = response.json()

                if res_data.get("choices"):
                    logger.info("LLM 推理完成，成功获取响应流。")
                    return res_data["choices"][0]["message"]["content"]
                else:
                    logger.warning(f"接口返回异常数据格式: {res_data}")

            except requests.exceptions.RequestException as e:
                logger.error(f"网络通信层发生错误: {e}")

            if attempt < SYS_CONFIG["MAX_RETRIES"]:
                logger.info(f"等待 {SYS_CONFIG['RETRY_DELAY']} 秒后启动重试机制...")
                time.sleep(SYS_CONFIG["RETRY_DELAY"])

        logger.error("达到最大重试次数，LLM 引擎调用彻底失败。")
        return None


class FeishuNotifier:
    """飞书企业级消息推送模块"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.headers = {"Content-Type": "application/json"}

    def push_message(self, title: str, content: str) -> bool:
        """
        将格式化内容推送到指定的飞书终端。

        :param title: 消息区块标题
        :param content: 消息主体内容
        :return: 推送是否成功
        """
        formatted_text = f"📌 【{title}】\n{'-' * 30}\n{content}"
        payload = {
            "msg_type": "text",
            "content": {"text": formatted_text}
        }

        try:
            logger.info("正在将报告数据序列化并推送到 Feishu Webhook 节点...")
            response = requests.post(
                self.webhook_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                logger.info("企业微信/飞书节点推送成功！")
                return True
            else:
                logger.warning(f"推送遭遇异常状态码: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"消息投递过程中发生致命错误: {e}")
            return False


# ==========================================
# 3. 主程序入口与业务编排
# ==========================================
def main():
    """系统主控函数"""
    logger.info("初始化自动化办公助手部署脚本...")

    # 实例化各核心组件
    llm_engine = LLMEngine(SYS_CONFIG["MINIMAX_API_KEY"], SYS_CONFIG["LLM_MODEL_VERSION"])
    notifier = FeishuNotifier(SYS_CONFIG["FEISHU_WEBHOOK"])

    # 定义测试业务场景 (在此验证算法与系统集成度)
    test_task_query = "你好，请用一段精炼的学术语言，总结一下 A* 算法在复杂自动驾驶路网进行路径规划时的核心优势及其启发式函数的工程意义。"

    logger.info(f"分配系统任务: {test_task_query}")

    # 1. 触发 LLM 思考
    result = llm_engine.request_reasoning(test_task_query)

    # 2. 结果校验与推送编排
    if result:
        push_status = notifier.push_message("数字员工-自动驾驶算法分析简报", result)
        if push_status:
            logger.info("✅ 整个业务管线执行完毕，系统状态正常。")
        else:
            logger.error("❌ LLM 推理成功，但在最终的推送环节发生阻塞。")
    else:
        error_msg = "告警：大模型节点响应超时或鉴权拒绝，请检查系统网络或 Token 状态。"
        logger.error(error_msg)
        notifier.push_message("系统严重告警", error_msg)


if __name__ == "__main__":
    main()