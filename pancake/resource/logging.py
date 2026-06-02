import logging
import logging.config
import os


def logging_init():
    """设置日志配置 - 仅记录到文件"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.getenv("LOG_FILE", "framework.log"), encoding="utf-8")
        ]
    )
    # 减少不必要的日志输出
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("src").setLevel(logging.INFO)

logging_init()
