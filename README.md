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

## 飞书云文档表格配置指南

如果您想将数据同步到飞书表格，需要进行以下配置：

### 4.1 创建飞书云文档表格

1. 打开飞书，创建一个新的云文档表格
2. 确保表格具有适当的列结构，程序会自动创建所需的列

### 4.2 创建飞书企业自建应用

1. 访问 [飞书开发者中心](https://open.feishu.cn/app)
2. 点击「创建企业自建应用」
3. 填写应用名称和描述，创建应用

### 4.3 配置应用基础权限

1. 在应用详情页中，找到「权限管理」部分
2. 添加以下**基础文档权限**：
   - `获取文档元数据`: 用于获取表格基本信息
   - `文档内容读`: 用于读取表格内容
   - `文档内容写`: 用于写入表格内容

3. 添加以下**电子表格权限**（针对普通表格）：
   - `sheets:spreadsheet:readonly`: 读取电子表格元数据
   - `sheets:spreadsheet:write`: 写入电子表格元数据
   - `sheets:sheet:readonly`: 读取电子表格内工作表数据
   - `sheets:sheet:write`: 写入电子表格内工作表数据

4. 添加以下**智能表格权限**（如果使用智能表）：
   - `bitable:app:readonly`: 读取智能表应用元数据
   - `bitable:app:write`: 写入智能表应用元数据
   - `bitable:table:readonly`: 读取智能表表格数据
   - `bitable:table:write`: 写入智能表表格数据

5. 保存权限配置

### 4.4 获取应用凭证

1. 在应用详情页中，找到「凭证与基础信息」部分
2. 获取 `App ID` 和 `App Secret`，这些将用于环境变量配置
   - 当前配置的App ID: `cli_a9acdd01b5f85bde`

### 4.5 获取表格信息

方法一：从URL获取

1. 打开您的飞书表格：`https://ai.feishu.cn/sheets/YyQ8smi5vhIiThtOpVZco1HInDg?sheet=5beb2b`
2. 从浏览器地址栏复制URL
3. 提取以下值：
   - `FEISHU_SPREADSHEET_TOKEN`: `YyQ8smi5vhIiThtOpVZco1HInDg` (URL路径部分)
   - `FEISHU_SHEET_ID`: `5beb2b` (URL参数sheet的值)

方法二：通过工作表信息获取

1. 打开您创建的飞书表格
2. 右键点击底部的工作表标签
3. 选择「查看工作表信息」
4. 复制「Sheet ID」字段值

### 4.6 配置环境变量

根据您获取的信息，配置以下环境变量：

```bash
# 飞书配置
FEISHU_APP_ID="cli_a9acdd01b5f85bde"
FEISHU_APP_SECRET="您的飞书应用密钥"
FEISHU_SPREADSHEET_TOKEN="YyQ8smi5vhIiThtOpVZco1HInDg"
FEISHU_SHEET_ID="5beb2b"
```

或者直接在代码中修改默认值（已配置了正确的文档ID和Sheet ID）。

### 4.7 发布应用

**重要：应用必须发布后才能正常访问API！**

1. 在应用详情页中，找到「版本管理与发布」部分
2. 创建一个新版本并发布
3. 发布后等待几分钟让配置生效

### 4.8 配置表格协作者（关键步骤）

**这是最常见的错误原因，请务必正确执行！**

1. 打开您的飞书表格：`https://ai.feishu.cn/sheets/YyQ8smi5vhIiThtOpVZco1HInDg?sheet=5beb2b`
2. 点击右上角的分享按钮
3. 在分享设置中，点击「添加协作者」
4. **关键操作**：在搜索框中输入应用的 `App ID`: `cli_a9acdd01b5f85bde`（**不要用应用名称搜索**）
5. 找到您的应用并添加为协作者
6. 设置权限级别为「编辑者」或以上
7. 点击确认并保存设置

### 4.9 验证配置

运行以下命令验证飞书配置：

```bash
python main.py --validate-sheet-id
```

这个工具会帮助您检查：
- 配置是否完整
- Token获取是否成功
- 表格类型是否正确识别
- Sheet ID是否有效
- 应用是否有访问权限

### 4.10 常见问题排查

如果遇到404或403错误，请检查：

1. **应用是否已发布**：只有发布后的应用才能正常访问API
2. **协作者是否正确添加**：确保使用App ID `cli_a9acdd01b5f85bde` 添加，而非名称
3. **权限是否完整**：确保已添加所有必要的权限
4. **表格是否可访问**：确认表格未被删除或移动
5. **等待配置生效**：权限变更后可能需要几分钟时间生效

完成上述配置后，程序将能够自动将数据同步到您的飞书表格。

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