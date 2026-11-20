# Exact flow mapper from DaFern/music-assistant-alarm-clock-server
# revision f0c825c708fcca577430aac46aa30f8cbf23b79b, used for regression tests.
def _get_flow_queue_stream_index(
        self, queue: PlayerQueue, player: Player
    ) -> tuple[int | None, float]:
        """
        Calculate current queue index and current track elapsed time when flow mode is active.

        The player reports cumulative stream-time (post-atempo). The returned
        track elapsed time is in media-time, scaled by the current item's
        playback_speed when we hit the active entry.
        """
        queue_data = self._queue_data[queue.queue_id]
        elapsed_time_queue_total = player.state.corrected_elapsed_time or 0
        if queue.current_index is None and not queue_data.flow_mode_stream_log:
            return queue.current_index, queue.elapsed_time

        # For each track that has been streamed/buffered to the player,
        # a playlog entry will be created with the queue item id
        # and the amount of seconds streamed. We traverse the playlog to figure
        # out where we are in the queue, accounting for actual streamed
        # seconds (and not duration) and skipped seconds. If a track has been repeated,
        # it will simply be in the playlog multiple times.
        played_time = 0.0
        queue_index: int | None = queue.current_index or 0
        track_time = 0.0
        flow_log = queue_data.flow_mode_stream_log
        for log_index, play_log_entry in enumerate(flow_log):
            # seconds_streamed is bytes-derived stream-time, so the boundary check
            # doesn't need a speed factor. Normally only the still-streaming tail entry
            # has seconds_streamed=None (we'll break inside it before the sentinel
            # matters); an abandoned probe entry is the exception, handled below.
            if play_log_entry.seconds_streamed is not None:
                # NOTE: 'seconds_streamed' can be 0 if there was a stream error
                entry_stream_duration = play_log_entry.seconds_streamed
            elif log_index < len(flow_log) - 1:
                # Some players open the same flow URL several times while probing the
                # stream. A probe can leave an unfinished entry behind before the
                # connection that actually plays the audio appends the next entry.
                # Recover the completed stream duration from the shared QueueItem;
                # treating this non-tail entry as the active sentinel would pin the
                # queue to the previous track and let elapsed time overflow its duration.
                stale_queue_item = self.get_item(queue.queue_id, play_log_entry.queue_item_id)
                if (
                    stale_queue_item
                    and stale_queue_item.streamdetails
                    and stale_queue_item.streamdetails.seconds_streamed is not None
                ):
                    entry_stream_duration = stale_queue_item.streamdetails.seconds_streamed
                else:
                    entry_stream_duration = 0
            else:
                entry_stream_duration = 3600 * 24 * 7
            if elapsed_time_queue_total > (entry_stream_duration + played_time):
                # total elapsed time is more than (streamed) track duration
                # this track has been fully played, move on.
                played_time += entry_stream_duration
            else:
                # no more seconds left to divide, this is our track
                # account for any seeking by adding the skipped/seeked seconds
                queue_index = self.index_by_id(queue.queue_id, play_log_entry.queue_item_id)
                queue_item = self.get_item(queue.queue_id, queue_index)
                if queue_item and queue_item.streamdetails:
                    track_sec_skipped = queue_item.streamdetails.seek_position
                else:
                    track_sec_skipped = 0
                # stream-time within this entry, scaled to media-time using the
                # speed of the entry we broke on (queue.current_item may still be
                # the previous entry during a transition)
                entry_speed = (
                    float(queue_item.extra_attributes.get("playback_speed") or 1.0)
                    if queue_item
                    else 1.0
                )
                stream_pos_in_item = elapsed_time_queue_total - played_time
                track_time = track_sec_skipped + stream_pos_in_item * entry_speed
                break
        if player.state.playback_state != PlaybackState.PLAYING:
            # if the player is not playing, we can't be sure that the elapsed time is correct
            # so we just return the queue index and the elapsed time
            return queue.current_index, queue.elapsed_time
        return queue_index, track_time
