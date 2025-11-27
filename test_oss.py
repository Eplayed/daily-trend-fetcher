import os
import sys
import oss2
import logging

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
    logger.info("成功从配置文件读取OSS配置")
except Exception as e:
    logger.error(f"读取配置文件失败: {e}")
    sys.exit(1)

# 检查配置是否完整
if not all([OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_ENDPOINT, OSS_BUCKET_NAME]):
    logger.error("OSS配置不完整")
    sys.exit(1)

logger.info(f"OSS配置信息:")
logger.info(f"- Access Key ID: {OSS_ACCESS_KEY_ID[:3]}****{OSS_ACCESS_KEY_ID[-3:]}")
logger.info(f"- Endpoint: {OSS_ENDPOINT}")
logger.info(f"- Bucket Name: {OSS_BUCKET_NAME}")

try:
    # 创建OSS认证对象
    auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
    logger.info("创建OSS认证对象成功")
    
    # 创建OSS Bucket对象
    bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
    logger.info("创建OSS Bucket对象成功")
    
    # 尝试列出Bucket中的对象
    logger.info("尝试列出Bucket中的对象...")
    objects = list(oss2.ObjectIterator(bucket, max_keys=5))
    if objects:
        logger.info(f"成功列出{len(objects)}个对象:")
        for obj in objects:
            logger.info(f"- {obj.key} (大小: {obj.size} bytes)")
    else:
        logger.info("Bucket中没有对象")
    
    logger.info("OSS连接测试成功！")
except Exception as e:
    logger.error(f"OSS连接测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)