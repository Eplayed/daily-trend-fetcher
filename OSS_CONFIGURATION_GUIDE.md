# OSS 配置与测试指南

本文档详细说明如何正确配置阿里云OSS（对象存储服务）以及如何测试OSS连接，以解决上传时遇到的502错误问题。

## 一、需要提供的OSS配置项

在`config.py`文件中，需要正确设置以下OSS相关配置项：

```python
# OSS 配置
OSS_ACCESS_KEY_ID = "您的AccessKeyID"       # 必填
OSS_ACCESS_KEY_SECRET = "您的AccessKeySecret" # 必填
OSS_ENDPOINT = "oss-cn-您的区域.aliyuncs.com" # 必填，公网端点
OSS_BUCKET_NAME = "您的Bucket名称"            # 必填
OSS_FILE_PATH = "存储目录/"                  # 可选，默认为根目录
```

### 各配置项的说明：

1. **OSS_ACCESS_KEY_ID** 和 **OSS_ACCESS_KEY_SECRET**
   - 这些是阿里云账号的访问密钥，用于身份验证
   - 获取方法：登录阿里云控制台 -> 访问控制RAM -> 用户 -> 点击用户 -> 安全凭证 -> 创建AccessKey
   - 注意：请妥善保管这些密钥，不要泄露

2. **OSS_ENDPOINT**
   - OSS服务的访问端点，格式为：`oss-cn-区域.aliyuncs.com`
   - 常见区域：`hangzhou`（杭州）、`shanghai`（上海）、`beijing`（北京）、`shenzhen`（深圳）等
   - 本地环境必须使用公网端点，不要使用内部端点（以`-internal`结尾）
   - 可以在阿里云OSS控制台的"概览"页面查看Bucket对应的Endpoint

3. **OSS_BUCKET_NAME**
   - 您在阿里云OSS创建的存储桶名称
   - 存储桶必须已经存在，且位于OSS_ENDPOINT指定的区域
   - 创建方法：登录阿里云OSS控制台 -> 点击"创建Bucket"

4. **OSS_FILE_PATH**
   - 文件在OSS存储桶中的保存路径前缀
   - 例如：`hot/`、`github_trends/`等
   - 若不设置或为空，则保存在存储桶根目录

## 二、如何测试OSS连接

### 方法一：使用提供的测试脚本

项目中已包含`test_oss.py`脚本，用于测试OSS连接是否正常：

```bash
python test_oss.py
```

此脚本会：
1. 读取配置文件中的OSS配置
2. 尝试创建OSS认证对象和Bucket对象
3. 列出Bucket中的前5个对象
4. 输出详细的测试结果和错误信息

### 方法二：使用更详细的上传测试脚本

项目中已包含`upload_csv_to_oss.py`脚本，提供更详细的上传测试：

```bash
python upload_csv_to_oss.py
```

此脚本会：
1. 自动查找最新的数据文件（优先JSON，后CSV）
2. 尝试上传文件到OSS
3. 提供详细的错误诊断和解决方案
4. 在上传失败时给出手动上传建议

## 三、502错误的常见原因及解决方案

上传文件到OSS时遇到502错误，通常是以下原因导致的：

### 1. 网络连接问题
- **症状**：无法连接到OSS服务器，出现连接超时
- **解决方案**：
  - 检查本地网络连接是否正常
  - 确认防火墙或代理设置没有阻止连接
  - 尝试使用`ping oss-cn-区域.aliyuncs.com`测试网络连通性

### 2. OSS端点配置错误
- **症状**：使用了内部端点或错误的区域端点
- **解决方案**：
  - 确保使用公网端点（格式为`oss-cn-区域.aliyuncs.com`）
  - 不要使用内部端点（以`-internal`结尾的端点）
  - 确认端点的区域与Bucket所在区域一致

### 3. Bucket不存在或不在指定区域
- **症状**：显示Bucket不存在的错误
- **解决方案**：
  - 登录阿里云OSS控制台，确认Bucket名称是否正确
  - 检查Bucket是否在OSS_ENDPOINT指定的区域
  - 如Bucket不存在，请先创建Bucket

### 4. 凭证不正确或权限不足
- **症状**：显示访问被拒绝的错误
- **解决方案**：
  - 确认Access Key ID和Access Key Secret是否正确
  - 检查RAM用户是否有足够的OSS访问权限
  - 可以尝试使用阿里云账号的主AccessKey进行测试（仅用于测试）

## 四、替代上传方案

如果您在本地环境无法正常上传到OSS，可以使用以下替代方案：

1.2. **手动上传**：
   - 登录阿里云OSS控制台
   - 找到对应的Bucket
   - 进入指定目录
   - 上传生成的JSON或CSV文件（系统会优先使用JSON格式） **使用模拟上传功能**：
   - 程序会自动将文件复制到`oss_upload_simulator`目录
   - 您可以稍后手动将这些文件上传到OSS

## 五、最佳实践

1. **安全性**：
   - 不要将Access Key直接硬编码在代码中
   - 使用`config.py`文件并将其添加到`.gitignore`
   - 为RAM用户分配最小权限原则

2. **配置验证**：
   - 在上传前检查所有配置项是否完整
   - 使用测试脚本验证配置是否正确
   - 记录详细的日志以便排查问题

3. **错误处理**：
   - 添加适当的错误处理逻辑
   - 实现备用上传方案
   - 提供清晰的错误信息和解决建议

## 六、参考资源

- [阿里云OSS官方文档](https://help.aliyun.com/document_detail/31885.html)
- [OSS Python SDK使用指南](https://help.aliyun.com/document_detail/32026.html)
- [RAM访问控制文档](https://help.aliyun.com/document_detail/28648.html)