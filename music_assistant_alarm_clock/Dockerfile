FROM ghcr.io/dafern/music-assistant-alarm-clock-server@sha256:8a6fa5278b043c6f3f3afbe12728a7261657f900ec8c669d05318017f8a02bba
COPY install_alexa_recovery.py alexa_recovery_timeline.py /tmp/
RUN python /tmp/install_alexa_recovery.py && rm /tmp/install_alexa_recovery.py /tmp/alexa_recovery_timeline.py
