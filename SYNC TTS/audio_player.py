import queue

def play_audio(audio_queue, audio_generation_complete, stream):
    while not (audio_generation_complete.is_set() and audio_queue.empty()):
        try:
            audio_chunk = audio_queue.get(timeout=0.5)
            stream.write(audio_chunk)
        except queue.Empty:
            continue
