from subprocess import Popen, PIPE
import re
from celery import Celery
import subprocess
import os
import time
import azure.cognitiveservices.speech as speechsdk
import datetime
import database


CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379"),
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")

celery_app= Celery("tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)


@celery_app.task(name="transcribe")
def transcribe(file_path: str, subscription: str):
    basename = os.path.basename(file_path)
    if database.touch_record(basename):
        print(f"{basename} already exists!")
        return
    wav_path = os.path.join("waves", os.path.splitext(basename)[0] + ".wav")

    database.create_record(basename, "-", "pending")
    status = "ok"

    for _ in range(60*60):
        time.sleep(1)
        files = os.listdir(os.path.dirname(file_path))
        if len(list(filter(lambda x: basename in x, files))) > 0:
            break
    else:
        print("file has not been downloaded!")
        status = "upload error"

    if status is "ok": 
        duration, ffmpeg_status = ffmpegit(file_path, wav_path)
        if ffmpeg_status is False:
            print("Some FFMPEG error occured!")
            status = "ffmpeg error"

        if status is "ok":
            database.update_field(basename, "duration", duration)
            database.update_field(basename, "status", "processing")
            txt_path = os.path.join("results", os.path.splitext(basename)[0] + ".txt")
            full_text, rec_status = recognize(wav_path, subscription)
            with open(txt_path, 'w') as f:
                f.write(full_text)

            if rec_status is False:
                print("Some AZURE error occured!")
                status = "recognition error"


    database.update_field(basename, "status", status)
    try:
        os.remove(file_path)
    except:
        pass
    try:
        os.remove(new_path)
    except:
        pass


def ffmpegit(file_path: str, wav_path: str) -> (str, bool):
    command = ['ffmpeg', '-y', '-i', file_path, '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', wav_path]
    print(f"Command to be run: {' '.join(command)}")
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate()
    rc = p.returncode
    if rc != 0:
        print(err)
        return '', False
    ffmpeg_output = err.decode().split('\n')
    duration = '00:00:00'
    for line in ffmpeg_output:
        if 'size' in line and 'time' in line:
            res = re.match(r".*time=(.*?) bitrate", line)
            duration = res.groups()[0].rsplit('.')[0]
    return duration, True



def recognize(wav_path: str, subscription: str) -> (str, bool):
    print(subscription)
    print(wav_path)
    speech_config = speechsdk.SpeechConfig(subscription=subscription, region="eastus")
    audio_input = speechsdk.AudioConfig(filename=wav_path)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

    done = False
    all_results = []
    all_times = []

    #https://docs.microsoft.com/en-us/python/api/azure-cognitiveservices-speech/azure.cognitiveservices.speech.recognitionresult?view=azure-python
    def handle_final_result(evt):
        if len(evt.result.text) > 0:
            all_results.append(evt.result.text) 
            seconds = int(evt.offset / 1000 / 1000 / 1000 * 100)
            all_times.append(str(datetime.timedelta(seconds=seconds)))
            print(f'{str(datetime.timedelta(seconds=seconds))}\n{evt.result.text}')


    def stop_cb(evt):
        """callback that signals to stop continuous recognition upon receiving an event `evt`"""
        print('CLOSING on {}'.format(evt))
        nonlocal done
        done = True

    #Appends the recognized text to the all_results variable. 
    speech_recognizer.recognized.connect(handle_final_result) 

    # Connect callbacks to the events fired by the speech recognizer
    speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
    speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
    speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))
    # stop continuous recognition on either session stopped or canceled events
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # Start continuous speech recognition
    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(1)

    full_text = []
    for text, _time in zip(all_results, all_times):
        full_text.append(f'{_time}:\n{text}\n\n')

    if len(full_text) == 0:
        return '', False

    full_text = ''.join(full_text)
    return full_text, True

