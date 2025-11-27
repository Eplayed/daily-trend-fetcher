# GitHub 高星项目抓取工具

这是一个自动化脚本，可以抓取 GitHub 上的高星项目，并使用 AI 进行多标签分类和README内容概括，最终导出为 CSV 文件并上传到阿里云 OSS。

## 功能特点

- 🌟 自动抓取 GitHub 上高星（stars>5000）项目，按 Star 数量排序
- 🏷️ 使用 AI（OpenAI/DeepSeek）分析项目，进行多标签分类（如开源框架/库、开发者工具、教育/学习资源等）
- 📝 将项目 README 内容概括为简洁的 1-2 句中文描述
- 📁 导出为 CSV 文件，可直接用 Excel 打开
- ☁️ 自动上传 CSV 文件到阿里云 OSS，便于查看和分享
- ⚡ 支持部署到阿里云函数计算 FC，实现完全自动化
- 🔄 通过 GitHub Actions 实现每日定时执行
- 🔧 测试模式下仅抓取 3 条项目数据，提高开发效率

## 准备工作

在使用前，你需要准备以下内容：

### 1. GitHub Token
- 访问 [GitHub Settings - Developer settings - Personal access tokens](https://github.com/settings/tokens)
- 点击 "Generate new token" -> "Generate new token (classic)"
- 勾选 `public_repo` 权限
- 生成后保存好你的 Token

### 2. AI API Key
- 推荐使用 DeepSeek（价格便宜，中文支持好），注册并获取 API Key
- 也可以使用 OpenAI API Key

### 3. 阿里云 OSS 配置
- 阿里云账号
- 创建 OSS Bucket
- 获取 AccessKey ID、AccessKey Secret、Endpoint 和 Bucket 名称

### 4. Python 环境
- 如果你想在本地运行，需要安装 Python 3.6 或更高版本

## 本地运行指南

### 安装依赖

```bash
pip install -r requirements.txt
```

## 安全配置指南

**重要提示：** 永远不要将API密钥、密码等敏感信息直接硬编码在代码中或提交到GitHub仓库！本项目提供了以下安全的配置方式：

### 本地调试配置（推荐）

为了方便本地开发和调试，我们提供了通过配置文件设置敏感信息的方式：

1. 将 `config.py.example` 复制并重命名为 `config.py`
2. 打开 `config.py` 文件，填写您的配置信息
3. 运行脚本，系统会自动从 `config.py` 读取配置

**注意：** `config.py` 文件已添加到 `.gitignore` 中，不会被提交到代码仓库。

### 环境变量配置

所有敏感信息都应该通过环境变量设置。以下是可用的环境变量：

```bash
# GitHub Token
GITHUB_TOKEN="您的GitHub Token"

# AI 配置
AI_API_KEY="您的AI API密钥"
AI_BASE_URL="AI API的基础URL"
AI_MODEL="使用的AI模型名称"

# 阿里云OSS配置
OSS_ACCESS_KEY_ID="您的OSS AccessKey ID"
OSS_ACCESS_KEY_SECRET="您的OSS AccessKey Secret"
OSS_ENDPOINT="您的OSS Endpoint"
OSS_BUCKET_NAME="您的OSS Bucket名称"
OSS_FILE_PATH="文件在OSS中的存储路径"
```

### 本地开发时配置

**Windows:**
```cmd
set GITHUB_TOKEN="您的GitHub Token"
set AI_API_KEY="您的AI API密钥"
set AI_BASE_URL="https://api.openai.com/v1"
set AI_MODEL="gpt-3.5-turbo"
set OSS_ACCESS_KEY_ID="您的OSS AccessKey ID"
set OSS_ACCESS_KEY_SECRET="您的OSS AccessKey Secret"
set OSS_ENDPOINT="oss-cn-hangzhou.aliyuncs.com"
set OSS_BUCKET_NAME="您的OSS Bucket名称"
set OSS_FILE_PATH="github_trends/"
```

**macOS/Linux:**
```bash
export GITHUB_TOKEN="您的GitHub Token"
export AI_API_KEY="您的AI API密钥"
export AI_BASE_URL="https://api.openai.com/v1"
export AI_MODEL="gpt-3.5-turbo"
export OSS_ACCESS_KEY_ID="您的OSS AccessKey ID"
export OSS_ACCESS_KEY_SECRET="您的OSS AccessKey Secret"
export OSS_ENDPOINT="oss-cn-hangzhou.aliyuncs.com"
export OSS_BUCKET_NAME="您的OSS Bucket名称"
export OSS_FILE_PATH="github_trends/"
```

您也可以创建一个 `.env` 文件并使用 `python-dotenv` 库来加载环境变量，但请确保将 `.env` 文件添加到 `.gitignore` 中。

### GitHub Actions 配置

当使用GitHub Actions自动运行时，请按照以下步骤配置敏感信息：

1. 进入您的GitHub仓库
2. 点击 "Settings" -> "Secrets and variables" -> "Actions"
3. 点击 "New repository secret" 添加以下密钥：
   - `MY_GITHUB_TOKEN`: 您的GitHub Token
   - `AI_API_KEY`: 您的AI API密钥
   - `AI_BASE_URL`: AI API的基础URL
   - `AI_MODEL`: 使用的AI模型名称
   - `OSS_ACCESS_KEY_ID`: 您的OSS AccessKey ID
   - `OSS_ACCESS_KEY_SECRET`: 您的OSS AccessKey Secret
   - `OSS_ENDPOINT`: 您的OSS Endpoint
   - `OSS_BUCKET_NAME`: 您的OSS Bucket名称
   - `OSS_FILE_PATH`: 文件在OSS中的存储路径

GitHub Actions工作流文件已正确配置为从secrets中读取这些值，无需修改。

### 运行脚本

```bash
python main.py
```

运行完成后，会在当前目录生成一个 CSV 文件，并自动上传到阿里云 OSS。

## GitHub Actions 自动化配置

为了实现完全自动化，你可以将代码上传到 GitHub 仓库，并配置 GitHub Actions：

### 1. 创建 GitHub 仓库

创建一个新的 GitHub 仓库（例如 `daily-trend-fetcher`），并上传所有文件。

### 2. 配置 Secrets

在仓库的 `Settings` -> `Secrets and variables` -> `Actions` 页面，添加以下密钥：

- **必须配置的密钥：**
  - `MY_GITHUB_TOKEN`: 你的 GitHub Token
  - `AI_API_KEY`: 你的 AI API Key
  - `AI_BASE_URL`: AI API的基础URL（默认：https://api.openai.com/v1）
  - `AI_MODEL`: 使用的AI模型名称（默认：gpt-3.5-turbo）
  - `OSS_ACCESS_KEY_ID`: 你的OSS AccessKey ID
  - `OSS_ACCESS_KEY_SECRET`: 你的OSS AccessKey Secret
  - `OSS_ENDPOINT`: 你的OSS Endpoint
  - `OSS_BUCKET_NAME`: 你的OSS Bucket名称
  - `OSS_FILE_PATH`: 文件在OSS中的存储路径（默认：github_trends/）

### 3. 启用工作流

GitHub Actions 工作流配置已包含在 `.github/workflows/daily.yml` 文件中，它会：
- 每天 UTC 时间 0:00（北京时间早上 8 点）自动运行
- 运行后将生成的 CSV 文件作为 Artifact 上传
- 自动上传 CSV 文件到阿里云 OSS

你可以在仓库的 `Actions` 页面手动触发运行或查看历史运行结果。

## 阿里云函数计算 FC 部署指南

该脚本可以部署到阿里云函数计算 FC，实现更稳定的自动化运行。

### 1. 准备工作

- 阿里云账号
- 已创建的函数计算服务
- 已创建的 OSS Bucket（用于存储生成的 CSV 文件）

### 2. 创建函数

1. 登录阿里云函数计算控制台
2. 在左侧导航栏中选择 "函数服务"
3. 点击 "创建函数"
4. 选择 "自定义运行时"
5. 配置函数基本信息：
   - 函数名称：daily-trend-fetcher
   - 运行时环境：Python 3.9
   - 内存规格：256 MB
   - 超时时间：60 秒

### 3. 上传代码

1. 将 main.py 和 requirements.txt 文件打包成 zip 格式
2. 在函数配置页面，点击 "上传代码包"
3. 选择打包好的 zip 文件
4. 点击 "确定"

### 4. 配置环境变量

在函数配置页面，点击 "环境变量" 标签页，添加以下环境变量：

- GITHUB_TOKEN: 你的 GitHub Token
- AI_API_KEY: 你的 AI API Key
- AI_BASE_URL: AI API的基础URL
- AI_MODEL: 使用的AI模型名称
- OSS_ACCESS_KEY_ID: 你的OSS AccessKey ID
- OSS_ACCESS_KEY_SECRET: 你的OSS AccessKey Secret
- OSS_ENDPOINT: 你的OSS Endpoint
- OSS_BUCKET_NAME: 你的OSS Bucket名称
- OSS_FILE_PATH: 文件在OSS中的存储路径

### 5. 配置触发器

1. 在函数配置页面，点击 "触发器配置" 标签页
2. 点击 "创建触发器"
3. 选择 "定时触发器"
4. 配置触发器信息：
   - 触发器名称：daily-trigger
   - 触发方式：定时触发
   - Cron表达式：0 8 * * * （每天北京时间8点触发）

### 6. 测试函数

1. 在函数配置页面，点击 "函数代码" 标签页
2. 点击 "测试函数"
3. 查看函数执行日志和结果

## 数据说明

生成的 CSV 文件包含以下字段：

- **项目标签**：AI 生成的项目多标签分类（可包含多个预定义标签，如开源框架/库、开发者工具、教育/学习资源、AI、基础设施/DevOps 等）
- **项目名称**：GitHub 项目名称
- **项目地址**：GitHub 项目链接
- **项目README**：项目 README 内容的中文概括（1-2句话）

## 支持的项目标签类别

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

## 阿里云 OSS 配置指南

### 创建 OSS Bucket

1. 登录阿里云 OSS 管理控制台
2. 在左侧导航栏中选择 "Bucket列表"
3. 点击 "创建Bucket"
4. 配置 Bucket 信息：
   - Bucket名称：选择一个全局唯一的名称
   - 地域：选择离你较近的地域
   - 存储类型：标准存储
   - 读写权限：公共读（根据实际需求选择）

### 获取 OSS 配置信息

1. 在 Bucket 列表页面，点击创建好的 Bucket 名称
2. 在左侧导航栏中选择 "基础设置" -> "概览"
3. 获取 Endpoint 信息（例如：oss-cn-hangzhou.aliyuncs.com）

### 创建 AccessKey

1. 登录阿里云控制台
2. 在右上角头像处，点击 "AccessKey管理"
3. 点击 "创建AccessKey"
4. 获取 AccessKey ID 和 AccessKey Secret

## 进阶玩法建议

1. **自定义搜索条件**：调整 `get_github_trending` 函数中的搜索参数，例如：
   - 修改 `stars:>5000` 搜索条件来获取不同星数级别的项目
   - 添加语言筛选 `language:python`
   - 调整 `per_page` 参数来获取更多或更少的项目
2. **增加更多分析维度**：修改 AI 提示词，获取更多项目信息
3. **数据可视化**：使用工具将 OSS 中的历史数据进行可视化分析
4. **多平台同步**：扩展代码支持同时同步到 Notion、钉钉等其他平台

## 注意事项

- AI 分析结果可能存在误差，特别是对于描述不完整的项目，请人工校对
- API 调用有频率限制，脚本中已添加 `time.sleep(1)` 避免触发限制
- 请妥善保管你的 API Key 和阿里云密钥，不要将其直接提交到代码仓库
- 阿里云函数计算和 OSS 使用会产生一定费用，请关注账单信息

## 许可证

MIT