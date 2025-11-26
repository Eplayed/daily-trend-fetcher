# GitHub 每日热门项目抓取工具

这是一个自动化脚本，可以每天抓取 GitHub 上最新热门的项目，并使用 AI 生成中文推荐语和分类信息，最终导出为 CSV 文件或自动同步到飞书表格。

## 功能特点

- 📊 自动抓取过去 24 小时内 Star 数增长最快的 GitHub 项目
- 🤖 使用 AI（OpenAI/DeepSeek）分析项目，生成中文推荐语和分类
- 📁 导出为 CSV 文件，可直接用 Excel 打开
- 📈 支持自动同步到飞书表格，手机即可查看
- ⚡ 通过 GitHub Actions 实现完全自动化，无需服务器

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

### 3. 飞书配置（可选）
如果需要将数据同步到飞书表格，需要准备：
- 飞书开放平台账号
- 创建飞书应用并获取 App ID 和 App Secret
- 准备一个飞书表格并获取表格 Token 和工作表 ID

### 4. Python 环境
- 如果你想在本地运行，需要安装 Python 3.6 或更高版本

## 本地运行指南

### 安装依赖

```bash
pip install requests pandas openai
```

### 配置脚本

编辑 `main.py` 文件，填入你的配置：

```python
# 1. GitHub Token
GITHUB_TOKEN = "你的_GITHUB_TOKEN"

# 2. AI 配置
AI_API_KEY = "你的_AI_API_KEY"
AI_BASE_URL = "https://api.deepseek.com" # 或 https://api.openai.com/v1
AI_MODEL = "deepseek-chat" # 或 gpt-3.5-turbo / gpt-4o-mini

# 3. 飞书配置 (可选)
FEISHU_APP_ID = "你的飞书应用APP_ID"  # 如不需要飞书功能可留空
FEISHU_APP_SECRET = "你的飞书应用APP_SECRET"  # 如不需要飞书功能可留空
FEISHU_SPREADSHEET_TOKEN = "你的飞书表格TOKEN"  # 如不需要飞书功能可留空
FEISHU_SHEET_ID = "你的飞书表格工作表ID"  # 如不需要飞书功能可留空
```

### 运行脚本

```bash
python main.py
```

运行完成后，会在当前目录生成一个 CSV 文件，包含当天的热门项目信息。

## GitHub Actions 自动化配置

为了实现完全自动化，你可以将代码上传到 GitHub 仓库，并配置 GitHub Actions：

### 1. 创建 GitHub 仓库

创建一个新的 GitHub 仓库（例如 `daily-trend-fetcher`），并上传所有文件。

### 2. 配置 Secrets

在仓库的 `Settings` -> `Secrets and variables` -> `Actions` 页面，添加以下密钥：

- **必须配置的密钥：**
  - `MY_GITHUB_TOKEN`: 你的 GitHub Token
  - `AI_API_KEY`: 你的 AI API Key
  
- **如果使用飞书功能，还需配置：**
  - `FEISHU_APP_ID`: 你的飞书应用 App ID
  - `FEISHU_APP_SECRET`: 你的飞书应用 App Secret
  - `FEISHU_SPREADSHEET_TOKEN`: 你的飞书表格 Token
  - `FEISHU_SHEET_ID`: 你的飞书表格工作表 ID

### 3. 启用工作流

GitHub Actions 工作流配置已包含在 `.github/workflows/daily.yml` 文件中，它会：
- 每天 UTC 时间 0:00（北京时间早上 8 点）自动运行
- 运行后将生成的 CSV 文件作为 Artifact 上传

你可以在仓库的 `Actions` 页面手动触发运行或查看历史运行结果。

## 数据说明

生成的 CSV 文件包含以下字段：

- **日期**：数据抓取日期
- **项目名称**：GitHub 项目名称
- **Star数**：项目的 Star 数量
- **分类**：AI 生成的项目分类（工具/AI/框架/资源/其他）
- **痛点**：项目解决的具体问题
- **推荐语**：AI 生成的吸睛介绍
- **链接**：GitHub 项目链接
- **原始描述**：项目的原始英文描述

## 飞书表格集成详细指南

### 1. 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 登录并创建一个新的企业自建应用
3. 在应用设置中，获取 `App ID` 和 `App Secret`
4. 在 "权限管理" 中添加以下权限：
   - `sheets:spreadsheet` - 电子表格读写权限
   - `sheets:sheet` - 表格读写权限

### 2. 获取飞书表格信息

1. 在飞书中创建一个新的电子表格
2. 打开表格，点击右上角的 "分享" 按钮
3. 复制浏览器地址栏中的 URL，从中提取：
   - `spreadsheetToken`: URL 中 `spreadsheet/` 后面的部分
   - `sheetId`: URL 中 `sheet/` 后面的部分（不包含 `?` 及其后面内容）

### 3. 配置飞书权限

1. 在飞书开放平台，将你的应用添加到白名单
2. 在电子表格中，点击 "分享" -> "添加成员" -> 搜索并添加你的应用名称

## 进阶玩法建议

1. **自定义搜索条件**：调整 `get_github_trending` 函数中的搜索参数，例如：
   - 去掉 `created` 条件，改用 `stars:>500` 搜索高 Star 老项目
   - 添加语言筛选 `language:python`
2. **增加更多分析维度**：修改 AI 提示词，获取更多项目信息
3. **数据可视化**：使用工具将历史数据进行可视化分析
4. **多平台同步**：扩展代码支持同时同步到 Notion、钉钉等其他平台

## 注意事项

- AI 分析结果可能存在误差，特别是对于描述不完整的项目，请人工校对
- API 调用有频率限制，脚本中已添加 `time.sleep(1)` 避免触发限制
- 请妥善保管你的 API Key，不要将其直接提交到代码仓库

## 许可证

MIT