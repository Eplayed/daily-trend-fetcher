# GenerateWx - 微信公众号文章生成工具

## 项目简介

GenerateWx 是一个用于自动生成微信公众号文章的工具，专门用于推荐每日精选开源项目。该工具能够从阿里云OSS读取项目数据，并使用AI（如OpenAI的GPT模型）生成符合微信公众号风格的文章内容，包括项目介绍、使用方法、生活场景应用和副业指导等。

## 功能特点

- 从阿里云OSS自动读取每日精选开源项目数据
- 使用AI生成口语化、自然流畅的文章内容
- 支持多种AI模型配置（通过OpenAI兼容API）
- 自动生成文章标题、引言、项目介绍等各个部分
- 生成Markdown格式的文章，便于编辑和发布
- 包含项目图片、标签、链接等完整信息
- 支持自定义文章分类

## 配置说明

在使用前，需要配置以下参数：

### 1. 创建配置文件

从项目根目录复制 `config.py.example` 到 `config.py` 并填写以下内容：

```python
# AI 配置
AI_API_KEY = "your_ai_api_key"
AI_BASE_URL = "https://api.openai.com/v1"  # 或其他兼容API的地址
AI_MODEL = "gpt-3.5-turbo"  # 或其他支持的模型

# OSS 配置
OSS_ACCESS_KEY_ID = "your_oss_access_key_id"
OSS_ACCESS_KEY_SECRET = "your_oss_access_key_secret"
OSS_ENDPOINT = "your_oss_endpoint"
OSS_BUCKET_NAME = "your_oss_bucket_name"
```

### 2. 环境变量配置（可选）

如果不想创建配置文件，也可以通过环境变量设置配置：

```bash
export AI_API_KEY="your_ai_api_key"
export AI_BASE_URL="https://api.openai.com/v1"
export AI_MODEL="gpt-3.5-turbo"
export OSS_ACCESS_KEY_ID="your_oss_access_key_id"
export OSS_ACCESS_KEY_SECRET="your_oss_access_key_secret"
export OSS_ENDPOINT="your_oss_endpoint"
export OSS_BUCKET_NAME="your_oss_bucket_name"
```

## 安装依赖

```bash
# 安装所有依赖
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
# 生成指定分类和日期的文章
python generate_wechat_article.py <category> [date]

# 示例：生成所有分类今天的文章
python generate_wechat_article.py all

# 示例：生成前端分类特定日期的文章
python generate_wechat_article.py frontend 2023-10-01
```

### 测试模式

```bash
# 使用测试脚本生成文章（仅测试前2个项目）
python generate_wechat_article_ai_test.py <category> [date]

# 示例：测试生成所有分类今天的文章
python generate_wechat_article_ai_test.py all
```

### 参数说明

- `category`: 文章分类，如 `all`、`frontend`、`backend`、`ai`、`tool` 等
- `date`: 可选参数，日期格式为 `YYYY-MM-DD`，默认为今天
- 测试脚本自动限制只处理前2个项目数据，提高测试效率

## 文章内容结构

生成的文章包含以下几个部分：

1. **文章标题**：由AI生成的吸引人的标题
2. **封面图**：使用第一个项目的相关图片
3. **引言**：介绍文章的主要内容和目的
4. **精选项目一览**：包含多个项目卡片，每个卡片包含：
   - 项目名称和序号
   - 项目图片
   - 项目标签
   - 项目介绍（由AI优化）
   - 如何使用（由AI生成）
   - 生活场景应用（由AI生成）
   - 副业指导（由AI生成）
   - 项目地址链接
5. **使用指南**：详细介绍如何使用这些开源项目
6. **生活场景应用**：介绍开源项目在日常生活中的应用
7. **副业建议**：如何利用开源项目开展副业
8. **结语**：总结文章内容并呼吁互动

## 输出文件

生成的文章会保存为Markdown格式的文件，文件名格式为：

```
wechat_article_<category>_<date>.md
```

## 注意事项

1. 确保AI API密钥和OSS配置正确，否则可能无法正常生成文章
2. 如遇AI生成失败，会使用默认的模板内容替代
3. 文件保存路径默认为当前运行目录
4. 如需调整文章风格或内容，可以修改代码中的提示词模板

## 故障排除

- **无法连接OSS**：检查OSS配置是否正确，网络连接是否正常
- **AI API调用失败**：检查AI_API_KEY和AI_BASE_URL是否正确，API配额是否足够
- **生成内容不符合预期**：调整代码中的提示词模板或AI参数（如temperature）

## 项目结构

```
GenerateWx/
├── generate_wechat_article.py       # 主程序文件
├── generate_wechat_article_ai_test.py  # 测试脚本（仅处理前2个项目）
├── requirements.txt           # 项目依赖
└── README.md                  # 项目说明文档
```