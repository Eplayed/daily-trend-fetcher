import sys
import os
import oss2
import logging
import time
from datetime import datetime

OSS_ACCESS_KEY_ID = ""
OSS_ACCESS_KEY_SECRET = ""
OSS_ENDPOINT = ""
OSS_BUCKET_NAME = ""
OSS_FILE_PATH = ""
PROJECT_TAG = "all"

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OSSUploader:
    """OSS文件上传工具类"""
    def __init__(self):
        # 从配置文件读取配置
        try:
            import config
            self.OSS_ACCESS_KEY_ID = getattr(config, 'OSS_ACCESS_KEY_ID', '')
            self.OSS_ACCESS_KEY_SECRET = getattr(config, 'OSS_ACCESS_KEY_SECRET', '')
            self.OSS_ENDPOINT = getattr(config, 'OSS_ENDPOINT', '')
            self.OSS_BUCKET_NAME = getattr(config, 'OSS_BUCKET_NAME', '')
            self.OSS_FILE_PATH = getattr(config, 'OSS_FILE_PATH', '')
            self.PROJECT_TAG = getattr(config, 'PROJECT_TAG', '')
            logger.info("成功从配置文件读取OSS配置")
        except ImportError:
            logger.info("未找到配置文件，将从环境变量读取配置")
            self.OSS_ACCESS_KEY_ID = os.environ.get('OSS_ACCESS_KEY_ID', OSS_ACCESS_KEY_ID)
            self.OSS_ACCESS_KEY_SECRET = os.environ.get('OSS_ACCESS_KEY_SECRET', OSS_ACCESS_KEY_SECRET)
            self.OSS_ENDPOINT = os.environ.get('OSS_ENDPOINT', OSS_ENDPOINT)
            self.OSS_BUCKET_NAME = os.environ.get('OSS_BUCKET_NAME', OSS_BUCKET_NAME)
            self.OSS_FILE_PATH = os.environ.get('OSS_FILE_PATH', OSS_FILE_PATH)
            self.PROJECT_TAG = os.environ.get('PROJECT_TAG', PROJECT_TAG)
        except Exception as e:
            logger.error(f"读取配置文件失败: {e}")
            logger.info("请确保正确的OSS配置")
            sys.exit(1)
        
        # 检查配置是否完整
        self._check_config()
    
    def _check_config(self):
        """检查OSS配置是否完整"""
        missing_configs = []
        if not self.OSS_ACCESS_KEY_ID: missing_configs.append('OSS_ACCESS_KEY_ID')
        if not self.OSS_ACCESS_KEY_SECRET: missing_configs.append('OSS_ACCESS_KEY_SECRET')
        if not self.OSS_ENDPOINT: missing_configs.append('OSS_ENDPOINT')
        if not self.OSS_BUCKET_NAME: missing_configs.append('OSS_BUCKET_NAME')
        if not self.OSS_FILE_PATH: missing_configs.append('OSS_FILE_PATH')
        if not self.PROJECT_TAG: missing_configs.append('PROJECT_TAG')
        
        if missing_configs:
            logger.error(f"OSS配置不完整，缺少: {', '.join(missing_configs)}")
            sys.exit(1)
    
    def get_data_file(self):
        """查找要上传的数据文件（优先JSON，后CSV）"""
        # 尝试获取今天的JSON文件
        today = datetime.now().strftime('%Y%m%d')
        json_filename = f"{self.PROJECT_TAG.lower()}_projects_{today}.json"
        
        if os.path.exists(json_filename):
            logger.info(f"找到今天的JSON文件: {json_filename}")
            return json_filename
        
        # 如果今天的JSON文件不存在，尝试CSV文件
        csv_filename = f"{self.PROJECT_TAG.lower()}_projects_{today}.csv"
        if os.path.exists(csv_filename):
            logger.info(f"找到今天的CSV文件: {csv_filename}")
            return csv_filename
        
        # 如果今天的文件不存在，查找最新的JSON文件
        json_files = [f for f in os.listdir('.') if f.startswith('github_stars_projects_') and f.endswith('.json')]
        if json_files:
            # 按文件名排序，最新的文件在最后
            json_files.sort()
            latest_json = json_files[-1]
            logger.info(f"未找到今天的数据文件，使用最新的JSON文件: {latest_json}")
            return latest_json
        
        # 最后尝试查找最新的CSV文件（向后兼容）
        csv_files = [f for f in os.listdir('.') if f.startswith('github_stars_projects_') and f.endswith('.csv')]
        if csv_files:
            # 按文件名排序，最新的文件在最后
            csv_files.sort()
            latest_csv = csv_files[-1]
            logger.info(f"未找到JSON文件，使用最新的CSV文件: {latest_csv}")
            return latest_csv
        
        logger.error("未找到任何数据文件")
        return None
    
    def get_csv_file(self):
        """查找要上传的CSV文件（向后兼容）"""
        return self.get_data_file()
    
    def upload_file_to_oss(self, file_path, oss_file_path=None):
        """上传文件到OSS，增加重试逻辑"""
        if not oss_file_path:
            # 如果未提供OSS文件路径，构建默认路径
            oss_directory = self.OSS_FILE_PATH.rstrip('/') + '/' if self.OSS_FILE_PATH else ''
            oss_file_path = oss_directory + os.path.basename(file_path)
        
        # 设置重试次数和间隔
        max_retries = 3  # 重试次数
        retry_interval = 5  # 秒
        
        # 尝试上传文件
        for attempt in range(max_retries):
            try:
                # 创建OSS认证对象
                auth = oss2.Auth(self.OSS_ACCESS_KEY_ID, self.OSS_ACCESS_KEY_SECRET)
                if attempt == 0:
                    logger.info("创建OSS认证对象成功")
                
                # 创建OSS Bucket对象
                bucket = oss2.Bucket(auth, self.OSS_ENDPOINT, self.OSS_BUCKET_NAME)
                if attempt == 0:
                    logger.info(f"创建OSS Bucket对象成功，Bucket: {self.OSS_BUCKET_NAME}")
                
                # 设置连接超时和重试策略
                oss2.defaults.connect_timeout = 60  # 60秒连接超时
                oss2.defaults.socket_timeout = 60   # 60秒套接字超时
                
                # 上传文件
                logger.info(f"开始上传文件到OSS: {oss_file_path} (尝试 {attempt+1}/{max_retries})...")
                result = bucket.put_object_from_file(oss_file_path, file_path)
                
                if result.status == 200:
                    logger.info(f"✅ 文件上传成功！")
                    logger.info(f"- 本地文件: {file_path}")
                    logger.info(f"- OSS路径: {oss_file_path}")
                    logger.info(f"- OSS Bucket: {self.OSS_BUCKET_NAME}")
                    logger.info(f"- OSS Endpoint: {self.OSS_ENDPOINT}")
                    return True
                else:
                    logger.error(f"文件上传失败，HTTP状态码: {result.status}")
                    if attempt < max_retries - 1:
                        logger.info(f"{retry_interval}秒后重试...")
                        time.sleep(retry_interval)
                    else:
                        break
            except oss2.exceptions.NoSuchBucket as e:
                logger.error(f"Bucket不存在: {self.OSS_BUCKET_NAME}")
                logger.info("请确认Bucket名称是否正确，以及是否已在阿里云OSS控制台创建")
                break
            except oss2.exceptions.NoSuchKey as e:
                logger.error(f"文件不存在或访问权限不足")
                break
            except oss2.exceptions.AccessDenied as e:
                logger.error(f"访问被拒绝，可能是Access Key ID或Access Key Secret不正确")
                logger.info("请确认OSS访问凭证是否正确，并具有足够的权限")
                break
            except oss2.exceptions.ServerError as e:
                logger.error(f"OSS服务器错误: {e}")
                if hasattr(e, 'status') and e.status == 502:
                    logger.info("502错误可能是网络问题、OSS端点配置错误或Bucket不在指定区域")
                    logger.info("请检查:")
                    logger.info(f"1. 网络连接是否正常")
                    logger.info(f"2. OSS_ENDPOINT是否正确(当前: {self.OSS_ENDPOINT})")
                    logger.info(f"3. Bucket '{self.OSS_BUCKET_NAME}'是否在指定的区域")
                if attempt < max_retries - 1:
                    logger.info(f"{retry_interval}秒后重试...")
                    time.sleep(retry_interval)
                else:
                    break
            except oss2.exceptions.RequestError as e:
                logger.error(f"请求错误: {e}")
                logger.info("可能是网络连接问题或OSS端点配置错误")
                if attempt < max_retries - 1:
                    logger.info(f"{retry_interval}秒后重试...")
                    time.sleep(retry_interval)
                else:
                    break
            except Exception as e:
                logger.error(f"上传文件时发生未知错误: {e}")
                import traceback
                traceback.print_exc()
                if attempt < max_retries - 1:
                    logger.info(f"{retry_interval}秒后重试...")
                    time.sleep(retry_interval)
                else:
                    break
        
        # 提供手动上传的建议
        logger.info("\n如果自动上传失败，您可以尝试手动上传:")
        logger.info(f"1. 登录阿里云OSS控制台")
        logger.info(f"2. 找到Bucket: {self.OSS_BUCKET_NAME}")
        logger.info(f"3. 进入目录: {self.OSS_FILE_PATH or '根目录'}")
        logger.info(f"4. 上传文件: {file_path}")
        
        return False
    
    def upload_data(self, filename=None):
        """上传数据文件到OSS，如未指定文件名则自动查找"""
        # 如果未指定文件名，自动查找
        if not filename:
            filename = self.get_data_file()
            if not filename:
                return False
        
        # 构建OSS文件路径
        oss_directory = self.OSS_FILE_PATH.rstrip('/') + '/' if self.OSS_FILE_PATH else ''
        oss_file_path = oss_directory + os.path.basename(filename)
        
        # 上传文件
        return self.upload_file_to_oss(filename, oss_file_path)

