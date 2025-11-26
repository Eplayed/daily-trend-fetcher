import requests
import pandas as pd
from datetime import datetime, timedelta
from openai import OpenAI
import time
import os
import logging
import json

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 确保中文正常显示
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]

# ================= 配置区域 =================
# 优先从环境变量读取配置，如果环境变量不存在则使用默认值
# 1. GitHub Token
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', "")

# 2. AI 配置 (这里以 DeepSeek 为例，兼容 OpenAI 格式)
# 如果用 ChatGPT，Base URL 改为 `https://api.openai.com/v1`
AI_API_KEY = os.environ.get('AI_API_KEY', "sk-42f84356d53a44ecbdbaebbeb5a12738")
AI_BASE_URL = os.environ.get('AI_BASE_URL', "https://dashscope.aliyuncs.com/compatible-mode/v1")
AI_MODEL = os.environ.get('AI_MODEL', "qwen3-max") # 或 gpt-3.5-turbo / gpt-4o-mini

# 3. 飞书配置 (可选)
FEISHU_APP_ID = os.environ.get('FEISHU_APP_ID', "cli_a9acdd01b5f85bde")  # 如不需要飞书功能可留空
FEISHU_APP_SECRET = os.environ.get('FEISHU_APP_SECRET', "TvHIIH4bc5HSWIMhafWPZgmM0deXyIHR")  # 如不需要飞书功能可留空
FEISHU_SPREADSHEET_TOKEN = os.environ.get('FEISHU_SPREADSHEET_TOKEN', "YyQ8smi5vhIiThtOpVZco1HInDg")  # 如不需要飞书功能可留空
FEISHU_SHEET_ID = os.environ.get('FEISHU_SHEET_ID', "5beb2b")  # 如不需要飞书功能可留空 - 从URL中获取的正确工作表ID

# 调试模式
DEBUG_MODE = True

# ===========================================
def get_github_trending():
    """获取过去 24 小时最热门的项目"""
    logger.info("正在抓取 GitHub 数据...")
    
    # 搜索条件：过去 24 小时创建的，按 Star 排序
    # 如果想看老项目近期热门，可以去掉 created 条件，改用 stars:>500
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
        "per_page": 10  # 每天只看前 10 名，贪多嚼不烂
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

