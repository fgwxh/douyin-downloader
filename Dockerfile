FROM python:3.11-slim

# 设置时区为亚洲/上海
ENV TZ=Asia/Shanghai
# 禁用Python字节码生成
ENV PYTHONDONTWRITEBYTECODE=1
# 禁用Python缓冲
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 安装必要的系统依赖，xclip在Docker容器中不需要（web界面剪贴板由浏览器处理）
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get autoremove -y \
    && apt-get clean

COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

# 创建数据和下载目录并设置权限
RUN mkdir -p ./data ./downloads && chmod -R 777 ./data ./downloads

# 暴露FastAPI端口
EXPOSE 8501

# 运行FastAPI应用
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8501", "--workers", "1"]
