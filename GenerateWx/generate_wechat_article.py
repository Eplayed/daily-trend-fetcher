#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timedelta
import oss2
import openai

# 添加当前目录到Python路径，确保可以导入GenerateWx目录下的config.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# ================= AI 配置读取 =================
# AI 相关配置
AI_API_KEY = ""
AI_BASE_URL = "https://api.openai.com/v1"
AI_MODEL = "gpt-3.5-turbo"

# 尝试从配置文件读取AI配置
try:
    import config
    # 仅当配置文件中存在且非空时才覆盖默认值
    if hasattr(config, 'AI_API_KEY') and config.AI_API_KEY:
        AI_API_KEY = config.AI_API_KEY
    if hasattr(config, 'AI_BASE_URL') and config.AI_BASE_URL:
        AI_BASE_URL = config.AI_BASE_URL
    if hasattr(config, 'AI_MODEL') and config.AI_MODEL:
        AI_MODEL = config.AI_MODEL
    logger.info("成功从配置文件读取AI配置")
except ImportError:
    logger.info("未找到配置文件，使用默认AI配置或从环境变量读取")
    # 从环境变量读取AI配置
    AI_API_KEY = os.environ.get('AI_API_KEY', AI_API_KEY)
    AI_BASE_URL = os.environ.get('AI_BASE_URL', AI_BASE_URL)
    AI_MODEL = os.environ.get('AI_MODEL', AI_MODEL)
except Exception as e:
    logger.error(f"读取配置文件时出错: {e}")
    # 出错时从环境变量读取配置
    AI_API_KEY = os.environ.get('AI_API_KEY', "")
    AI_BASE_URL = os.environ.get('AI_BASE_URL', "https://api.openai.com/v1")
    AI_MODEL = os.environ.get('AI_MODEL', "gpt-3.5-turbo")

# ================= 配置区域 =================
# 优先从配置文件读取配置，如果配置文件不存在则从环境变量读取
# 默认配置为空字符串
OSS_ACCESS_KEY_ID = ""
OSS_ACCESS_KEY_SECRET = ""
OSS_ENDPOINT = ""
OSS_BUCKET_NAME = ""

# 尝试从配置文件读取配置
try:
    import config
    # 仅当配置文件中存在且非空时才覆盖默认值
    if hasattr(config, 'OSS_ACCESS_KEY_ID') and config.OSS_ACCESS_KEY_ID:
        OSS_ACCESS_KEY_ID = config.OSS_ACCESS_KEY_ID
    if hasattr(config, 'OSS_ACCESS_KEY_SECRET') and config.OSS_ACCESS_KEY_SECRET:
        OSS_ACCESS_KEY_SECRET = config.OSS_ACCESS_KEY_SECRET
    if hasattr(config, 'OSS_ENDPOINT') and config.OSS_ENDPOINT:
        OSS_ENDPOINT = config.OSS_ENDPOINT
    if hasattr(config, 'OSS_BUCKET_NAME') and config.OSS_BUCKET_NAME:
        OSS_BUCKET_NAME = config.OSS_BUCKET_NAME
    logger.info("成功从配置文件读取配置")
except ImportError:
    logger.info("未找到配置文件，将从环境变量读取配置")
    # 从环境变量读取配置
    OSS_ACCESS_KEY_ID = os.environ.get('OSS_ACCESS_KEY_ID', OSS_ACCESS_KEY_ID)
    OSS_ACCESS_KEY_SECRET = os.environ.get('OSS_ACCESS_KEY_SECRET', OSS_ACCESS_KEY_SECRET)
    OSS_ENDPOINT = os.environ.get('OSS_ENDPOINT', OSS_ENDPOINT)
    OSS_BUCKET_NAME = os.environ.get('OSS_BUCKET_NAME', OSS_BUCKET_NAME)
