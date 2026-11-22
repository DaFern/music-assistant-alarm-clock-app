FROM ghcr.io/dafern/music-assistant-alarm-clock-server@sha256:8a6fa5278b043c6f3f3afbe12728a7261657f900ec8c669d05318017f8a02bba
COPY install_alexa_recovery.py alexa_recovery_timeline.py /tmp/
RUN python /tmp/install_alexa_recovery.py && rm /tmp/install_alexa_recovery.py /tmp/alexa_recovery_timeline.py
ADD --checksum=sha256:ed4c418d16d5f58f248774f8eefe17eb28605ec186782100bbd5cd28f1cf2293 https://raw.githubusercontent.com/DaFern/HA-Alarm-Clock/8606f2db0f496d989ffa59b4695a514b313f3f3b/prototypes/ma_one_shot/alarm_commands.py.txt /tmp/alarm_commands.py.txt
ADD --checksum=sha256:86af6b4e51a11a21ec654d67c1032923b038056b7d01e750ba90e63d273af7ca https://raw.githubusercontent.com/DaFern/HA-Alarm-Clock/8606f2db0f496d989ffa59b4695a514b313f3f3b/prototypes/ma_one_shot/test_commands.py.txt /tmp/test_commands.py.txt
COPY install_queue_modes.py /tmp/
RUN python /tmp/install_queue_modes.py && rm /tmp/install_queue_modes.py /tmp/alarm_commands.py.txt /tmp/test_commands.py.txt
