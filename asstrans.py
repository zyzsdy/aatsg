import sys
import openaiconfig
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

def parse_ass_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    events_section = False
    dialogues = []

    for line in lines:
        if "[Events]" in line:
            events_section = True
            continue
        if events_section:
            if line.startswith("Dialogue:"):
                linepart = line[10:].strip()
                parts = line.split(',')
                start = parts[1]
                end = parts[2]
                text = parts[-1]
                dialogues.append({
                    'start': start,
                    'end': end,
                    'text': text.strip()
                })

    if not events_section:
        print("Error: ASS解析失败：你的字幕里至少得有[Events]吧。")
        sys.exit(1)

    return dialogues

def send_trans_api(transbag):
    orig_json = [{'id': i + 1, 'text': t['text']} for i, t in enumerate(transbag)]
    orig_json_string = json.dumps(orig_json, indent=4, ensure_ascii=False, separators=(', ', ': '))

    conf = openaiconfig.OpenAIConfig()

    user_prompt = conf.multiple_prompt
    user_prompt = user_prompt.replace("{{json}}", orig_json_string)
    user_prompt = user_prompt.replace("{{user_dict}}", conf.user_dict)


    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {conf.api_key}"
    }
    data = {
        "model": conf.model_name,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": f"{conf.system_prompt}"
            },
            {
                "role": "user",
                "content": f"{user_prompt}"
            }
        ]
    }
    if conf.use_stream:
        data['stream'] = True
    else:
        data['stream'] = False

    if conf.use_json_schema:
        data['response_format'] = {
            "type": "json_schema",
            "json_schema": {
                "name": "translation",
                "schema": {
                    "type": "object",
                    "properties": {
                        "result": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {
                                        "type": "integer"
                                    },
                                    "text": {
                                        "type": "string"
                                    }
                                },
                                "additionalProperties": False,
                                "required": [
                                    "id",
                                    "text"
                                ]
                            }
                        }
                    },
                    "additionalProperties": False,
                    "required": [
                        "result"
                    ]
                }
            }
        }
    else:
        data['response_format'] = {
            "type": "json_object"
        }

    for i in range(3):
        succ = False
        try:
            if conf.use_stream:
                with requests.post(conf.url, headers=headers, data=json.dumps(data, ensure_ascii=False).encode('utf-8'), stream=True) as response:
                    if response.status_code != 200:
                        print(f"Error: 翻译API请求失败：{response.status_code}")
                        print(response.text)
                        break

                    assistant_message = ""
                    for chunk in response.iter_lines():
                        if chunk:
                            decoded_chunk = chunk.decode('utf-8')
                            if decoded_chunk.startswith("data: "):
                                try:
                                    chunk_data = json.loads(decoded_chunk[6:])

                                    if 'choices' in chunk_data:
                                        
                                        choices_delta = chunk_data['choices'][0]['delta']
                                        content = choices_delta.get('content', None)
                                        if content:
                                            assistant_message += content
                                            print(content, end='', flush=True)
                                except json.JSONDecodeError:
                                    continue


                    if assistant_message:
                        response_json = assistant_message
            else:
                response = requests.post(conf.url, headers=headers, data=json.dumps(data, ensure_ascii=False).encode('utf-8'))
                response_data = response.json()
                response_json = response_data['choices'][0]['message']['content']
                print(response_json)

        except Exception as e:
            print(f"Error: 翻译API请求失败：{e}")
            print(response.text)
            continue

        try:
            translated_obj = json.loads(response_json)
            translated_list = translated_obj['result']
            succ = True
        except Exception as e:
            print(f"Error: 翻译结果解析失败：{e}")
            print(response_json)
            continue

        break

    if succ:
        for t in translated_list:
            index = t['id'] - 1
            transbag[index]['translated'] = t['text']

    return transbag


def translate_ass(dialogues, max_workers=3):
    translated = [{} for _ in range(len(dialogues))]  # 预分配结果数组
    
    def process_batch(batch_with_index):
        batch, start_index = batch_with_index
        result = send_trans_api(batch)
        return (result, start_index)

    # 准备批次数据，每批10条
    batches = []
    batch = []
    
    for i, dialogue in enumerate(dialogues):
        batch.append(dialogue)
        if len(batch) == 10:
            batches.append((batch.copy(), i - len(batch) + 1))
            batch = []

    if batch:
        batches.append((batch, len(dialogues) - len(batch)))

    total_batches = len(batches)
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_batch = {executor.submit(process_batch, batch_data): batch_data 
                         for batch_data in batches}

        # 处理完成的任务
        for future in as_completed(future_to_batch):
            batch_result, start_index = future.result()
            completed += 1
            print(f"翻译进度：{completed}/{total_batches} 批次")
            
            # 将结果放入对应位置
            for i, item in enumerate(batch_result):
                translated[start_index + i] = item

    return translated

def gen_ass(trans, target_file):

    ass_header = """[Script Info]
; Script generated by aatsg
; https://github.com/zyzsdy/aatsg
Original Script: aatsg
ScriptType: v4.00+
PlayDepth: 0
Timer: 100.0000
WrapStyle: 0
ScaledBorderAndShadow: no
YCbCr Matrix: None
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Orig,思源黑体 Light,60,&H0084E5F7,&H000000FF,&H000C4D4E,&H00000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,45,1
Style: Target,思源黑体 Normal,70,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,45,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    ass_lines = []
    for text in trans:
        start = text['start']
        end = text['end']
        orig = text['text']
        tran = ""
        if 'translated' in text:
            tran = text['translated']
        ass_lines.append(f"Dialogue: 0,{start},{end},Orig,SPEAKER_00,0,0,0,,{orig}")
        ass_lines.append(f"Dialogue: 0,{start},{end},Target,SPEAKER_00,0,0,0,,{tran}")

    ass_file = ass_header + '\n'.join(ass_lines)

    with open(target_file, 'w', encoding='utf-8') as file:
        file.write(ass_file)

        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ASS字幕翻译工具')
    parser.add_argument('ass_file', help='输入的ASS文件路径')
    parser.add_argument('--workers', type=int, default=10, help='并发翻译线程数（默认为10）')
    args = parser.parse_args()
    
    ass_file_path = args.ass_file
    target_file_path = ass_file_path.replace('.ass', '_translated.ass')

    dialogues = parse_ass_file(ass_file_path)
    translated_result = translate_ass(dialogues, args.workers)
    gen_ass(translated_result, target_file_path)

    print("ASS文件已经生成在：" + target_file_path)
