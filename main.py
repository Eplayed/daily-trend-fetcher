import requests
import pandas as pd
from datetime import datetime, timedelta
from openai import OpenAI
import time
import os

# ================= 配置区域 =================
# 优先从环境变量读取配置，如果环境变量不存在则使用默认值
# 1. GitHub Token
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', "你的_GITHUB_TOKEN")

# 2. AI 配置 (这里以 DeepSeek 为例，兼容 OpenAI 格式)
# 如果用 ChatGPT，Base URL 改为 `https://api.openai.com/v1`
AI_API_KEY = os.environ.get('AI_API_KEY', "你的_AI_API_KEY")
AI_BASE_URL = os.environ.get('AI_BASE_URL', "https://api.deepseek.com")
AI_MODEL = os.environ.get('AI_MODEL', "deepseek-chat") # 或 gpt-3.5-turbo / gpt-4o-mini

# 3. 飞书配置 (可选)
FEISHU_APP_ID = os.environ.get('FEISHU_APP_ID', "")  # 如不需要飞书功能可留空
FEISHU_APP_SECRET = os.environ.get('FEISHU_APP_SECRET', "")  # 如不需要飞书功能可留空
FEISHU_SPREADSHEET_TOKEN = os.environ.get('FEISHU_SPREADSHEET_TOKEN', "")  # 如不需要飞书功能可留空
FEISHU_SHEET_ID = os.environ.get('FEISHU_SHEET_ID', "")  # 如不需要飞书功能可留空

# ===========================================

def get_github_trending():
    """获取过去 24 小时最热门的项目"""
    print("正在抓取 GitHub 数据...")
    
    # 搜索条件：过去 24 小时创建的，按 Star 排序
    # 如果想看老项目近期热门，可以去掉 created 条件，改用 stars:>500
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    url = "https://api.github.com/search/repositories"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    params = {
        "q": f"created:>{yesterday}",
        "sort": "stars",
        "order": "desc",
        "per_page": 10  # 每天只看前 10 名，贪多嚼不烂
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"GitHub API Error: {response.text}")
        return []
        
    return response.json().get('items', [])

def analyze_with_ai(repo):
    """调用 AI 进行总结和分类"""
    client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    
    repo_name = repo['name']
    repo_desc = repo['description'] or "无描述"
    repo_url = repo['html_url']
    stars = repo['stargazers_count']
    
    print(f"正在分析: {repo_name}...")
    
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
    
    try:
        completion = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"AI Error: {e}")
        return "AI分析失败"

def get_feishu_token():
    """获取飞书访问令牌"""
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        return None
        
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json().get("tenant_access_token")
        print(f"获取飞书Token失败: {response.text}")
        return None
    except Exception as e:
        print(f"飞书API异常: {e}")
        return None

def write_to_feishu_sheet(data_list):
    """将数据写入飞书表格"""
    if not FEISHU_SPREADSHEET_TOKEN or not FEISHU_SHEET_ID:
        print("飞书表格配置不完整，跳过写入飞书")
        return False
        
    token = get_feishu_token()
    if not token:
        return False
        
    # 准备写入数据
    # 飞书表格API要求的格式
    # 先构造标题行
    title_row = ["日期", "项目名称", "Star数", "分类", "痛点", "推荐语", "链接", "原始描述"]
    
    # 构造数据行
    data_rows = []
    for item in data_list:
        row = [
            item["日期"],
            item["项目名称"],
            item["Star数"],
            item["分类"],
            item["痛点"],
            item["推荐语"],
            item["链接"],
            item["原始描述"] or ""
        ]
        data_rows.append(row)
    
    # 组合所有行
    all_rows = [title_row] + data_rows
    
    # 调用飞书API写入数据
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}/sheets/{FEISHU_SHEET_ID}/range_values"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 计算数据范围 (A1到Hn，n为行数)
    row_count = len(all_rows)
    range_str = f"A1:H{row_count}"
    
    payload = {
        "value_range": {
            "range": range_str,
            "values": all_rows
        },
        "override": True  # 覆盖现有数据
    }
    
    try:
        response = requests.put(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"✅ 数据已成功写入飞书表格")
            return True
        print(f"写入飞书表格失败: {response.text}")
        return False
    except Exception as e:
        print(f"飞书表格写入异常: {e}")
        return False

def main():
    repos = get_github_trending()
    data_list = []
    
    for repo in repos:
        ai_result = analyze_with_ai(repo)
        
        # 简单的文本解析（实际生产可以要求 AI 返回 JSON）
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
    print(f"✅ 完成！数据已保存为 {filename}")
    
    # 尝试写入飞书表格
    write_to_feishu_sheet(data_list)

if __name__ == "__main__":
    main()