def get_feishu_token():
    """获取飞书访问令牌"""
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        logger.warning("飞书App ID或App Secret为空")
        return None
        
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }
    
    try:
        # 确保请求头正确处理Unicode
        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        logger.info(f"正在请求飞书Token: {url}")
        session = requests.Session()
        response = session.post(url, json=payload, headers=headers)
        
        logger.info(f"飞书Token请求响应状态码: {response.status_code}")
        logger.info(f"飞书Token请求响应内容: {response.text}")
        
        if response.status_code == 200:
            token = response.json().get("tenant_access_token")
            if token:
                logger.info(f"成功获取飞书Token")
                return token
            else:
                logger.error(f"飞书Token为空")
                return None
        logger.error(f"获取飞书Token失败: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"飞书API请求异常: {e}")
        return None
    except Exception as e:
        logger.error(f"飞书API其他异常: {e}")
        import traceback
        traceback.print_exc()
        return None

def diagnose_feishu_config():
    """诊断飞书配置问题，提供详细的配置检查和修复建议"""
    logger.info("===== 飞书配置诊断工具 =====")
    results = {
        "config_complete": True,
        "token_success": False,
        "table_access": False,
        "write_permission": False,
        "table_type": "unknown",
        "issues": []
    }
    
    # 1. 配置完整性检查
    logger.info("\n1. 配置完整性检查:")
    if not FEISHU_APP_ID:
        results["config_complete"] = False
        results["issues"].append("FEISHU_APP_ID 未配置")
    if not FEISHU_APP_SECRET:
        results["config_complete"] = False
        results["issues"].append("FEISHU_APP_SECRET 未配置")
    if not FEISHU_SPREADSHEET_TOKEN:
        results["config_complete"] = False
        results["issues"].append("FEISHU_SPREADSHEET_TOKEN 未配置")
    if not FEISHU_SHEET_ID:
        results["config_complete"] = False
        results["issues"].append("FEISHU_SHEET_ID 未配置")
    
    # 打印配置状态
    logger.info(f"- FEISHU_APP_ID: {'已配置' if FEISHU_APP_ID else '未配置'}")
    logger.info(f"- FEISHU_APP_SECRET: {'已配置' if FEISHU_APP_SECRET else '未配置'}")
    logger.info(f"- FEISHU_SPREADSHEET_TOKEN: {'已配置' if FEISHU_SPREADSHEET_TOKEN else '未配置'}")
    logger.info(f"- FEISHU_SHEET_ID: {'已配置' if FEISHU_SHEET_ID else '未配置'} (当前值: {FEISHU_SHEET_ID})")
    
    if not results["config_complete"]:
        logger.error("配置不完整，以下项缺失:")
        for issue in results["issues"]:
            logger.error(f"  - {issue}")
        return results
    
    # 2. Token获取测试
    logger.info("\n2. Token获取测试:")
    token = get_feishu_token()
    if not token:
        results["issues"].append("无法获取飞书访问令牌")
        logger.error("无法获取飞书Token")
        logger.info("可能的原因:")
        logger.info("- FEISHU_APP_ID 和 FEISHU_APP_SECRET 不正确")
        logger.info("- 飞书应用未启用")
        logger.info("- 网络连接问题")
        logger.info("- 应用权限不足")
        return results
    
    results["token_success"] = True
    logger.info("✅ 成功获取飞书Token")
    
    # 3. 表格访问权限测试
    logger.info("\n3. 表格访问权限测试:")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    try:
        session = requests.Session()
        
        # 测试智能表API
        bitable_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_SPREADSHEET_TOKEN}"
        response = session.get(bitable_url, headers=headers)
        if response.status_code == 200:
            results["table_access"] = True
            results["table_type"] = "智能表"
            logger.info("✅ 成功访问智能表")
            logger.info(f"表格类型: 智能表")
        else:
            # 测试普通表格API
            sheet_url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}"
            response = session.get(sheet_url, headers=headers)
            if response.status_code == 200:
                results["table_access"] = True
                results["table_type"] = "普通表格"
                logger.info("✅ 成功访问普通表格")
                logger.info(f"表格类型: 普通表格")
            else:
                results["issues"].append("无法访问表格")
                logger.error(f"无法访问表格，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                logger.info("可能的原因:")
                logger.info(f"- FEISHU_SPREADSHEET_TOKEN 不正确 ({FEISHU_SPREADSHEET_TOKEN})")
                logger.info("- 应用未获得表格的访问权限")
                logger.info("- 表格未共享给应用")
                
                # 检查表格是否存在的另一种方法
                if response.status_code == 404:
                    logger.warning("表格可能不存在，请确认 FEISHU_SPREADSHEET_TOKEN 是否正确")
                elif response.status_code == 403:
                    logger.warning("无访问权限，请确保应用已添加为表格的协作者")
    except Exception as e:
        results["issues"].append(f"表格访问异常: {str(e)}")
        logger.error(f"表格访问异常: {e}")
    
    if not results["table_access"]:
        return results
    
    # 4. Sheet ID 验证
    logger.info("\n4. Sheet ID 验证:")
    try:
        if results["table_type"] == "智能表":
            # 智能表的工作表检查
            tables_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_SPREADSHEET_TOKEN}/tables"
            response = session.get(tables_url, headers=headers)
            if response.status_code == 200:
                tables_data = response.json()
                table_ids = [table['table_id'] for table in tables_data.get('data', {}).get('items', [])]
                if FEISHU_SHEET_ID in table_ids:
                    logger.info(f"✅ Sheet ID '{FEISHU_SHEET_ID}' 在智能表中存在")
                else:
                    results["issues"].append(f"Sheet ID '{FEISHU_SHEET_ID}' 在智能表中不存在")
                    logger.error(f"Sheet ID '{FEISHU_SHEET_ID}' 在智能表中不存在")
                    logger.info(f"智能表中可用的表格ID: {', '.join(table_ids)}")
            else:
                logger.warning(f"无法获取智能表的工作表列表，状态码: {response.status_code}")
        else:
            # 普通表格的工作表检查
            sheets_url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}/sheets"
            response = session.get(sheets_url, headers=headers)
            if response.status_code == 200:
                sheets_data = response.json()
                sheet_ids = [sheet['properties']['sheetId'] for sheet in sheets_data.get('data', {}).get('sheets', [])]
                if FEISHU_SHEET_ID in sheet_ids:
                    logger.info(f"✅ Sheet ID '{FEISHU_SHEET_ID}' 在普通表格中存在")
                else:
                    results["issues"].append(f"Sheet ID '{FEISHU_SHEET_ID}' 在普通表格中不存在")
                    logger.error(f"Sheet ID '{FEISHU_SHEET_ID}' 在普通表格中不存在")
                    logger.info(f"表格中可用的Sheet ID: {', '.join(sheet_ids)}")
            else:
                logger.warning(f"无法获取普通表格的工作表列表，状态码: {response.status_code}")
    except Exception as e:
        logger.error(f"Sheet ID验证异常: {e}")
    
    # 5. 写入权限测试
    logger.info("\n5. 写入权限测试:")
    try:
        test_data = {
            "测试日期": datetime.now().strftime('%Y-%m-%d'),
            "测试项目": "诊断测试",
            "测试Star": 1,
            "测试分类": "工具",
            "测试痛点": "无",
            "测试推荐语": "这是一个诊断测试",
            "测试链接": "https://github.com",
            "测试描述": "配置诊断自动生成的测试数据"
        }
        
        if results["table_type"] == "智能表":
            # 智能表写入测试
            write_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_SPREADSHEET_TOKEN}/tables/{FEISHU_SHEET_ID}/records/batch_create"
            payload = {
                "records": [
                    {"fields": test_data}
                ]
            }
            response = session.post(write_url, headers=headers, json=payload)
        else:
            # 普通表格写入测试
            write_url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}/values/{FEISHU_SHEET_ID}:A1:H2"
            payload = {
                "value_range": {
                    "values": [
                        ["测试日期", "测试项目", "测试Star", "测试分类", "测试痛点", "测试推荐语", "测试链接", "测试描述"],
                        list(test_data.values())
                    ]
                },
                "value_input_option": "USER_ENTERED"
            }
            response = session.put(write_url, headers=headers, json=payload)
        
        logger.info(f"写入API: {write_url}")
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text}")
        
        if response.status_code in [200, 201]:
            results["write_permission"] = True
            logger.info("✅ 写入权限测试通过！")
        else:
            results["issues"].append("写入权限不足或Sheet ID错误")
            logger.error("写入权限测试失败")
            
            # 分析常见错误
            if response.status_code == 404:
                logger.warning("错误: 404 Not Found")
                logger.warning("可能的原因:")
                logger.warning("- Sheet ID 不正确")
                logger.warning("- API URL 格式错误")
                logger.warning("- 表格类型与使用的API不匹配")
            elif response.status_code == 403:
                logger.warning("错误: 403 Forbidden")
                logger.warning("可能的原因:")
                logger.warning("- 应用没有表格的编辑权限")
                logger.warning("- 应用未获得足够的API权限")
                logger.warning("- 表格处于只读状态")
            elif response.status_code == 429:
                logger.warning("错误: 429 Too Many Requests")
                logger.warning("可能的原因: API调用频率过高")
    except Exception as e:
        results["issues"].append(f"写入测试异常: {str(e)}")
        logger.error(f"写入测试异常: {e}")
    
    return results

