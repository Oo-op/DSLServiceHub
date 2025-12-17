DSL 对话系统项目
项目概述
这是一个基于领域特定语言（DSL）的智能对话系统
系统支持多轮对话、意图识别、静默超时处理等功能，适用于客服咨询、信息查询等场景。

项目结构
DSL-Project/
├── back/                          # 后端核心模块
│   ├── interpreter.py            # DSL解释器（词法分析、语法分析）
│   ├── LLMClient.py              # 星火大模型客户端
│   └── __pycache__/
├── webapp/                       # Web前端应用
│   ├── frontend/
│   │   ├── static/              # 静态资源
│   │   ├── templates/           # HTML模板
│   │   └── web_output.py        # Flask Web服务器
│   └── __pycache__/
├── test/                         # 测试模块
│   ├── test_suite.py            # 完整测试套件
│   ├── test_stubs.py            # 测试桩
│   └── __pycache__/
├── spotServer.dsl               # 故宫博物院客服DSL脚本
├── productSale.dsl              # 产品销售DSL脚本（范例1）
├── weather.dsl                  # 天气查询DSL脚本（范例2）
├── .env                         # 环境变量配置
├── README                       # 项目说明
└── venv/                        # Python虚拟环境

核心功能
1. DSL 解释器
词法分析：将DSL脚本分解为Token流
语法分析：构建抽象语法树（AST）
语义执行：根据AST执行对话流程

2. 对话管理
多轮对话状态维护
关键词精确匹配
AI意图识别（备用）
静默超时处理

3. Web 接口
RESTful API
会话管理
实时对话交互
DSL 语法规范

4.dsl基础结构
Step step_name
  Speak "消息内容"
  Listen 单次超时, 总超时
  Branch "关键词", 目标步骤
  Default 默认步骤
  Silence 静默处理步骤
  Exit
关键字说明
Step: 定义对话步骤
Speak: 机器人发言
Listen: 监听用户输入，设置超时
Branch: 关键词分支跳转
Default: 默认跳转（无匹配时）
Silence: 静默超时处理
Exit: 结束对话


环境要求
Python 3.7+
Flask 2.0+
websocket-client

运行测试
cd test
python test_suite.py

启动Web服务
cd frontend
python web_output.py
访问 http://localhost:5000 开始对话

测试框架
1.单元测试
    测试核心组件功能：
    词法分析器 (Lexer)
    语法分析器 (Parser)
    AST 构建

2.集成测试
测试完整对话流程：
    意图识别
    多轮对话
    错误处理
    超时机制
    运行测试

# 运行所有测试
python test_suite.py

配置说明
LLM 客户端配置
    支持多个星火大模型版本：
    v3.5: 通用版本（默认）
    max: 最大版本
    pro: 专业版本

超时配置
    单次超时: 提醒用户的时间间隔
    总超时: 结束对话的总静默时间