except Exception as e:
    logger.error(f"读取配置文件时出错: {e}")
    # 出错时从环境变量读取配置
    OSS_ACCESS_KEY_ID = os.environ.get('OSS_ACCESS_KEY_ID', "")
    OSS_ACCESS_KEY_SECRET = os.environ.get('OSS_ACCESS_KEY_SECRET', "")
    OSS_ENDPOINT = os.environ.get('OSS_ENDPOINT', "")
    OSS_BUCKET_NAME = os.environ.get('OSS_BUCKET_NAME', "")

# ================= 工具函数 =================
def get_oss_bucket():
    """获取OSS Bucket对象"""
    if not all([OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_ENDPOINT, OSS_BUCKET_NAME]):
        logger.error("OSS配置不完整")
        return None
    
    auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
    return oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)

def fetch_data_from_oss(bucket, date_str, category):
    """从 OSS 读取指定日期和分类的数据文件 (优先JSON)"""
    # 与main.py中的文件格式保持一致
    type_prefix = category.lower() if category and category.lower() != "all" else "all"
    
    # 首先尝试读取JSON文件
    json_file_paths = [
        f"{type_prefix}_projects_{date_str.replace('-', '')}.json",  # 格式: type_projects_YYYYMMDD.json
        f"archive/{type_prefix}_projects_{date_str.replace('-', '')}.json",  # 格式: archive/type_projects_YYYYMMDD.json
        f"{type_prefix}_projects_{date_str}.json",  # 格式: type_projects_YYYY-MM-DD.json
        f"archive/{date_str}.json",  # 格式: archive/YYYY-MM-DD.json
        f"{date_str.replace('-', '')}.json"  # 格式: YYYYMMDD.json
    ]
    
    for file_path in json_file_paths:
        try:
            logger.info(f"尝试读取文件: {file_path}")
            obj = bucket.get_object(file_path)
            content = obj.read().decode('utf-8-sig')  # utf-8-sig 去除 BOM
            data = json.loads(content)
            logger.info(f"成功读取JSON文件: {file_path}")
            return data
        except oss2.exceptions.NoSuchKey:
            # 文件不存在，尝试下一个路径
            logger.info(f"尝试读取JSON文件失败(文件不存在): {file_path}")
            continue
        except json.JSONDecodeError:
            # JSON解析错误，记录日志并继续尝试下一个文件
            logger.warning(f"JSON文件格式错误: {file_path}")
            continue
        except Exception as e:
            logger.error(f"读取JSON文件 {file_path} 失败: {e}")
            continue
    
    logger.error(f"未找到任何有效的JSON数据文件")
    return []

def get_project_image_url(project_name, project_url):
    """获取项目相关图片URL，优先从GitHub项目README中提取"""
    # 如果是GitHub项目，尝试从README中提取图片
    if project_url and "github.com" in project_url:
        try:
            # 构建raw内容URL
            repo_path = project_url.replace("https://github.com/", "").replace("http://github.com/", "")
            readme_url = f"https://raw.githubusercontent.com/{repo_path}/main/README.md"
            
            # 发送请求获取README内容
            response = requests.get(readme_url, timeout=5)
            if response.status_code == 200:
                readme_content = response.text
                
                # 尝试提取README中的第一张图片
                # 匹配Markdown格式的图片: ![alt](url)
                import re
                img_match = re.search(r'!\[[^\]]*\]\(([^)]+)\)', readme_content)
                if img_match:
                    img_url = img_match.group(1)
                    # 如果是相对路径，转换为绝对路径
                    if img_url.startswith('/'):
                        img_url = f"https://github.com{img_url}"
                    elif not img_url.startswith('http'):
                        img_url = f"https://github.com/{repo_path}/raw/main/{img_url}"
                    logger.info(f"从GitHub项目README中提取图片URL: {img_url}")
                    return img_url
        except Exception as e:
            logger.warning(f"获取GitHub项目图片失败: {e}")
    
    # 如果无法从GitHub获取图片或不是GitHub项目，使用占位图服务
    base_image_url = "https://api.dicebear.com/7.x/avataaars/svg?seed="
    
    # 为每个项目生成一个唯一的图片URL
    if project_url:
        # 从URL中提取项目信息作为seed
        seed = project_url.replace("https://", "").replace("http://", "").replace("/", "-")
        return f"{base_image_url}{seed}"
    else:
        # 如果没有URL，使用项目名称作为seed
        return f"{base_image_url}{project_name}"

