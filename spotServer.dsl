# spotServer.dsl (无人工版本)

# 欢迎步骤，对话入口
Step welcome
  Speak "您好，这里是故宫博物院智能客服，请问有什么可以帮您的？"
  Listen 5, 20
  Branch "门票", ticketProc
  Branch "开放时间", timeProc
  Branch "游玩攻略", playProc
  Branch "没有", exitProc
  Silence silenceProc
  Default defaultProc

# --- 门票相关流程 ---
Step ticketProc
  Speak "故宫门票分旺季和淡季。请问您想了解成人票、学生票还是老人票？"
  Listen 5, 30
  Branch "成人票", adultTicketProc
  Branch "学生票", studentTicketProc
  Branch "老人票", elderTicketProc
  Branch "没有", exitProc
  Default defaultProc

Step adultTicketProc
  Speak "旺季（4月1日-10月31日）成人票60元/人，淡季（11月1日-3月31日）40元/人。门票需提前7天通过官方小程序实名预约。"
  Default continueProc

Step studentTicketProc
  Speak "学生票旺季30元/人、淡季20元/人，需凭有效学生证购买并核验。"
  Default continueProc

Step elderTicketProc
  Speak "60岁以上老人凭身份证可免票入园，入园时请准备好有效证件。"
  Default continueProc

# --- 其他主题流程 ---
Step timeProc
  Speak "故宫旺季开放时间为 08:30-17:00（16:10停止入园）；淡季为 08:30-16:30（15:40停止入园）。全年周一常规闭馆（法定节假日除外）。"
  Default continueProc

Step playProc
  Speak "推荐您沿中轴线游览，大约需要3-4小时。如果您时间充裕，可以参观两侧的珍宝馆、钟表馆，深度游玩建议5-6小时。上午9:30至11:30是入园高峰，建议错峰出行。"
  Branch "必看景点", spotProc
  Default continueProc

Step spotProc
  Speak "中轴线上的必看景点有：太和殿、乾清宫、御花园。如果您喜欢拍照，午门、角楼和红墙走廊都是绝佳的取景地。"
  Default continueProc

# --- 通用与异常处理流程 ---

# 静默处理：当用户超时未输入时触发
Step silenceProc
  Speak "还在吗？如果您有需要，可以直接告诉我您的问题。比如 '门票'、'开放时间'。如果没有问题了，可以说 '没有'。"
  Listen 5, 20
  # 再次提供主要选项
  Branch "门票", ticketProc
  Branch "开放时间", timeProc
  Branch "游玩攻略", playProc
  Branch "没有", exitProc
  # 如果再次静默，则结束对话
  Silence exitProc
  Default defaultProc

# 默认处理：当用户输入无法匹配任何Branch时触发
Step defaultProc
  Speak "抱歉，我不太理解您的问题。您可以试试问我关于“门票”、“开放时间”或“游玩攻略”的问题。"
  Listen 5, 30
  Branch "门票", ticketProc
  Branch "开放时间", timeProc
  Branch "游玩攻略", playProc
  Branch "没有", exitProc
  Silence silenceProc
  Default continueProc

# 继续服务：在完成一个问答后，主动询问用户是否还有其他问题
Step continueProc
  Speak "请问还有其他可以帮您的吗？"
  Listen 5, 30
  # 提供主要选项，实现连续问答
  Branch "门票", ticketProc
  Branch "开放时间", timeProc
  Branch "游玩攻略", playProc
  Branch "没有", exitProc
  Silence silenceProc
  Default defaultProc

# 结束对话
Step exitProc
  Speak "感谢您的咨询，祝您游玩愉快！再见。"
  Exit