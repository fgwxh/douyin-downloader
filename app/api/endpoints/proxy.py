from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
import requests

router = APIRouter()

@router.get("/video")
async def proxy_video(url: str = Query(..., description="视频URL")):
    """代理视频请求，绕过CORS限制
    
    当前端尝试直接加载抖音视频时，会遇到CORS限制，导致视频无法加载。
    此接口通过后端代理请求视频，绕过CORS限制，使视频可以正常加载。
    
    Args:
        url: 视频的原始URL
        
    Returns:
        StreamingResponse: 视频流响应
    """
    try:
        # 添加必要的请求头，模拟浏览器请求
        headers = {
            "Referer": "https://www.douyin.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "video",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1"
        }
        
        # 向抖音服务器请求视频
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        
        # 检查响应状态
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"抖音服务器返回错误: {response.status_code}")
        
        # 提取内容类型
        content_type = response.headers.get("Content-Type", "video/mp4")
        
        # 返回视频流
        return StreamingResponse(
            response.iter_content(chunk_size=1024*1024),
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename=video.mp4",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"视频代理请求失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视频代理失败: {str(e)}")
