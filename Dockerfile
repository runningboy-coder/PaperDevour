# 使用一个轻量级的 Python 3.9 官方镜像作为基础
FROM python:3.9-slim

# 设置工作目录，后续所有操作都在这个目录内进行
WORKDIR /app

# 为了利用 Docker 的层缓存机制，先只复制依赖文件
COPY requirements.txt .

# 安装所有 Python 依赖
# --no-cache-dir 减少镜像体积
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目的所有文件到工作目录
COPY . .

# 暴露 Flask 应用运行的端口
EXPOSE 5006

# 容器启动时执行的命令
# 使用 gunicorn 作为生产环境的 WSGI 服务器，比 Flask 自带的更稳定
# 我们将在 docker-compose 中覆盖这个命令以方便开发
CMD ["gunicorn", "--bind", "0.0.0.0:5006", "app:app"]