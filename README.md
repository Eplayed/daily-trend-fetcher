# GitHub 热门项目自动化抓取与分析工具

这是一个自动化脚本，可以抓取 GitHub 上的高星项目，并使用 AI 进行多标签分类和README内容概括，最终导出为 JSON 文件并上传到阿里云 OSS。

## 功能特点

- 🌟 自动抓取 GitHub 上高星（stars>5000）项目，按 Star 数量排序
- 🏷️ 使用 AI（OpenAI/DeepSeek）分析项目，进行多标签分类
- 📝 将项目 README 内容概括为简洁的 1-2 句中文描述
- 📁 导出为 JSON 文件，更方便前端应用读取
- ☁️ 自动上传 JSON 文件到阿里云 OSS，便于查看和分享
- ⚡ 支持部署到阿里云函数计算 FC 或 GitHub Actions，实现完全自动化
- 🔧 支持多标签并行抓取和自定义获取数量
- 🔍 支持标签映射和验证，确保GitHub搜索标签准确性

## 准备工作

在使用前，你需要准备以下内容：

1. **GitHub Token** - 访问 [GitHub Settings - Developer settings - Personal access tokens](https://github.com/settings/tokens) 生成，需勾选 `public_repo` 权限
2. **AI API Key** - 推荐使用 DeepSeek（价格便宜，中文支持好）或 OpenAI API Key
3. **阿里云 OSS 配置** - 包括 AccessKey ID、AccessKey Secret、Endpoint 和 Bucket 名称
4. **Python 环境** - 本地运行时需要 Python 3.6 或更高版本

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置方式

**重要提示：** 永远不要将API密钥等敏感信息直接硬编码在代码中或提交到GitHub仓库！

### 方式1：配置文件（推荐本地开发使用）

1. 将 `config.py.example` 复制并重命名为 `config.py`
2. 打开 `config.py` 文件，填写您的配置信息

```python
# GitHub Token
GH_TOKEN = "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# AI 配置
AI_API_KEY = "sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
AI_BASE_URL = "https://api.openai.com/v1"  # 默认使用OpenAI API
AI_MODEL = "gpt-3.5-turbo" # 或 gpt-4o-mini / qwen3-max

# OSS 配置
OSS_ACCESS_KEY_ID = "LTAIXXXXXXXXXXXXXXXX"
OSS_ACCESS_KEY_SECRET = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
OSS_ENDPOINT = "oss-cn-hangzhou.aliyuncs.com"  # 公网端点
OSS_BUCKET_NAME = "your-bucket-name"
OSS_FILE_PATH = "github_trends/"  # 存储路径

# GitHub 项目筛选配置
PROJECT_TAG = "all"  # 可选值："all"（全类型）或特定标签名称（如 "ai", "web" 等）
PROJECT_COUNT = 10  # 项目获取数量
```

### 方式2：环境变量

所有配置都可以通过环境变量设置：

**Windows:**
```cmd
set GH_TOKEN="您的GitHub Token"
set AI_API_KEY="您的AI API密钥"
set AI_BASE_URL="https://api.openai.com/v1"
set AI_MODEL="gpt-3.5-turbo"
set OSS_ACCESS_KEY_ID="您的OSS AccessKey ID"
set OSS_ACCESS_KEY_SECRET="您的OSS AccessKey Secret"
set OSS_ENDPOINT="oss-cn-hangzhou.aliyuncs.com"
set OSS_BUCKET_NAME="您的OSS Bucket名称"
set OSS_FILE_PATH="github_trends/"
set PROJECT_TAG="all"
set PROJECT_COUNT="30"
```

**macOS/Linux:**
```bash
export GH_TOKEN="您的GitHub Token"
export AI_API_KEY="您的AI API密钥"
export AI_BASE_URL="https://api.openai.com/v1"
export AI_MODEL="gpt-3.5-turbo"
export OSS_ACCESS_KEY_ID="您的OSS AccessKey ID"
export OSS_ACCESS_KEY_SECRET="您的OSS AccessKey Secret"
export OSS_ENDPOINT="oss-cn-hangzhou.aliyuncs.com"
export OSS_BUCKET_NAME="您的OSS Bucket名称"
export OSS_FILE_PATH="github_trends/"
export PROJECT_TAG="all"
export PROJECT_COUNT="30"
```

## 本地运行

配置完成后，直接运行脚本：

```bash
python main.py
```

运行完成后，会在当前目录生成一个 JSON 文件，并自动上传到阿里云 OSS。

## 自动化部署

### 方式1：GitHub Actions

1. 创建 GitHub 仓库并上传所有文件
2. 在仓库的 `Settings` -> `Secrets and variables` -> `Actions` 页面，添加所有必要的密钥（与环境变量同名）
3. GitHub Actions 会在每5天 UTC 时间 0:00（北京时间早上 8 点）自动运行（配置在 `.github/workflows/daily.yml`）
4. 系统会并行处理多个标签类别，每个标签生成独立的JSON文件并上传到OSS

### 方式2：阿里云函数计算 FC

1. 登录阿里云函数计算控制台，创建函数（自定义运行时，Python 3.9）
2. 将 main.py 和 requirements.txt 文件打包成 zip 格式并上传
3. 配置环境变量（与本地环境变量相同）
4. 创建定时触发器，设置 Cron 表达式（例如：0 8 */5 * * 每5天北京时间8点触发）

## 数据说明

### 生成的 JSON 字段

- **项目标签**：AI 生成的项目多标签分类
- **项目名称**：GitHub 项目名称
- **项目地址**：GitHub 项目链接
- **项目README**：项目 README 内容的中文概括（1-2句话）

### 支持的项目标签类别

脚本支持以下预定义标签类别：

- 开源框架/库（Frameworks & Libraries）
- 开发者工具（Developer Tools）
- 实用工具/脚本（Utilities/Scripts）
- 教育/学习资源（Education/Resources）
- AI
- 社区/文化项目（Community/Culture）
- 游戏/图形（Games/Graphics）
- 科学计算/人工智能（Science/AI）
- 移动应用/嵌入式（Mobile/Embedded）
- 企业级应用（Enterprise）
- 基础设施/DevOps（Infrastructure/DevOps）
- 机器学习（machine-learning）
- 人工智能（artificial-intelligence）
- Web开发（web-development）
- 前端开发（frontend）
- 后端开发（backend）
- Python
- JavaScript
- Docker
- Kubernetes
- DevOps
- 移动开发（mobile-development）
- 数据科学（data-science）

## 工作流程

1. **获取热门项目**：通过GitHub API获取指定标签下的高星项目
2. **AI分析处理**：使用AI对每个项目进行标签分类和README概括
3. **数据保存**：将处理后的数据保存为JSON文件
4. **OSS上传**：自动将JSON文件上传到阿里云OSS
5. **状态报告**：输出执行结果和上传状态

## 注意事项

- AI 分析结果可能存在误差，特别是对于描述不完整的项目，请人工校对
- API 调用有频率限制，脚本中已添加延迟避免触发限制
- 请妥善保管你的 API Key 和阿里云密钥
- 阿里云函数计算和 OSS 使用会产生一定费用，请关注账单信息
- 在GitHub Actions中，每个标签类别会生成独立的文件，命名格式为"{标签}_projects_{日期}.json"

## 许可证

MIT