import requests

# 测试加载作品列表API
print("测试加载作品列表API...")
try:
    # 发送GET请求到/api/works接口
    response = requests.get("http://localhost:8501/api/works", params={"account_id": 1, "page": 1, "page_size": 50}, timeout=10)
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应体: {response.text}")
    print("\n测试成功！加载作品列表API可用。")
except Exception as e:
    print(f"错误: {e}")
    print("\n测试失败！加载作品列表API不可用。")
