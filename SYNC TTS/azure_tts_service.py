from tts_service_interface import TTSService
import queue
import azure.cognitiveservices.speech as speechsdk

class AzureTTSService(TTSService):
    def __init__(self, speech_config, sentence_queue, audio_queue, sentence_processing_complete, audio_generation_complete):
        self.speech_config = speech_config
        self.sentence_queue = sentence_queue
        self.audio_queue = audio_queue
        self.sentence_processing_complete = sentence_processing_complete
        self.audio_generation_complete = audio_generation_complete

        # Set the speech synthesis output format to raw PCM
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Raw24Khz16BitMonoPcm
        )

        # Create a Speech Synthesizer
        self.synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=None)

    def generate_audio(self):
        while not (self.sentence_processing_complete.is_set() and self.sentence_queue.empty()):
            try:
                sentence = self.sentence_queue.get(timeout=0.5)

                # Synthesize the text to an audio data stream
                result = self.synthesizer.speak_text_async(sentence).get()

                # Check result
                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    audio_data = result.audio_data
                    self.audio_queue.put(audio_data)

                    # Add a short pause between sentences
                    self.audio_queue.put(b'\x00' * 4800)  # 0.1 seconds of silence at 24000 Hz
                else:
                    print(f"Speech synthesis failed: {result.reason}")

            except queue.Empty:
                continue

        self.audio_generation_complete.set()
