import requests

# 测试获取账号列表API
print("测试获取账号列表API...")
try:
    # 发送GET请求到/api/accounts接口
    response = requests.get("http://localhost:8501/api/accounts", timeout=10)
    print(f"状态码: {response.status_code}")
    print(f"响应体: {response.text}")
    print("\n测试成功！获取账号列表API可用。")
except Exception as e:
    print(f"错误: {e}")
    print("\n测试失败！获取账号列表API不可用。")
