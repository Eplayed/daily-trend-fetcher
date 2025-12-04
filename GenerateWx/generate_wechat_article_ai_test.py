#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timedelta
import openai
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

# ================= 模拟数据生成 =================
def generate_mock_data():
    """生成模拟的开源项目数据"""
    mock_data = [
        {
            "项目名称": "AI智能写作助手",
            "项目标签": "AI,写作,工具",
            "项目README": "这是一个基于AI的智能写作助手，可以帮助用户快速生成文章、报告、邮件等各种文本内容。支持多种文本类型和风格选择，内置丰富的模板和素材库。",
            "项目地址": "https://github.com/example/ai-writing-assistant"
        },
        {
            "项目名称": "智能家居控制中心",
            "项目标签": "智能家居,IoT,自动化",
            "项目README": "一个开源的智能家居控制中心，可以统一管理家中的各种智能设备。支持语音控制、定时任务、场景模式等功能，可扩展性强，兼容多种主流智能设备品牌。",
            "项目地址": "https://github.com/example/smart-home-center"
        },
        {
            "项目名称": "个人财务管理系统",
            "项目标签": "财务管理,数据分析,工具",
            "项目README": "这是一个个人财务管理系统，可以帮助用户记录和分析日常收支、制定预算计划、跟踪投资收益等。界面简洁易用，数据安全可靠，支持多平台同步。",
            "项目地址": "https://github.com/example/finance-manager"
        },
        {
            "项目名称": "在线学习平台",
            "项目标签": "教育,在线学习,平台",
            "项目README": "一个开源的在线学习平台，支持课程发布、视频播放、作业提交、讨论区等功能。专为教育机构和个人教师设计，可以快速搭建自己的在线课程网站。",
            "项目地址": "https://github.com/example/learning-platform"
        },
        {
            "项目名称": "图片处理工具箱",
            "项目标签": "图像处理,工具集,创意",
            "项目README": "这是一个功能强大的图片处理工具箱，包含图像编辑、滤镜效果、批量处理、格式转换等多种功能。界面友好，操作简单，适合设计师和摄影爱好者使用。",
            "项目地址": "https://github.com/example/image-toolkit"
        }
    ]
    return mock_data

# ================= 图片URL生成 =================
def get_project_image_url(project_name, project_url):
    """获取项目图片URL"""
    # 在测试环境中，我们使用占位图片服务
    base_image_url = "https://picsum.photos/800/450?random="
    return f"{base_image_url}{project_name}"

# ================= AI 内容生成函数 =================
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
        return f"""
# AI生成失败提示

由于AI API调用失败，无法生成AI内容。错误信息：{str(e)}
        """

def generate_usage_methods(tags, project_name, project_desc):
    """使用AI生成项目使用方法"""
    prompt = f"""
我刚用了{project_name}这个开源项目，想和朋友简单分享下怎么用。你能帮我用口语化的方式描述下使用方法吗？项目大概是这样的：{project_desc}。就像和朋友聊天一样，不用太正式，100字左右，说清楚核心步骤就行。
"""
    return call_ai_api(prompt, max_tokens=300)

def generate_life_scenarios(tags, project_name, project_desc):
    """使用AI生成项目在生活中的应用场景"""
    prompt = f"""
你能以我个人使用的口吻，简单说下{project_name}这个开源项目在日常生活中怎么用吗？项目大概是：{project_desc}。举1-2个真实的小场景例子，就像和朋友分享自己的使用经历一样，自然一点，每个例子1-2句话就行。
"""
    return call_ai_api(prompt, max_tokens=300)

def generate_side_hustle_guide(tags, project_name, project_desc):
    """使用AI生成如何利用项目开展副业"""
    prompt = f"""
如果用{project_name}这个开源项目赚点外快，你觉得有哪些简单可行的方向？项目是做{project_desc}的。你就以朋友聊天的方式简单说1个方向，2-3句话，别太复杂，实用点。
"""
    return call_ai_api(prompt, max_tokens=300)

def generate_project_desc(project):
    """使用AI优化项目介绍"""
    original_desc = project.get('项目README', '暂无介绍')
    project_name = project.get('项目名称', '未知项目')
    tags = project.get('项目标签', '')
    
    prompt = f"""
我想向朋友推荐{project_name}这个开源项目，你能帮我用聊天的口吻简单介绍一下吗？项目是做{original_desc}的，标签是{tags}。整体保持自然口语化，就像朋友之间分享好东西一样，100-150字左右，别太啰嗦。
"""
    return call_ai_api(prompt, max_tokens=300)

