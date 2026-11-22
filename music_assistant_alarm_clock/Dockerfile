FROM ghcr.io/dafern/music-assistant-alarm-clock-server@sha256:8a6fa5278b043c6f3f3afbe12728a7261657f900ec8c669d05318017f8a02bba
COPY install_alexa_recovery.py alexa_recovery_timeline.py /tmp/
RUN python /tmp/install_alexa_recovery.py && rm /tmp/install_alexa_recovery.py /tmp/alexa_recovery_timeline.py
ADD --checksum=sha256:816adf2af2a702295f09fdd59772001bb03dd97d8a738d1404d049999297a31b https://raw.githubusercontent.com/DaFern/HA-Alarm-Clock/821c78151d2d9a5250c992b57b5fb684af8ac84b/prototypes/ma_one_shot/alarm_commands.py.txt /tmp/alarm_commands.py.txt
ADD --checksum=sha256:1d0ddefdbd2f0d995470dcb09efad7580f5c4f987e3921745d7736ef490aded0 https://raw.githubusercontent.com/DaFern/HA-Alarm-Clock/821c78151d2d9a5250c992b57b5fb684af8ac84b/prototypes/ma_one_shot/test_commands.py.txt /tmp/test_commands.py.txt
COPY install_queue_modes.py /tmp/
RUN python /tmp/install_queue_modes.py && rm /tmp/install_queue_modes.py /tmp/alarm_commands.py.txt /tmp/test_commands.py.txt
