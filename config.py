import toml
import os
from typing import Dict, Any

class Config:
    _instance = None
    _config = None
    _config_path = "config.toml"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if Config._config is None:
            self.load_config()

    def load_config(self) -> None:
        """Load the configuration from config.toml file"""
        config_path = os.path.join(os.path.dirname(__file__), self._config_path)
        try:
            if os.path.exists(config_path):
                print("Load Config from config.toml")
                Config._config = toml.load(config_path)
            else:
                print("Config file not found, use default config.")
                Config._config = {}
        except Exception as e:
            print(f"Error: 加载配置文件时失败。 {e}")
            Config._config = {}

    def getModelConfig(self) -> Dict[str, Any]:
        # ~/.cache/huggingface/hub
        defaultDownloadRoot = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")

        defaultConfig = {
            'model_name': 'large-v3',
            'device': 'auto',
            'device_index': 0,
            'compute_type': 'float32',
            'cpu_threads': 1,
            'num_workers': 1,
            'download_root': defaultDownloadRoot,
            'local_files_only': True,
            'fix_v3_mel_filters': False
        }

        if Config._config is None:
            load_config()

        modelConfig = merge_config(Config._config.get('model'), defaultConfig)
        return modelConfig

    def getTranscribeConfig(self) -> Dict[str, Any]:
        defaultConfig = {
            'language': 'auto',
            'beam_size': 1,
            'best_of': 5,
            'patience': 1.0,
            'length_penalty': 2.0,
            'repetition_penalty': 1.0,
            'no_repeat_ngram_size': 0,
            'temperature': [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
            'compression_ratio_threshold': 2.2,
            'log_prob_threshold': -10,
            'no_speech_threshold': 0.75,
            'condition_on_previous_text': False,
            'prompt_reset_on_temperature': 0.5,
            'initial_prompt': "",
            'prefix': "",
            'suppress_blank': True,
            'suppress_tokens': [-1],
            'without_timestamps': False,
            'max_initial_timestamp': 1.0,
            'word_timestamps': False,
            'prepend_punctuations': "\"'“¿([{-",
            'append_punctuations': "\"'.。,，!！?？:：”)]}、",
            'max_new_tokens': 448,
            'chunk_length': 30,
            'clip_timestamps': "0",
            'hallucination_silence_threshold': 0.5,
            'hotwords': "",
            'language_detection_threshold': 0.5,
            'language_detection_segments': 1
        }

        if Config._config is None:
            load_config()

        transcribeConfig = merge_config(Config._config.get('transcribe'), defaultConfig)
        return transcribeConfig

    def getVadConfig(self) -> Dict[str, Any]:
        defaultConfig = {
            'enable_vad': True,
            'threshold': 0.2,
            'min_speech_duration_ms': 200,
            'min_silence_duration_ms': 2000,
            'max_speech_duration_s': 1800,
            'speech_pad_ms': 800
        }

        if Config._config is None:
            load_config()

        vadConfig = merge_config(Config._config.get('vad'), defaultConfig)
        return vadConfig

    def getStreamConfig(self) -> Dict[str, Any]:
        defaultConfig = {
            'buffer_trimming_time_s': 15,
            'buffer_time_offset': 0
        }

        if Config._config is None:
            load_config()

        streamConfig = merge_config(Config._config.get('stream'), defaultConfig)
        return streamConfig

def merge_config(userConfig, defaultConfig):
    if userConfig is None:
        return defaultConfig
    else:
        for key in defaultConfig:
            if key not in userConfig:
                userConfig[key] = defaultConfig[key]
        return userConfig

# Create a singleton instance
config = Config()
