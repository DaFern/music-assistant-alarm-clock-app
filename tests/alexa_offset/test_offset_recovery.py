import ast,asyncio,importlib.util,time,unittest
from enum import Enum
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import AsyncMock,patch
spec=importlib.util.spec_from_file_location('installer','music_assistant_alarm_clock/install_alexa_recovery.py');installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)
class PlaybackState(Enum):PLAYING='playing';PAUSED='paused'
def deco(*a,**k):return lambda f:f
ns={'api_command':deco,'handle_play_action':lambda f:f,'Scope':N(QUEUES_CONTROL='control'),'PlaybackState':PlaybackState,'time':time,'Any':object}
exec('class Controller:\n'+installer.METHOD,ns);Controller=ns['Controller']
tree=ast.parse(Path('tests/alexa_offset/pinned_flow_mapper.py').read_text())
method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_get_flow_queue_stream_index')
method.returns=None
for a in method.args.args:a.annotation=None
exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'mapper','exec'),ns)
Controller._get_flow_queue_stream_index=ns['_get_flow_queue_stream_index']
TOKEN='/flow/session/Office%20speakers/start/Office.mp3'
def fixture():
 c=Controller();q=N(queue_id='Office speakers',state=PlaybackState.PLAYING,ended=False,active=True,available=True,flow_mode=True,current_index=0,elapsed_time=9999)
 items=[N(queue_item_id='one',duration=120,streamdetails=N(seconds_streamed=100,seek_position=20),extra_attributes={}),N(queue_item_id='two',duration=200,streamdetails=N(seconds_streamed=None,seek_position=0),extra_attributes={})]
 entries=[N(queue_item_id='one',seconds_streamed=100),N(queue_item_id='two',seconds_streamed=None)]
 data=N(queue=q,session_id='session',flow_mode_stream_log=entries)
 player=N(provider=N(domain='alexa'),state=N(active_group=None,synced_to=None),_last_stream_url='http://internal:8097'+TOKEN)
 c._queue_data={'Office speakers':data};c.mass=N(players=N(get_player=lambda _:player));c._check_player_permission=lambda _:None
 c.index_by_id=lambda _,itemid:next((i for i,x in enumerate(items) if x.queue_item_id==itemid),None)
 c.get_item=lambda _,idx: (items[idx] if isinstance(idx,int) and idx<len(items) else next((x for x in items if x.queue_item_id==idx),None))
 c._play_index=AsyncMock();return c,data,player,items
