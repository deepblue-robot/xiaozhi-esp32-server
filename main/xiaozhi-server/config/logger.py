import os
import sys
import yaml
import multiprocessing
from loguru import logger
SERVER_VERSION = "0.8.10"
_logger_initialized = False

_initialized = False
def get_module_abbreviation(module_name, module_dict):
    """获取模块名称的缩写，如果为空则返回00
    如果名称中包含下划线，则返回下划线后面的前两个字符
    """
    module_value = module_dict.get(module_name, "")
    if not module_value:
        return "00"
    if "_" in module_value:
        parts = module_value.split("_")
        return parts[-1][:2] if parts[-1] else "00"
    return module_value[:2]


def build_module_string(selected_module):
    """构建模块字符串"""
    return (
        get_module_abbreviation("VAD", selected_module)
        + get_module_abbreviation("ASR", selected_module)
        + get_module_abbreviation("LLM", selected_module)
        + get_module_abbreviation("TTS", selected_module)
        + get_module_abbreviation("Memory", selected_module)
        + get_module_abbreviation("Intent", selected_module)
        + get_module_abbreviation("VLLM", selected_module)
    )


def formatter(record):
    """为没有 tag 的日志添加默认值，并处理动态模块字符串"""
    record["extra"].setdefault("tag", record["name"])
    # 如果没有设置 selected_module，使用默认值
    record["extra"].setdefault("selected_module", "00000000000000")
    # 将 selected_module 从 extra 提取到顶级，以支持 {selected_module} 格式
    record["selected_module"] = record["extra"]["selected_module"]
    return record["message"]

def read_config(config_path):
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    return config


def get_project_dir():
    """获取项目根目录"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"



def setup_logging(
        env: str = "dev"
):
    """
    全局配置 loguru，只需调用一次
    """
    global _initialized

    # 防止重复初始化
    if _initialized:
        return logger

    default_config_path = get_project_dir() + f"data/.config-{env}.yaml"
    default_config = read_config(default_config_path)
    log_config = default_config['log']

    log_format = log_config.get("log_format")
    log_format_file = log_config.get("log_format_file")


    log_level = log_config.get("log_level", "INFO")
    log_dir = log_config.get("log_dir", "tmp")
    log_file = log_config.get("log_file", "server.log")
    data_dir = log_config.get("data_dir", "data")
    rotation: str = "10 MB"
    retention: str = "30 days"
    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)

    # 默认格式
    if log_format is None:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[tag]}</cyan> | "
            "<level>{message}</level>"
        )

    if log_format_file is None:
        log_format_file = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{extra[tag]} | "
            "{message}"
        )

    # ========== 配置全局默认值 ==========
    logger.configure(
        extra={"tag": "default"},  # 设置默认 tag
    )

    # ========== 移除默认 handler ==========
    logger.remove()

    # ========== 添加控制台输出 ==========
    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # ========== 添加文件输出 ==========
    logger.add(
        os.path.join(log_dir, log_file),
        format=log_format_file,
        level=log_level,
        rotation=rotation,  # 日志轮转：10MB / "00:00" / "1 week"
        retention=retention,  # 保留时间
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
        enqueue=True,  # 异步写入，多进程安全
        backtrace=True,
        diagnose=True,
    )

    # ========== 可选：错误日志单独输出 ==========
    logger.add(
        os.path.join(log_dir, "error.log"),
        format=log_format_file,
        level="ERROR",
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        enqueue=True,
    )

    _initialized = True
    logger.info("日志系统初始化完成")

    return logger


def create_connection_logger(selected_module_str):
    """为连接创建独立的日志器，绑定特定的模块字符串"""
    return logger.bind(selected_module=selected_module_str)
