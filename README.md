# aatsg

Automatic Audio Transcription and Subtitle Generator

这个项目用于进行日文Vtuber直播的语音识别和翻译。其中语音识别是本地执行Whisper模型，翻译是调用OpenAI GPT-4o-mini实现。

个人自用，目前很多东西都没来得及完善。如果有什么不舒服的地方，请尽可能自己修改。如果修改后能给我一个PR就更好了（＾ω＾）

## 使用方法

### 环境初始化

使用环境：

* Python 3.10.9
* CUDA 12.4

如果你不是这个环境，你可能需要根据情况修改requirements.txt中的版本号。

在使用之前，请先初始化Python环境并进入虚拟环境：

```bash
python -m venv venv
source venv/bin/activate  # 对于Windows用户，使用 `venv\Scripts\activate.bat`
pip install -r requirements.txt
```

之后每次使用之前都需要先启动虚拟环境：

```bash
source venv/bin/activate  # 对于Windows用户，使用 `venv\Scripts\activate.bat`
```

### 语音识别

要进行语音识别，请运行以下命令：

```bash
python main.py <video_file>
```

该命令会输出一个`.ass`文件。

### 翻译

要进行翻译，请运行以下命令：

```bash
python asstrans.py <ass_file>
```

该命令会输出一个翻译后的`.ass`文件。

## 配置

在第一次使用之前，请修改`openaiconfig.py`中的`apikey`。

Whisper模型的参数配置在`config.toml`中。

## 注意事项

- 请确保在虚拟环境中执行命令。
- 确保配置文件中的API密钥和参数正确无误。
