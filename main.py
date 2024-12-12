from config import config
from transcriber import Transcriber, TranscriberJsonEncoder
from stream_processor import StreamProcessor
from capture_audio import AudioCapture
from assbuilder import genAssFile
import os
import sys
import json
import time
import logging
import wave
import numpy as np
import librosa

def main(audio_path, target_path):
    # Load the configuration
    modelConfig = config.getModelConfig()
    transcriberConfig = config.getTranscribeConfig()
    vadConfig = config.getVadConfig()

    # Create the transcriber
    transcriber = Transcriber(modelConfig, transcriberConfig, vadConfig)
    transcriber.load_model()

    # Start transcribing
    transcribeSegments = transcriber.start_transcribe(audio_path)
    print("开始生成ASS文件...")

    genAssFile(transcribeSegments, target_path)
    print(f"结束。请查看：{target_path}")

def stream_main(device_name, sample_rate=44100):
    # Load the configuration
    modelConfig = config.getModelConfig()
    transcriberConfig = config.getTranscribeConfig()
    vadConfig = config.getVadConfig()
    streamConfig = config.getStreamConfig()

    # Create the transcriber
    transcriber = Transcriber(modelConfig, transcriberConfig, vadConfig)
    transcriber.load_model()

    # Create the stream processor
    streamProcessor = StreamProcessor(sample_rate, streamConfig, transcriber)

    def stream_process(audio_chunk):
        streamProcessor.insert_audio_chunk(audio_chunk)
        try:
            res = streamProcessor.process_iter()
        except Exception as e:
            print(f"Error: [MAIN] {e}")
            logging.exception(e)
            pass
        else:
            if res is not None:
                print(f"==RES: [{res[0]}, {res[1]}] {res[2]}", flush=True)

    # recordFile = RecordToWaveFile("I:/VideoCaches/testccc.wav", sample_rate=sample_rate, target_rate=48000)

    # Create the audio capture
    audioCapture = AudioCapture(sample_rate=sample_rate)
    audioCapture.set_callback(stream_process)
    # audioCapture.set_callback(recordFile.receive_audio)
    audioCapture.start(device_name)

    # 挂起主线程，等待用户中断
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("==用户中断==")
            audioCapture.stop()
            break

    # 额外处理一下最后的结果
    streamProcessor.finish()
    if res is not None:
        print(f"==RES: [{res[0]}, {res[1]}] {res[2]}", flush=True)
    print("==结束==")
    # recordFile.close()

class RecordToWaveFile:
    def __init__(self, file_path, sample_rate=44100, target_rate=16000):
        self.file_path = file_path
        self.sample_rate = sample_rate
        self.target_rate = target_rate
        self.wave_file = wave.open(file_path, 'wb')
        self.wave_file.setnchannels(2)
        self.wave_file.setsampwidth(2)
        self.wave_file.setframerate(target_rate)

    def receive_audio(self, audio_chunk):
        # Resample to target rate
        audio_chunk = librosa.resample(audio_chunk, orig_sr=self.sample_rate, target_sr=self.target_rate)
        # Convert float32 [-1.0, 1.0] to int16 [-32768, 32767]
        audio_int16 = (audio_chunk * 32767).astype(np.int16)
        self.wave_file.writeframes(audio_int16.tobytes())

    def close(self):
        self.wave_file.close()
        self.wave_file = None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_mp4_file>")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    target_path = os.path.splitext(audio_path)[0] + '.ass'

    main(audio_path, target_path)

    # device_name = "Realtek Digital Output"
    # stream_main(device_name, sample_rate=48000)