def call_ai_api(prompt, max_tokens=1000, temperature=0.8):
    """调用AI API生成内容"""
    if not AI_API_KEY:
        logger.error("AI API密钥未配置，无法调用AI API")
        return """
# AI生成失败提示

由于AI API密钥未配置，无法生成AI内容。请在config.py中配置AI_API_KEY、AI_BASE_URL和AI_MODEL参数。
        """
    
    try:
        # 初始化OpenAI客户端
        client = openai.OpenAI(
            api_key=AI_API_KEY,
            base_url=AI_BASE_URL
        )
        
        # 调用AI API
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是一位经验丰富的技术博主，以个人视角和真实体验分享技术内容。你的写作风格非常自然、亲切，完全符合人类日常交流的表达方式。请确保生成的内容：1) 使用自然口语化的表达；2) 避免模板化和模式化的结构；3) 加入个人真实体验感；4) 语言简洁精炼，不冗余；5) 绝对避免任何AI生成特有的痕迹。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
            frequency_penalty=0.2,
            presence_penalty=0.2
        )
        
        # 提取生成的内容
        content = response.choices[0].message.content.strip()
        return content
    except Exception as e:
        logger.error(f"调用AI API失败: {e}")
        return """
# AI生成失败提示

由于AI API调用失败，无法生成AI内容。错误信息：{str(e)}
        """

def generate_usage_methods(tags, project_name, project_desc):
    """使用AI生成项目使用方法"""
    prompt = f"""
我最近在用{project_name}这个开源项目（{tags}），想和朋友分享下实际使用体验。这个项目{project_desc}。

请帮我用自然口语化的方式描述下它的使用方法，就像朋友之间聊天一样。注意：
1. 用"我"的个人体验视角来写
2. 不说"按照要求""首先"这种模板化的话
3. 内容要简洁，重点突出，别太啰嗦
4. 加入一点使用时的小感受或小技巧
5. 100字左右就行，别太长
"""
    return call_ai_api(prompt, max_tokens=300)

def generate_life_scenarios(tags, project_name, project_desc):
    """使用AI生成项目在生活中的应用场景"""
    prompt = f"""
我发现{project_name}这个开源工具（{tags}）挺有意思的，它{project_desc}。

你能帮我用个人经历的口吻，说说它在日常生活中的实际应用场景吗？注意：
1. 用"我"或"我朋友"的真实经历来举例
2. 语气要自然，像和朋友聊天一样
3. 具体描述1-2个生活场景，别太笼统
4. 加入一点使用后的小感受
5. 100字左右，简洁明了
"""
    return call_ai_api(prompt, max_tokens=300)

def generate_side_hustle_guide(tags, project_name, project_desc):
    """使用AI生成如何利用项目开展副业"""
    prompt = f"""
我知道{project_name}这个开源项目（{tags}）挺实用的，它{project_desc}。

你能以一个有经验的自由职业者的口吻，分享下怎么利用这个项目赚点外快吗？注意：
1. 用"我"的第一人称经验分享
2. 语气要实在，不说空话
3. 给出1-2个具体可行的副业方向
4. 说点实际操作中的小建议
5. 100字左右，简洁实用
"""
    return call_ai_api(prompt, max_tokens=300)

def generate_project_desc(project):
    """使用AI优化项目介绍"""
    original_desc = project.get('项目README', '暂无介绍')
    project_name = project.get('项目名称', '未知项目')
    tags = project.get('项目标签', '')
    
    prompt = f"""
我最近发现了一个叫{project_name}的开源项目（{tags}），原始介绍是这样的：{original_desc}。

请帮我用自然口语化的方式重新介绍一下，就像我在向朋友推荐一样。注意：
1. 用"我"的个人推荐视角
2. 突出项目最吸引我的亮点和核心功能
3. 加入一点我对这个项目的直观感受
4. 语言要简洁，别太啰嗦
5. 100字左右，重点突出
"""
    return call_ai_api(prompt, max_tokens=300)

