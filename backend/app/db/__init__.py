"""数据库持久化层（可选）。

配置环境变量 ``DATABASE_URL``（如
``mysql+pymysql://user:password@host:3306/energy``）即启用 MySQL 持久化；
留空则整套系统回退到 JSON/CSV 文件存储，保持离线运行与测试不受影响。
"""
