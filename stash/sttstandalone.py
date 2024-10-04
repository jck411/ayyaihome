import os
import pyaudio
import queue
from google.cloud import speech_v1p1beta1 as speech
from dotenv import load_dotenv


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/jack/ayyaihome/backend/googlekey.json"

# Audio recording parameters
RATE = 16000  # Best practice: 16000 Hz for speech
CHUNK = int(RATE / 10)  # 100ms frame size, best tradeoff between efficiency and latency

class MicrophoneStream:
    """Opens a recording stream as a generator yielding audio chunks."""
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1, rate=self._rate, input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            yield chunk

def listen_print_loop(responses):
    """Iterate through the server responses and print them, including speaker tags and word timestamps."""
    
    # Mapping speaker tags to specific people
    speaker_labels = {
        1: "Jack",   # Assign speaker 1 to Jack
        2: "Sanja",  # Assign speaker 2 to Sanja
        # Any other speaker will be assigned later as "Guest"
    }

    for response in responses:
        for result in response.results:
            if result.is_final:
                print("Final Transcript: {}".format(result.alternatives[0].transcript))

                # Print out speaker and timestamp information for each word
                for word_info in result.alternatives[0].words:
                    speaker_tag = word_info.speaker_tag
                    speaker_name = speaker_labels.get(speaker_tag, "Guest")  # Default to "Guest" if speaker not Jack or Sanja
                    start_time = word_info.start_time.total_seconds()
                    end_time = word_info.end_time.total_seconds()
                    print(f"Word: {word_info.word}, Speaker: {speaker_name}, Start time: {start_time:.2f}s, End time: {end_time:.2f}s")

            else:
                print("Interim Transcript: {}".format(result.alternatives[0].transcript))

            # Speaker diarization and word time offset information for interim results too
            for word in result.alternatives[0].words:
                start_time_seconds = word.start_time.total_seconds()
                end_time_seconds = word.end_time.total_seconds()
                speaker_tag = word.speaker_tag
                speaker_name = speaker_labels.get(speaker_tag, "Guest")
                print(f"Word: {word.word}, Speaker: {speaker_name}, Start time: {start_time_seconds:.2f}s, End time: {end_time_seconds:.2f}s")

def transcribe_streaming_with_model_selection_and_punctuation():
    """Streams audio from microphone and transcribes with speaker diarization, automatic punctuation, spoken punctuation, emojis, and model selection."""
    client = speech.SpeechClient()

    # Define phrase hints for commonly used terms or domain-specific phrases
    speech_context = speech.SpeechContext(
        phrases=["Jack", "Sanja", "Guest", "ChatGPT", "OpenAI", "machine learning"],
        boost=15.0  # Boost specific phrases
    )

    # Enable speaker diarization for multi-speaker scenarios
    diarization_config = speech.SpeakerDiarizationConfig(
        enable_speaker_diarization=True,
        min_speaker_count=2,  # Min number of speakers expected
        max_speaker_count=10   # Max speakers (Jack, Sanja, and possibly guests)
    )

    # Enable language recognition for multiple languages
    primary_language = "en-US"  # Primary language
    alternative_languages = ["pl-PL", "hr-HR"]  # Polish and Croatian as alternatives

    # Use the latest_long model for conversational audio
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,  # Lossless encoding
        sample_rate_hertz=RATE,  # 16,000 Hz sampling rate
        language_code=primary_language,  # Set primary language to English (US)
        alternative_language_codes=alternative_languages,  # Set alternative languages to Polish and Croatian
        speech_contexts=[speech_context],  # Phrase hints
        diarization_config=diarization_config,  # Enable speaker diarization
        enable_word_time_offsets=True,  # Enable word time offsets
        enable_automatic_punctuation=True,  # Enable automatic punctuation
        enable_spoken_punctuation=True,  # Enable spoken punctuation
        enable_spoken_emojis=True,  # Enable spoken emojis
        max_alternatives=1,  # Only return the best result for performance
        model="latest_long",  # Specify the model for long conversational audio
        profanity_filter=False  # Optional: enable profanity filtering
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True,  # Get interim results for real-time feedback
        single_utterance=False  # Set to True if you expect short commands
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in audio_generator)

        responses = client.streaming_recognize(streaming_config, requests)

        # Process responses in real-time
        listen_print_loop(responses)

if __name__ == '__main__':
    transcribe_streaming_with_model_selection_and_punctuation()
