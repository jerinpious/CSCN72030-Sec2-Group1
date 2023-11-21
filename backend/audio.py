#utils/audio_utils.py
import pyaudio
import wave
import random
import os

# Global variable to control the recording state
RECORDING_FLAG = True

def record_audio():
    global RECORDING_FLAG
    print("Recording audio...")
    audio = pyaudio.PyAudio()

    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    frames = []

    try:
        while RECORDING_FLAG:
            data = stream.read(1024)
            frames.append(data)

    except KeyboardInterrupt:
        pass

    print("Saving audio file...")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Ensure that the 'audio_recordings' directory exists before saving the audio file
    audio_directory = 'backend/audio_recordings/'
    os.makedirs(audio_directory, exist_ok=True)

    randval = random.randint(1, 9999)
    sound_file = wave.open(f"{audio_directory}recording{randval}.wav", 'wb')
    sound_file.setnchannels(1)
    sound_file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    sound_file.setframerate(44100)
    sound_file.writeframes(b''.join(frames))
    sound_file.close()

    # Reset the recording flag
    RECORDING_FLAG = True

# Function to stop the recording
def stop_recording():
    global RECORDING_FLAG
    print("Stopping audio recording...")
    RECORDING_FLAG = False

if __name__ == "__main__":
    record_audio()