def generate_wechat_article(data, category, date_str):
    """生成公众号文章内容"""
    if not data:
        return """# 未找到数据

无法获取指定日期和分类的数据，请检查参数是否正确。"""
    
    # 格式化当前日期为中文格式
    formatted_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y年%m月%d日')
    
    # 生成AI文章标题
    title_prompt = f"""
我今天整理了一份{formatted_date}的{category}开源项目推荐清单，想给朋友发个微信分享。你能帮我想个简单亲切的标题吗？就像朋友之间聊天一样，别太正式，15-20字左右。
"""
    article_title = call_ai_api(title_prompt, max_tokens=50)
    if not article_title or "AI生成失败提示" in article_title:
        # 如果AI生成失败，使用默认标题
        article_title = f"{formatted_date} {category}精选开源项目推荐"
    
    # 文章标题
    article = f"""# {article_title}\n\n"""
    
    # 文章封面图（使用第一个项目的图片）
    if data:
        first_project = data[0]
        cover_image_url = get_project_image_url(first_project.get('项目名称', '开源项目'), 
                                              first_project.get('项目地址', ''))
        article += f"![封面图]({cover_image_url})\n\n"
    
    # 生成AI文章引言
    intro_prompt = f"""
我今天整理了一份{formatted_date}的{category}开源项目推荐，想在朋友圈分享。你能帮我用自然口语化的方式写一段开头吗？就像和朋友聊天一样，说说我为什么想分享这些项目，语气要亲切，别太正式。150字左右就行。
"""
    article_intro = call_ai_api(intro_prompt, max_tokens=400)
    if not article_intro or "AI生成失败提示" in article_intro:
        # 如果AI生成失败，使用默认引言
        article_intro = f"""
大家好呀！

最近我在GitHub上又挖到了一些实用的开源项目，忍不住想和你们分享。这些项目都是我自己试用过或者仔细研究过的，确实能解决一些实际问题或者提升效率。

今天的这份清单涵盖了{category}领域的几个精选项目，希望能给你们的工作或学习带来一点帮助。话不多说，我们直接来看项目吧！
        """
    article += article_intro + "\n\n"
    
    # 项目列表
    article += "## 精选项目一览\n\n"
    
    # 生成项目卡片
    for i, project in enumerate(data, 1):
        project_name = project.get('项目名称', '未知项目')
        project_tags = project.get('项目标签', '').replace('[', '').replace(']', '')
        project_desc = project.get('项目README', '暂无介绍')
        project_url = project.get('项目地址', '')
        
        # 获取项目图片
        project_image_url = get_project_image_url(project_name, project_url)
        
        # 使用AI生成项目介绍、使用方法、生活场景和副业指导
        optimized_desc = generate_project_desc(project)
        if not optimized_desc or "AI生成失败提示" in optimized_desc:
            optimized_desc = project_desc
        
        usage_methods = generate_usage_methods(project_tags, project_name, project_desc)
        if not usage_methods or "AI生成失败提示" in usage_methods:
            # 如果AI生成失败，使用默认内容
            usage_methods = f"按照项目README中的安装指南进行部署，建议先从基础功能开始试用，逐步探索高级特性。如有问题，可以查看项目的Issues页面或加入社区寻求帮助。"
        
        life_scenarios = generate_life_scenarios(project_tags, project_name, project_desc)
        if not life_scenarios or "AI生成失败提示" in life_scenarios:
            # 如果AI生成失败，使用默认内容
            life_scenarios = f"{project_name}在日常生活中有很多应用场景，比如辅助学习、提高工作效率、解决实际问题等。你可以根据自己的需求，发挥创意，探索更多有趣的用法。"
        
        side_hustle_guide = generate_side_hustle_guide(project_tags, project_name, project_desc)
        if not side_hustle_guide or "AI生成失败提示" in side_hustle_guide:
            # 如果AI生成失败，使用默认内容
            side_hustle_guide = f"围绕{project_name}，你可以提供技术支持、定制化开发、培训课程等服务。也可以将{project_name}与其他技术结合，开发创新应用。建议先积累一些成功案例，然后通过社交媒体和专业平台宣传自己的服务。"
        
        # 项目卡片
        article += f"""### {i}. {project_name}\n\n"""
        article += f"![{project_name}]({project_image_url})\n\n"
        article += f"**项目标签**: {project_tags}\n\n"
        article += f"**项目介绍**: {optimized_desc}\n\n"
        article += f"**如何使用**: {usage_methods}\n\n"
        article += f"**生活场景应用**: {life_scenarios}\n\n"
        article += f"**副业指导**: {side_hustle_guide}\n\n"
        article += f"**项目地址**: [{project_url}]({project_url})\n\n"
        
        # 添加项目分隔符
        if i < len(data):
            article += "---\n\n"
    
    # 使用AI生成使用指南部分
    usage_guide_prompt = f"""
我发现很多朋友对开源项目感兴趣，但不知道从何入手。你能以我的口吻，给他们分享一些使用开源项目的实用经验吗？就像朋友之间聊天一样，别说太多技术术语，重点说说实际操作中需要注意的地方。5个简单的小技巧就行，每个技巧用1-2句话说清楚，别太啰嗦。
"""
    usage_guide = call_ai_api(usage_guide_prompt, max_tokens=800)
    if not usage_guide or "AI生成失败提示" in usage_guide:
        # 如果AI生成失败，使用默认内容
        usage_guide = """
## 给新手的开源项目使用小技巧

很多朋友问我怎么开始用开源项目，其实没那么复杂，分享几个我自己的小经验：

1. **先看README**：不管对哪个项目感兴趣，第一步一定是仔细看README文档，这里面基本包含了所有你需要知道的信息。

2. **从小需求入手**：刚开始别想着一下子掌握全部功能，先解决一个具体的小问题，用熟了再慢慢探索其他功能。

3. **善用搜索**：遇到问题别急着放弃，先在项目的Issues里搜索关键词，很可能已经有人遇到过同样的问题并解决了。

4. **动手实践**：光看文档是不够的，一定要自己动手安装、配置、运行，遇到问题才能真正理解项目。

5. **加入社区**：如果真的喜欢某个项目，可以加入它的社区，和其他开发者交流，不仅能解决问题，还能学到更多。
        """
    article += usage_guide + "\n\n"
    
    # 使用AI生成生活场景部分
    life_scenarios_prompt = f"""
你能以我的口吻，分享一些开源项目在日常生活中的实际应用案例吗？就像朋友之间聊天一样，说说我或我身边朋友是怎么用开源项目解决实际问题的。举3个具体的小例子，每个例子用1-2句话说清楚，别太啰嗦。
"""
    life_scenarios_section = call_ai_api(life_scenarios_prompt, max_tokens=800)
    if not life_scenarios_section or "AI生成失败提示" in life_scenarios_section:
        # 如果AI生成失败，使用默认内容
        life_scenarios_section = """
## 开源项目其实就在我们身边

很多人觉得开源项目离自己很远，其实它早就渗透到我们的日常生活中了。分享几个我和朋友的真实经历：

### 用开源工具做家庭相册

我朋友用开源的PhotoPrism搭建了一个家庭相册服务器，把全家人的照片都存了进去，不仅可以自动分类整理，还能通过手机随时查看，比存在网盘里安全多了。

### 用开源软件管理个人财务

我自己一直在用开源的GnuCash管理个人财务，它虽然界面简单，但功能很强大，能帮我清楚地记录每一笔收入和支出，还能生成各种财务报表，让我对自己的财务状况一目了然。

### 用开源系统搭建智能家居

我邻居用开源的Home Assistant配合树莓派，自己动手搭建了一套智能家居系统，实现了灯光、空调、窗帘的自动化控制，成本不到市面上同类产品的三分之一。
        """
    article += life_scenarios_section + "\n\n" 
    
    # 使用AI生成副业建议部分
    side_hustle_prompt = f"""
我有个朋友想利用开源项目赚点外快，但不知道从何入手。你能以我的口吻，给他分享一些实用的副业方向吗？就像朋友之间聊天一样，别说太多理论，重点说说实际可行的方法和操作建议。4个具体的方向就行，每个方向用2-3句话说清楚，要实在一点。
"""
    side_hustle_section = call_ai_api(side_hustle_prompt, max_tokens=1000)
    if not side_hustle_section or "AI生成失败提示" in side_hustle_section:
        # 如果AI生成失败，使用默认内容
        side_hustle_section = """
## 用开源项目赚点外快的几个方向

很多朋友问我能不能用开源项目赚点外快，其实还真的可以。分享几个我知道的可行方向：

### 1. 做技术支持

如果你对某个热门开源项目特别熟悉，可以在一些技术平台上接技术支持的单子。很多中小企业在用开源项目但没人懂维护，他们愿意花钱请人解决问题。

### 2. 定制开发

有些企业需要基于开源项目做定制化开发，如果你有开发能力，可以接这类活。比如给WordPress做个企业主题，或者给开源ERP系统加个模块。

### 3. 开发插件

给热门开源软件开发插件或扩展也是个不错的选择。比如给VS Code、Chrome或者Obsidian开发插件，做好了可以在应用商店收费，或者接受捐赠。

### 4. 写教程

如果你擅长写作，可以写一些开源项目的入门教程，发布在知乎、CSDN等平台上。有了一定的阅读量后，可以接广告或者开付费专栏，收入也不错。
        """
    article += side_hustle_section + "\n\n"
    
    # 使用AI生成结语
    conclusion_prompt = f"""
你能以我的口吻，给这篇开源项目推荐文章写个自然亲切的结尾吗？就像和朋友聊天一样，简单总结下今天分享的内容，表达下感谢，再提醒他们点个赞或者分享给需要的朋友。100字左右就行，别太正式。
"""
    conclusion = call_ai_api(conclusion_prompt, max_tokens=300)
    if not conclusion or "AI生成失败提示" in conclusion:
        # 如果AI生成失败，使用默认结语
        conclusion = """
好了，今天的开源项目推荐就到这里了。

这些项目都是我最近觉得比较实用或者有趣的，希望能给你们的工作或学习带来一点帮助。开源世界真的很精彩，有很多免费又好用的工具等着我们去发现。

如果你觉得这篇文章还不错，别忘了点个赞支持一下，也可以分享给身边同样喜欢技术的朋友。你们的支持是我继续分享的动力！

咱们下次再见啦！
        """
    article += conclusion + "\n\n"
    
    # 文章尾部
    article += f"""---\n\n**免责声明**：本文推荐的开源项目仅供学习和参考，使用前请仔细阅读项目的许可协议。\n\n**发布时间**：{formatted_date}\n\n"""
    
    return article

