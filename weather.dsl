# 简单问答型对话脚本

Step welcome
  Speak "您好，欢迎使用简单问答服务"
  Speak "请问您需要查询天气还是时间？"
  Listen 5, 20
  Branch "天气", weather_info
  Branch "时间", time_info
  Default unknown_query

Step weather_info
  Speak "今天天气晴朗，温度25度，适合外出"
  Speak "还需要其他帮助吗？"
  Listen 5, 20
  Branch "天气", weather_info
  Branch "时间", time_info
  Branch "结束", exit_proc
  Default unknown_query

Step time_info
  Speak "现在是北京时间下午3点"
  Speak "还需要其他帮助吗？"
  Listen 5, 20
  Branch "天气", weather_info
  Branch "时间", time_info
  Branch "结束", exit_proc
  Default unknown_query

Step unknown_query
  Speak "抱歉，我只能回答天气和时间相关问题"
  Speak "请告诉我您想查询天气还是时间？"
  Listen 5, 20
  Branch "天气", weather_info
  Branch "时间", time_info
  Branch "结束", exit_proc
  Default unknown_query

Step exit_proc
  Speak "感谢使用，再见！"
  Exit