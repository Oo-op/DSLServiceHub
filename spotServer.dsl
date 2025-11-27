# 文件名: spotServer.dsl

# 欢迎步骤，对话入口
Step welcome
  Speak "您好，这里是故宫博物院智能客服，请问有什么可以帮您的？"
  Listen 10, 40   #十秒无响应发出提醒，40秒无响应终止对话，每次提问后重置计时器
  Branch "门票", ticketProc
  Branch "成人票", adultTicketProc
  Branch "学生票", studentTicketProc
  Branch "老人票", elderTicketProc
  Branch "时间", timeProc
  Branch "游玩攻略", playProc
  Branch "购票", howToBuyProc
  Branch "买票", howToBuyProc        # 新增关键词
  Branch "怎么买", howToBuyProc      # 新增关键词
  Branch "物品", whatToBringProc
  Branch "没有", exitProc
  Silence silenceProc
  Default defaultProc

# --- 门票相关流程 ---
Step ticketProc
  Speak "故宫门票分旺季和淡季。请问您想了解成人票、学生票还是老人票？或者您想了解购票、需要带什么证件？"
  Listen 10, 40
  Branch "成人票", adultTicketProc
  Branch "学生票", studentTicketProc
  Branch "老人票", elderTicketProc
  Branch "购票", howToBuyProc
  Branch "买票", howToBuyProc       
  Branch "怎么买", howToBuyProc      
  Branch "需要带什么", whatToBringProc
  Branch "物品", whatToBringProc     
  Branch "没有", exitProc
  Default defaultProc

Step adultTicketProc
  Speak "旺季（4月1日-10月31日）成人票60元/人，淡季（11月1日-3月31日）40元/人。门票需提前7天通过官方小程序实名预约。"
  Speak "请问还有其他可以帮您的吗？"  # 直接显示继续服务消息
  Listen 10, 40
  Branch "门票", ticketProc
  Branch "成人票", adultTicketProc
  Branch "学生票", studentTicketProc
  Branch "老人票", elderTicketProc
  Branch "时间", timeProc
  Branch "游玩攻略", playProc
  Branch "购票", howToBuyProc
  Branch "买票", howToBuyProc        
  Branch "物品", whatToBringProc
  Branch "没有", exitProc
  Silence silenceProc
  Default defaultProc

Step studentTicketProc
  Speak "学生票旺季30元/人、淡季20元/人，需凭有效学生证购买并核验。"
  Speak "请问还有其他可以帮您的吗？"  # 直接显示继续服务消息
  Listen 10, 40
  Branch "门票", ticketProc
  Branch "成人票", adultTicketProc
  Branch "学生票", studentTicketProc
  Branch "老人票", elderTicketProc
  Branch "时间", timeProc
  Branch "游玩攻略", playProc
  Branch "购票", howToBuyProc
  Branch "买票", howToBuyProc       
  Branch "物品", whatToBringProc
  Branch "没有", exitProc
  Silence silenceProc
  Default defaultProc

Step elderTicketProc
  Speak "60岁以上老人凭身份证可免票入园，入园时请准备好有效证件。"
  Speak "请问还有其他可以帮您的吗？"  # 直接显示继续服务消息
  Listen 10, 40
  Branch "门票", ticketProc
  Branch "成人票", adultTicketProc
  Branch "学生票", studentTicketProc
  Branch "老人票", elderTicketProc
  Branch "时间", timeProc
  Branch "游玩攻略", playProc
  Branch "购票", howToBuyProc
  Branch "买票", howToBuyProc       
  Branch "物品", whatToBringProc
  Branch "没有", exitProc
  Silence silenceProc
  Default defaultProc

# --- 购票和准备流程 ---
Step howToBuyProc
  Speak "故宫实行实名制预约购票，您可以通过以下方式购票：
1. 故宫博物院官方小程序（推荐）
2. 故宫博物院官方网站
3. 官方授权的第三方平台

所有门票需提前1-7天预约，不支持现场购票。预约时需要提供参观者的真实姓名和身份证号码。"
  Speak "请问还有其他可以帮您的吗？"  # 直接显示继续服务消息
  Listen 10, 40
  Branch "门票", ticketProc
  Branch "成人票", adultTicketProc
  Branch "学生票", studentTicketProc
  Branch "老人票", elderTicketProc
  Branch "时间", timeProc
  Branch "游玩攻略", playProc
  Branch "购票", howToBuyProc
  Branch "买票", howToBuyProc        # 新增
  Branch "物品", whatToBringProc
  Branch "没有", exitProc
  Silence silenceProc
  Default defaultProc

