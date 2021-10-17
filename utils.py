import subprocess
import os


def ffmpegit(file_path: str) -> str:
    
    subprocess.call(['ffmpeg', '-i', file_path, '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', 'test.wav'])
    return 'test'


def recognize():
    return
