import requests

print("测试健康检查API...")
try:
    # 发送GET请求到/health接口
    response = requests.get("http://localhost:8501/health", timeout=10)
    print(f"状态码: {response.status_code}")
    print(f"响应体: {response.text}")
    print("\n测试成功！健康检查API可用。")
except Exception as e:
    print(f"错误: {e}")
    print("\n测试失败！健康检查API不可用。")
