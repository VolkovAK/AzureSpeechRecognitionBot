# AzureSpeechRecognitionSite
Site for recognizing speech from video or audio  

-----------
#### Technologies used

1) Python 3 - as main programming language
2) Flask - for system management via web-page
3) Celery - for asynchronous tasks
4) Postgres - as database with results for processed files
5) Docker, docker-compose - for deployment
6) html, css (no js) - for web-page
7) Azure Speech-to-Text API - for actual recognition


#### Usage

You need to create at project root directory two files:
- azure.key - with your Microsoft Azure Speech-to-Text subscription key,
- auth.key - this string will be used as password for site login.


-----------
17.10.2021 for M.I.A.
