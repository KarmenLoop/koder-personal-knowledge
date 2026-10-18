"""Synthetic local acceptance; never reads an existing personal knowledge base."""
import importlib.util
import json
import os
from pathlib import Path, PureWindowsPath
import subprocess
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parents[1] / 'koder-personal-knowledge'
SCRIPT = PACKAGE / 'scripts' / 'knowledge.py'


class KnowledgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SCRIPT.is_file():
            return
        spec = importlib.util.spec_from_file_location('knowledge', SCRIPT)
        cls.k = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.k)

    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), 'Missing local knowledge implementation')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'knowledge'
        self.store = self.k.Knowledge(self.root)
        self.store.init('owner-1')

    def record(self, **changes):
        data = dict(category='profile', title='\u8868\u8fbe\u504f\u597d', body='\u504f\u597d\u7b80\u6d01\u7684\u4e2d\u6587\u56de\u590d\u3002',
                    kind='fact', source={'channel': 'terminal', 'ref': 'synthetic:message-1'})
        data.update(changes)
        return data

    def put(self, **changes):
        return self.store.remember(self.record(**changes), 'owner-1', 'personal')

    def test_default_drives_and_non_windows(self):
        self.assertEqual(str(self.k.default_root('Windows', 'C:/Users/Test', True)), 'D:\\KoderKnowledge')
        self.assertEqual(str(self.k.default_root('Windows', 'C:/Users/Test', False)), 'C:\\Users\\Test\\KoderKnowledge')
        self.assertEqual(self.k.default_root('Darwin', '/Users/Test'), Path('/Users/Test/KoderKnowledge'))

    def test_windows_without_d_still_uses_c_for_redirected_profile(self):
        self.assertEqual(str(self.k.default_root('Windows', 'E:/Profiles/Test', False)), 'C:\\Users\\Test\\KoderKnowledge')

    def test_persistence_and_exact_source(self):
        item = self.put()
        other = self.k.Knowledge(self.root)
        got = other.get(item['id'], 'owner-1')
        self.assertEqual(got['source'], self.record()['source'])
        self.assertEqual(got['body'], self.record()['body'])
        self.assertIn('created_at', got)

    def test_idempotent_event_and_conflicting_retry(self):
        item = self.put(event_id='channel:bot:chat:message:fact1')
        same = self.put(event_id='channel:bot:chat:message:fact1')
        self.assertEqual(same['id'], item['id'])
        with self.assertRaisesRegex(self.k.KnowledgeError, 'EVENT_CONFLICT'):
            self.put(event_id='channel:bot:chat:message:fact1', body='\u4e0d\u540c\u5185\u5bb9')

    def test_correction_preserves_history_and_search_uses_current(self):
        old = self.put(body='\u559c\u6b22\u957f\u7bc7\u56de\u590d')
        new = self.put(supersedes=old['id'])
        self.assertEqual(self.store.get(old['id'], 'owner-1')['status'], 'superseded')
        self.assertEqual(self.store.search('\u56de\u590d', 'owner-1')['items'][0]['id'], new['id'])
        self.assertEqual(self.store.search('\u957f\u7bc7', 'owner-1')['items'], [])

    def test_inference_never_becomes_confirmed_fact_implicitly(self):
        item = self.put(kind='inference', confidence=0.6, body='\u53ef\u80fd\u504f\u597d\u65e9\u95f4\u5de5\u4f5c')
        self.assertEqual(item['status'], 'unconfirmed')
        self.assertEqual(self.store.search('\u65e9\u95f4', 'owner-1')['items'], [])
        self.assertEqual(len(self.store.search('\u65e9\u95f4', 'owner-1', include_unconfirmed=True)['items']), 1)

    def test_cross_channel_same_space_and_provenance(self):
        self.put(category='work', body='\u9879\u76ee\u884c\u4e1a\u672f\u8bed\u4e3a\u5408\u6210\u6821\u9a8c', source={'channel': 'weixin', 'ref': 'synthetic:wx1'})
        item = self.put(category='life', body='\u751f\u6d3b\u4e60\u60ef\u4e3a\u6563\u6b65', source={'channel': 'feishu', 'ref': 'synthetic:fs1'})
        self.assertEqual(len(self.store.list_entries('owner-1')['items']), 2)
        self.assertEqual(self.store.search('\u6563\u6b65', 'owner-1')['items'][0]['source']['channel'], 'feishu')

    def test_verified_group_grant_and_revoke(self):
        item = self.put()
        with self.assertRaisesRegex(self.k.KnowledgeError, 'ACCESS_DENIED'):
            self.store.get(item['id'], 'group:synthetic:one')
        self.store.grant('owner-1', 'personal', 'group:synthetic:one', 'reader')
        self.assertEqual(self.store.get(item['id'], 'group:synthetic:one')['id'], item['id'])
        with self.assertRaisesRegex(self.k.KnowledgeError, 'ACCESS_DENIED'):
            self.store.remember(self.record(), 'group:synthetic:one')
        self.store.grant('owner-1', 'personal', 'group:synthetic:one', 'revoke')
        with self.assertRaisesRegex(self.k.KnowledgeError, 'ACCESS_DENIED'):
            self.store.get(item['id'], 'group:synthetic:one')

    def test_space_isolation_even_after_personal_grant(self):
        self.store.create_space('owner-1', 'work-project', '\u9879\u76ee\u8d44\u6599')
        private = self.store.remember(self.record(body='\u9879\u76ee\u9694\u79bb\u6570\u636e'), 'owner-1', 'work-project')
        self.store.grant('owner-1', 'personal', 'group:synthetic:one', 'reader')
        with self.assertRaisesRegex(self.k.KnowledgeError, 'ACCESS_DENIED'):
            self.store.get(private['id'], 'group:synthetic:one')
        with self.assertRaisesRegex(self.k.KnowledgeError, 'ACCESS_DENIED'):
            self.store.grant('group:synthetic:one', 'work-project', 'intruder', 'writer')

    def test_text_import_copies_original_and_searches_content(self):
        original = Path(self.tmp.name) / '\u884c\u4e1a\u672f\u8bed.txt'
        original.write_text('\u51b7\u94fe\u7269\u6d41\u662f\u672c\u6d4b\u8bd5\u7684\u884c\u4e1a\u672f\u8bed', encoding='utf-8')
        item = self.store.import_file(original, 'owner-1', source={'channel': 'wecom', 'ref': 'synthetic:file1'})
        original.write_text('\u539f\u59cb\u8def\u5f84\u5df2\u53d8\u5316', encoding='utf-8')
        self.assertIn('\u51b7\u94fe', self.store.search('\u51b7\u94fe\u7269\u6d41', 'owner-1')['items'][0]['body'])
        self.assertEqual((self.root / item['attachment']['path']).read_text(encoding='utf-8'), '\u51b7\u94fe\u7269\u6d41\u662f\u672c\u6d4b\u8bd5\u7684\u884c\u4e1a\u672f\u8bed')

    def test_binary_original_is_kept_without_fake_extraction(self):
        original = Path(self.tmp.name) / '\u8d44\u6599.pdf'
        original.write_bytes(b'%PDF-1.4 synthetic fixture')
        item = self.store.import_file(original, 'owner-1', source={'channel': 'terminal', 'ref': 'synthetic:pdf1'})
        self.assertEqual(item['attachment']['extraction'], 'attachment_only')
        self.assertTrue((self.root / item['attachment']['path']).is_file())

    def test_secret_not_saved_and_no_raw_error_echo(self):
        secret = 'sk-' + 'a' * 40
        with self.assertRaisesRegex(self.k.KnowledgeError, 'SECRET_DETECTED') as err:
            self.put(body='API key=' + secret)
        self.assertNotIn(secret, str(err.exception))
        self.assertEqual(self.store.list_entries('owner-1')['items'], [])
        self.assertNotIn(secret.encode(), (self.root / 'knowledge.sqlite3').read_bytes())

    def test_delete_scrubs_record_attachment_and_views(self):
        original = Path(self.tmp.name) / 'private.txt'
        original.write_text('SYNTHETIC-DELETE-MARKER', encoding='utf-8')
        item = self.store.import_file(original, 'owner-1', source={'channel': 'terminal', 'ref': 'synthetic:delete'})
        self.store.render('owner-1')
        self.store.forget(item['id'], 'owner-1')
        with self.assertRaisesRegex(self.k.KnowledgeError, 'NOT_FOUND'):
            self.store.get(item['id'], 'owner-1')
        self.assertFalse((self.root / item['attachment']['path']).exists())
        for path in self.root.rglob('*'):
            if path.is_file():
                self.assertNotIn(b'SYNTHETIC-DELETE-MARKER', path.read_bytes(), str(path))
        self.assertTrue(original.exists())

    def test_browser_view_escapes_content_and_shows_all_categories(self):
        self.put(body='<script>alert(1)</script> \u5408\u6210\u5185\u5bb9')
        self.put(kind='inference', body='\u5f85\u786e\u8ba4\u7684\u504f\u597d')
        output = self.store.render('owner-1')
        page = Path(output['index']).read_text(encoding='utf-8')
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', page)
        self.assertIn('\u5f85\u786e\u8ba4\u7684\u504f\u597d', page)
        self.assertIn('Personal profile', page)
        self.assertTrue(list((self.root / 'views' / 'notes').glob('*.md')))

    def test_search_is_bounded_and_chinese_partial_match(self):
        for i in range(8):
            self.put(title='\u5de5\u5177\u504f\u597d' + str(i), category='tools', body='\u98de\u4e66\u7528\u4e8e\u9879\u76ee\u6c9f\u901a\u3002' * 500)
        result = self.store.search('\u9879\u76ee\u6c9f\u901a', 'owner-1', limit=3, max_chars=1200)
        self.assertLessEqual(len(result['items']), 3)
        self.assertLessEqual(len(json.dumps(result, ensure_ascii=False)), 1200)
        self.assertTrue(result['items'])
        self.assertTrue(result['truncated'])

    def test_unknown_root_read_does_not_initialize(self):
        unknown = Path(self.tmp.name) / 'absent'
        with self.assertRaisesRegex(self.k.KnowledgeError, 'NOT_INITIALIZED'):
            self.k.Knowledge(unknown).search('hello', 'owner-1')
        self.assertFalse(unknown.exists())

    def test_multiple_process_writers_keep_all_entries(self):
        record = Path(self.tmp.name) / 'record.json'
        record.write_text(json.dumps(self.record(), ensure_ascii=False), encoding='utf-8')
        jobs = [subprocess.Popen([sys.executable, str(SCRIPT), '--root', str(self.root), '--principal', 'owner-1', 'remember', '--record', str(record)], stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(4)]
        for job in jobs:
            out, err = job.communicate(timeout=20)
            self.assertEqual(job.returncode, 0, (out, err))
        self.assertEqual(len(self.store.list_entries('owner-1')['items']), 4)

    def test_invalid_metadata_never_partially_supersedes(self):
        old = self.put()
        with self.assertRaises(self.k.KnowledgeError):
            self.put(category='../../escape', supersedes=old['id'])
        self.assertEqual(self.store.get(old['id'], 'owner-1')['status'], 'active')

    def test_same_library_reinit_does_not_switch_owner(self):
        self.put()
        with self.assertRaisesRegex(self.k.KnowledgeError, 'OWNER_MISMATCH'):
            self.store.init('other-owner')
        self.assertEqual(len(self.store.list_entries('owner-1')['items']), 1)

    def test_search_budget_also_bounds_long_query_metadata(self):
        self.put()
        result = self.store.search('\u5f88\u957f\u7684\u95ee\u9898' * 120, 'owner-1', max_chars=600)
        self.assertLessEqual(len(json.dumps(result, ensure_ascii=False)), 600)

    def test_forgotten_event_cannot_be_resurrected_by_retry(self):
        item = self.put(event_id='synthetic:one-event')
        self.store.forget(item['id'], 'owner-1')
        with self.assertRaisesRegex(self.k.KnowledgeError, 'EVENT_FORGOTTEN'):
            self.put(event_id='synthetic:one-event')

    def test_initialization_refuses_unrelated_nonempty_directory(self):
        another = Path(self.tmp.name) / 'unrelated'
        another.mkdir()
        (another / 'user-file.txt').write_text('untouched', encoding='utf-8')
        with self.assertRaisesRegex(self.k.KnowledgeError, 'NONEMPTY_ROOT'):
            self.k.Knowledge(another).init('owner-1')
        self.assertFalse((another / 'knowledge.sqlite3').exists())

    def test_symlink_cannot_redirect_library_writes(self):
        outside = Path(self.tmp.name) / 'outside'
        outside.mkdir()
        try:
            (self.root / 'library').symlink_to(outside, target_is_directory=True)
        except OSError as error:
            if sys.platform == 'win32' and getattr(error, 'winerror', None) == 1314:
                self.skipTest('Windows account lacks the privilege to create a symlink')
            raise
        original = Path(self.tmp.name) / 'example.txt'
        original.write_text('synthetic attachment', encoding='utf-8')
        with self.assertRaisesRegex(self.k.KnowledgeError, 'SYMLINK_IN_LIBRARY'):
            self.store.import_file(original, 'owner-1', source={'channel': 'terminal', 'ref': 'synthetic:symlink'})
        self.assertEqual(list(outside.iterdir()), [])

    def test_invalid_record_types_fail_as_controlled_input(self):
        for changes in [{'category': []}, {'kind': []}, {'source': 'invalid'}, {'confidence': True}]:
            with self.subTest(changes=changes):
                with self.assertRaises(self.k.KnowledgeError):
                    self.put(**changes)

    def test_full_text_retrieval_can_be_paged_without_loss(self):
        body = '\u884c\u4e1a\u8d44\u6599\u9010\u6bb5\u9605\u8bfb\u3002' * 1400
        item = self.put(body=body)
        chunks, offset = [], 0
        while True:
            page = self.store.get(item['id'], 'owner-1', offset=offset, max_chars=1000)
            self.assertLessEqual(len(page['body']), 1000)
            chunks.append(page['body'])
            if page['next_offset'] is None:
                break
            offset = page['next_offset']
        self.assertEqual(''.join(chunks), body)


if __name__ == '__main__':
    unittest.main(verbosity=2)
