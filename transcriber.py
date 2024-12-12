from faster_whisper import WhisperModel
from faster_whisper.vad import VadOptions
import json
import logging

class Transcriber:
    def __init__(self, modelConfig, transcribeConfig, vadConfig):
        self.modelConfig = modelConfig

        if transcribeConfig['language'] == "auto":
            transcribeConfig['language'] = None
        if transcribeConfig['max_new_tokens'] == 0 or transcribeConfig['max_new_tokens'] == 448: # 448 is the default value
            transcribeConfig['max_new_tokens'] = None
        self.para = transcribeConfig

        # vad
        self.useVad = vadConfig['enable_vad']
        self.vadOption = None
        if self.useVad:
            self.vadOption = VadOptions(
                threshold=vadConfig['threshold'],
                min_speech_duration_ms=vadConfig['min_speech_duration_ms'],
                min_silence_duration_ms=vadConfig['min_silence_duration_ms'],
                max_speech_duration_s=vadConfig['max_speech_duration_s'],
                speech_pad_ms=vadConfig['speech_pad_ms'],
            )
        
        # running status
        self.modelLoaded = False
        self.running = False

    def load_model(self):
        print("开始加载模型...")
        self.model = None
        self.modelLoaded = False

        modelConfig = self.modelConfig
        try:
            self.model = WhisperModel(modelConfig['model_name'],
                device=modelConfig['device'],
                device_index=modelConfig['device_index'],
                compute_type=modelConfig['compute_type'],
                cpu_threads=modelConfig['cpu_threads'],
                num_workers=modelConfig['num_workers'],
                download_root=modelConfig['download_root'],
                local_files_only=modelConfig['local_files_only'])

            if modelConfig['fix_v3_mel_filters']:
                self.model.feature_extractor.mel_filters = self.model.feature_extractor.get_mel_filters(self.model.feature_extractor.sampling_rate, self.model.feature_extractor.n_fft, n_mels=128)
        except Exception as e:
            self.model = None
            print(f"Error: 加载模型失败：{e}")
            raise e

        self.modelLoaded = True
        print(f"模型加载成功 {self.modelConfig['model_name']} on {self.modelConfig['device']}:{self.modelConfig['device_index']}")

    def start_transcribe(self, audio_path):
        if not self.modelLoaded:
            print("Error: 模型未加载")
            return None

        try:
            print("开始识别音频...")
            self.running = True
            para = self.para
                    
            segments, info = self.model.transcribe(audio=audio_path, 
                language=para['language'],
                task="transcribe",
                beam_size=para['beam_size'],
                best_of=para['best_of'],
                patience=para['patience'],
                length_penalty=para['length_penalty'],
                repetition_penalty=para['repetition_penalty'],
                no_repeat_ngram_size=para['no_repeat_ngram_size'],
                temperature=para['temperature'],
                compression_ratio_threshold=para['compression_ratio_threshold'],
                log_prob_threshold=para['log_prob_threshold'],
                no_speech_threshold=para['no_speech_threshold'],
                condition_on_previous_text=para['condition_on_previous_text'],
                prompt_reset_on_temperature=para['prompt_reset_on_temperature'],
                initial_prompt=para['initial_prompt'],
                prefix=para['prefix'],
                suppress_blank=para['suppress_blank'],
                suppress_tokens=para['suppress_tokens'],
                without_timestamps=para['without_timestamps'],
                max_initial_timestamp=para['max_initial_timestamp'],
                word_timestamps=para['word_timestamps'],
                prepend_punctuations=para['prepend_punctuations'],
                append_punctuations=para['append_punctuations'],
                vad_filter=self.useVad,
                vad_parameters=self.vadOption,
                max_new_tokens=para['max_new_tokens'],
                chunk_length=para['chunk_length'],
                clip_timestamps=para['clip_timestamps'],
                hallucination_silence_threshold=para['hallucination_silence_threshold'],
                hotwords=para['hotwords'],
                language_detection_threshold=para['language_detection_threshold'],
                language_detection_segments=para['language_detection_segments']
                )

            self.duration = info.duration
            print(f"音频检测完成。")
            print(f"语言：{info.language} ({info.language_probability * 100:.2f}%)")
            print(f"音频时长：{info.duration} 秒")
            print(f"VAD 时长：{info.duration_after_vad} 秒")

            print(f"开始转录...")
            transcribedSegments = []
            for seg in segments:
                if not self.running:
                    print("用户中断")
                    return transcribedSegments

                percent = seg.start / self.duration * 100
                print(f"[{percent:.2f}%] ({seg.start:.2f} -> {seg.end:.2f}) {seg.text.lstrip()}")

                transcribedSegments.append(TranscribeSegment(segment=seg))

            print("音频转录完成")
            return transcribedSegments
        except Exception as e:
            print(f"Error: 识别音频失败：{e}")
            raise e

    def stream_transcribe(self, audio, init_prompt=""):
        if not self.modelLoaded:
            print("Error: 模型未加载")
            return None

        try:
            para = self.para
                    
            segments, info = self.model.transcribe(audio=audio, 
                language=para['language'],
                task="transcribe",
                beam_size=para['beam_size'],
                best_of=para['best_of'],
                patience=para['patience'],
                length_penalty=para['length_penalty'],
                repetition_penalty=para['repetition_penalty'],
                no_repeat_ngram_size=para['no_repeat_ngram_size'],
                temperature=para['temperature'],
                compression_ratio_threshold=para['compression_ratio_threshold'],
                log_prob_threshold=para['log_prob_threshold'],
                no_speech_threshold=para['no_speech_threshold'],
                condition_on_previous_text=True, # 实时转录需要使用前一次的输出
                prompt_reset_on_temperature=para['prompt_reset_on_temperature'],
                initial_prompt=init_prompt, # 使用实时转录时需要迭代传入前一次的输出
                prefix=para['prefix'],
                suppress_blank=para['suppress_blank'],
                suppress_tokens=para['suppress_tokens'],
                without_timestamps=para['without_timestamps'],
                max_initial_timestamp=para['max_initial_timestamp'],
                word_timestamps=True, # 实时转录需要输出字符级别的时间戳
                prepend_punctuations=para['prepend_punctuations'],
                append_punctuations=para['append_punctuations'],
                vad_filter=self.useVad,
                vad_parameters=self.vadOption,
                max_new_tokens=para['max_new_tokens'],
                chunk_length=para['chunk_length'],
                clip_timestamps=para['clip_timestamps'],
                hallucination_silence_threshold=para['hallucination_silence_threshold'],
                hotwords=para['hotwords'],
                language_detection_threshold=para['language_detection_threshold'],
                language_detection_segments=para['language_detection_segments']
                )
            
            return segments
        except Exception as e:
            # print(f"Error: 实时转录失败：{e}")
            logging.error(f"Error: 实时转录失败")
            logging.exception(e)


class TranscribeSegment:
    def __init__(self, segment=None, start=0.0, end=0.0, text=""):
        if segment is not None:
            self.start = segment.start
            self.end = segment.end
            self.text = segment.text
            try:
                if segment.words is not None:
                    self.words = segment.words
                else:
                    self.words = []
            except:
                self.words = []
        else:
            self.start = start
            self.end = end
            self.text = text
            self.words = []
        
        self.speaker = None

    def to_dict(self):
        return {
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "words": self.words,
            "speaker": self.speaker
        }

class TranscriberJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, TranscribeSegment):
            return obj.to_dict()
        return json.JSONEncoder.default(self, obj)
