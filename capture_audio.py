import pyaudiowpatch as pyaudio
import numpy as np


class AudioCapture:
    def __init__(self, chunk=1024, sample_rate=44100, channels=2):
        self.chunk = chunk
        self.sample_rate = sample_rate
        self.channels = channels
        self.p = pyaudio.PyAudio()
        self.running = False

    def find_device(self, device_name):        
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if dev['name'].find(device_name) != -1 and dev['isLoopbackDevice'] and dev['hostApi'] == 2: # 选择WASAPI环回设备
                print(f"[Record] 找到设备： {dev}")
                return i
        
        print(f"Error: [Record] 找不到指定的设备： {device_name}")
        return -1
    
    # 设置获得音频流数据后的处理函数
    def set_callback(self, callback):
        self.callback = callback

    # 录音
    def record(self, device_index):
        if self.callback is None:
            print("Error: [Record] 未设置回调函数，无法处理音频数据")
            return
        
        print("[Record] 开始录音...")
        self.running = True

        stream = self.p.open(input_device_index=device_index,
                             format=pyaudio.paFloat32,
                             channels=self.channels,
                             rate=self.sample_rate,
                             input=True,
                             frames_per_buffer=self.chunk)

        # Read stream
        frames = []
        duration = 0
        while self.running:
            data = stream.read(self.chunk)
            frames.append(data)
            duration += self.chunk / self.sample_rate

            if duration >= 1.5:
                block_audio = np.frombuffer(b''.join(frames), dtype=np.float32)
                self.callback(block_audio)
                frames = []
                duration = 0
        
        print("[Record] 结束录音")
        stream.stop_stream()
        stream.close()
        self.p.terminate()
        self.running = False

    # 停止录音
    def stop(self):
        self.running = False

    # 启动录音（在新线程中启动）
    def start(self, device_name):
        device_index = self.find_device(device_name)
        if device_index == -1:
            print("Error: [Record] 未找到指定的设备")
            return

        import threading
        t = threading.Thread(target=self.record, args=(device_index,))
        t.start()

