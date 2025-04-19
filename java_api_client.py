import requests
import json

class JavaAPIClient:
    def __init__(self, api_url="http://localhost:8082/system/llm/execute"):
        """
        初始化Java API客户端
        
        Args:
            api_url (str): Java API的URL
        """
        self.api_url = api_url
    
    def execute_sql(self, sql):
        """
        执行SQL查询
        
        Args:
            sql (str): 要执行的SQL语句
            
        Returns:
            dict: API返回的JSON结果
        """
        headers = {
            "accept": "*/*",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # 确保SQL是干净的，去除可能的多余字符
        sql = sql.strip()
        
        try:
            # 打印SQL调试信息
            print(f"发送SQL: {sql}")
            print(f"SQL类型: {type(sql)}")
            
            # 发送请求
            # 注意：API期望的是原始SQL字符串，不是JSON对象
            response = requests.post(self.api_url, data=sql.encode('utf-8'), headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"调用Java API时出错: {e}")
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    if 'msg' in error_details:
                        error_msg = error_details['msg']
                except:
                    if e.response.text:
                        error_msg = e.response.text
            
            # 打印更详细的错误信息
            import traceback
            traceback.print_exc()
            
            return {
                "msg": f"SQL执行失败: {error_msg}",
                "code": -1,
                "data": []
            } 