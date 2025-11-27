import sys
import os

# 添加当前目录下的libs文件夹到Python模块搜索路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))

import requests
import pandas as pd
from datetime import datetime, timedelta
from openai import OpenAI
import time
import logging
import json
import oss2

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================= 配置区域 =================
# 优先从配置文件读取配置，如果配置文件不存在则从环境变量读取
# 注意：请将 config.py.example 复制为 config.py 并填写实际值
# config.py 已添加到 .gitignore 中，不会被提交到代码仓库

# 默认配置为空字符串
GITHUB_TOKEN = ""
AI_API_KEY = ""
AI_BASE_URL = "https://api.openai.com/v1"
AI_MODEL = "gpt-3.5-turbo"
OSS_ACCESS_KEY_ID = ""
OSS_ACCESS_KEY_SECRET = ""
OSS_ENDPOINT = ""
OSS_BUCKET_NAME = ""
OSS_FILE_PATH = ""

# 尝试从配置文件读取配置
try:
    import config
    # 仅当配置文件中存在且非空时才覆盖默认值
    if hasattr(config, 'GITHUB_TOKEN') and config.GITHUB_TOKEN:
        GITHUB_TOKEN = config.GITHUB_TOKEN
    if hasattr(config, 'AI_API_KEY') and config.AI_API_KEY:
        AI_API_KEY = config.AI_API_KEY
    if hasattr(config, 'AI_BASE_URL') and config.AI_BASE_URL:
        AI_BASE_URL = config.AI_BASE_URL
    if hasattr(config, 'AI_MODEL') and config.AI_MODEL:
        AI_MODEL = config.AI_MODEL
    if hasattr(config, 'OSS_ACCESS_KEY_ID') and config.OSS_ACCESS_KEY_ID:
        OSS_ACCESS_KEY_ID = config.OSS_ACCESS_KEY_ID
    if hasattr(config, 'OSS_ACCESS_KEY_SECRET') and config.OSS_ACCESS_KEY_SECRET:
        OSS_ACCESS_KEY_SECRET = config.OSS_ACCESS_KEY_SECRET
    if hasattr(config, 'OSS_ENDPOINT') and config.OSS_ENDPOINT:
        OSS_ENDPOINT = config.OSS_ENDPOINT
    if hasattr(config, 'OSS_BUCKET_NAME') and config.OSS_BUCKET_NAME:
        OSS_BUCKET_NAME = config.OSS_BUCKET_NAME
    if hasattr(config, 'OSS_FILE_PATH') and config.OSS_FILE_PATH:
        OSS_FILE_PATH = config.OSS_FILE_PATH
    logger.info("成功从配置文件读取配置")
except ImportError:
    logger.info("未找到配置文件，将从环境变量读取配置")
    # 从环境变量读取配置
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', GITHUB_TOKEN)
    AI_API_KEY = os.environ.get('AI_API_KEY', AI_API_KEY)
    AI_BASE_URL = os.environ.get('AI_BASE_URL', AI_BASE_URL)
    AI_MODEL = os.environ.get('AI_MODEL', AI_MODEL)
    OSS_ACCESS_KEY_ID = os.environ.get('OSS_ACCESS_KEY_ID', OSS_ACCESS_KEY_ID)
    OSS_ACCESS_KEY_SECRET = os.environ.get('OSS_ACCESS_KEY_SECRET', OSS_ACCESS_KEY_SECRET)
    OSS_ENDPOINT = os.environ.get('OSS_ENDPOINT', OSS_ENDPOINT)
    OSS_BUCKET_NAME = os.environ.get('OSS_BUCKET_NAME', OSS_BUCKET_NAME)
    OSS_FILE_PATH = os.environ.get('OSS_FILE_PATH', OSS_FILE_PATH)
except Exception as e:
    logger.error(f"读取配置文件时出错: {e}")
    # 出错时从环境变量读取配置
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', "")
    AI_API_KEY = os.environ.get('AI_API_KEY', "")
    AI_BASE_URL = os.environ.get('AI_BASE_URL', "https://api.openai.com/v1")
    AI_MODEL = os.environ.get('AI_MODEL', "gpt-3.5-turbo")
    OSS_ACCESS_KEY_ID = os.environ.get('OSS_ACCESS_KEY_ID', "")
    OSS_ACCESS_KEY_SECRET = os.environ.get('OSS_ACCESS_KEY_SECRET', "")
    OSS_ENDPOINT = os.environ.get('OSS_ENDPOINT', "")
    OSS_BUCKET_NAME = os.environ.get('OSS_BUCKET_NAME', "")
    OSS_FILE_PATH = os.environ.get('OSS_FILE_PATH', "")

# 调试模式
DEBUG_MODE = True

