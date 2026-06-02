import os
import logging

logger = logging.getLogger(__name__)

def check_struct():
    dirs = [
        "src",
        os.path.join("src", "resource"),
        os.path.join("src", "resource", "json"),
        os.path.join("src", "resource", "yaml"),
    ]
    for d in dirs:
        if not os.path.exists(d):
            os.mkdir(d)
            logger.info(f"{d} 目录已创建")
