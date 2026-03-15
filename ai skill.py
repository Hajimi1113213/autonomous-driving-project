"""
@File    : its_v2x_agent.py
@Author  : [李彦超/0122202930922]
@Date    : 2026-03-14
@Desc    : 面向智能交通系统的 V2X 车路协同数字专家。
           支持 Function Calling，能够动态获取交叉口信号灯相位与实时拥堵指数，
           并结合自动驾驶算法生成协同决策建议。
"""

import json
import time
import logging
import requests

# ==========================================
# 1. 系统配置与日志
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("ITS_Agent")

MINIMAX_API_KEY = "YOUR_API_KEY_HERE"
FEISHU_WEBHOOK = "YOUR_FEISHU_WEBHOOK_HERE"


# ==========================================
# 2. 交通工程专属 Skill (车路协同 V2X 接口)
# ==========================================
def get_v2x_intersection_status(intersection_id: str) -> str:
    """
    [核心 Skill] 模拟车路协同(V2X)系统，查询指定交叉口的实时信号灯相位与交通流数据。
    """
    logger.info(f"🚦 触发 V2X Skill: 正在向城市交通大脑请求 [{intersection_id}] 交叉口的实时流控数据...")
    time.sleep(1.5)  # 模拟 5G/V2X 通信延迟

    # 模拟从交通控制中心获取的实时 JSON 数据
    mock_traffic_data = {
        "intersection_id": intersection_id,
        "current_phase": "红灯",  # 当前信号灯相位
        "countdown_seconds": 45,  # 剩余倒计时（秒）
        "congestion_index": 4.2,  # 拥堵指数 (0-5，4以上为严重拥堵)
        "average_speed_kmh": 12.5,  # 交叉口各进口道平均通行车速
        "control_strategy": "自适应绿波控制介入中"
    }
    logger.info(f"🚦 V2X 握手成功，获取路侧单元(RSU)数据: {mock_traffic_data}")
    return json.dumps(mock_traffic_data, ensure_ascii=False)


# 注册本地工具
AVAILABLE_TOOLS = {
    "get_v2x_intersection_status": get_v2x_intersection_status
}

# 严格遵循 OpenAI 工具描述规范的 Schema
LLM_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_v2x_intersection_status",
            "description": "获取指定城市交叉口的实时车路协同(V2X)数据，包括信号灯相位、倒计时、拥堵指数等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "intersection_id": {
                        "type": "string",
                        "description": "交叉口的标准化编号，例如 Jiedaokou-001 或 Guanshan-Avenue-005"
                    }
                },
                "required": ["intersection_id"]
            }
        }
    }
]


# ==========================================
# 3. 智能交通 Agent 核心引擎
# ==========================================
class ITSAgentEngine:
    def __init__(self, api_key: str):
        self.endpoint = "https://api.minimax.chat/v1/text/chatcompletion_v2"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def chat_with_tools(self, user_prompt: str) -> str:
        messages = [{"role": "user", "name": "user", "content": user_prompt}]

        payload = {
            "model": "abab6.5s-chat",
            "messages": messages,
            "tools": LLM_TOOLS_SCHEMA
        }

        logger.info("🤖 智能驾驶中枢：评估路线策略，检查是否需要调用路侧单元(RSU)数据...")
        response = requests.post(self.endpoint, headers=self.headers, json=payload).json()
        response_msg = response["choices"][0]["message"]

        if "tool_calls" in response_msg and response_msg["tool_calls"]:
            tool_call = response_msg["tool_calls"][0]
            func_name = tool_call["function"]["name"]
            func_args = json.loads(tool_call["function"]["arguments"])

            logger.info(f"🤖 中枢决策：前方路况未知，下发 V2X 查询指令 [{func_name}]，参数: {func_args}")

            messages.append(response_msg)

            # 执行交通查询 Skill
            if func_name in AVAILABLE_TOOLS:
                function_result = AVAILABLE_TOOLS[func_name](**func_args)
            else:
                function_result = json.dumps({"error": "V2X node offline"})

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "name": func_name,
                "content": function_result
            })

            logger.info("🤖 智能驾驶中枢：已融合实时路况，正在重新计算行驶建议...")
            payload["messages"] = messages
            payload.pop("tools")

            final_response = requests.post(self.endpoint, headers=self.headers, json=payload).json()
            return final_response["choices"][0]["message"]["content"]
        else:
            return response_msg["content"]


def send_to_feishu(text: str):
    logger.info("🚀 正在将交通管控简报推送至飞书终端...")
    payload = {"msg_type": "text", "content": {"text": f"🌐 【车路协同(V2X)控制中心汇报】\n{'-' * 30}\n{text}"}}
    requests.post(FEISHU_WEBHOOK, headers={"Content-Type": "application/json"}, json=payload)
    logger.info("✅ 飞书推送成功！")


# ==========================================
# 4. 业务主线程
# ==========================================
if __name__ == "__main__":
    # 极具交通工程专业度的测试指令
    test_task = "自动驾驶测试车正接近 Jiedaokou-001 交叉口。请帮我查一下该路口的实时 V2X 数据，并结合 A* 算法的代价函数（Cost Function），告诉我测试车现在应该保持原路径等待，还是立刻重新规划路线？"

    agent = ITSAgentEngine(MINIMAX_API_KEY)
    final_report = agent.chat_with_tools(test_task)

    send_to_feishu(f"【车载系统指令】{test_task}\n\n【云端控制中心反馈】\n{final_report}")
    print("\n🎉 交通大脑部署完毕！快去飞书查看自动驾驶的协同决策！")