# ===========================================
def get_github_trending():
    """获取GitHub上的高星项目"""
    logger.info("正在抓取 GitHub 高星项目数据...")
    
    url = "https://api.github.com/search/repositories"
    
    # 确保 headers 是ASCII编码
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 搜索条件：高星项目，按 Star 排序，根据DEBUG_MODE决定获取数量
    params = {
        "q": "stars:>5000",
        "sort": "stars",
        "order": "desc",
        "per_page": 3 if DEBUG_MODE else 30
    }
    
    try:
        # 使用 session 来确保正确处理编码
        session = requests.Session()
        # 解决Unicode编码问题
        encoded_headers = {k: v.encode('ascii', 'ignore').decode('ascii') for k, v in headers.items()}
        response = session.get(url, headers=encoded_headers, params=params)
        if response.status_code != 200:
            logger.error(f"GitHub API Error: {response.text}")
            return []
        
        repos = response.json().get('items', [])
        
        # 获取每个项目的README和完整标签信息
        for i, repo in enumerate(repos):
            logger.info(f"正在获取 {repo['name']} 的README和标签信息...")
            
            # 获取README
            readme_url = f"https://raw.githubusercontent.com/{repo['full_name']}/master/README.md"
            try:
                readme_response = session.get(readme_url)
                if readme_response.status_code == 200:
                    repo['readme'] = readme_response.text
                else:
                    # 尝试其他分支
                    readme_url = f"https://raw.githubusercontent.com/{repo['full_name']}/main/README.md"
                    readme_response = session.get(readme_url)
                    if readme_response.status_code == 200:
                        repo['readme'] = readme_response.text
                    else:
                        repo['readme'] = "README not available"
            except Exception as e:
                logger.warning(f"获取README失败: {e}")
                repo['readme'] = "README获取失败"
            
            # 获取完整标签列表
            try:
                tags_url = f"https://api.github.com/repos/{repo['full_name']}/tags"
                tags_response = session.get(tags_url, headers=encoded_headers)
                if tags_response.status_code == 200:
                    repo['all_tags'] = [tag['name'] for tag in tags_response.json()]
                else:
                    repo['all_tags'] = repo.get('topics', [])
            except Exception as e:
                logger.warning(f"获取标签失败: {e}")
                repo['all_tags'] = repo.get('topics', [])
            
            # 避免 API 速率限制
            time.sleep(1)
        
        return repos
    except requests.exceptions.RequestException as e:
        logger.error(f"GitHub 请求异常: {e}")
        # 提供备用数据用于测试
        return [
            {
                'name': 'react',
                'description': 'A declarative, efficient, and flexible JavaScript library for building user interfaces.',
                'html_url': 'https://github.com/facebook/react',
                'stargazers_count': 220000,
                'full_name': 'facebook/react',
                'readme': 'React is a JavaScript library for building user interfaces. It lets you compose complex UIs from small and isolated pieces of code called "components".',
                'all_tags': ['javascript', 'react', 'ui', 'web-development']
            },
            {
                'name': 'tensorflow',
                'description': 'An Open Source Machine Learning Framework for Everyone',
                'html_url': 'https://github.com/tensorflow/tensorflow',
                'stargazers_count': 180000,
                'full_name': 'tensorflow/tensorflow',
                'readme': 'TensorFlow is an end-to-end open source platform for machine learning. It has a comprehensive, flexible ecosystem of tools, libraries and community resources that lets researchers push the state-of-the-art in ML and developers easily build and deploy ML powered applications.',
                'all_tags': ['machine-learning', 'tensorflow', 'deep-learning', 'ai']
            },
            {
                'name': 'kubernetes',
                'description': 'Production-Grade Container Scheduling and Management',
                'html_url': 'https://github.com/kubernetes/kubernetes',
                'stargazers_count': 170000,
                'full_name': 'kubernetes/kubernetes',
                'readme': 'Kubernetes, also known as K8s, is an open-source system for automating deployment, scaling, and management of containerized applications.',
                'all_tags': ['kubernetes', 'containers', 'docker', 'devops', 'cloud']
            }
        ]
    except Exception as e:
        logger.error(f"GitHub 其他异常: {e}")
        import traceback
        traceback.print_exc()
        return []

