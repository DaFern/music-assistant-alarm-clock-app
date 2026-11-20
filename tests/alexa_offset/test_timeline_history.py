"""Regression for a reconnect replacing the log before the failure callback."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace as N
from test_offset_recovery import fixture, helper, TOKEN, PlaybackState


class TimelineHistoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_reconnect_short_log_uses_original_track_and_position(self):
        controller, data, player, items = fixture()
        helper.remember_flow(controller, 'Office speakers', 'session')
        # A new HTTP producer for the same session publishes a short, aborted log.
        data.flow_mode_stream_log = [N(queue_item_id='one', seconds_streamed=1)]
        result = await controller.recover_alexa_flow('Office speakers', TOKEN, 194517)
        self.assertTrue(result['ok'])
        controller._play_index.assert_awaited_once_with('Office speakers', 'two', 92, False)

    async def test_snapshots_do_not_follow_mutated_stream_details(self):
        controller, data, player, items = fixture()
        helper.remember_flow(controller, 'Office speakers', 'session')
        data.flow_mode_stream_log[0].seconds_streamed = 1
        data.flow_mode_stream_log = [N(queue_item_id='one', seconds_streamed=1)]
        items[1].streamdetails.seek_position = 99
        items[1].duration = 1
        result = await controller.recover_alexa_flow('Office speakers', TOKEN, 194517)
        self.assertTrue(result['ok'])
        controller._play_index.assert_awaited_once_with('Office speakers', 'two', 92, False)

    async def test_disagreeing_valid_timelines_do_not_choose_arbitrarily(self):
        controller, data, player, items = fixture()
        data.flow_mode_stream_log = [N(queue_item_id='two', seconds_streamed=200)]
        helper.remember_flow(controller, 'Office speakers', 'session')
        data.flow_mode_stream_log = [N(queue_item_id='one', seconds_streamed=100), N(queue_item_id='two', seconds_streamed=None)]
        result = await controller.recover_alexa_flow('Office speakers', TOKEN, 150000)
        self.assertEqual(result['reason'], 'ambiguous_stream_timeline')
        controller._play_index.assert_not_awaited()

    async def test_expired_history_does_not_recover_old_offset(self):
        controller, data, player, items = fixture()
        with patch.object(helper.time, 'monotonic', return_value=100):
            helper.remember_flow(controller, 'Office speakers', 'session')
        data.flow_mode_stream_log = [N(queue_item_id='one', seconds_streamed=1)]
        with patch.object(helper.time, 'monotonic', return_value=221):
            result = await controller.recover_alexa_flow('Office speakers', TOKEN, 194517)
        self.assertFalse(result['ok'])
        controller._play_index.assert_not_awaited()

    async def test_history_cannot_cross_new_session(self):
        controller, data, player, items = fixture()
        helper.remember_flow(controller, 'Office speakers', 'session')
        data.session_id = 'new'
        data.flow_mode_stream_log = [N(queue_item_id='one', seconds_streamed=1)]
        player._last_stream_url = TOKEN.replace('/session/', '/new/')
        result = await controller.recover_alexa_flow('Office speakers', TOKEN.replace('/session/', '/new/'), 194517)
        self.assertFalse(result['ok'])
        controller._play_index.assert_not_awaited()

    async def test_history_bound_refuses_instead_of_discarding_ambiguity(self):
        controller, data, player, items = fixture()
        for _ in range(helper.MAX_SNAPSHOTS + 1):
            helper.remember_flow(controller, 'Office speakers', 'session')
        result = await controller.recover_alexa_flow('Office speakers', TOKEN, 150000)
        self.assertEqual(result['reason'], 'timeline_history_overflow')
        controller._play_index.assert_not_awaited()

    async def test_non_alexa_streams_do_not_capture_history(self):
        controller, data, player, items = fixture()
        player.provider.domain = 'other'
        helper.remember_flow(controller, 'Office speakers', 'session')
        self.assertFalse(getattr(controller, '_alexa_flow_snapshots', {}))

    async def test_archived_timeline_does_not_override_pause(self):
        controller, data, player, items = fixture()
        helper.remember_flow(controller, 'Office speakers', 'session')
        data.queue.state = PlaybackState.PAUSED
        result = await controller.recover_alexa_flow('Office speakers', TOKEN, 150000)
        self.assertFalse(result['ok'])
        controller._play_index.assert_not_awaited()
