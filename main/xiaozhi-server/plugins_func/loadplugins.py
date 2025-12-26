import importlib
import pkgutil
import multiprocessing

TAG = __name__


def auto_import_modules(package_name):
    """
    自动导入指定包内的所有模块。

    Args:
        package_name (str): 包的名称，如 'functions'。
    """

    # 子进程跳过配置（会继承主进程的配置）
    if multiprocessing.current_process().name != 'MainProcess':
        return
    # 获取包的路径
    package = importlib.import_module(package_name)
    package_path = package.__path__


    # 遍历包内的所有模块
    for _, module_name, _ in pkgutil.iter_modules(package_path):
        # 导入模块
        full_module_name = f"{package_name}.{module_name}"
        importlib.import_module(full_module_name)
        #logger.bind(tag=TAG).info(f"模块 '{full_module_name}' 已加载")