def analyze_with_ai(repo):
    """调用 AI 进行多标签分类和README概括"""
    try:
        client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
        
        repo_name = repo['name']
        repo_desc = repo['description'] or "无描述"
        repo_url = repo['html_url']
        stars = repo['stargazers_count']
        readme = repo['readme'] or "无README"
        tags = ', '.join(repo['all_tags']) if repo['all_tags'] else "无标签"
        
        logger.info(f"正在分析: {repo_name}...")
        
        # 限制README长度以避免超过token限制
        max_readme_length = 2000
        if len(readme) > max_readme_length:
            readme = readme[:max_readme_length] + "\n... (内容过长，已截断)"
        
        prompt = f"""
        我是一个 GitHub 聚合网站的编辑。请根据以下项目信息，帮我进行多标签分类并概括README内容。
        
        项目名称: {repo_name}
        项目链接: {repo_url}
        原始描述: {repo_desc}
        Star数: {stars}
        标签: {tags}
        README内容: {readme}
        
        请从以下分类中选择适合该项目的所有标签（可以选择多个）：
        开源框架/库（Frameworks & Libraries）
        开发者工具（Developer Tools）
        实用工具/脚本（Utilities/Scripts）
        教育/学习资源（Education/Resources）
        AI
        社区/文化项目（Community/Culture）
        游戏/图形（Games/Graphics）
        科学计算/人工智能（Science/AI）
        移动应用/嵌入式（Mobile/Embedded）
        企业级应用（Enterprise）
        基础设施/DevOps（Infrastructure/DevOps）
        
        请严格按照以下格式返回（不要多余废话）：
        标签: [标签1, 标签2, ...]  # 使用英文逗号分隔，保留中文标签名称
        README概括: [将README内容概括为1-2句话，用中文表达]
        """
        
        completion = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"AI Error: {e}")
        # 根据项目信息手动分配一个合理的标签
        tags = []
        if any(tag in ['ai', 'machine-learning', 'deep-learning', 'neural-network', 'artificial-intelligence'] for tag in repo.get('all_tags', [])):
            tags.extend(['AI', '科学计算/人工智能（Science/AI）'])
        elif any(tag in ['kubernetes', 'docker', 'devops', 'cloud', 'infrastructure'] for tag in repo.get('all_tags', [])):
            tags.append('基础设施/DevOps（Infrastructure/DevOps）')
        elif any(tag in ['react', 'vue', 'angular', 'framework', 'library'] for tag in repo.get('all_tags', [])):
            tags.append('开源框架/库（Frameworks & Libraries）')
        else:
            tags.append('开发者工具（Developer Tools）')
        
        # 概括README
        if repo.get('description'):
            readme_summary = repo['description'] + "（AI概括失败，使用原始描述）"
        else:
            readme_summary = "无法概括README内容（AI概括失败）"
        
        return f"标签: {', '.join(tags)}\nREADME概括: {readme_summary}"

def main():
    """主函数"""
    try:
        repos = get_github_trending()
        data_list = []
        
        if not repos:
            logger.warning("未获取到GitHub项目数据")
            # 创建一些模拟数据用于测试
            data_list.append({
                "项目标签": "开发者工具（Developer Tools）",
                "项目名称": "测试项目",
                "项目地址": "https://github.com",
                "项目README": "这是一个测试项目的README概括"
            })
        else:
            for repo in repos:
                ai_result = analyze_with_ai(repo)
                
                # 解析AI结果
                lines = ai_result.split('\n')
                tags_line = next((line for line in lines if '标签' in line), "标签: 开发者工具（Developer Tools）")
                # 提取标签并去掉可能的方括号
                tags = tags_line.split(':')[1].strip()
                if tags.startswith('[') and tags.endswith(']'):
                    tags = tags[1:-1].strip()
                
                readme_summary_line = next((line for line in lines if 'README概括' in line), "README概括: 无法概括README内容")
                readme_summary = readme_summary_line.split(':')[1].strip()
                
                data_list.append({
                    "项目标签": tags,
                    "项目名称": repo['name'],
                    "项目地址": repo['html_url'],
                    "项目README": readme_summary
                })
                
                # 避免 API 速率限制
                time.sleep(1)

        # 保存到 CSV
        df = pd.DataFrame(data_list)
        filename = f"github_stars_projects_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False, encoding='utf_8_sig')
        logger.info(f"✅ 完成！数据已保存为 {filename}")
        
        # 输出最终状态报告
        logger.info("\n===== 程序运行总结 =====")
        logger.info(f"- 处理项目数量: {len(data_list)}")
        logger.info(f"- 数据已保存到CSV: {filename}")
        logger.info(f"- OSS配置状态: {'已配置' if all([OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_ENDPOINT, OSS_BUCKET_NAME]) else '未完全配置'}")
        logger.info("====================")
    except Exception as e:
        logger.error(f"程序运行异常: {e}")
        import traceback
        traceback.print_exc()

def handler(event, context):
    """函数计算FC入口函数"""
    try:
        logger.info("函数计算FC触发执行")
        
        # 执行主函数
        main()
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "执行成功",
                "timestamp": datetime.now().isoformat()
            })
        }
    except Exception as e:
        logger.error(f"函数执行异常: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "执行失败",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        }


if __name__ == "__main__":
    # 正常运行主程序
    main()