def test_feishu_connection():
    """测试飞书连接和权限配置"""
    logger.info("===== 开始测试飞书连接 =====")
    
    # 调用诊断工具
    results = diagnose_feishu_config()
    
    # 打印诊断结果总结
    logger.info("\n===== 飞书配置诊断结果 =====")
    logger.info(f"- 配置完整性: {'✅ 完整' if results['config_complete'] else '❌ 不完整'}")
    logger.info(f"- Token获取: {'✅ 成功' if results['token_success'] else '❌ 失败'}")
    logger.info(f"- 表格访问: {'✅ 成功' if results['table_access'] else '❌ 失败'}")
    logger.info(f"- 写入权限: {'✅ 成功' if results['write_permission'] else '❌ 失败'}")
    logger.info(f"- 表格类型: {results['table_type']}")
    
    if results['issues']:
        logger.error("\n发现以下问题:")
        for i, issue in enumerate(results['issues'], 1):
            logger.error(f"{i}. {issue}")
        
        # 提供详细的修复建议
        logger.info("\n修复建议:")
        if "无法获取飞书访问令牌" in results['issues']:
            logger.info("1. 检查FEISHU_APP_ID和FEISHU_APP_SECRET是否正确")
            logger.info("   - 确保从飞书开放平台复制了正确的值")
            logger.info("   - 检查应用是否已启用")
        
        if "无法访问表格" in results['issues']:
            logger.info("2. 检查FEISHU_SPREADSHEET_TOKEN是否正确")
            logger.info("   - 从分享链接中正确提取spreadsheetToken")
            logger.info("3. 确保表格已共享给应用")
            logger.info("   - 打开表格 -> 分享 -> 添加成员 -> 输入应用的App ID")
            logger.info("   - 设置权限为'编辑者'")
        
        if any("Sheet ID" in issue for issue in results['issues']):
            logger.info("4. 检查FEISHU_SHEET_ID是否正确")
            logger.info("   - 正确的获取方式:")
            logger.info("     a. 打开飞书表格")
            logger.info("     b. 点击底部的工作表标签")
            logger.info("     c. 右键点击工作表名称，选择'查看工作表信息'")
            logger.info("     d. 在弹出的对话框中，复制'Sheet ID'字段值")
        
        if "写入权限" in str(results['issues']):
            logger.info("5. 确保应用拥有正确的API权限")
            logger.info("   - 对于普通表格，需要以下权限:")
            logger.info("     - 电子表格读写权限 (sheets:spreadsheet)")
            logger.info("     - 表格读写权限 (sheets:sheet)")
            logger.info("   - 对于智能表，需要以下权限:")
            logger.info("     - 管理多维表格数据 (bitable:app)")
            logger.info("     - 获取多维表格元数据 (bitable:app:readonly)")
            logger.info("     - 获取多维表格数据 (bitable:table:readonly)")
    else:
        logger.info("✅ 所有测试通过！飞书配置正常")
    
    return results['write_permission']
    
    # 3. 尝试调用API获取表格信息
    logger.info("尝试获取表格信息...")
    
    # 尝试不同的API版本
    api_versions = [
        f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}",
        f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}",
        # 智能表API
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_SPREADSHEET_TOKEN}"
    ]
    
    success = False
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    table_type = "普通表格"
    
    for api_url in api_versions:
        try:
            logger.info(f"尝试API: {api_url}")
            session = requests.Session()
            response = session.get(api_url, headers=headers)
            
            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                logger.info("✅ 成功获取表格信息！")
                success = True
                
                # 检查是否为智能表
                if "bitable" in api_url:
                    table_type = "智能表"
                else:
                    table_type = "普通表格"
                    
                logger.info(f"表格类型: {table_type}")
                break
        except Exception as e:
            logger.error(f"API调用异常: {e}")
    
    if not success:
        logger.error("无法获取表格信息，测试失败")
        logger.info("请检查:")
        logger.info("1. FEISHU_SPREADSHEET_TOKEN 是否正确")
        logger.info("2. 应用是否已获得表格的访问权限")
        logger.info("3. 表格是否已共享给应用")
        logger.info("4. 应用是否拥有正确的权限(sheets:spreadsheet, sheets:sheet)")
    else:
        logger.info("===== 飞书连接测试通过 =====")
        
        # 4. 尝试写入一行测试数据
        logger.info("尝试写入测试数据...")
        test_data = [
            ["测试日期", "测试项目", "测试Star", "测试分类", "测试痛点", "测试推荐语", "测试链接", "测试描述"],
            [datetime.now().strftime('%Y-%m-%d'), "测试项目1", 100, "工具", "测试问题", "这是一个测试", "https://github.com", "测试描述内容"]
        ]
        
        # 根据表格类型选择不同的API
        write_apis = []
        
        if table_type == "智能表":
            # 智能表API - 智能表使用不同的数据结构，需要转换为记录格式
            logger.info("检测到智能表，使用智能表API...")
            # 先获取表格字段信息
            try:
                fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_SPREADSHEET_TOKEN}/tables/{FEISHU_SHEET_ID}/fields"
                fields_response = session.get(fields_url, headers=headers)
                logger.info(f"字段信息响应: {fields_response.status_code}, {fields_response.text}")
                
                if fields_response.status_code == 200:
                    fields_data = fields_response.json()
                    logger.info(f"智能表字段信息获取成功")
                    
                    # 尝试写入记录
                    records_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_SPREADSHEET_TOKEN}/tables/{FEISHU_SHEET_ID}/records/batch_create"
                    records_payload = {
                        "records": [
                            {
                                "fields": {
                                    "测试日期": datetime.now().strftime('%Y-%m-%d'),
                                    "测试项目": "测试项目1",
                                    "测试Star": 100,
                                    "测试分类": "工具",
                                    "测试痛点": "测试问题",
                                    "测试推荐语": "这是一个测试",
                                    "测试链接": "https://github.com",
                                    "测试描述": "测试描述内容"
                                }
                            }
                        ]
                    }
                    write_apis.append({
                        "url": records_url,
                        "payload": records_payload
                    })
                else:
                    logger.warning(f"无法获取智能表字段信息，尝试普通表格API作为备选")
            except Exception as e:
                logger.error(f"获取智能表字段信息异常: {e}")
        
        # 添加普通表格API作为备选
        # 新版本API
        write_apis.append({
            "url": f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}/values/{FEISHU_SHEET_ID}:A1:H{len(test_data)}",
            "payload": {
                "value_range": {
                    "values": test_data
                },
                "value_input_option": "USER_ENTERED"
            }
        })
        # 旧版本API
        write_apis.append({
            "url": f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}/sheets/{FEISHU_SHEET_ID}/range_values",
            "payload": {
                "value_range": {
                    "range": f"A1:H{len(test_data)}",
                    "values": test_data
                },
                "override": True
            }
        })
        # 另一种可能的API格式
        write_apis.append({
            "url": f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}/values",
            "payload": {
                "value_ranges": [{
                    "range": f"{FEISHU_SHEET_ID}!A1:H{len(test_data)}",
                    "values": test_data
                }]
            }
        })
        
        write_success = False
        for api in write_apis:
            try:
                logger.info(f"尝试写入API: {api['url']}")
                response = session.put(api['url'], headers=headers, json=api['payload'])
                
                logger.info(f"写入响应状态码: {response.status_code}")
                logger.info(f"写入响应内容: {response.text}")
                
                if response.status_code == 200:
                    logger.info("✅ 成功写入测试数据！")
                    write_success = True
                    break
            except Exception as e:
                logger.error(f"写入异常: {e}")
        
        if not write_success:
            logger.error("无法写入测试数据")
            logger.info("请检查:")
            logger.info("1. FEISHU_SHEET_ID 是否正确")
            logger.info("2. 应用是否拥有表格的编辑权限")
            logger.info("3. 表格是否处于可编辑状态")
            logger.info("\n如何获取正确的Sheet ID:")
            logger.info("- 打开飞书表格")
            logger.info("- 点击底部的工作表标签")
            logger.info("- 右键点击工作表名称，选择'查看工作表信息'")
            logger.info("- 在弹出的对话框中，复制'Sheet ID'字段值")
            logger.info("\n注意:")
            logger.info("- 智能表和普通表格的API不兼容")
            logger.info("- 如果是智能表，需要使用bitable API")
            logger.info("- 确保应用已获得对应的权限(sheets:spreadsheet, sheets:sheet或bitable:app)")
        else:
            logger.info("===== 飞书数据写入测试通过 =====")
    
    return success