# ================= 文章生成函数 =================
def generate_wechat_article(data, category, date_str):
    """生成公众号文章内容"""
    if not data:
        return """# 未找到数据

无法获取指定日期和分类的数据，请检查参数是否正确。"""
    
    # 格式化当前日期为中文格式
    formatted_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y年%m月%d日')
    
    # 生成AI文章标题
    title_prompt = f"""
想给朋友发个微信分享开源项目，帮忙想个简单亲切的标题，20字左右，别太正式，就像朋友之间分享好东西一样。文章是关于{formatted_date}的{category}领域精选开源项目。
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
想在朋友圈分享几个不错的{category}开源项目，你能帮我写个自然的开头吗？就像和朋友聊天一样，简单打个招呼，说说为什么想分享这些项目，100字左右，别太啰嗦。今天是{formatted_date}。
"""
    article_intro = call_ai_api(intro_prompt, max_tokens=300)
    if not article_intro or "AI生成失败提示" in article_intro:
        # 如果AI生成失败，使用默认引言
        article_intro = f"""
嘿，朋友们！

最近我发现了几个挺有意思的{category}开源项目，用起来感觉还不错，想着分享给你们。这些工具有的能提升工作效率，有的能丰富日常生活，都是免费又好用的。

咱们一起看看吧～
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
想用朋友分享经验的口吻，简单说几个使用开源项目的小技巧。就像平时聊天一样，自然亲切，别太正式，说3个实用的小技巧就行，每个技巧1-2句话。
"""
    usage_guide = call_ai_api(usage_guide_prompt, max_tokens=400)
    if not usage_guide or "AI生成失败提示" in usage_guide:
        # 如果AI生成失败，使用默认内容
        usage_guide = """
## 给新手的开源项目使用小技巧

作为过来人，想和刚开始接触开源项目的朋友分享几个小经验：

1. 别被复杂的文档吓到，先找个最简单的教程跟着做一遍，上手后再慢慢研究细节。

2. 如果遇到问题，除了看文档，还可以去项目的GitHub Issues里搜一搜，说不定已经有人遇到过同样的问题。

3. 刚开始别想着一次性学会所有功能，先把最常用的功能用熟练了再说。
        """
    article += usage_guide + "\n\n"
    
    # 使用AI生成生活场景部分
    life_scenarios_prompt = f"""
你能以我个人经历的口吻，简单说说开源项目在日常生活中都有哪些实际用途吗？就像和朋友聊天一样，自然亲切，举3个具体的小例子，每个例子1-2句话。
"""
    life_scenarios_section = call_ai_api(life_scenarios_prompt, max_tokens=400)
    if not life_scenarios_section or "AI生成失败提示" in life_scenarios_section:
        # 如果AI生成失败，使用默认内容
        life_scenarios_section = """
## 开源项目其实就在我们身边

其实开源项目离我们的生活并不远，我自己就经常用：

1. 我用PhotoPrism搭了个家庭相册，把全家人的照片都存进去，随时都能翻出来看看，特别方便。

2. 用GnuCash记了两年账了，现在对自己的收支情况一目了然，再也不会稀里糊涂不知道钱花哪儿了。

3. 还在家用Home Assistant连了几个智能设备，用手机就能控制灯光和温度，科技感十足。
        """
    article += life_scenarios_section + "\n\n" 
    
    # 使用AI生成副业建议部分
    side_hustle_prompt = f"""
你能以朋友聊天的方式，简单说说怎么用开源项目赚点外快吗？别太复杂，就说3-4个具体可行的方向，每个方向2-3句话，自然口语化。
"""
    side_hustle_section = call_ai_api(side_hustle_prompt, max_tokens=400)
    if not side_hustle_section or "AI生成失败提示" in side_hustle_section:
        # 如果AI生成失败，使用默认内容
        side_hustle_section = """
## 用开源项目赚点外快的几个方向

其实用开源项目赚点零花钱的方法挺多的，我身边就有朋友在做：

1. 如果你对某个开源项目特别熟，可以在网上接技术支持的活儿，帮别人解决问题，按次收费。

2. 可以基于热门开源项目做定制开发，很多小公司或个人用户有这方面的需求，价格也不错。

3. 给常用的开源软件开发插件，好用的话可以设置捐赠或者小额付费下载，积少成多也是一笔收入。

4. 还可以写开源项目的教程或者拍视频，有了流量之后可以接广告或者做知识付费。
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
    article += f"""
---

免责声明：本文仅代表作者个人观点，不构成任何投资建议。所有开源项目信息均来自网络，如有侵权请联系删除。

发布时间：{formatted_date}"""
    
    return article

# ================= 主函数 =================
def main():
    """主函数"""
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("Usage: python generate_wechat_article_ai_test.py <category> [date]")
        print("category: all, frontend, backend, ai, tool, etc.")
        print("date: YYYY-MM-DD format, default is today")
        sys.exit(1)
    
    # 获取分类参数
    category = sys.argv[1]
    
    # 获取日期参数
    if len(sys.argv) > 2:
        date_str = sys.argv[2]
        # 验证日期格式
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            print("Date format error, please use YYYY-MM-DD format")
            sys.exit(1)
    else:
        # 默认使用今天的日期
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    logger.info(f"开始生成{category}分类，{date_str}日期的公众号文章")
    
    # 生成模拟数据
    data = generate_mock_data()
    
    # 仅测试2个项目
    data = data[:2]
    logger.info(f"仅测试前2个项目")
    
    # 生成文章
    article = generate_wechat_article(data, category, date_str)
    
    # 保存文章到文件
    file_name = f"wechat_article_{category}_{date_str}.md"
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(article)
    
    logger.info(f"文章已生成并保存到：{os.path.abspath(file_name)}")

# ================= 程序入口 =================
if __name__ == "__main__":
    main()
