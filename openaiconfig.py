# openai.py

class OpenAIConfig:
    def __init__(self):
        self.url = "http://127.0.0.1:1234/v1/chat/completions"
        self.api_key = "sk-0000000000000000000000000000000000"
        self.model_name = "qwen2.5-14b-instruct"
        self.use_json_schema = True # 使用openai时，将其置为False，使用Ollama时，将其置为True
        self.use_stream = False # 如果打开流式传输，那么服务器将会每推理出一些字符就会返回并且显示，否则将会等待推理完成后一次性返回。对于本工具完成的任务，流式传输似乎没有意义。
        self.system_prompt = """你是一个高水平的翻译家，精通电视剧、广播节目和娱乐视频的翻译字幕制作。
你能将视频中的对话信息精准的翻译成简体中文，简洁，尽最大可能保留原格式，且不失风趣幽默。
提供给你的原文字幕来自语音识别，因此可能有一些错误，请尽可能的推测真实含义。
你需要翻译的文本内容是Vtuber的直播节目，内容涉及到偶像、娱乐活动、游戏和日常聊天。

请将下面以JSON格式给出的文本翻译成简体中文。对于JSON中的每一个对象，你都需要将其中的“text”字段翻译成简体中文。
请严格按照给出的例子，返回翻译好的JSON格式，不要包含任何的附加内容。

以下是一些专有名词和对应的翻译，供参考：
{{user_dict}}

参考格式：

<Example Input>
{
  "result": [
    {
      "id": 1,
      "text": "Hello, world!"
    },
    {
      "id": 2,
      "text": "Goodbye, world!"
    },
    {
      "id": 3,
      "text": "Good morning, world!"
    }
  ]
}
</Example Input>
<Example Output>
{
  "result": [
    {
      "id": 1,
      "text": "你好，世界！"
    },
    {
      "id": 2,
      "text": "再见，世界！"
    },
    {
      "id": 3,
      "text": "早上好，世界！"
    }
  ]
}
</Example Output>
"""
        self.user_prompt = "请将下面的文本翻译成简体中文。请只输出翻译文本，不要附加任何其他内容。" + \
            "以下是一些专有名词和对应的翻译，供参考：\n{{user_dict}}" + \
            "\n" + \
            "原文本：\n" + \
            "{{source_text}}" + \
            "\n" + \
            "翻译结果：\n"
        self.multiple_prompt = """{{json}}\n"""
        self.user_dict = """
結城さくな：结城昨奈
さくな：昨奈
さくなだふぁみりあ：Sakunada Familia （圣奈家族） 【结城昨奈的粉丝名，原meme：由Sagrada Familia 圣家堂变换而来】
サクファミ：Sakufami 【粉丝名的简称】
あてぃし：人家 【可爱的自称】"""