def write_to_feishu_sheet(data_list):
    """将数据写入飞书表格，支持普通表格和智能表"""
    if not FEISHU_SPREADSHEET_TOKEN or not FEISHU_SHEET_ID:
        logger.warning("飞书表格配置不完整，跳过写入飞书")
        return False
        
    token = get_feishu_token()
    if not token:
        return False
        
    # 确保请求头正确处理Unicode
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    try:
        session = requests.Session()
        
        # 1. 首先检测表格类型（普通表格还是智能表）
        logger.info("检测飞书表格类型...")
        table_type = "unknown"
        
        # 尝试智能表API
        bitable_api_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_SPREADSHEET_TOKEN}"
        try:
            response = session.get(bitable_api_url, headers=headers)
            if response.status_code == 200:
                table_type = "智能表"
                logger.info("✅ 检测到表格类型: 智能表")
            else:
                # 尝试普通表格API
                sheet_api_url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}"
                response = session.get(sheet_api_url, headers=headers)
                if response.status_code == 200:
                    table_type = "普通表格"
                    logger.info("✅ 检测到表格类型: 普通表格")
                else:
                    logger.warning(f"无法确定表格类型，尝试默认API")
        except Exception as e:
            logger.warning(f"表格类型检测异常: {e}")
        
        # 2. 根据表格类型准备写入数据
        if table_type == "智能表":
            # 智能表需要使用记录格式
            logger.info("使用智能表API格式准备数据...")
            
            # 先获取智能表的字段信息
            fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_SPREADSHEET_TOKEN}/tables/{FEISHU_SHEET_ID}/fields"
            fields_response = session.get(fields_url, headers=headers)
            if fields_response.status_code == 200:
                fields_data = fields_response.json()
                logger.info(f"✅ 智能表字段信息获取成功")
            else:
                logger.warning(f"无法获取智能表字段信息，使用默认映射")
            
            # 准备智能表记录数据
            records = []
            for item in data_list:
                record = {
                    "fields": {
                        "日期": item["日期"],
                        "项目名称": item["项目名称"],
                        "Star数": item["Star数"],
                        "分类": item["分类"],
                        "痛点": item["痛点"],
                        "推荐语": item["推荐语"],
                        "链接": item["链接"],
                        "原始描述": item["原始描述"] or ""
                    }
                }
                records.append(record)
            
            # 智能表写入API
            write_apis = [
                {
                    "url": f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_SPREADSHEET_TOKEN}/tables/{FEISHU_SHEET_ID}/records/batch_create",
                    "payload": {
                        "records": records
                    }
                }
            ]
        else:
            # 普通表格格式
            logger.info("使用普通表格API格式准备数据...")
            
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
            
            # 尝试不同的普通表格写入API
            write_apis = [
                # 新版本API
                {
                    "url": f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}/values/{FEISHU_SHEET_ID}:A1:H{len(all_rows)}",
                    "payload": {
                        "value_range": {
                            "values": all_rows
                        },
                        "value_input_option": "USER_ENTERED"
                    }
                },
                # 旧版本API
                {
                    "url": f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}/sheets/{FEISHU_SHEET_ID}/range_values",
                    "payload": {
                        "value_range": {
                            "range": f"A1:H{len(all_rows)}",
                            "values": all_rows
                        },
                        "override": True
                    }
                },
                # 另一种可能的API格式
                {
                    "url": f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}/values",
                    "payload": {
                        "value_ranges": [{
                            "range": f"{FEISHU_SHEET_ID}!A1:H{len(all_rows)}",
                            "values": all_rows
                        }]
                    }
                }
            ]
        
        # 3. 尝试写入数据
        success = False
        for i, api in enumerate(write_apis):
            logger.info(f"尝试写入API {i+1}/{len(write_apis)}: {api['url']}")
            if DEBUG_MODE:
                logger.debug(f"请求数据: {json.dumps(api['payload'], ensure_ascii=False)}")
            
            # 根据表格类型选择合适的请求方法
            if table_type == "智能表":
                response = session.post(api['url'], headers=headers, json=api['payload'])
            else:
                response = session.put(api['url'], headers=headers, json=api['payload'])
            
            logger.info(f"飞书API响应状态码: {response.status_code}")
            logger.info(f"飞书API响应内容: {response.text}")
            
            if response.status_code in [200, 201]:
                logger.info("✅ 数据已成功写入飞书表格")
                success = True
                break
            logger.error(f"写入飞书表格失败: 状态码={response.status_code}, 响应={response.text}")
        
        if not success:
            logger.error("所有API格式尝试均失败")
            # 提供飞书配置检查建议
            logger.info("请检查以下配置项:")
            logger.info(f"1. FEISHU_SPREADSHEET_TOKEN: {FEISHU_SPREADSHEET_TOKEN}")
            logger.info(f"2. FEISHU_SHEET_ID: {FEISHU_SHEET_ID}")
            logger.info(f"3. 应用是否已添加为表格编辑者")
            logger.info(f"4. 应用是否已获得正确的权限(sheets:spreadsheet, sheets:sheet)")
            logger.info(f"5. 飞书表格是否存在且可访问")
            logger.info("\n配置步骤回顾:")
            logger.info("1. 创建飞书企业自建应用")
            logger.info("2. 获取App ID和App Secret")
            logger.info("3. 添加必要的权限(sheets:spreadsheet, sheets:sheet)")
            logger.info("4. 创建飞书表格并获取spreadsheetToken和sheetId")
            logger.info("5. 将应用添加为表格的编辑者")
            
            # 如果开启调试模式，运行测试函数
            if DEBUG_MODE:
                logger.info("\n运行飞书连接测试...")
                test_feishu_connection()
        
        return success
    except requests.exceptions.RequestException as e:
        logger.error(f"飞书表格写入请求异常: {e}")
        return False
    except Exception as e:
        logger.error(f"飞书表格写入其他异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    try:
        # 如果开启调试模式，先运行飞书连接测试
        if DEBUG_MODE:
            logger.info("\n===== 调试模式：运行飞书连接测试 =====")
            test_feishu_connection()
            logger.info("====================================\n")
            
            # 等待用户输入继续
            input("按Enter键继续执行主程序...")
        
        repos = get_github_trending()
        data_list = []
        
        if not repos:
            logger.warning("未获取到GitHub项目数据")
            # 创建一些模拟数据用于测试飞书功能
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
        logger.info(f"✅ 完成！数据已保存为 {filename}")
        
        # 尝试写入飞书表格
        if data_list:
            write_to_feishu_sheet(data_list)
        else:
            logger.warning("没有数据可写入飞书表格")
            
        # 输出最终状态报告
        logger.info("\n===== 程序运行总结 =====")
        logger.info(f"- 处理项目数量: {len(data_list)}")
        logger.info(f"- 数据已保存到CSV: {filename}")
        logger.info(f"- 飞书配置状态: {'已配置' if FEISHU_SPREADSHEET_TOKEN and FEISHU_SHEET_ID else '未完全配置'}")
        logger.info("====================")
    except Exception as e:
        logger.error(f"程序运行异常: {e}")
        import traceback
        traceback.print_exc()

# 添加一个命令行入口，允许单独测试飞书连接
import re

def validate_sheet_id():
    """验证Sheet ID是否正确的工具，支持URL解析和表格类型检测"""
    logger.info("===== Sheet ID 验证工具 =====")
    
    # 基本配置检查
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        logger.error("FEISHU_APP_ID 或 FEISHU_APP_SECRET 未配置")
        return False
    
    if not FEISHU_SPREADSHEET_TOKEN:
        logger.error("FEISHU_SPREADSHEET_TOKEN 未配置")
        return False
    
    if not FEISHU_SHEET_ID:
        logger.error("FEISHU_SHEET_ID 未配置")
        return False
    
    logger.info(f"当前配置:")
    logger.info(f"- FEISHU_SPREADSHEET_TOKEN: {FEISHU_SPREADSHEET_TOKEN}")
    logger.info(f"- FEISHU_SHEET_ID: {FEISHU_SHEET_ID}")
    
    # 解析用户提供的URL
    user_url = "https://ai.feishu.cn/sheets/YyQ8smi5vhIiThtOpVZco1HInDg?sheet=5beb2b"
    parsed_url = parse_feishu_url(user_url)
    if parsed_url:
        logger.info(f"\n解析用户提供的飞书URL:")
        logger.info(f"- 文档ID: {parsed_url['document_id']}")
        logger.info(f"- Sheet ID: {parsed_url['sheet_id']}")
        
        # 比较解析出的ID与配置的ID是否一致
        if parsed_url['document_id'] == FEISHU_SPREADSHEET_TOKEN:
            logger.info("✅ 文档ID与配置一致")
        else:
            logger.warning("⚠️ 文档ID与配置不一致")
            logger.warning(f"URL中的文档ID: {parsed_url['document_id']}")
            logger.warning(f"配置的SPREADSHEET_TOKEN: {FEISHU_SPREADSHEET_TOKEN}")
        
        if parsed_url['sheet_id'] == FEISHU_SHEET_ID:
            logger.info("✅ Sheet ID与配置一致")
        else:
            logger.warning("⚠️ Sheet ID与配置不一致")
            logger.warning(f"URL中的Sheet ID: {parsed_url['sheet_id']}")
            logger.warning(f"配置的SHEET_ID: {FEISHU_SHEET_ID}")
    
    # 获取Token
    token = get_feishu_token()
    if not token:
        logger.error("无法获取飞书Token")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    try:
        session = requests.Session()
        
        # 先检测表格类型
        table_type = detect_table_type(session, headers)
        
        if table_type == "智能表":
            logger.info("\n尝试获取智能表信息...")
            # 智能表API
            app_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_SPREADSHEET_TOKEN}"
            response = session.get(app_url, headers=headers)
            logger.info(f"API URL: {app_url}")
            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                try:
                    app_data = response.json()
                    logger.info(f"智能表信息: {app_data.get('data', {}).get('app', {}).get('name', '未知')}")
                    
                    # 检查表格ID
                    table_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_SPREADSHEET_TOKEN}/tables/{FEISHU_SHEET_ID}"
                    table_response = session.get(table_url, headers=headers)
                    if table_response.status_code == 200:
                        logger.info(f"✅ Sheet ID '{FEISHU_SHEET_ID}' 在智能表中有效")
                    else:
                        logger.error(f"❌ Sheet ID '{FEISHU_SHEET_ID}' 在智能表中无效")
                except json.JSONDecodeError:
                    logger.error("响应不是有效的JSON格式")
            else:
                logger.error("无法获取智能表信息")
        elif table_type == "普通表格":
            # 尝试获取普通表格的工作表列表
            logger.info("\n尝试获取普通表格的工作表列表...")
            sheets_url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}/sheets"
            response = session.get(sheets_url, headers=headers)
            
            logger.info(f"API URL: {sheets_url}")
            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                try:
                    sheets_data = response.json()
                    logger.info("\n表格中的工作表信息:")
                    
                    if "data" in sheets_data and "sheets" in sheets_data["data"]:
                        found = False
                        for sheet in sheets_data["data"]["sheets"]:
                            sheet_id = sheet["properties"].get("sheetId", "未知")
                            sheet_name = sheet["properties"].get("title", "未知")
                            logger.info(f"- 名称: '{sheet_name}', ID: '{sheet_id}'")
                            
                            if sheet_id == FEISHU_SHEET_ID:
                                found = True
                                logger.info(f"✅ Sheet ID '{FEISHU_SHEET_ID}' 已找到，对应工作表名称: '{sheet_name}'")
                        
                        if not found:
                            logger.error(f"❌ Sheet ID '{FEISHU_SHEET_ID}' 未在表格中找到")
                            logger.info("请使用以上列表中的正确Sheet ID")
                    else:
                        logger.warning("无法解析工作表信息")
                except json.JSONDecodeError:
                    logger.error("响应不是有效的JSON格式")
            else:
                logger.error("无法获取工作表列表")
                analyze_sheet_error(response.status_code)
        else:
            logger.warning(f"未确定表格类型: {table_type}")
            
            # 尝试使用文档API检查URL有效性
            doc_url = f"https://open.feishu.cn/open-apis/drive/v1/files/{FEISHU_SPREADSHEET_TOKEN}/meta"
            response = session.get(doc_url, headers=headers)
            logger.info(f"\n尝试使用文档API验证URL...")
            logger.info(f"API URL: {doc_url}")
            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                logger.info("✅ 文档ID有效，但无法确定具体表格类型")
            else:
                logger.error("❌ 文档ID无效")
                analyze_sheet_error(response.status_code)
        
        logger.info("\n===== Sheet ID 验证完成 =====")
        logger.info("\n如果验证失败，请尝试以下步骤:")
        logger.info(f"1. 确认表格URL: {user_url}")
        logger.info("2. 确认您使用的是正确的配置方式:")
        logger.info("   - FEISHU_SPREADSHEET_TOKEN 应从URL路径中获取: 'YyQ8smi5vhIiThtOpVZco1HInDg'")
        logger.info("   - FEISHU_SHEET_ID 应从URL参数中获取: '5beb2b'")
        logger.info("3. 确保应用已被添加为表格的编辑者:")
        logger.info("   a. 打开飞书表格")
        logger.info("   b. 点击右上角分享按钮")
        logger.info("   c. 在分享设置中添加应用作为编辑者")
        logger.info("   d. 使用应用的App ID (不是名称) 进行搜索: cli_a9acdd01b5f85bde")
        logger.info("4. 确保应用已获得必要的权限:")
        logger.info("   - 基础权限: 文档 (获取文档元数据、文档内容读、文档内容写)")
        logger.info("   - 普通表格: sheets:spreadsheet、sheets:sheet (读写权限)")
        logger.info("   - 智能表: bitable:app、bitable:table (读写权限)")
        logger.info("5. 检查应用状态是否已发布，只有发布后的应用才能正常访问API")
        
    except Exception as e:
        logger.error(f"验证过程发生异常: {e}")
        import traceback
        traceback.print_exc()
    
    return True