class ServerTests(unittest.IsolatedAsyncioTestCase):
 async def test_actual_mapper_crosses_tracks(self):
  c,*_=fixture();result=await c.recover_alexa_flow('Office speakers',TOKEN,150000)
  self.assertTrue(result['ok']);c._play_index.assert_awaited_once_with('Office speakers','two',48,False)
 async def test_format_conversion_is_same_stream(self):
  for codec in ('flac','wav','aac'):
   with self.subTest(codec=codec):
    c,d,p,items=fixture();p._last_stream_url=p._last_stream_url.replace('.mp3','.'+codec)
    result=await c.recover_alexa_flow('Office speakers',TOKEN,150000)
    self.assertTrue(result['ok']);c._play_index.assert_awaited_once_with('Office speakers','two',48,False)
 async def test_format_normalization_preserves_identity_guards(self):
  for part,replacement in (('session','other-session'),('start','other-item'),('Office.mp3','Other.flac'),('Office%20speakers','Bedroom')):
   with self.subTest(part=part):
    c,d,p,items=fixture();p._last_stream_url=TOKEN.replace(part,replacement)
    result=await c.recover_alexa_flow('Office speakers',TOKEN,150000)
    self.assertEqual(result['reason'],'newer_stream');c._play_index.assert_not_awaited()
 async def test_actual_mapper_seek(self):
  c,*_=fixture();await c.recover_alexa_flow('Office speakers',TOKEN,30000);c._play_index.assert_awaited_once_with('Office speakers','one',48,False)
 async def test_rate(self):
  c,d,p,items=fixture();items[1].extra_attributes={'playback_speed':2};await c.recover_alexa_flow('Office speakers',TOKEN,150000);c._play_index.assert_awaited_once_with('Office speakers','two',98,False)
 async def test_rejections(self):
  for case in ('paused','stale','otherplayer','newstream','group','synced','emptylog','outside','missingitem','ambiguous','nonalexa','ended','negative','bool','permission'):
   with self.subTest(case=case):
    c,d,p,items=fixture();offset=150000;token=TOKEN
    if case=='paused':d.queue.state=PlaybackState.PAUSED
    if case=='stale':d.session_id='new'
    if case=='otherplayer':token=token.replace('Office%20speakers','Bedroom')
    if case=='newstream':p._last_stream_url='/announcement/Office.mp3'
    if case=='group':p.state.active_group='group'
    if case=='synced':p.state.synced_to='leader'
    if case=='emptylog':d.flow_mode_stream_log=[]
    if case=='outside':offset=999999
    if case=='missingitem':items.clear()
    if case=='ambiguous':d.flow_mode_stream_log[0].seconds_streamed=None;items[0].streamdetails.seconds_streamed=None
    if case=='nonalexa':p.provider.domain='other'
    if case=='ended':d.queue.ended=True
    if case=='negative':offset=-1
    if case=='bool':offset=True
    if case=='permission':
     def deny(_):raise PermissionError()
     c._check_player_permission=deny
     with self.assertRaises(PermissionError):await c.recover_alexa_flow('Office speakers',token,offset)
    else:
     result=await c.recover_alexa_flow('Office speakers',token,offset);self.assertFalse(result['ok'])
    c._play_index.assert_not_awaited()
 async def test_duplicate_consumed(self):
  c,*_=fixture();await c.recover_alexa_flow('Office speakers',TOKEN,150000);r=await c.recover_alexa_flow('Office speakers',TOKEN,150000);self.assertEqual(r['reason'],'retry_limit');self.assertEqual(c._play_index.await_count,1)
 async def test_uncertain_dispatch_not_retried(self):
  c,*_=fixture();c._play_index.side_effect=TimeoutError
  with self.assertRaises(TimeoutError):await c.recover_alexa_flow('Office speakers',TOKEN,150000)
  r=await c.recover_alexa_flow('Office speakers',TOKEN,150000);self.assertEqual(r['reason'],'retry_limit')
 async def test_budget(self):
  c,d,p,_=fixture()
  for session in ('a','b'):
   token=TOKEN.replace('session',session);d.session_id=session;p._last_stream_url=token;self.assertTrue((await c.recover_alexa_flow('Office speakers',token,150000))['ok'])
  d.session_id='c';p._last_stream_url=TOKEN.replace('session','c');self.assertEqual((await c.recover_alexa_flow('Office speakers',p._last_stream_url,150000))['reason'],'retry_limit')
spec=importlib.util.spec_from_file_location('offset','tests/alexa_offset/skill_offset_recovery.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SkillTests(unittest.TestCase):
 def setUp(self):m._devices.clear()
 def test_offset_requires_failure(self):
  m.started('d',TOKEN)
  with patch.object(m.threading,'Thread') as t:m.event('d',TOKEN,150000);t.assert_not_called()
 def test_failed_then_stopped(self):
  m.started('d',TOKEN)
  with patch.object(m.threading,'Thread') as t:
   m.event('d',TOKEN,failure=True);t.assert_not_called();m.event('d',TOKEN,150000);self.assertEqual(t.call_count,1);self.assertEqual(t.call_args.kwargs['args'][3],150000)
 def test_stopped_then_failed(self):
  m.started('d',TOKEN)
  with patch.object(m.threading,'Thread') as t:m.event('d',TOKEN,150000);m.event('d',TOKEN,failure=True);self.assertEqual(t.call_count,1)
 def test_cancel(self):
  m.started('d',TOKEN);m.cancel('d')
  with patch.object(m.threading,'Thread') as t:m.event('d',TOKEN,failure=True);m.event('d',TOKEN,150000);t.assert_not_called()
 def test_stale(self):
  m.started('d',TOKEN)
  with patch.object(m.threading,'Thread') as t:m.event('d',TOKEN+'x',failure=True);m.event('d',TOKEN,150000);t.assert_not_called()
 def test_duplicate(self):
  m.started('d',TOKEN)
  with patch.object(m.threading,'Thread') as t:
   m.event('d',TOKEN,failure=True);m.event('d',TOKEN,150000);m._devices['d']['busy']=False;m.event('d',TOKEN,150000);self.assertEqual(t.call_count,1)
if __name__ == '__main__': unittest.main()