# 提供便捷的函数供外部调用
def upload_to_oss(filename=None, access_key_id=None, access_key_secret=None, endpoint=None, bucket_name=None, oss_file_path=None):
    """便捷的上传函数，可直接调用或通过参数覆盖配置"""
    # 创建上传器实例
    uploader = OSSUploader()
    
    # 如果提供了参数，覆盖配置
    if access_key_id: uploader.OSS_ACCESS_KEY_ID = access_key_id
    if access_key_secret: uploader.OSS_ACCESS_KEY_SECRET = access_key_secret
    if endpoint: uploader.OSS_ENDPOINT = endpoint
    if bucket_name: uploader.OSS_BUCKET_NAME = bucket_name
    if oss_file_path:
        # 从路径中提取目录和文件名
        uploader.OSS_FILE_PATH = os.path.dirname(oss_file_path)
        return uploader.upload_file_to_oss(filename, oss_file_path)
    
    # 调用上传数据方法
    return uploader.upload_data(filename)

def main():
    """主函数，用于直接运行脚本"""
    logger.info("===== OSS上传工具 ======")
    
    # 创建OSSUploader实例
    oss_uploader = OSSUploader()
    
    # 查找今天的数据文件
    data_file = oss_uploader.get_data_file()
    if not data_file:
        logger.error("未找到今天的数据文件")
        return
    
    logger.info(f"找到今天的数据文件: {data_file}")
    
    # 上传文件
    success = oss_uploader.upload_file_to_oss(data_file)
    
    logger.info("\n===== 上传结果 ======")
    if success:
        logger.info("✅ 上传成功！")
    else:
        logger.info("❌ 上传失败，请参考上面的错误信息进行排查")
    logger.info("====================")

if __name__ == "__main__":
    main()