Step welcome
  Speak "欢迎来到智能客服系统"
  Speak "请选择服务类型：产品咨询、技术支持或投诉建议"
  Listen 8, 50
  Branch "产品", product_flow
  Branch "技术", tech_flow
  Branch "投诉", complaint_flow
  Silence silence_reminder

Step product_flow
  Speak "产品咨询请选择：价格查询、功能说明、购买方式"
  Listen 8, 50
  Branch "价格", price_info
  Branch "功能", feature_info
  Branch "购买", purchase_info
  Branch "返回", welcome
  Default product_default

Step price_info
  Speak "基础版：100元，专业版：300元，企业版：800元"
  Speak "需要了解哪个版本的功能详情？"
  Listen 8, 50
  Branch "基础", basic_feature
  Branch "专业", pro_feature
  Branch "企业", enterprise_feature
  Branch "返回", product_flow
  Default product_default

Step basic_feature
  Speak "基础版包含核心功能A和B，适合个人用户"
  Branch "购买", purchase_info
  Branch "返回", product_flow
  Default product_default

Step pro_feature
  Speak "专业版增加功能C和D，支持团队协作"
  Branch "购买", purchase_info
  Branch "返回", product_flow
  Default product_default

Step enterprise_feature
  Speak "企业版包含所有功能，提供专属技术支持"
  Branch "购买", purchase_info
  Branch "返回", product_flow
  Default product_default

Step tech_flow
  Speak "技术支持请描述您遇到的问题"
  Speak "或选择：安装问题、使用问题、故障排除"
  Listen 8, 50
  Branch "安装", install_help
  Branch "使用", usage_help
  Branch "故障", troubleshooting
  Branch "返回", welcome
  Default tech_default

Step complaint_flow
  Speak "投诉建议请详细描述您的情况"
  Speak "我们将尽快处理并回复"
  Listen 10, 50
  Branch "返回", welcome
  Silence complaint_silence

Step purchase_info
  Speak "购买方式：官网在线购买、客服电话订购、代理商处购买"
  Speak "推荐官网购买，享受最新优惠"
  Branch "返回", product_flow
  Default product_default

Step install_help
  Speak "安装问题请检查系统要求和安装包完整性"
  Speak "详细教程请访问官网帮助中心"
  Branch "返回", tech_flow
  Default tech_default

Step product_default
  Speak "请选择：价格查询、功能说明或购买方式"
  Branch "返回", product_flow
  Default product_flow

Step tech_default
  Speak "请选择：安装问题、使用问题或故障排除"
  Branch "返回", tech_flow
  Default tech_flow

Step silence_reminder
  Speak "您还在吗？请选择服务类型：产品咨询、技术支持或投诉建议"
  Listen 5, 20
  Branch "产品", product_flow
  Branch "技术", tech_flow
  Branch "投诉", complaint_flow
  Silence final_warning

Step complaint_silence
  Speak "如果您需要提交投诉，请详细描述情况，或选择返回主菜单"
  Listen 8, 25
  Branch "返回", welcome
  Silence final_warning

Step final_warning
  Speak "由于长时间无响应，对话即将结束"
  Speak "如需帮助请重新开始对话"
  Exit