import simpleaudio as sa
import io

def play_audio(audio_data):
    """
    Plays the given audio data.
    """
    # Define the sample rate and other parameters
    sample_rate = 24000  # 24kHz
    num_channels = 1     # Mono
    bytes_per_sample = 2 # 16-bit

    # Create an audio object from the raw data
    wave_obj = sa.WaveObject(audio_data, num_channels, bytes_per_sample, sample_rate)
    play_obj = wave_obj.play()
    play_obj.wait_done()
