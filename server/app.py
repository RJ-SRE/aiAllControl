"""
Flask Web服务器 - Flask Web Server

提供Web界面和API服务,支持实时WebSocket通信。

主要功能:
1. 静态文件服务 - 提供前端HTML/CSS/JS
2. REST API - 聊天、系统信息等接口
3. WebSocket - 实时消息推送

使用示例:
    python server/app.py
    # 访问 http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.ai_client import create_ai_client
from infrastructure.conversation import ConversationManager
from infrastructure.tools import get_tool_schemas
from infrastructure.tool_executor import ToolExecutor
from infrastructure.logger import logger

app = Flask(__name__, 
            static_folder='../frontend/static',
            template_folder='../frontend/templates')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

conversation_manager = ConversationManager()
tool_executor = ToolExecutor()


@app.route('/')
def index():
    """
    渲染主页
    
    返回:
        HTML: 前端页面
    """
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health():
    """
    健康检查接口
    
    返回:
        JSON: 服务状态
    """
    return jsonify({
        'status': 'ok',
        'service': 'MacMind Web API',
        'version': '1.0.0'
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    同步聊天接口
    
    请求体:
        {
            "message": "用户消息"
        }
    
    返回:
        JSON: AI响应
    """
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': '消息不能为空'
            }), 400
        
        ai_client = create_ai_client()
        tools = get_tool_schemas()
        
        conversation_manager.add_user_message(user_message)
        
        max_iterations = 5
        iteration = 0
        tool_calls_log = []
        
        while iteration < max_iterations:
            iteration += 1
            context = conversation_manager.get_context()
            
            response = ai_client.client.chat.completions.create(
                model=ai_client.model,
                messages=context,
                tools=tools,
                tool_choice="auto"
            )
            
            if not response.choices:
                raise ValueError("AI响应格式无效")
            
            message = response.choices[0].message
            
            if message.tool_calls:
                tool_calls_list = []
                for tool_call in message.tool_calls:
                    tool_calls_list.append({
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    })
                
                conversation_manager.add_tool_call_message(tool_calls_list)
                
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    result = tool_executor.execute(function_name, arguments)
                    result_json = json.dumps(result, ensure_ascii=False)
                    
                    tool_calls_log.append({
                        'function': function_name,
                        'arguments': arguments,
                        'result': result
                    })
                    
                    conversation_manager.add_tool_result_message(
                        tool_call.id,
                        function_name,
                        result_json
                    )
                
                continue
            
            else:
                if not message.content:
                    raise ValueError("AI响应内容为空")
                
                response_text = message.content
                conversation_manager.add_assistant_message(response_text)
                
                return jsonify({
                    'success': True,
                    'message': response_text,
                    'tool_calls': tool_calls_log
                })
        
        return jsonify({
            'success': False,
            'error': '达到最大工具调用次数限制'
        }), 500
    
    except Exception as e:
        logger.error(f"聊天接口错误: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """
    获取对话历史
    
    返回:
        JSON: 对话历史列表
    """
    try:
        history = conversation_manager.get_context()
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        logger.error(f"获取历史错误: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/clear', methods=['POST'])
def clear_history():
    """
    清空对话历史
    
    返回:
        JSON: 操作结果
    """
    try:
        conversation_manager.clear_history()
        return jsonify({
            'success': True,
            'message': '对话历史已清空'
        })
    except Exception as e:
        logger.error(f"清空历史错误: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@socketio.on('connect')
def handle_connect():
    """
    WebSocket连接建立
    """
    logger.info('客户端已连接')
    
    if conversation_manager.get_message_count() == 0:
        conversation_manager.add_system_message(
            conversation_manager.get_optimized_system_prompt()
        )
        logger.info('已初始化系统提示词')
    
    emit('connected', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """
    WebSocket连接断开
    """
    logger.info('客户端已断开')


@socketio.on('chat_message')
def handle_chat_message(data):
    """
    WebSocket聊天消息处理
    
    参数:
        data: {"message": "用户消息"}
    """
    try:
        user_message = data.get('message', '')
        
        if not user_message:
            emit('error', {'error': '消息不能为空'})
            return
        
        emit('user_message', {'message': user_message})
        
        ai_client = create_ai_client()
        tools = get_tool_schemas()
        
        conversation_manager.add_user_message(user_message)
        
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            context = conversation_manager.get_context()
            
            response = ai_client.client.chat.completions.create(
                model=ai_client.model,
                messages=context,
                tools=tools,
                tool_choice="auto"
            )
            
            if not response.choices:
                raise ValueError("AI响应格式无效")
            
            message = response.choices[0].message
            
            if message.tool_calls:
                tool_calls_list = []
                for tool_call in message.tool_calls:
                    tool_calls_list.append({
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    })
                
                conversation_manager.add_tool_call_message(tool_calls_list)
                
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    emit('tool_execution', {
                        'function': function_name,
                        'arguments': arguments
                    })
                    
                    result = tool_executor.execute(function_name, arguments)
                    result_json = json.dumps(result, ensure_ascii=False)
                    
                    emit('tool_result', {
                        'function': function_name,
                        'success': result['success'],
                        'data': result.get('data'),
                        'error': result.get('error')
                    })
                    
                    conversation_manager.add_tool_result_message(
                        tool_call.id,
                        function_name,
                        result_json
                    )
                
                continue
            
            else:
                if not message.content:
                    raise ValueError("AI响应内容为空")
                
                response_text = message.content
                conversation_manager.add_assistant_message(response_text)
                
                emit('ai_response', {'message': response_text})
                break
        
        if iteration >= max_iterations:
            emit('error', {'error': '达到最大工具调用次数限制'})
    
    except Exception as e:
        logger.error(f"WebSocket聊天错误: {e}", exc_info=True)
        emit('error', {'error': str(e)})


if __name__ == '__main__':
    logger.info("启动 MacMind Web 服务...")
    logger.info("访问地址: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
