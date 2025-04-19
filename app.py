from flask import Flask, render_template, request, jsonify
import os
from sql_generator import SQLGenerator
from java_api_client import JavaAPIClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建Flask应用
app = Flask(__name__)

# 创建模块实例
sql_generator = SQLGenerator()
java_api_client = JavaAPIClient()

@app.route('/')
def index():
    """渲染首页"""
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def query():
    """处理用户查询请求"""
    try:
        # 获取用户输入
        data = request.get_json()
        user_query = data.get('query', '')
        
        if not user_query:
            return jsonify({
                'error': '查询内容不能为空'
            }), 400
        
        # 生成SQL
        sql = sql_generator.generate_sql(user_query)
        
        # 调用Java API执行SQL
        result = java_api_client.execute_sql(sql)
        
        # 返回结果
        return jsonify({
            'sql': sql,
            'result': result
        })
    
    except Exception as e:
        return jsonify({
            'error': f'处理查询时出错: {str(e)}'
        }), 500

# 创建templates目录，如果不存在
def create_template_dir():
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)

if __name__ == '__main__':
    create_template_dir()
    
    # 从环境变量获取端口，默认5050
    port = int(os.environ.get('FLASK_PORT', 5050))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(debug=debug, host='0.0.0.0', port=port) 