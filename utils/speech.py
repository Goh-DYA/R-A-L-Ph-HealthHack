# Speech-to-text and text-to-speech functionality for RALPh.

import os
from datetime import datetime
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
from elevenlabs.client import ElevenLabs
from elevenlabs import play

from config import ELEVENLABS_API_KEY, AUDIO_FILES_DIR


# Initialize ElevenLabs client
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)


def record_audio(output_filename="recording.wav", duration=10, sample_rate=44100):
    """
    Record audio from the default microphone and save as WAV file.
    
    Args:
        output_filename (str): Output file path
        duration (int): Recording duration in seconds
        sample_rate (int): Sample rate in Hz
        
    Returns:
        str: Path to the recorded audio file
    """
    print(f"Recording for {duration} seconds...")

    # Capture audio
    audio_data = sd.rec(
        int(duration * sample_rate), 
        samplerate=sample_rate, 
        channels=1, 
        dtype=np.int16
    )
    sd.wait()  # Ensure recording is completed

    # Save to WAV file
    wav.write(output_filename, sample_rate, audio_data)
    print(f"Recording saved as {output_filename}")
    
    return output_filename


def audio_to_text(audio_file):
    """
    Convert audio file to text using ElevenLabs API.
    
    Args:
        audio_file (str): Path to audio file
        
    Returns:
        tuple: (text, language, language_probability, words)
    """
    # Check if file exists
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"Audio file not found: {audio_file}")
    
    # Send to ElevenLabs API
    with open(audio_file, "rb") as audio:
        response = client.speech_to_text.convert(
            model_id="scribe_v1",
            file=audio,
            num_speakers=1,
        )

    text = response.text
    lang = response.language_code
    lang_probability = response.language_probability
    words = response.words

    return text, lang, lang_probability, words


def text_to_audio(text_input):
    """
    Convert text to audio using ElevenLabs API.
    
    Args:
        text_input (str): Text to convert to speech
        
    Returns:
        tuple: (audio_generator, audio_file_path)
    """
    # Ensure audio files directory exists
    os.makedirs(AUDIO_FILES_DIR, exist_ok=True)
    
    # Input validation
    if not text_input or not isinstance(text_input, str):
        raise ValueError("Invalid text input")

    # Convert to audio - creates a generator object
    audio = client.text_to_speech.convert(
        text=text_input,
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_flash_v2_5",
        output_format="mp3_44100_128",
    )

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_file = os.path.join(AUDIO_FILES_DIR, f"output_audio_{timestamp}.mp3")
    
    # Save to mp3 file
    with open(audio_file, "wb") as f:
        for chunk in audio:
            if chunk:
                f.write(chunk)

    # Return a fresh generator and the file path
    with open(audio_file, "rb") as f:
        audio_data = f.read()
    
    # Recreate generator to avoid exhaustion
    def audio_generator():
        yield audio_data
    
    return audio_generator(), audio_file