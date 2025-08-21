# PaperDevour 吞文研究助手

<p align="center">
  <img src="static/imgs/logo.png" alt="PaperDevour Banner">
</p>

<p align="center">
  <strong>一款为你 7x24 小时工作的 AI 研究伙伴，自动追踪、深度解析并与你探讨前沿学术论文。</strong>
</p>

<p align="center">
  <a href="https://github.com/runningboy-coder/PaperDevour/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/runningboy-coder/PaperDevour?style=for-the-badge"></a>
  <a href="https://github.com/runningboy-coder/PaperDevour/network/members"><img alt="GitHub forks" src="https://img.shields.io/github/forks/runningboy-coder/PaperDevour?style=for-the-badge"></a>
  <a href="https://github.com/runningboy-coder/PaperDevour/issues"><img alt="GitHub issues" src="https://img.shields.io/github/issues/runningboy-coder/PaperDevour?style=for-the-badge&color=success"></a>
  <a href="https://github.com/runningboy-coder/PaperDevour/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/runningboy-coder/PaperDevour?style=for-the-badge&color=blue"></a>
</p>

---

## 🚀 核心功能

PaperDevour 不仅仅是一个论文下载器，它是一个智能化的工作流引擎：

* **智能追踪**: 根据您设定的关键词，自动定时（或手动触发）从 arXiv 等平台抓取最新的学术论文。
* **双重 AI 解析**:
    * **智能摘要**: 利用大语言模型（LLM）将论文摘要提炼为简短、易懂的核心观点。
    * **深度解析**: 提供结构化的深度分析，包括**研究背景**、**核心方法**、**创新点**和**潜在影响**。
* **交互式问答**: 针对任意一篇已收录的论文，您可以像和真人一样进行提问，AI 会结合上下文为您解答。
* **即时搜索与导入**: 直接通过关键词在 arXiv 上进行海量搜索，并批量选择感兴趣的论文一键导入、分析。
* **个人化知识库**: 所有文章、分析和问答记录都将安全地存储在您的本地数据库中，形成一个专属的、可随时检索的知识库。
* **优雅的深色界面**: 专为长时间阅读和研究设计的现代化、护眼的深色主题界面。

## 🛠️ 技术栈

* **后端**: Python, Flask, SQLAlchemy
* **数据库**: SQLite
* **AI 模型**: DeepSeek API (通过 OpenAI 兼容接口)
* **任务调度**: APScheduler
* **前端**: HTML, Tailwind CSS, JavaScript
* **部署**: Docker, Gunicorn

## 🏁 开始使用

### 1. 环境准备

* [Docker Desktop](https://www.docker.com/products/docker-desktop/)
* 一个 DeepSeek API Key

### 2. 安装与运行 (推荐方式)

1.  **克隆仓库**
    ```bash
    git clone [https://github.com/runningboy-coder/PaperDevour.git](https://github.com/runningboy-coder/PaperDevour.git)
    cd PaperDevour
    ```

2.  **创建配置文件**
    * 复制 `.env.example` 文件并重命名为 `.env`。
    * 打开 `.env` 文件，填入您的 `DEEPSEEK_API_KEY` 和希望保存 PDF 的 `SAVE_PATH`。

3.  **使用 Docker Compose 启动**
    ```bash
    docker-compose up --build
    ```
    应用启动后，您的 AI 研究伙伴将在 `http://12_7.0.0.1:5006` 上等待您的指令。

---
### (备选) 手动安装

1.  **克隆仓库并安装依赖**
    ```bash
    git clone [https://github.com/runningboy-coder/PaperDevour.git](https://github.com/runningboy-coder/PaperDevour.git)
    cd PaperDevour
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
2.  **配置并运行**
    * 创建 `.env` 文件并填入配置。
    * 运行 `python3 app.py`。

## 自动化检查 (CI)

本项目已配置 GitHub Actions。每次向 `main` 分支推送代码或提交 Pull Request 时，都会自动执行代码规范检查 (Linting)，以确保代码库的质量和一致性。

## 🗺️ 项目路线图 (Roadmap)

我们对 PaperDevour 的未来充满期待！以下是一些我们计划实现的功能，欢迎您参与贡献：

* [ ] **个性化推荐引擎**: 基于您的阅读历史和偏好，主动为您推荐可能感兴趣的论文。
* [ ] **多数据源支持**: 除了 arXiv，增加对 PubMed, Google Scholar 等其他学术平台的支持。
* [ ] **知识图谱构建**: 将论文、作者、关键词之间的关系可视化，帮助您发现研究趋势。
* [ ] **引入 Celery & Redis**: 使用专业的任务队列优化后台任务处理。

## 🤝 如何贡献

我们热烈欢迎所有形式的贡献！请参考我们的 [贡献指南 (CONTRIBUTING.md)](CONTRIBUTING.md) 来开始您的第一步。

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。