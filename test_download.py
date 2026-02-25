import requests
import json

# 测试下载功能
def test_download():
    print("测试下载功能...")
    try:
        # 发送POST请求到/api/download端点
        response = requests.post(
            "http://localhost:8501/api/download",
            json={
                "account_id": 1,
                "work_ids": []
            },
            timeout=30
        )
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应体: {response.text}")
        
        if response.status_code == 200:
            print("\n测试成功！下载功能可用。")
        else:
            print(f"\n测试失败！状态码: {response.status_code}")
    except Exception as e:
        print(f"错误: {e}")
        print("\n测试失败！下载功能不可用。")

if __name__ == "__main__":
    test_download()
