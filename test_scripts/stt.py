import sounddevice as sd
import numpy as np
import torch
import whisperx  # <-- Using WhisperX instead of faster_whisper
import queue
import threading
import time
import sys
import logging

# Configure Logging
logging.basicConfig(level=logging.CRITICAL, format='%(asctime)s [%(levelname)s] %(message)s')

# Configuration Parameters
SAMPLE_RATE = 16000  # Whisper expects 16kHz
CHUNK_DURATION = 1   # seconds
CHANNELS = 1         # Mono audio
MODEL_SIZE = "base"  # WhisperX model size
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"  # Use GPU if available
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "float32"

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

# ------------------------------------------------------------------------------
# 1) Load the WhisperX Model
# ------------------------------------------------------------------------------
print(f"Loading WhisperX model '{MODEL_SIZE}' on device '{DEVICE}'...")
model = whisperx.load_model(
    MODEL_SIZE, 
    device=DEVICE, 
    compute_type=COMPUTE_TYPE
)
print("Model loaded successfully.")

# Confirm CUDA Usage
if DEVICE == "cuda":
    print(f"CUDA is available and being used.")
    print(f"GPU Name: {torch.cuda.get_device_name(0)}")
    print(f"CUDA Version: {torch.version.cuda}")
    print(f"Number of GPUs Available: {torch.cuda.device_count()}")
else:
    print("CUDA is not available. Running on CPU.")

# ------------------------------------------------------------------------------
# 2) Setup a basic alignment model (Optional if you want alignment features)
#    If you want forced alignment, you typically do it after the entire
#    audio is available. Realtime chunking may limit full alignment usage.
# ------------------------------------------------------------------------------
alignment_model, metadata = whisperx.load_align_model(
    language_code="en",
    device=DEVICE
)

# ------------------------------------------------------------------------------
# 3) Global Variables for Real-Time Transcription
# ------------------------------------------------------------------------------
audio_queue = queue.Queue()
recording = False
transcribing = False
stop_signal = False

def audio_callback(indata, frames, time_info, status):
    """
    This callback is called for each audio block from the microphone.
    It puts the audio data into a queue for processing.
    """
    if status:
        print(f"Audio status: {status}", file=sys.stderr)
    audio_data = np.squeeze(indata)
    audio_queue.put(audio_data.copy())

def record_audio():
    """
    Records audio from the microphone in chunks and puts them into a queue.
    """
    global recording, stop_signal
    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            callback=audio_callback,
            blocksize=int(SAMPLE_RATE * CHUNK_DURATION)
        ):
            print("Recording... Press Ctrl+C to stop.")
            recording = True
            while not stop_signal:
                try:
                    sd.sleep(1000)  # Sleep for 1 second
                except KeyboardInterrupt:
                    print("\nStopping recording...")
                    stop_signal = True
                    break
    except Exception as e:
        logging.error(f"Error in audio stream: {e}")
        stop_signal = True
    finally:
        recording = False

def transcribe_audio():
    """
    Continuously gets audio chunks from the queue and transcribes them using WhisperX.
    """
    global transcribing, stop_signal
    transcribing = True
    print("Transcription started. Awaiting audio...")
    
    # Accumulate audio in a buffer to pass to WhisperX each time
    # because WhisperX expects the entire audio segment. 
    audio_buffer = []

    while transcribing and not stop_signal:
        try:
            audio_chunk = audio_queue.get(timeout=1)  # Wait for 1 second for audio
        except queue.Empty:
            continue  # No audio received in this interval

        if audio_chunk is None:
            continue

        # Convert to float32 if needed
        if audio_chunk.dtype != np.float32:
            audio_chunk = audio_chunk.astype(np.float32) / np.iinfo(np.int16).max
        
        # Append the new chunk to the buffer
        audio_buffer.append(audio_chunk)

        # We combine the accumulated audio for transcription
        # More frequent calls => more responsive, but heavier overhead.
        combined_audio = np.concatenate(audio_buffer, axis=0)

        try:
            # 1) Transcribe using WhisperX
            result = model.transcribe(
                combined_audio, 
                language="en"
            )
            
            # 2) (Optional) Align 
            # Typically alignment is done after the entire audio is processed, 
            # but here we show how you might run partial align:
            # alignment_result = whisperx.align(
            #     result["segments"], 
            #     alignment_model, 
            #     metadata, 
            #     combined_audio, 
            #     device=DEVICE
            # )
            
            # 3) Print the last recognized segments
            # We only print the latest text to simulate real-time updates.
            # For example, print the final segment text.
            if "segments" in result and len(result["segments"]) > 0:
                last_segment = result["segments"][-1]
                print(last_segment["text"].strip())

        except Exception as e:
            logging.error(f"Failed to transcribe audio with WhisperX: {e}")

    transcribing = False


def main():
    global stop_signal

    record_thread = threading.Thread(target=record_audio, daemon=True)
    record_thread.start()

    transcribe_thread = threading.Thread(target=transcribe_audio, daemon=True)
    transcribe_thread.start()

    try:
        while record_thread.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Exiting...")
        stop_signal = True

    record_thread.join()
    transcribe_thread.join()
    print("Transcription stopped.")

if __name__ == "__main__":
    main()
