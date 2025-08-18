# PaperDevour 论文吞噬者

<p align="center">
  <img src="https://placehold.co/600x300/0f172a/38bdf8?text=PaperDevour&font=raleway" alt="PaperDevour Banner">
</p>

<p align="center">
  <strong>一款为你 7x24 小时工作的 AI 研究伙伴，自动追踪、深度解析并与你探讨前沿学术论文。</strong>
</p>

<p align="center">
  <img alt="GitHub stars" src="https://img.shields.io/github/stars/[YOUR GITHUB USERNAME]/PaperDevour?style=for-the-badge">
  <img alt="GitHub forks" src="https://img.shields.io/github/forks/[YOUR GITHUB USERNAME]/PaperDevour?style=for-the-badge">
  <img alt="GitHub issues" src="https://img.shields.io/github/issues/[YOUR GITHUB USERNAME]/PaperDevour?style=for-the-badge&color=success">
  <img alt="License" src="https://img.shields.io/github/license/[YOUR GITHUB USERNAME]/PaperDevour?style=for-the-badge&color=blue">
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

## 🏁 开始使用

### 1. 环境准备

* Python 3.9+
* 一个 DeepSeek API Key

### 2. 安装步骤

1.  **克隆仓库**
    ```bash
    git clone [https://github.com/](https://github.com/)[YOUR GITHUB USERNAME]/PaperDevour.git
    cd PaperDevour
    ```

2.  **创建并激活虚拟环境** (推荐)
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate  # Windows
    ```

3.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

4.  **配置应用**
    * 在 `services.py` 文件中，找到并修改以下配置项：
        * `DEEPSEEK_API_KEY`: 填入您的 DeepSeek API 金鑰。
        * `SAVE_PATH`: 填入您希望保存 PDF 文件的本地文件夾绝对路径。

5.  **运行应用**
    ```bash
    python3 app.py
    ```
    应用启动后，您的 AI 研究伙伴将在 `http://127.0.0.1:5006` 上等待您的指令。

## 🗺️ 项目路线图 (Roadmap)

我们对 PaperDevour 的未来充满期待！以下是一些我们计划实现的功能，欢迎您参与贡献：

* [ ] **个性化推荐引擎**: 基于您的阅读历史和偏好，主动为您推荐可能感兴趣的论文。
* [ ] **多数据源支持**: 除了 arXiv，增加对 PubMed, Google Scholar 等其他学术平台的支持。
* [ ] **作者与机构追踪**: 关注特定的学者或研究机构，当他们有新成果时获得通知。
* [ ] **知识图谱构建**: 将论文、作者、关键词之间的关系可视化，帮助您发现研究趋势。
* [ ] **Docker 一键部署**: 提供 Dockerfile，实现更简单的部署和分发。

## 🤝 如何贡献

我们热烈欢迎所有形式的贡献！无论是报告一个 Bug、提交一个新功能，还是改进文档，您的每一份努力都对社区至关重要。

**贡献流程:**

1.  **Fork** 本仓库。
2.  创建您的特性分支 (`git checkout -b feature/AmazingFeature`)。
3.  提交您的更改 (`git commit -m 'Add some AmazingFeature'`)。
4.  将您的分支推送到远程 (`git push origin feature/AmazingFeature`)。
5.  **提交一个 Pull Request**，并清晰地描述您的工作。

我们建议您先从标记有 `good first issue` 的问题开始。

## 📄 许可证

本项目采用 [MIT License](LICENSE.txt) 开源许可证。