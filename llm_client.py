import requests
import json
import re
import os
from enum import Enum

class LLMProvider(Enum):
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    DEEPSEEK = "deepseek"

class LLMClient:
    def __init__(self, provider=LLMProvider.OPENROUTER, base_url=None, model=None, api_key=None):
        """
        初始化LLM客户端
        
        Args:
            provider (LLMProvider): LLM提供商，可选Ollama、OpenRouter或DeepSeek
            base_url (str, optional): API基础URL
            model (str, optional): 模型名称
            api_key (str, optional): API密钥(OpenRouter和DeepSeek需要)
        """
        self.provider = provider
        
        # OpenRouter配置 (默认启用)
        if provider == LLMProvider.OPENROUTER:
            self.base_url = base_url or "https://openrouter.ai/api/v1"
            self.model = model or "qwen/qwen-2.5-coder-32b-instruct:free"
            # 从环境变量获取API密钥或使用传入的值
            self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
            if not self.api_key:
                print("警告: 未设置OpenRouter API密钥，请设置OPENROUTER_API_KEY环境变量或在初始化时传入")
            self.api_url = f"{self.base_url}/chat/completions"
            
        # DeepSeek配置 (默认注释)
        # elif provider == LLMProvider.DEEPSEEK:
        #     self.base_url = base_url or "https://api.deepseek.com/v1"
        #     self.model = model or "deepseek-chat"
        #     self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        #     if not self.api_key:
        #         print("警告: 未设置DeepSeek API密钥，请设置DEEPSEEK_API_KEY环境变量或在初始化时传入")
        #     self.api_url = f"{self.base_url}/chat/completions"
            
        # Ollama配置
        else:  # Ollama
            self.base_url = base_url or "http://localhost:11434"
            self.model = model or "qwen2.5-coder:latest"
            self.api_key = None  # Ollama不需要API密钥
            self.api_url = f"{self.base_url}/api/generate"
            print(f"使用Ollama模式，API URL: {self.api_url}, 模型: {self.model}")
    
    def generate_sql(self, user_query, schema):
        """
        根据用户查询和表结构生成SQL
        
        Args:
            user_query (str): 用户的自然语言查询
            schema (str): 数据库表结构
            
        Returns:
            str: 生成的SQL语句
        """
        prompt = f"""
你是一个专业的SQL转换助手，请根据以下表结构和用户的查询，生成相应的SQL语句。
请只返回SQL语句本身，不要添加任何解释、注释或者markdown格式（如```sql或```等标记）。
不要使用反引号、代码块或其他格式标记，只返回可以直接执行的纯SQL语句。

生成SQL时请遵循以下规则：
1. 在SELECT语句中，除了基本的ts_code和stock_name字段外，还应包含用户查询条件中涉及的所有字段
2. 例如，如果用户查询关于"市盈率(pe)"和"换手率(turnover_rate)"的数据，应确保这些字段也包含在SELECT语句中
3. 确保生成的SQL语法正确且高效
4. 请注意：某些技术指标字段需要添加表前缀，具体如下：
   - MACD相关字段: macd_dif → factor_macd_dif, macd_dea → factor_macd_dea, macd → factor_macd
   - KDJ相关字段: kdj_k → factor_kdj_k, kdj_d → factor_kdj_d, kdj_j → factor_kdj_j
   - RSI相关字段: rsi_6 → factor_rsi_6, rsi_12 → factor_rsi_12, rsi_24 → factor_rsi_24
   - 布林带相关字段: boll_upper → factor_boll_upper, boll_mid → factor_boll_mid, boll_lower → factor_boll_lower
   - 价格字段: open → factor_open, high → factor_high, low → factor_low, close → daily_close

### 表结构：
{schema}

### 用户查询：
{user_query}

### 生成的SQL语句（请只输出纯SQL语句，不要有任何其他内容）：
"""
        
        # 根据不同提供商调用不同的API
        if self.provider == LLMProvider.OPENROUTER:
            return self._call_openrouter_api(prompt)
        # elif self.provider == LLMProvider.DEEPSEEK:
        #     return self._call_deepseek_api(prompt)
        else:  # Ollama
            return self._call_ollama_api(prompt)
    
    def _call_openrouter_api(self, prompt):
        """调用OpenRouter API"""
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://text2sql.app",  # 您的应用URL
            "X-Title": "Text2SQL应用"  # 您的应用名称
        }
        
        # 添加更多调试信息
        print(f"发送查询内容类型: {type(prompt)}")
        print(f"发送查询内容前几个字符: {prompt[:30]}")
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个专业的SQL转换助手，只输出SQL语句，不做任何解释。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,  # 低温度，更确定性的输出
            "max_tokens": 500
        }
        
        try:
            # 将编码流程分解，以便更好地调试
            json_str = json.dumps(data, ensure_ascii=False)
            print(f"JSON字符串类型: {type(json_str)}")
            json_bytes = json_str.encode('utf-8')
            print(f"JSON字节类型: {type(json_bytes)}")
            
            # 使用json参数而非data参数，让requests自动处理编码
            response = requests.post(
                self.api_url, 
                json=data,  # 使用json参数自动处理编码
                headers=headers
            )
            
            response.raise_for_status()
            result = response.json()
            sql = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
            # 清理SQL，移除可能的markdown格式和注释
            sql = self._clean_sql(sql)
            
            return sql
        except Exception as e:
            print(f"调用OpenRouter API时出错: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"响应内容: {e.response.text}")
            # 打印更多异常信息
            import traceback
            traceback.print_exc()
            return None
    
    # def _call_deepseek_api(self, prompt):
    #     """调用DeepSeek API"""
    #     headers = {
    #         "Content-Type": "application/json",
    #         "Authorization": f"Bearer {self.api_key}"
    #     }
    #     
    #     data = {
    #         "model": self.model,
    #         "messages": [
    #             {"role": "system", "content": "你是一个专业的SQL转换助手，只输出SQL语句，不做任何解释。"},
    #             {"role": "user", "content": prompt}
    #         ],
    #         "temperature": 0.1
    #     }
    #     
    #     try:
    #         response = requests.post(self.api_url, json=data, headers=headers)
    #         response.raise_for_status()
    #         result = response.json()
    #         sql = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    #         
    #         # 清理SQL，移除可能的markdown格式和注释
    #         sql = self._clean_sql(sql)
    #         
    #         return sql
    #     except Exception as e:
    #         print(f"调用DeepSeek API时出错: {e}")
    #         return None
    
    def _call_ollama_api(self, prompt):
        """调用Ollama API"""
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(self.api_url, json=data)
            response.raise_for_status()
            result = response.json()
            sql = result.get("response", "").strip()
            
            # 清理SQL，移除可能的markdown格式和注释
            sql = self._clean_sql(sql)
            
            return sql
        except Exception as e:
            print(f"调用Ollama API时出错: {e}")
            return None
    
    def _clean_sql(self, sql):
        """清理SQL，移除markdown格式和注释"""
        # 移除markdown代码块标记
        sql = re.sub(r'```(\w*\n?|\n)', '', sql)
        sql = re.sub(r'```$', '', sql)
        
        # 移除SQL注释
        sql = re.sub(r'--.*?(\n|$)', '', sql)
        
        # 移除多余的空行
        sql = re.sub(r'\n\s*\n', '\n', sql)
        
        return sql.strip() 