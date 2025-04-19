import requests
import json

class EmbeddingModel:
    def __init__(self, base_url="http://localhost:11434", model="bge-large:latest"):
        """
        初始化向量嵌入模型
        
        Args:
            base_url (str): Ollama服务的基础URL
            model (str): 嵌入模型名称
        """
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api/embeddings"
    
    def get_embedding(self, text):
        """
        获取文本的向量嵌入
        
        Args:
            text (str): 输入文本
            
        Returns:
            list: 向量嵌入结果
        """
        data = {
            "model": self.model,
            "prompt": text
        }
        
        try:
            response = requests.post(self.api_url, json=data)
            response.raise_for_status()
            result = response.json()
            return result.get("embedding", [])
        except Exception as e:
            print(f"获取嵌入向量时出错: {e}")
            return []
    
    def calculate_similarity(self, text1, text2):
        """
        计算两段文本的相似度
        
        Args:
            text1 (str): 第一段文本
            text2 (str): 第二段文本
            
        Returns:
            float: 相似度得分 (0-1之间)
        """
        embedding1 = self.get_embedding(text1)
        embedding2 = self.get_embedding(text2)
        
        if not embedding1 or not embedding2:
            return 0.0
        
        # 计算余弦相似度
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = sum(a * a for a in embedding1) ** 0.5
        magnitude2 = sum(b * b for b in embedding2) ** 0.5
        
        if magnitude1 * magnitude2 == 0:
            return 0.0
            
        return dot_product / (magnitude1 * magnitude2) 