Step whatToBringProc
  Speak "参观故宫需要携带：
1. 本人有效身份证件原件（身份证、护照等）
2. 预约成功的二维码或短信
3. 学生、老人等优惠票需携带相应优惠证件
4. 建议携带：饮用水、舒适鞋子、防晒用品

重要提示：入园时需人证票合一核验，请务必携带预约时使用的身份证件原件。"
  Speak "请问还有其他可以帮您的吗？"  # 直接显示继续服务消息
  Listen 10, 40
  Branch "门票", ticketProc
  Branch "成人票", adultTicketProc
  Branch "学生票", studentTicketProc
  Branch "老人票", elderTicketProc
  Branch "时间", timeProc
  Branch "游玩攻略", playProc
  Branch "购票", howToBuyProc
  Branch "买票", howToBuyProc        # 新增
  Branch "物品", whatToBringProc
  Branch "没有", exitProc
  Silence silenceProc
  Default defaultProc

# --- 其他主题流程 ---
Step timeProc
  Speak "故宫旺季（4月1日-10月31日）开放时间为 08:30-17:00（16:10停止入园）；淡季（11月1日-3月31日）为 08:30-16:30（15:40停止入园）。全年周一常规闭馆（法定节假日除外）。"
  Speak "请问还有其他可以帮您的吗？"  # 直接显示继续服务消息
  Listen 10, 40
  Branch "门票", ticketProc
  Branch "成人票", adultTicketProc
  Branch "学生票", studentTicketProc
  Branch "老人票", elderTicketProc
  Branch "时间", timeProc
  Branch "游玩攻略", playProc
  Branch "购票", howToBuyProc
  Branch "买票", howToBuyProc        # 新增
  Branch "物品", whatToBringProc
  Branch "没有", exitProc
  Silence silenceProc
  Default defaultProc

Step playProc
  Speak "推荐您沿中轴线游览，大约需要3-4小时。如果您时间充裕，可以参观两侧的珍宝馆、钟表馆，深度游玩建议5-6小时。上午9:30至11:30是入园高峰，建议错峰出行。"
  Speak "请问还有其他可以帮您的吗？"  # 直接显示继续服务消息
  Listen 10, 40
  Branch "门票", ticketProc
  Branch "成人票", adultTicketProc
  Branch "学生票", studentTicketProc
  Branch "老人票", elderTicketProc
  Branch "时间", timeProc
  Branch "游玩攻略", playProc
  Branch "购票", howToBuyProc
  Branch "买票", howToBuyProc        # 新增
  Branch "物品", whatToBringProc
  Branch "没有", exitProc
  Silence silenceProc
  Default defaultProc


# --- 通用与异常处理流程 ---

# 静默处理：当用户超时未输入时触发
Step silenceProc
  Speak "还在吗？如果您有需要，可以直接告诉我您的问题。比如 '门票'、'时间'、'购票'、'物品'。如果没有问题了，可以说 '没有'。"
  Listen 10, 40
  # 再次提供主要选项
  Branch "门票", ticketProc
  Branch "成人票", adultTicketProc
  Branch "学生票", studentTicketProc
  Branch "老人票", elderTicketProc
  Branch "时间", timeProc
  Branch "游玩攻略", playProc
  Branch "购票", howToBuyProc
  Branch "买票", howToBuyProc        # 新增
  Branch "物品", whatToBringProc
  Branch "没有", exitProc
  # 如果再次静默，则结束对话
  Silence exitProc
  Default defaultProc

# 默认处理：当用户输入无法匹配任何Branch时触发
Step defaultProc
  Speak "抱歉，我不太理解您的问题。您可以试试问我关于门票、时间、游玩攻略、购票或物品的问题。或者可以拨打咨询电话400-950-1925咨询更多问题"
  Speak "请问还有其他可以帮您的吗？"  # 直接显示继续服务消息
  Listen 10, 40
  Branch "门票", ticketProc
  Branch "成人票", adultTicketProc
  Branch "学生票", studentTicketProc
  Branch "老人票", elderTicketProc
  Branch "时间", timeProc
  Branch "游玩攻略", playProc
  Branch "购票", howToBuyProc
  Branch "买票", howToBuyProc        # 新增
  Branch "物品", whatToBringProc
  Branch "没有", exitProc
  Silence silenceProc
  Default defaultProc

# 结束对话
Step exitProc
  Speak "感谢您的咨询，祝您游玩愉快！再见。"
  Exit