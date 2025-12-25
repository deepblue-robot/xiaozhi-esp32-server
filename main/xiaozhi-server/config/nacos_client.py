import nacos
import json
import threading
import time
from typing import Callable, Optional
import socket
import os
import yaml


def get_instance_ip() -> str:
    """
    自动获取当前服务实例的真实 IP
    - 支持本地运行
    - 支持 Docker 容器
    - 支持 Kubernetes Pod（使用 POD_IP 自动注入）
    """

    # 如果 K8s 注入了 POD_IP，优先使用
    pod_ip = os.getenv("POD_IP")
    if pod_ip:
        return pod_ip

    # 通用方式：适用于本地 + Docker
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 不需要真的连得上，只是为了获取本机出口 IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        pass

    # 兜底：有些 Docker 网络下需要这样获取
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "127.0.0.1"

class NacosClient:
    def __init__(
            self,
            server_addr: str = "127.0.0.1:8848",  # Nacos 服务器地址
            namespace: str = "",  # 命名空间ID，public 留空
            username: str = "nacos",
            password: str = "nacos"
    ):
        self.server_addr = server_addr
        self.namespace = namespace
        self._init_directories()
        self.client = nacos.NacosClient(
            server_addr,
            namespace=namespace,
            username=username,
            password=password
        )
        self.config_cache = {}

    # ============ 服务注册 ============
    def register_service(
            self,
            service_name: str,
            ip: str,
            port: int,
            group_name: str = "DEFAULT_GROUP",
            cluster_name: str = "DEFAULT",
            weight: float = 1.0,
            metadata: dict = None,
            enable: bool = True,
            healthy: bool = True,
            ephemeral: bool = True  # 临时实例，断开自动注销
    ):
        """注册服务到 Nacos"""
        self.client.add_naming_instance(
            service_name=service_name,
            ip=ip,
            port=port,
            group_name=group_name,
            cluster_name=cluster_name,
            weight=weight,
            metadata=metadata or {},
            enable=enable,
            healthy=healthy,
            ephemeral=ephemeral
        )
        print(f"✅ 服务注册成功: {service_name} -> {ip}:{port}")

        # 启动心跳线程保持注册状态
        if ephemeral:
            self._start_heartbeat(service_name, ip, port, group_name, cluster_name)

    def _init_directories(self):
        """初始化 Nacos 所需的本地目录"""
        nacos_home = os.path.expanduser('~/nacos/config')
        for subdir in ['snapshot', 'failover']:
            dir_path = os.path.join(nacos_home, subdir)
            try:
                os.makedirs(dir_path, mode=0o755, exist_ok=True)
                print(f"📁 确保目录存在: {dir_path}")
            except Exception as e:
                print(f"❌ 创建目录失败 {dir_path}: {e}")
    def _start_heartbeat(self, service_name, ip, port, group_name, cluster_name):
        """心跳保活"""

        def heartbeat():
            while True:
                try:
                    self.client.send_heartbeat(
                        service_name=service_name,
                        ip=ip,
                        port=port,
                        group_name=group_name,
                        cluster_name=cluster_name
                    )
                except Exception as e:
                    print(f"⚠️ 心跳发送失败: {e}")
                time.sleep(5)

        t = threading.Thread(target=heartbeat, daemon=True)
        t.start()

    def deregister_service(
            self,
            service_name: str,
            ip: str,
            port: int,
            group_name: str = "DEFAULT_GROUP",
            cluster_name: str = "DEFAULT"
    ):
        """注销服务"""
        self.client.remove_naming_instance(
            service_name=service_name,
            ip=ip,
            port=port,
            group_name=group_name,
            cluster_name=cluster_name
        )
        print(f"✅ 服务注销成功: {service_name}")

    # ============ 配置管理 ============
    def get_config(
            self,
            data_id: str,
            group: str = "DEFAULT_GROUP",
            default: str = None
    ) -> str:
        """获取配置"""
        try:
            config = self.client.get_config(data_id, group)
            self.config_cache[f"{group}:{data_id}"] = config
            return config
        except Exception as e:
            print(f"⚠️ 获取配置失败: {e}")
            return default

    def get_config_json(
            self,
            data_id: str,
            group: str = "DEFAULT_GROUP",
            default: dict = None
    ) -> dict:
        """获取 JSON 格式配置"""
        config = self.get_config(data_id, group)
        if config:
            try:
                return json.loads(config)
            except json.JSONDecodeError:
                print(f"⚠️ 配置解析失败，非 JSON 格式")
        return default or {}

    def publish_config(
            self,
            data_id: str,
            content: str,
            group: str = "DEFAULT_GROUP"
    ) -> bool:
        """发布配置"""
        return self.client.publish_config(data_id, group, content)

    def listen_config(
            self,
            data_id: str,
            group: str = "DEFAULT_GROUP",
            callback: Callable[[str], None] = None
    ):
        """监听配置变化"""

        def wrapper(config):
            key = f"{group}:{data_id}"
            old_config = self.config_cache.get(key)
            self.config_cache[key] = config
            print(f"🔄 配置更新: {data_id}")
            if callback:
                callback(config)

        self.client.add_config_watcher(data_id, group, wrapper)
        print(f"👀 开始监听配置: {data_id}")

    def get_config_yaml(self, data_id: str, group: str = "DEFAULT_GROUP", default: dict = None) -> dict:
        config = self.get_config(data_id, group)
        if config:
            try:
                return yaml.safe_load(config)
            except Exception as e:
                print(f"⚠️ YAML 解析失败: {e}")
        return default or {}

