import numpy as np
import librosa
from faster_whisper.transcribe import Segment
from collections.abc import Iterable
from transcriber import Transcriber

class HypothesisBuffer:
    def __init__(self):
        self.commited_in_buffer = []
        self.buffer = []
        self.new = []
        self.last_commited_time = 0
        self.last_commited_word = None

    def insert(self, new, offset):
        new = [(a + offset, b + offset, t) for a, b, t in new]
        self.new = [(a, b, t) for a, b, t in new if a > self.last_commited_time - 0.1]

        if len(self.new) > 1:
            a, b, t = self.new[0]
            if abs(a - self.last_commited_time) < 1:
                if self.commited_in_buffer:
                    cn = len(self.commited_in_buffer)
                    nn = len(self.new)
                    for i in range(1, min(min(cn, nn), 5) + 1): # 最多5个
                        c = " ".join([self.commited_in_buffer[-j][2] for j in range(1, i+ 1)][::-1])
                        tail = " ".join(self.new[j - 1][2] for j in range(1, i + 1))
                        if c == tail:
                            words = []
                            for j in range(i):
                                words.append(repr(self.new.pop(0)))
                            words_msg = " ".join(words)
                            break

    def flush(self):
        commit = []
        while self.new:
            na, nb, nt = self.new[0]
            if len(self.buffer) == 0:
                break

            if nt == self.buffer[0][2]:
                commit.append((na, nb, nt))
                self.last_commited_word = nt
                self.last_commited_time = nb
                self.buffer.pop(0)
                self.new.pop(0)
            else:
                break
        
        self.buffer = self.new
        self.new = []
        self.commited_in_buffer.extend(commit)
        return commit
    
    def pop_commited(self, time):
        while self.commited_in_buffer and self.commited_in_buffer[0][1] <= time:
            self.commited_in_buffer.pop(0)
        
    def complete(self):
        return self.buffer

class StreamProcessor:
    def __init__(self, sample_rate=44100, streamConfig=None, transcriber: Transcriber=None):
        self.sample_rate = sample_rate
        if streamConfig is None:
            streamConfig = {
                'buffer_trimming_time_s': 15,
                'buffer_time_offset': 0
            }
        self.buffer_trimming_time_s = streamConfig['buffer_trimming_time_s']
        self.buffer_time_offset = streamConfig['buffer_time_offset']

        self.transcriber = transcriber
        self.target_sr = self.transcriber.model.feature_extractor.sampling_rate

        self.audio_buffer = np.array([], dtype=np.float32)
        self.transcript_buffer = HypothesisBuffer()
        self.transcript_buffer.last_commited_time = self.buffer_time_offset
        self.commited = []
        self.sep = ""

    def insert_audio_chunk(self, audio_chunk):
        # Convert audio_chunk to mono if it is not already
        if audio_chunk.ndim > 1:
            audio_chunk = librosa.to_mono(audio_chunk)

        # Resample audio_chunk to target_sr
        sr_audio = librosa.resample(audio_chunk, orig_sr=self.sample_rate, target_sr=self.target_sr)

        self.audio_buffer = np.append(self.audio_buffer, sr_audio)
    
    def prompt(self):
        k = max(0, len(self.commited) - 1)
        while k > 0 and self.commited[k - 1][1] > self.buffer_time_offset:
            k -= 1

        p = self.commited[:k]
        p = [t for _, _, t in p]
        prompt = []

        l = 0
        while p and l < 200: # prompt长度上限200
            x = p.pop(-1)
            l += len(x) + 1
            prompt.append(x)
        non_prompt = self.commited[k:]

        return self.sep.join(prompt[::-1]), self.sep.join(t for _, _, t in non_prompt)

    def ts_words(self, segments: Iterable[Segment]):
        o = []
        for segment in segments:
            print(f"Segment: {segment}")
            for word in segment.words:
                if segment.no_speech_prob > 0.9:
                    continue

                w = word.word
                t = (word.start, word.end, w)
                o.append(t)

        return o
    
    def segments_end_ts(self, res):
        return [s.end for s in res]

    
    def process_iter(self):
        prompt, non_prompt = self.prompt()
        print(f"Audio: {len(self.audio_buffer) / self.target_sr:.2f} s from {self.buffer_time_offset:.2f} / Prompt: {prompt} / Context: {non_prompt}")

        res = self.transcriber.stream_transcribe(self.audio_buffer, init_prompt=prompt)
        tsw = self.ts_words(res)

        self.transcript_buffer.insert(tsw, self.buffer_time_offset)
        o = self.transcript_buffer.flush()
        self.commited.extend(o)
        completed = self.to_flush(o)

        print(f">>>Completed: {completed}")
        the_rest = self.to_flush(self.transcript_buffer.complete())
        print(f">>>The rest: {the_rest}")

        s = self.buffer_trimming_time_s
        if len(self.audio_buffer) / self.target_sr > s:
            self.chunk_completed(res)

        return self.to_flush(o)

    def chunk_completed(self, res):
        if self.commited == []:
            return

        ends = self.segments_end_ts(res)
        t = self.commited[-1][1]

        if len(ends) > 1:
            e = ends[-2] + self.buffer_time_offset
            while len(ends) > 2 and e > t:
                ends.pop(-1)
                e = ends[-2] + self.buffer_time_offset
            if e <= t:
                print(f"---------Segment chunked at {e:.2f} s")
                self.chunk_at(e)
            else:
                print(f"---------last segment not within commited area")
        else:
            print(f"---------not enough segments to chunk")

    def chunk_at(self, time):
        self.transcript_buffer.pop_commited(time)
        cut_seconds = time - self.buffer_time_offset
        self.audio_buffer = self.audio_buffer[int(cut_seconds * self.target_sr):]
        self.buffer_time_offset = time

    def to_flush(self, sents, sep=None, offset=0):
        if sep is None:
            sep = self.sep
        t = sep.join(s[2] for s in sents)
        if len(sents) == 0:
            b = None
            e = None
        else:
            b = offset + sents[0][0]
            e = offset + sents[-1][1]
        
        return (b, e, t)

    def finish(self):
        o = self.transcript_buffer.complete()
        f = self.to_flush(o)
        print(f"Final flush: {f}")
        self.buffer_time_offset += len(self.audio_buffer) / self.target_sr
        return f
            