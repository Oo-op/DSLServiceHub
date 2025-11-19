# 故宫客服DSL
Step welcome
  Speak "您好，请问有什么可以帮您的？"
  Listen 5, 20  # 等待用户输入
    #若0-5秒内用户有输入：直接执行后续的Branch关键词匹配；
    #若5秒内无输入：触发Silence silenceProc，跳转到silenceProc步骤，说 “听不清，请您再说一遍？”，并再次等待用户输入（仍沿用Listen 5, 20的超时规则）；
    #若累计 20 秒仍无输入：仍无回应则执行Exit结束对话
  Branch "门票", ticketProc  
  Branch "开放时间", timeProc  
  Branch "游玩攻略", playProc  
  Branch "人工", transferHuman  
  Silence silenceProc  # 无输入时，跳转到silenceProc
  Default defaultProc  # 未匹配时，跳转到defaultProc



Step ticketProc
  Speak "故宫门票分旺季和淡季~ 请问您想了解成人票、学生票还是老人票？"
  Listen 5, 30
  Branch "成人票", adultTicketProc
  Branch "学生票", studentTicketProc
  Branch "老人票", elderTicketProc
  Branch "人工", transferHuman  # 新增：支持中途转人工
  Default defaultProc


Step adultTicketProc
  Speak "旺季（4.1-10.31）成人票60元/人，淡季（11.1-3.31）40元/人，需提前7天实名预约~"
  Branch "预约方式", bookProc  # 追问“预约方式”
  Branch "人工", transferHuman  # 新增：支持中途转人工
  Default thanks


Step studentTicketProc
  Speak "学生票旺季30元/人、淡季20元/人，需凭有效学生证购买并核验~"
  Branch "人工", transferHuman  # 新增：支持中途转人工
  Default thanks


Step elderTicketProc
  Speak "60岁以上老人凭身份证免票，入园时请出示证件~"
  Branch "人工", transferHuman  # 新增：支持中途转人工
  Default thanks


Step timeProc
  Speak "旺季开放时间：08:30-17:00（16:10停止入园）；淡季：08:30-16:30（15:40停止入园），周一常规闭馆~"
  Branch "人工", transferHuman  # 新增：支持中途转人工
  Default thanks


Step playProc
  Speak "常规游玩推荐3-4小时（逛中轴线），深度游建议5-6小时（含珍宝馆/钟表馆），避开9:30-11:30高峰~"
  Branch "必看景点", spotProc
  Branch "人工", transferHuman  # 新增：支持中途转人工
  Default thanks


Step spotProc
  Speak "必看景点：太和殿、乾清宫、御花园；拍照推荐：角楼、红墙走廊~"
  Branch "人工", transferHuman  # 新增：支持中途转人工
  Default thanks


Step silenceProc
  Speak "听不清，请您再说一遍可以吗？若需要人工客服，可直接说“人工”~"  # 新增：提示转人工
  Listen 5, 20
  Branch "门票", ticketProc
  Branch "开放时间", timeProc
  Branch "人工", transferHuman  # 新增：支持超时后转人工
  Silence transferHuman  # 新增：累计超时后直接转人工
  Default defaultProc


Step defaultProc
  Speak "抱歉，我只聚焦故宫游览相关问题（如门票，游玩攻略，时间等）~ 若想要~"
  Branch "人工", transferHuman  # 新增：未匹配时支持转人工
  Default welcome


# 新增：转人工步骤
Step transferHuman
  Speak "正在为您转接人工客服，请您稍候~ 人工客服工作时间：09:00-18:00"
  Exit  # 转接后结束当前机器人流程


Step thanks
  Speak "感谢您的咨询，祝您游玩愉快！"
  Exit