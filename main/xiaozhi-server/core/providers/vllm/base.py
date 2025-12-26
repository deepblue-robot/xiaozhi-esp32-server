from abc import ABC, abstractmethod
# from config.logger import setup_logging

TAG = __name__
from loguru import logger


class VLLMProviderBase(ABC):
    @abstractmethod
    def response(self, question, base64_image):
        """VLLM response generator"""
        pass
