import glob
import pyaudio
import wave
import math
import os
import threading
from pynput import keyboard
import sys
from sharedQueue import audio_queue


class AudioPlayer:
    def __init__(self):
        self.chunk = 1024
        self.audio = pyaudio.PyAudio()
        self._running = False
        self.current_file_index = 0
        self.audio_files = []
        self.play_thread = None

    def get_audio_length(self, audiopath):
        wf = wave.open(audiopath, 'rb')
        frames = wf.getnframes()
        rate = wf.getframerate()
        total_length = frames / float(rate)
        minutes = int(total_length // 60)
        seconds = int(total_length % 60)
        return f"{minutes}:{seconds:02}"

    def play(self):
        self._running = True
        while self._running:
            if self.current_file_index < 0 or self.current_file_index >= len(self.audio_files):
                break
            audiopath = self.audio_files[self.current_file_index]
            self.chunktotal = 0
            wf = wave.open(audiopath, 'rb')
            stream = self.audio.open(format=self.audio.get_format_from_width(wf.getsampwidth()), 
                                     channels=wf.getnchannels(), 
                                     rate=wf.getframerate(), 
                                     output=True)
            data = wf.readframes(self.chunk)
            audiolength = self.get_audio_length(audiopath)
            percentage = 0
            current_seconds = 0
            temp_perc = percentage
            curr_sec = current_seconds

            while self._running and data != b'':
                stream.write(data)
                self.chunktotal += self.chunk
                data = wf.readframes(self.chunk)
                if curr_sec < current_seconds:
                    minutes = current_seconds // 60
                    seconds = current_seconds % 60
                    time_str = f"{minutes}:{seconds:02}"
                    print("Current time: ", time_str, " / ", audiolength)
                    curr_sec = current_seconds
                    temp_perc = percentage
                percentage = math.floor((self.chunktotal / wf.getnframes()) * 100)
                current_seconds = math.floor(self.chunktotal / float(wf.getframerate()))

            stream.close()
            if self._running:
                self.next()

    def stop(self):
        self._running = False
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join()

    def next(self):
        self.current_file_index = (self.current_file_index + 1) % len(self.audio_files)

    def previous(self):
        self.current_file_index = (self.current_file_index - 1) % len(self.audio_files)

    def set_audio_files(self, audio_files):
        self.audio_files = audio_files

    def start_playback(self):
        if self.play_thread and self.play_thread.is_alive():
            self.stop()
        self.play_thread = threading.Thread(target=self.play)
        self.play_thread.start()

def list_audio_files(directory):
    audio_files = glob.glob(os.path.join(directory, "*.wav"))
    return audio_files

def on_press(key, player):
    try:
        if key.char == 's':
            player.start_playback()
        elif key.char == " ":
            player.stop()
        elif key.char == 'n':
            player.stop()
            player.next()
            player.start_playback()
        elif key.char == 'p':
            player.stop()
            player.previous()
            player.start_playback()
    except AttributeError:
        pass

def handle_keyboard_input(player):
    listener = keyboard.Listener(on_press=lambda key: on_press(key, player))
    listener.start()
    listener.join()

audio_folder = "songs"
audio_files = list_audio_files(audio_folder)
if not audio_files:
    print("No audio files found in the directory.")
else:
    print("Available audio files:")
    for i, file in enumerate(audio_files, 1):
        print(f"{i}. {os.path.basename(file)}")

    aa = AudioPlayer()
    aa.set_audio_files(audio_files)
    handle_keyboard_input(aa)