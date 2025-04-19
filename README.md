# Text2SQL 项目

---

## 1. 项目结构建议

```
text2sql/
├── app.py                # Flask主入口
├── llm_client.py         # 本地Ollama大模型API封装
├── sql_generator.py      # 生成SQL的核心逻辑
├── java_api_client.py    # 调用Java接口的封装
├── schema_knowledge.py   # 本地知识库（表结构等）
├── static/               # 前端静态文件
│   └── ...
├── templates/            # 前端页面模板
│   └── index.html
└── requirements.txt
```

---

## 2. 主要功能模块说明

### 2.1 本地知识库（表结构）

- 以`schema_knowledge.py`存储表结构信息，便于大模型理解和生成SQL。

### 2.2 LLM大模型API封装

- `llm_client.py`负责与Ollama本地API通信，传递prompt和schema，返回SQL。

### 2.3 SQL生成逻辑

- `sql_generator.py`负责组织prompt，调用大模型，解析返回的SQL。

### 2.4 Java接口调用

- `java_api_client.py`负责将SQL POST到`http://localhost:8082/system/llm/execute`，并返回结果。

### 2.5 Flask后端

- `app.py`负责路由、前后端交互，接收用户问题，调用上述模块，返回结果。

### 2.6 前端页面

- 参考ChatGPT风格，用户输入问题，展示结果。

---

## 3. 关键代码示例

### 3.1 llm_client.py

```python
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:latest"

def generate_sql(prompt, schema):
    data = {
        "model": MODEL,
        "prompt": f"{schema}\n用户需求：{prompt}\n请生成对应的SQL语句。",
        "stream": False
    }
    resp = requests.post(OLLAMA_URL, json=data)
    return resp.json().get("response", "")
```

### 3.2 java_api_client.py

```python
import requests

JAVA_API_URL = "http://localhost:8082/system/llm/execute"

def execute_sql(sql):
    headers = {"accept": "*/*", "Content-Type": "application/json"}
    resp = requests.post(JAVA_API_URL, data=sql, headers=headers)
    return resp.json()
```

### 3.3 schema_knowledge.py

```python
# 直接存储表结构字符串
STOCK_BUSINESS_SCHEMA = """
CREATE TABLE `stock_business` (
  `ts_code` varchar(20) NOT NULL COMMENT 'TS股票代码',
  ...
  `ma120` decimal(10,3) DEFAULT NULL COMMENT '120日均线'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='股票业务表';
"""
```

### 3.4 app.py

```python
from flask import Flask, request, render_template, jsonify
from llm_client import generate_sql
from java_api_client import execute_sql
from schema_knowledge import STOCK_BUSINESS_SCHEMA

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form["user_input"]
        sql = generate_sql(user_input, STOCK_BUSINESS_SCHEMA)
        result = execute_sql(sql)
        return jsonify({"sql": sql, "result": result})
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
```

### 3.5 前端简述

- `templates/index.html`：一个输入框+提交按钮+结果展示区，风格可参考ChatGPT。

---

## 4. requirements.txt

```
flask
requests
```

---

## 5. 运行说明

1. 启动Ollama本地大模型服务
2. 启动Java接口服务
3. `python app.py` 启动Flask服务
4. 浏览器访问`http://localhost:5000`，输入自然语言问题，获取SQL和查询结果

---

## 部署说明

### 环境要求
- Docker
- Docker Compose
- Linux/Unix 环境

### 部署步骤

1. 克隆项目到服务器
```bash
git clone <项目地址>
cd text2sql
```

2. 配置环境变量
```bash
cp .env.example .env
# 根据需要修改 .env 文件中的配置
```

3. 执行部署脚本
```bash
chmod +x deploy.sh
./deploy.sh
```

4. 检查服务状态
```bash
docker-compose ps
```

5. 查看日志
```bash
docker-compose logs -f
```

### 访问服务
- Web界面：http://服务器IP:5000
- Ollama API：http://服务器IP:11434

### 注意事项
- 确保服务器有足够的磁盘空间（建议至少20GB）
- 确保服务器已安装Docker和Docker Compose
- 首次部署时，模型下载可能需要较长时间
- 如需停止服务，执行：`docker-compose down`

---

## 常见问题解决

### 中文编码问题

如果遇到如下错误：
```
调用OpenRouter API时出错: 'latin-1' codec can't encode characters in position 8-9: ordinal not in range(256)
生成的SQL无效，返回默认查询
```

这是由于中文字符编码问题导致的。解决方法：

1. 使用本地部署的Ollama而非OpenRouter API（推荐）
   - 在`sql_generator.py`中初始化LLMClient时使用Ollama提供商
   - 确保`llm_client.py`中的Ollama相关代码已启用

2. 如果必须使用OpenRouter，确保正确处理编码：
   - 在HTTP请求头中设置 `Content-Type: application/json; charset=utf-8`
   - 使用`json.dumps(data, ensure_ascii=False).encode('utf-8')`确保中文字符正确编码
   - 发送API请求时使用data参数而非json参数：`requests.post(url, data=json_bytes, headers=headers)`

3. 对于Java API调用，同样需要确保正确编码：
   - 使用`sql.encode('utf-8')`确保中文字符正确编码
   - 设置正确的Content-Type头部

---