def parse_feishu_url(url):
    """解析飞书文档URL，提取文档ID和Sheet ID"""
    try:
        # 匹配飞书表格URL模式
        pattern = r"https://ai\.feishu\.cn/sheets/([^/?]+)(?:\?sheet=([^&]+))?"
        match = re.match(pattern, url)
        if match:
            document_id = match.group(1)
            sheet_id = match.group(2) if match.group(2) else ""
            return {"document_id": document_id, "sheet_id": sheet_id}
        return None
    except Exception:
        return None

def detect_table_type(session, headers):
    """检测表格类型（智能表或普通表格）"""
    logger.info("检测飞书表格类型...")
    
    # 尝试智能表API
    bitable_api_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_SPREADSHEET_TOKEN}"
    try:
        response = session.get(bitable_api_url, headers=headers)
        if response.status_code == 200:
            logger.info("✅ 检测到表格类型: 智能表")
            return "智能表"
    except Exception as e:
        logger.warning(f"智能表检测异常: {e}")
    
    # 尝试普通表格API
    sheet_api_url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}"
    try:
        response = session.get(sheet_api_url, headers=headers)
        if response.status_code == 200:
            logger.info("✅ 检测到表格类型: 普通表格")
            return "普通表格"
    except Exception as e:
        logger.warning(f"普通表格检测异常: {e}")
    
    # 尝试文档API
    doc_api_url = f"https://open.feishu.cn/open-apis/drive/v1/files/{FEISHU_SPREADSHEET_TOKEN}/meta"
    try:
        response = session.get(doc_api_url, headers=headers)
        if response.status_code == 200:
            try:
                doc_data = response.json()
                file_type = doc_data.get('data', {}).get('file_type', '')
                if file_type == 'sheet':
                    logger.info("✅ 检测到文档类型: 电子表格")
                    return "普通表格"
                elif file_type == 'bitable':
                    logger.info("✅ 检测到文档类型: 智能表格")
                    return "智能表"
                else:
                    logger.warning(f"未知文档类型: {file_type}")
            except json.JSONDecodeError:
                pass
    except Exception as e:
        logger.warning(f"文档检测异常: {e}")
    
    logger.warning("无法确定表格类型")
    return "unknown"

