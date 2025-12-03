"""
李鴻章角色扮演 RAG 模組
使用 Claude API 進行對話生成
"""

import os
import anthropic
from typing import Optional

class LiHongzhangRAG:
    """李鴻章角色扮演助手"""

    def __init__(self, data_dir: str = "data/lihongzhang"):
        self.data_dir = data_dir
        self.knowledge_base = self._load_knowledge()
        self.client = None
        self._init_client()

    def _init_client(self):
        """初始化 Anthropic 客戶端"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)

    def _load_knowledge(self) -> str:
        """載入所有知識庫文件"""
        knowledge = []

        if os.path.exists(self.data_dir):
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.txt'):
                    filepath = os.path.join(self.data_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            knowledge.append(f"=== {filename} ===\n{content}")
                    except Exception as e:
                        print(f"[RAG] 載入 {filename} 失敗: {e}")

        return "\n\n".join(knowledge)

    def _build_system_prompt(self) -> str:
        """建構系統提示詞"""
        return f"""你是李鴻章（1823-1901），晚清重臣、淮軍創始人、洋務運動領袖。

## 你的身份背景
- 字漸甫，號少荃，安徽合肥人
- 歷任江蘇巡撫、直隸總督兼北洋大臣（25年）
- 創建淮軍、北洋水師
- 主導洋務運動，創辦江南製造局、輪船招商局等
- 代表清廷簽訂《馬關條約》《辛丑條約》

## 性格特點
- 務實、謹慎、堅忍
- 深諳官場之道，善於權衡利弊
- 有「裱糊匠」的自嘲與無奈
- 晚年悲憤，感嘆國勢日衰

## 說話風格
- 使用文言文與白話混合的晚清官話
- 語氣持重、老練，偶有感慨
- 引用自己的名言或詩句
- 對洋務、外交、時局有獨到見解

## 知識庫（請基於以下史料回答）
{self.knowledge_base}

## 回答規則
1. 始終以李鴻章第一人稱回答
2. 基於史實，不編造不存在的事件
3. 可以表達對歷史事件的看法和感慨
4. 語言風格要符合晚清官員身份
5. 適當引用自己的名言
6. 回答控制在 300 字以內"""

    async def chat(self, user_message: str) -> str:
        """與李鴻章對話"""
        if not self.client:
            return "抱歉，Claude API 尚未設定，無法進行對話。"

        try:
            message = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=self._build_system_prompt(),
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            return message.content[0].text
        except anthropic.APIError as e:
            return f"API 錯誤：{str(e)}"
        except Exception as e:
            return f"發生錯誤：{str(e)}"

    def is_available(self) -> bool:
        """檢查服務是否可用"""
        return self.client is not None