# ============ 使用示例 ============
class XiaoZhiServer:
    def __init__(self, server_ip, server_port, username, password, namespace, group, data_id, service_name):
        self.nacos = NacosClient(
            server_addr=server_ip + ":" + str(server_port),
            namespace=namespace,  # public 命名空间
            username=username,
            password=password
        )
        self.config = {}
        self.ip = get_instance_ip()
        self.port = 8000
        self.group = group
        self.data_id = data_id
        self.service_name = service_name

    def get_config(self) -> dict:
        self.config = self.nacos.get_config_yaml(
            data_id = self.data_id,
            group = self.group,
            default={
                "llm_model": "gpt-4",
                "max_tokens": 2048,
                "temperature": 0.7
            }
        )
        print(f"📋 初始配置: {self.config}")
        return self.config

    def register_and_observe(self):
        # 1. 注册服务
        self.nacos.register_service(
            self.service_name,
            ip=self.ip,
            port=self.port,
            metadata={
                "version": "1.0.0",
                "type": "agent"
            }
        )

        # 2. 监听配置变化
        self.nacos.listen_config(
            data_id = self.data_id,
            group =self.group,
            callback=self._on_config_change
        )

    def start(self):
        # 1. 注册服务
        self.nacos.register_service(
            service_name="xiaozhi-agent-server",
            ip=self.ip,
            port=self.port,
            metadata={
                "version": "1.0.0",
                "type": "agent"
            }
        )

        # 2. 获取初始配置
        self.config = self.nacos.get_config_yaml(
            data_id="xiaozhi-agent-config",
            group="DEFAULT_GROUP",
            default={
                "llm_model": "gpt-4",
                "max_tokens": 2048,
                "temperature": 0.7
            }
        )
        print(f"📋 初始配置: {self.config}")

        # 3. 监听配置变化
        self.nacos.listen_config(
            data_id="xiaozhi-agent-config",
            group="DEFAULT_GROUP",
            callback=self._on_config_change
        )

    def _on_config_change(self, config_str: str):
        """配置变更回调"""
        try:
            new_config = yaml.safe_load(config_str.get('content'))
            self.config.update(new_config)
            print(f"✅ 配置已更新: {self.config}")
            # 这里可以触发重新加载逻辑
            self._reload_components()
        except Exception as e:
            print(f"❌ 配置更新失败: {e}")

    def _reload_components(self):
        """重新加载组件（根据新配置）"""
        # 比如重新初始化 LLM client 等
        pass

    def stop(self):
        self.nacos.deregister_service(
            service_name="xiaozhi-agent-server",
            ip=self.ip,
            port=self.port
        )


# if __name__ == "__main__":
# #     print("")
#     server = XiaoZhiServer("127.0.0.1", 8848, "", "", "deepblue-agent-dev","DEFAULT_GROUP", "agent-config", "deepblue-agent")
#     server.get_config()
#     server.register_and_observe()
#
#     # 保持运行
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         server.stop()