def analyze_sheet_error(status_code):
    """分析表格访问错误的可能原因"""
    if status_code == 404:
        logger.warning("错误: 404 Not Found")
        logger.warning("可能的原因:")
        logger.warning("- FEISHU_SPREADSHEET_TOKEN 不正确")
        logger.warning("- 应用没有访问表格的权限")
        logger.warning("- 表格已被删除或移动")
        logger.warning("- 表格是共享文件夹中的文件，但应用没有共享文件夹权限")
    elif status_code == 403:
        logger.warning("错误: 403 Forbidden")
        logger.warning("可能的原因:")
        logger.warning("- 应用没有足够的权限访问表格")
        logger.warning("- 应用已被添加但权限不足")
        logger.warning("- 请确保应用已添加必要的API权限")
    elif status_code == 401:
        logger.warning("错误: 401 Unauthorized")
        logger.warning("可能的原因:")
        logger.warning("- Token过期或无效")
        logger.warning("- 应用认证失败")
    else:
        logger.warning(f"错误: 状态码 {status_code}")
        logger.warning("请检查应用权限和表格配置")


if __name__ == "__main__":
    import sys
    # 设置中文显示
    plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
    
    # 检查是否以测试模式运行
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-feishu":
            logger.info("执行飞书连接测试...")
            test_feishu_connection()
        elif sys.argv[1] == "--validate-sheet-id":
            logger.info("执行Sheet ID验证...")
            validate_sheet_id()
        else:
            logger.info("未知参数，正常运行主程序")
            main()
    else:
        # 正常运行主程序
        main()