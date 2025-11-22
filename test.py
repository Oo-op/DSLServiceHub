# 文件名: test_api_versions.py

import sys
import os
sys.path.append(os.path.dirname(__file__))

from LLMClient import LLMClient

def test_single_version(version):
    """测试单个版本"""
    print(f"\n{'='*50}")
    print(f"测试版本: {version}")
    print(f"{'='*50}")
    
    app_id = "d48801c2"
    api_key = "bf818c60404ba8d6d6297a4aeb677a5d"
    api_secret = "NzUwN2M1MTMyOTA5YTU1N2UxYjQyNWMw"
    
    try:
        # 创建客户端
        client = LLMClient(app_id, api_key, api_secret, version)
        print(f"✅ 客户端创建成功")
        
        # 测试意图识别
        print("正在测试API调用...")
        result = client.recognize_intent("我想买门票", ["门票", "开放时间", "游玩攻略"])
        
        if result:
            print(f"✅ API调用成功！识别结果: '{result}'")
        else:
            print(f"⚠️  API调用完成但未匹配到意图")
            
        return True
        
    except Exception as e:
        print(f"❌ 版本 {version} 测试失败: {e}")
        return False

def main():
    """测试所有可能的版本"""
    print("开始测试讯飞星火API版本...")
    
    # 所有可能的版本
    versions_to_test = [
        "v3.5",    # 通用版本
        "lite",     # Spark Lite
        "pro",      # Spark Pro  
        "max",      # Spark Max
        "ultra",    # Spark Ultra
        "v1.5",     # 传统版本（可能已停用）
        "v2.0",     # 传统版本
        "v3.0",     # 传统版本
    ]
    
    working_versions = []
    
    for version in versions_to_test:
        if test_single_version(version):
            working_versions.append(version)
    
    print(f"\n{'='*60}")
    print("测试总结:")
    print(f"{'='*60}")
    
    if working_versions:
        print(f"✅ 可用的版本: {working_versions}")
        print(f"💡 建议在 main.py 中使用: spark_version='{working_versions[0]}'")
    else:
        print("❌ 所有版本都不可用")
        print("💡 可能原因:")
        print("   - API凭证无效或已过期")
        print("   - 账户未开通相应服务")
        print("   - 网络连接问题")
        print("   - 建议使用模拟客户端继续开发")

if __name__ == "__main__":
    main()