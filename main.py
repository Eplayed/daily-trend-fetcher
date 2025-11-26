import requests
import pandas as pd
from datetime import datetime, timedelta
from openai import OpenAI
import time
import os
import logging
import json
import oss2

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================= 配置区域 =================
# 优先从环境变量读取配置，如果环境变量不存在则使用默认值
# 1. GitHub Token
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', "")

# 2. AI 配置
# 注意：请从环境变量设置实际值，不要将敏感信息硬编码在代码中
AI_API_KEY = os.environ.get('AI_API_KEY', "")
AI_BASE_URL = os.environ.get('AI_BASE_URL', "https://api.openai.com/v1")  # 默认使用OpenAI API
AI_MODEL = os.environ.get('AI_MODEL', "gpt-3.5-turbo") # 或 gpt-4o-mini / qwen3-max

# 3. OSS 配置
# 注意：请从环境变量设置实际值，不要将敏感信息硬编码在代码中
OSS_ACCESS_KEY_ID = os.environ.get('OSS_ACCESS_KEY_ID', "")
OSS_ACCESS_KEY_SECRET = os.environ.get('OSS_ACCESS_KEY_SECRET', "")
OSS_ENDPOINT = os.environ.get('OSS_ENDPOINT', "")  # 例如: oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME = os.environ.get('OSS_BUCKET_NAME', "")
OSS_FILE_PATH = os.environ.get('OSS_FILE_PATH', "")  # 例如: github_trends/

# 调试模式
DEBUG_MODE = True

# ===========================================
def get_github_trending():
    """获取过去 24 小时最热门的项目"""
    logger.info("正在抓取 GitHub 数据...")
    
    # 搜索条件：过去 24 小时创建的，按 Star 排序
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    url = "https://api.github.com/search/repositories"
    
    # 确保 headers 是ASCII编码
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    params = {
        "q": f"created:>{yesterday}",
        "sort": "stars",
        "order": "desc",
        "per_page": 10  # 每天只看前 10 名
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
        
        return response.json().get('items', [])
    except requests.exceptions.RequestException as e:
        logger.error(f"GitHub 请求异常: {e}")
        # 提供备用数据用于测试
        return [{
            'name': 'test-repo',
            'description': '测试仓库描述',
            'html_url': 'https://github.com/test/repo',
            'stargazers_count': 100
        }]
    except Exception as e:
        logger.error(f"GitHub 其他异常: {e}")
        import traceback
        traceback.print_exc()
        return []

def analyze_with_ai(repo):
    """调用 AI 进行总结和分类"""
    try:
        client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
        
        repo_name = repo['name']
        repo_desc = repo['description'] or "无描述"
        repo_url = repo['html_url']
        stars = repo['stargazers_count']
        
        logger.info(f"正在分析: {repo_name}...")
        
        prompt = f"""
        我是一个 GitHub 聚合网站的编辑。请根据以下项目信息，帮我生成一段吸引人的中文推荐语。
        
        项目名称: {repo_name}
        项目链接: {repo_url}
        原始描述: {repo_desc}
        Star数: {stars}
        
        请严格按照以下格式返回（不要多余废话）：
        分类: [工具/AI/框架/资源/其他]
        一句话痛点: [这个项目解决了什么具体问题]
        适合人群: [程序员/设计师/小白/学生]
        推荐语: [50字以内的吸睛介绍，口语化]
        """
        
        completion = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "AI分析失败"

def upload_to_oss(file_path, oss_path):
    """将文件上传到OSS"""
    if not all([OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_ENDPOINT, OSS_BUCKET_NAME]):
        logger.warning("OSS配置不完整，跳过上传到OSS")
        return False
    
    try:
        # 创建OSS连接
        auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
        
        # 上传文件
        logger.info(f"正在上传文件到OSS: {file_path} -> {oss_path}")
        result = bucket.put_object_from_file(oss_path, file_path)
        
        # 检查上传是否成功
        if result.status == 200:
            logger.info(f"✅ 文件已成功上传到OSS: {oss_path}")
            return True
        else:
            logger.error(f"上传到OSS失败: 状态码={result.status}")
            return False
    except Exception as e:
        logger.error(f"OSS上传异常: {e}")
        return False

def main():
    """主函数"""
    try:
        repos = get_github_trending()
        data_list = []
        
        if not repos:
            logger.warning("未获取到GitHub项目数据")
            # 创建一些模拟数据用于测试
            data_list.append({
                "日期": datetime.now().strftime('%Y-%m-%d'),
                "项目名称": "测试项目",
                "Star数": 100,
                "分类": "工具",
                "痛点": "解决测试问题",
                "推荐语": "这是一个测试项目",
                "链接": "https://github.com",
                "原始描述": "测试描述"
            })
        else:
            for repo in repos:
                ai_result = analyze_with_ai(repo)
                
                # 简单的文本解析
                lines = ai_result.split('\n')
                category = next((line.split(':')[1] for line in lines if '分类' in line), "未分类").strip()
                pain_point = next((line.split(':')[1] for line in lines if '一句话痛点' in line), "").strip()
                summary = next((line.split(':')[1] for line in lines if '推荐语' in line), "").strip()
                
                data_list.append({
                    "日期": datetime.now().strftime('%Y-%m-%d'),
                    "项目名称": repo['name'],
                    "Star数": repo['stargazers_count'],
                    "分类": category,
                    "痛点": pain_point,
                    "推荐语": summary,
                    "链接": repo['html_url'],
                    "原始描述": repo['description']
                })
                
                # 避免 API 速率限制
                time.sleep(1)

        # 保存到 CSV
        df = pd.DataFrame(data_list)
        filename = f"github_hot_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False, encoding='utf_8_sig')
        logger.info(f"✅ 完成！数据已保存为 {filename}")
        
        # 上传到OSS
        if data_list and OSS_FILE_PATH:
            oss_path = f"{OSS_FILE_PATH.rstrip('/')}/{filename}"
            upload_to_oss(filename, oss_path)
        else:
            logger.warning("OSS文件路径未配置，跳过上传到OSS")
            
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