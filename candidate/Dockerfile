FROM ghcr.io/music-assistant/server@sha256:7eb272e2e13da9a5d61dcbc4e1fcfc734776222b23f2825a9b5690d4427cfafb
COPY overlay /opt/alarmclock/overlay
COPY install.py /opt/alarmclock/install.py
RUN /app/venv/bin/python /opt/alarmclock/install.py
LABEL org.opencontainers.image.title="MA – HA Alarm Clock" \
      org.opencontainers.image.source="https://github.com/DaFern/music-assistant-alarm-clock-app" \
      org.opencontainers.image.revision="f0c825c708fcca577430aac46aa30f8cbf23b79b" \
      io.hass.name="MA – HA Alarm Clock" \
      io.hass.version="2.10.12-alarmclock.2"
