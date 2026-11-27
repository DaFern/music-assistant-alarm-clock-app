FROM ghcr.io/dafern/music-assistant-alarm-clock-server@sha256:8a6fa5278b043c6f3f3afbe12728a7261657f900ec8c669d05318017f8a02bba
COPY install_alexa_recovery.py alexa_recovery_timeline.py /tmp/
RUN python /tmp/install_alexa_recovery.py && rm /tmp/install_alexa_recovery.py /tmp/alexa_recovery_timeline.py
ADD --checksum=sha256:aaceedf0e734a7eb36e4a598f996d82534ee6308b12dfcaab3f7738e44df7505 https://raw.githubusercontent.com/DaFern/HA-Alarm-Clock/3c983f0b103045af9b6105da42c4ca7b95ae993d/prototypes/ma_one_shot/alarm_commands.py.txt /tmp/alarm_commands.py.txt
ADD --checksum=sha256:1d0ddefdbd2f0d995470dcb09efad7580f5c4f987e3921745d7736ef490aded0 https://raw.githubusercontent.com/DaFern/HA-Alarm-Clock/3c983f0b103045af9b6105da42c4ca7b95ae993d/prototypes/ma_one_shot/test_commands.py.txt /tmp/test_commands.py.txt
COPY install_queue_modes.py /tmp/
RUN python /tmp/install_queue_modes.py && rm /tmp/install_queue_modes.py /tmp/alarm_commands.py.txt /tmp/test_commands.py.txt
