import os
import sys
import oss2
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 从配置文件读取配置
try:
    import config
    OSS_ACCESS_KEY_ID = getattr(config, 'OSS_ACCESS_KEY_ID', '')
    OSS_ACCESS_KEY_SECRET = getattr(config, 'OSS_ACCESS_KEY_SECRET', '')
    OSS_ENDPOINT = getattr(config, 'OSS_ENDPOINT', '')
    OSS_BUCKET_NAME = getattr(config, 'OSS_BUCKET_NAME', '')
    OSS_FILE_PATH = getattr(config, 'OSS_FILE_PATH', '')
    logger.info("成功从配置文件读取OSS配置")
except Exception as e:
    logger.error(f"读取配置文件失败: {e}")
    logger.info("请确保config.py文件存在且包含正确的OSS配置")
    sys.exit(1)

# 检查配置是否完整
missing_configs = []
if not OSS_ACCESS_KEY_ID: missing_configs.append('OSS_ACCESS_KEY_ID')
if not OSS_ACCESS_KEY_SECRET: missing_configs.append('OSS_ACCESS_KEY_SECRET')
if not OSS_ENDPOINT: missing_configs.append('OSS_ENDPOINT')
if not OSS_BUCKET_NAME: missing_configs.append('OSS_BUCKET_NAME')

if missing_configs:
    logger.error(f"OSS配置不完整，缺少: {', '.join(missing_configs)}")
    sys.exit(1)

# 确定要上传的CSV文件
def get_csv_file():
    # 尝试获取今天的CSV文件
    today = datetime.now().strftime('%Y%m%d')
    csv_filename = f"github_stars_projects_{today}.csv"
    
    if os.path.exists(csv_filename):
        logger.info(f"找到今天的CSV文件: {csv_filename}")
        return csv_filename
    
    # 如果今天的文件不存在，查找最新的CSV文件
    csv_files = [f for f in os.listdir('.') if f.startswith('github_stars_projects_') and f.endswith('.csv')]
    if csv_files:
        # 按文件名排序，最新的文件在最后
        csv_files.sort()
        latest_csv = csv_files[-1]
        logger.info(f"未找到今天的CSV文件，使用最新的CSV文件: {latest_csv}")
        return latest_csv
    
    logger.error("未找到任何CSV文件")
    return None

def upload_file_to_oss(file_path, oss_file_path):
    """上传文件到OSS"""
    try:
        # 创建OSS认证对象
        auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
        logger.info("创建OSS认证对象成功")
        
        # 创建OSS Bucket对象
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
        logger.info(f"创建OSS Bucket对象成功，Bucket: {OSS_BUCKET_NAME}")
        
        # 上传文件
        logger.info(f"开始上传文件到OSS: {oss_file_path}")
        
        # 设置连接超时和重试策略
        oss2.defaults.connect_timeout = 30  # 30秒连接超时
        oss2.defaults.socket_timeout = 30   # 30秒套接字超时
        
        # 上传文件
        result = bucket.put_object_from_file(oss_file_path, file_path)
        
        if result.status == 200:
            logger.info(f"✅ 文件上传成功！")
            logger.info(f"- 本地文件: {file_path}")
            logger.info(f"- OSS路径: {oss_file_path}")
            logger.info(f"- OSS Bucket: {OSS_BUCKET_NAME}")
            logger.info(f"- OSS Endpoint: {OSS_ENDPOINT}")
            return True
        else:
            logger.error(f"文件上传失败，HTTP状态码: {result.status}")
            return False
            
    except oss2.exceptions.NoSuchBucket as e:
        logger.error(f"Bucket不存在: {OSS_BUCKET_NAME}")
        logger.info("请确认Bucket名称是否正确，以及是否已在阿里云OSS控制台创建")
    except oss2.exceptions.NoSuchKey as e:
        logger.error(f"文件不存在或访问权限不足")
    except oss2.exceptions.AccessDenied as e:
        logger.error(f"访问被拒绝，可能是Access Key ID或Access Key Secret不正确")
        logger.info("请确认OSS访问凭证是否正确，并具有足够的权限")
    except oss2.exceptions.ServerError as e:
        logger.error(f"OSS服务器错误: {e}")
        if e.status == 502:
            logger.info("502错误可能是网络问题、OSS端点配置错误或Bucket不在指定区域")
            logger.info("请检查:")
            logger.info("1. 网络连接是否正常")
            logger.info("2. OSS_ENDPOINT是否正确(格式应为: oss-cn-region.aliyuncs.com)")
            logger.info("3. Bucket是否在指定的区域")
    except oss2.exceptions.RequestError as e:
        logger.error(f"请求错误: {e}")
        logger.info("可能是网络连接问题或OSS端点配置错误")
    except Exception as e:
        logger.error(f"上传文件时发生未知错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 提供手动上传的建议
    logger.info("\n如果自动上传失败，您可以尝试手动上传:")
    logger.info("1. 登录阿里云OSS控制台")
    logger.info("2. 找到Bucket: {OSS_BUCKET_NAME}")
    logger.info(f"3. 进入目录: {OSS_FILE_PATH or '根目录'}")
    logger.info(f"4. 上传文件: {file_path}")
    
    return False

def main():
    logger.info("===== OSS上传工具 ======")
    
    # 获取要上传的CSV文件
    csv_file = get_csv_file()
    if not csv_file:
        logger.error("没有找到要上传的CSV文件")
        sys.exit(1)
    
    # 构建OSS文件路径
    oss_directory = OSS_FILE_PATH.rstrip('/') + '/' if OSS_FILE_PATH else ''
    oss_file_path = oss_directory + csv_file
    
    # 上传文件
    success = upload_file_to_oss(csv_file, oss_file_path)
    
    logger.info("\n===== 上传结果 ======")
    if success:
        logger.info("✅ 上传成功！")
    else:
        logger.info("❌ 上传失败，请参考上面的错误信息进行排查")
    logger.info("====================")

if __name__ == "__main__":
    main()