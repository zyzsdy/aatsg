# openai.py

class OpenAIConfig:
    def __init__(self):
        self.url = "https://api.openai.com/v1/chat/completions"
        self.api_key = "sk-xxx<your-openai-api-key>"
        self.model_name = "gpt-4o-mini"
        self.system_prompt = "你是一个高水平的翻译家，精通电视剧、广播节目和娱乐视频的翻译字幕制作。" + \
            "你能将视频中的对话信息精准的翻译成简体中文，简洁，尽最大可能保留原格式，且不失风趣幽默。" + \
            "提供给你的原文字幕可能有一些错误，请尽可能的推测真实含义。你需要翻译的文本内容是Vtuber的直播节目，内容涉及到偶像、娱乐活动、游戏和日常聊天。\n"
        self.user_prompt = "请将下面的文本翻译成简体中文。请只输出翻译文本，不要附加任何其他内容。" + \
            "以下是一些专有名词和对应的翻译，供参考：\n{{user_dict}}" + \
            "\n" + \
            "原文本：\n" + \
            "{{source_text}}" + \
            "\n" + \
            "翻译结果：\n"
        self.multiple_prompt = """请将下面以YAML格式给出的文本翻译成简体中文。对于YAML中的每一个entry，你都需要将其中的“text”字段翻译成简体中文。
请严格按照给出的例子，返回翻译好的YAML格式，不要包裹在<yaml>标签内部，也不要包含任何的附加内容。以下是一些专有名词和对应的翻译，供参考：
{{user_dict}}

参考格式：

<example>
Input:
- id: 1
  text: ...
- id: 2
  text: ...
- id: 3
  text: ...
Output:
- id: 1
  text: <翻译后的文本>
- id: 2
  text: <翻译后的文本>
- id: 3
  text: <翻译后的文本>
</example>

下面是需要翻译的YAML格式文本：

<yaml>
{{yaml}}</yaml>
"""
        self.user_dict = """
結城さくな：结城昨奈
さくなだふぁみりあ：Sakunada Familia （圣奈家族） 【结城昨奈的粉丝名，原meme：由Sagrada Familia 圣家堂变换而来】
サクファミ：Sakufami 【粉丝名的简称】
あてぃし：人家 【可爱的自称】"""