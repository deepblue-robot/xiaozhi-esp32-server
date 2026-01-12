根据代码探索结果，我来整理完整的调用流程：

  ---
  Smart Audio 语音处理完整调用链路

  整体流程图

  ┌─────────────────────────────────────────────────────────────────────────┐
  │                           WebSocket 客户端                               │
  └─────────────────────────────────────────┬───────────────────────────────┘
                                            │ 音频数据 (Opus)
                                            ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  1. WebSocket 接收                                                       │
  │  websocket_server.py → connection.py._route_message()                   │
  └─────────────────────────────────────────┬───────────────────────────────┘
                                            │
                                            ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  2. VAD 语音活动检测                                                     │
  │  receiveAudioHandle.py → vad/silero.py.is_vad()                         │
  └─────────────────────────────────────────┬───────────────────────────────┘
                                            │ client_voice_stop = True
                                            ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  3. ASR 语音识别                                                         │
  │  asr/base.py.handle_voice_stop() → speech_to_text()                     │
  └─────────────────────────────────────────┬───────────────────────────────┘
                                            │ 识别文本
                                            ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  4. LLM 大模型处理                                                       │
  │  connection.py.chat() → llm/openai.py.response()                        │
  └─────────────────────────────────────────┬───────────────────────────────┘
                                            │ 流式响应
                                            ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  5. TTS 语音合成                                                         │
  │  tts_text_queue → sendAudioHandle.py                                    │
  └─────────────────────────────────────────┬───────────────────────────────┘
                                            │ 音频数据
                                            ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                           WebSocket 客户端                               │
  └─────────────────────────────────────────────────────────────────────────┘

  ---
  1. 语音接收与预处理

  1.1 WebSocket 入口

  文件: core/websocket_server.py

  class WebSocketServer:
      async def start(self):
          """启动 WS 服务器，监听 0.0.0.0:8000"""

      async def _handle_connection(self, websocket):
          """创建 ConnectionHandler 处理连接"""
          conn = ConnectionHandler(websocket, headers)
          await conn.handle_connection(websocket)

  1.2 消息路由

  文件: core/connection.py:443

  class ConnectionHandler:
      async def _route_message(self, message):
          """消息路由"""
          if isinstance(message, str):
              # 文本消息 → 文本处理
              await handleTextMessage(self, message)
          else:
              # 二进制音频 → 加入ASR队列
              await self.asr_audio_queue.put(message)

  1.3 音频优先级处理线程

  文件: core/providers/asr/base.py

  def asr_priority_thread(conn):
      """从队列取音频，按序处理"""
      while True:
          audio = conn.asr_audio_queue.get()
          await handleAudioMessage(conn, audio)

  1.4 VAD 语音活动检测

  文件: core/handle/receiveAudioHandle.py

  async def handleAudioMessage(conn, audio):
      """处理音频消息"""
      # 1. VAD 检测
      has_voice = conn.vad.is_vad(conn, audio)

      # 2. 缓存音频
      conn.asr_audio.append(audio)

      # 3. 检测到语音停止时触发 ASR
      if conn.client_voice_stop:
          await handle_voice_stop(conn)

  文件: core/providers/vad/silero.py

  class SileroVAD:
      def is_vad(self, conn, opus_packet) -> bool:
          """
          Silero VAD 检测流程:
          1. Opus → PCM 解码
          2. 512采样点分块
          3. 模型推理得到 speech_prob
          4. 双阈值判断 (0.5/0.2)
          5. 滑动窗口平滑 (5帧)
          6. 静默超时判断 (>1000ms)
          """

  ---
  2. 语音识别 (ASR) 转文字

  2.1 触发 ASR 处理

  文件: core/providers/asr/base.py

  async def handle_voice_stop(conn, asr_audio_task=None):
      """语音停止，开始识别"""

      # 1. 音频解码 (Opus → PCM)
      if audio_format == "opus":
          pcm_data = opus_decoder.decode(audio_chunk, frame_size)

      # 2. 并发执行 ASR 和声纹识别
      results = await asyncio.gather(
          speech_to_text(conn, audio_data),           # ASR 识别
          voiceprint_provider.identify_speaker(...)   # 声纹识别(可选)
      )

      # 3. 处理识别结果
      raw_text = results[0]

      # 4. 进入对话
      await startToChat(conn, raw_text)

  2.2 ASR 实现示例 (豆包流式)

  文件: core/providers/asr/doubao_stream.py

  class DoubaoStreamASR:
      async def receive_audio(self, conn, audio_data):
          """
          流式识别流程:
          1. 建立 WSS 连接
             wss://openspeech.bytedance.com/api/v3/sauc/bigmodel
          2. 发送初始化请求 (gzip JSON)
          3. 循环发送音频帧
          4. 接收识别结果
          """

      async def _forward_asr_results(self):
          """监听识别结果"""
          for message in ws:
              payload = json.loads(message)
              if payload["utterance"]["definite"]:
                  # 最终识别结果
                  return payload["utterance"]["text"]

      async def speech_to_text(self, audio_data):
          """非流式识别"""
          return recognized_text

  2.3 其他 ASR 提供商

  core/providers/asr/
  ├── aliyun.py / aliyun_stream.py    # 阿里云
  ├── xunfei_stream.py                 # 科大讯飞
  ├── baidu.py                         # 百度
  ├── openai.py                        # OpenAI Whisper
  ├── vosk.py                          # 本地 Vosk
  ├── sherpa_onnx_local.py             # 本地 ONNX
  └── qwen3_asr_flash.py               # 通义千问

  ---
  3. 大模型 (LLM) 处理逻辑

  3.1 进入对话

  文件: core/handle/intentHandler.py

  async def startToChat(conn, text):
      """从 ASR 结果进入聊天"""
      # 1. 发送 STT 消息给客户端
      await send_stt_message(conn, text)

      # 2. 在线程池中执行聊天
      conn.executor.submit(conn.chat, text)

  3.2 核心对话方法

  文件: core/connection.py:951

  def chat(self, query, depth=0):
      """核心对话处理"""

      # 1. 初始化会话状态
      self.llm_finish_task = False
      self.sentence_id = str(uuid.uuid4())

      # 2. 添加用户消息到对话历史
      self.dialogue.put(Message(role="user", content=query))

      # 3. 查询记忆 (可选)
      if self.memory:
          memory_str = await self.memory.query_memory(query)

      # 4. 构建对话上下文
      dialogue_with_memory = self.dialogue.get_llm_dialogue_with_memory(memory_str)

      # 5. 选择 LLM 调用方式
      if intent_type == "function_call":
          llm_responses = self.llm.response_with_functions(
              session_id, dialogue_with_memory, functions=functions
          )
      else:
          llm_responses = self.llm.response(
              session_id, dialogue_with_memory
          )

      # 6. 流式处理响应
      for response in llm_responses:
          # 处理内容
          content = response if not function_call else response[0]

          # 发送到 TTS 队列
          self.tts.tts_text_queue.put(TTSMessageDTO(
              sentence_type=SentenceType.MIDDLE,
              content_type=ContentType.TEXT,
              content_detail=content
          ))

          # 检测工具调用
          if "<tool_call>" in content:
              tool_call_flag = True

      # 7. 处理工具调用 (递归)
      if tool_call_flag:
          result = await self._handle_function_result(tool_calls)
          self.chat(query=None, depth=depth+1)  # 递归，最大深度 5

  3.3 LLM 实现 (OpenAI)

  文件: core/providers/llm/openai/openai.py:57-99

  class OpenAILLM:
      def response(self, session_id, dialogue, **kwargs):
          """标准流式对话"""
          request_params = {
              "model": self.model_name,
              "messages": dialogue,
              "stream": True,
              "max_tokens": kwargs.get("max_tokens", self.max_tokens),
              "temperature": kwargs.get("temperature", self.temperature),
          }

          responses = self.client.chat.completions.create(**request_params)

          is_active = True
          for chunk in responses:
              content = chunk.choices[0].delta.content or ""

              # 过滤思维过程标签
              if "<think>" in content:
                  is_active = False
              if "</think>" in content:
                  is_active = True

              if is_active:
                  yield content  # ← 生成器，流式返回

      def response_with_functions(self, session_id, dialogue, functions):
          """带函数调用的流式对话"""
          request_params = {
              "model": self.model_name,
              "messages": dialogue,
              "stream": True,
              "tools": functions,  # 函数定义
          }

          for chunk in responses:
              content = chunk.choices[0].delta.content or ""
              tool_calls = chunk.choices[0].delta.tool_calls
              yield content, tool_calls  # ← 返回元组

  3.4 工具调用处理

  文件: core/connection.py:1079-1150

  async def _handle_function_result(self, tool_calls):
      """执行工具调用"""

      # 1. 解析工具调用
      for tool_call in tool_calls:
          function_name = tool_call["function"]["name"]
          arguments = json.loads(tool_call["function"]["arguments"])

      # 2. 执行工具 (unified_tool_handler)
      results = await unified_tool_handler.execute(tool_calls)

      # 3. 添加工具响应到对话历史
      self.dialogue.put(Message(role="tool", content=result))

      # 4. 递归调用 chat 处理工具结果
      return self.chat(query=None, depth=depth+1)

  3.5 其他 LLM 提供商

  core/providers/llm/
  ├── openai/openai.py      # OpenAI (ChatGPT/GPT-4)
  ├── coze/                  # Coze 机器人平台
  ├── dify/                  # Dify
  ├── fastgpt/               # FastGPT
  ├── ollama/                # 本地 Ollama
  ├── gemini/                # Google Gemini
  └── AliBL/                 # 阿里云百炼

  ---
  4. TTS 语音合成与发送

  4.1 TTS 发送流程

  文件: core/handle/sendAudioHandle.py

  async def sendAudioMessage(conn, sentence_type, audio, text):
      """发送音频消息"""

      if sentence_type == SentenceType.FIRST:
          # 发送 "sentence_start" 消息
          await conn.websocket.send(json.dumps({
              "type": "sentence_start"
          }))

      # 流式发送音频 (带流控)
      audio_controller = AudioRateController(frame_duration=60)
      await conn.websocket.send(audio_data)

      if sentence_type == SentenceType.LAST:
          # 发送结束消息
          await conn.websocket.send(json.dumps({"type": "stop"}))
          conn.client_is_speaking = False

  ---
  5. 关键状态变量

  # ConnectionHandler 核心状态
  class ConnectionHandler:
      # 连接信息
      websocket: WebSocket
      device_id: str
      session_id: str

      # 组件实例
      vad: SileroVAD           # VAD 检测
      asr: ASRProvider         # 语音识别
      llm: LLMProvider         # 大模型
      tts: TTSProvider         # 语音合成
      memory: MemoryProvider   # 记忆模块

      # 音频状态
      asr_audio: list[bytes]   # 音频缓冲
      asr_audio_queue: Queue   # 音频队列

      # VAD 状态
      client_have_voice: bool  # 当前有声音
      client_voice_stop: bool  # 检测到停止

      # 对话状态
      dialogue: Dialogue       # 对话历史
      llm_finish_task: bool    # LLM 完成标志

  ---
  6. 调用链路总结表
  ┌──────────┬─────────────────────┬────────────────────┬───────────────────┐
  │   阶段   │      入口方法       │      核心文件      │       输出        │
  ├──────────┼─────────────────────┼────────────────────┼───────────────────┤
  │ 接收音频 │ _route_message()    │ connection.py:443  │ 音频入队列        │
  ├──────────┼─────────────────────┼────────────────────┼───────────────────┤
  │ VAD 检测 │ is_vad()            │ vad/silero.py      │ client_voice_stop │
  ├──────────┼─────────────────────┼────────────────────┼───────────────────┤
  │ ASR 识别 │ handle_voice_stop() │ asr/base.py        │ 识别文本          │
  ├──────────┼─────────────────────┼────────────────────┼───────────────────┤
  │ LLM 对话 │ chat()              │ connection.py:951  │ 流式响应          │
  ├──────────┼─────────────────────┼────────────────────┼───────────────────┤
  │ LLM 生成 │ response()          │ llm/openai.py:57   │ yield content     │
  ├──────────┼─────────────────────┼────────────────────┼───────────────────┤
  │ TTS 发送 │ sendAudioMessage()  │ sendAudioHandle.py │ 音频数据          │
  └──────────┴─────────────────────┴────────────────────┴───────────────────┘