def main():
    """主函数"""
    # 解析命令行参数
    category = sys.argv[1] if len(sys.argv) > 1 else "all"
    date_str = sys.argv[2] if len(sys.argv) > 2 else datetime.now().strftime('%Y-%m-%d')
    
    # 检查是否是测试模式（只处理2条项目）
    is_test_mode = len(sys.argv) > 3 and sys.argv[3] == "test"
    
    logger.info(f"开始生成公众号文章: 分类={category}, 日期={date_str}, 测试模式={is_test_mode}")
    
    # 获取OSS Bucket
    bucket = get_oss_bucket()
    if not bucket:
        logger.error("无法连接到OSS，程序退出")
        return
    
    # 从OSS读取数据
    data = fetch_data_from_oss(bucket, date_str, category)
    if not data:
        logger.error("未获取到数据，无法生成文章")
        return
    
    # 测试模式下，只处理前2条项目
    if is_test_mode:
        data = data[:2]  # 只使用前2条项目
        logger.info(f"测试模式：仅处理前{len(data)}条项目")
    
    # 生成公众号文章
    article = generate_wechat_article(data, category, date_str)
    
    # 保存文章到当前目录
    filename = f"wechat_article_{category}_{date_str}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(article)
    
    logger.info(f"公众号文章已保存到: {filename}")

if __name__ == "__main__":
    main()
