#!/usr/bin/env python3
"""Local personal knowledge store. Python 3.9+, standard library, no network.

Identity and channel authentication belong to the host Agent. A --principal
argument is a trusted local API input, not an authentication mechanism.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path, PureWindowsPath
import platform
import re
import sqlite3
import sys
import tempfile
from urllib.parse import quote
import uuid

CATEGORIES = {
    'profile': 'Personal profile', 'habits': 'Habits and preferences', 'people': 'People and relationships',
    'tools': 'Tools', 'work': 'Work and career', 'industry': 'Industry knowledge',
    'life': 'Everyday life', 'reference': 'Reference library',
}
TEXT_SUFFIXES = {'.txt', '.md', '.csv', '.json', '.log', '.yaml', '.yml', '.xml', '.html', '.htm', '.rst'}
MAX_FILE = 32 * 1024 * 1024
MAX_TEXT = 256 * 1024
SECRET = re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{24,}|(?:api[_ -]?key|access[_ -]?token|password|secret|\u5bc6\u7801|\u5bc6\u94a5)\s*[=:\uff1a]\s*[\"\']?[^\s\"\']{8,}', re.I)


class KnowledgeError(Exception):
    pass


def fail(code):
    raise KnowledgeError(code)


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def clean_text(value, limit, required=True):
    if not isinstance(value, str) or len(value) > limit or '\x00' in value or (required and not value.strip()):
        fail('INVALID_TEXT')
    return value.strip()


def default_root(system=None, home=None, d_exists=None):
    system = system or platform.system()
    home = str(home or Path.home())
    if system == 'Windows':
        available = Path('D:/').is_dir() if d_exists is None else d_exists
        profile = PureWindowsPath(home)
        fallback = profile if profile.drive.upper() == 'C:' else PureWindowsPath('C:/Users') / profile.name
        return PureWindowsPath('D:/KoderKnowledge') if available else fallback / 'KoderKnowledge'
    return Path(home) / 'KoderKnowledge'


def normalize(record):
    if not isinstance(record, dict):
        fail('INVALID_RECORD')
    unknown = set(record) - {'category', 'title', 'body', 'kind', 'confidence', 'source', 'tags', 'event_id', 'supersedes', 'attachment'}
    if unknown:
        fail('UNKNOWN_RECORD_FIELD')
    category = record.get('category')
    kind = record.get('kind', 'fact')
    if not isinstance(category, str) or not isinstance(kind, str) or category not in CATEGORIES or kind not in {'fact', 'inference', 'reference'}:
        fail('INVALID_CATEGORY_OR_KIND')
    source = record.get('source')
    if not isinstance(source, dict) or set(source) - {'channel', 'ref', 'speaker', 'observed_at', 'extractor'}:
        fail('INVALID_SOURCE')
    if 'channel' not in source or 'ref' not in source:
        fail('SOURCE_REQUIRED')
    source = {k: clean_text(v, 2048) for k, v in source.items()}
    tags = record.get('tags', [])
    if not isinstance(tags, list) or len(tags) > 24:
        fail('INVALID_TAGS')
    tags = sorted(set(clean_text(v, 80) for v in tags))
    confidence = record.get('confidence', 1.0 if kind != 'inference' else 0.5)
    if isinstance(confidence, bool) or not isinstance(confidence, (float, int)) or not 0 <= confidence <= 1:
        fail('INVALID_CONFIDENCE')
    data = dict(category=category, title=clean_text(record.get('title'), 240),
                body=clean_text(record.get('body'), MAX_TEXT), kind=kind,
                confidence=confidence, source=source, tags=tags)
    for field in ('event_id', 'supersedes'):
        data[field] = clean_text(record[field], 512) if record.get(field) is not None else None
    # Attachments are populated by import_file, never accepted from model JSON.
    if record.get('attachment') is not None:
        fail('USE_IMPORT_FILE_FOR_ATTACHMENTS')
    if SECRET.search(dump(data)):
        fail('SECRET_DETECTED')
    return data


class Knowledge:
    def __init__(self, root):
        self.root = Path(root).expanduser().absolute()

    def _path(self, relative):
        target = self.root / relative
        try:
            target.relative_to(self.root)
        except ValueError:
            fail('PATH_OUTSIDE_LIBRARY')
        if '..' in Path(relative).parts or Path(relative).is_absolute():
            fail('PATH_OUTSIDE_LIBRARY')
        current = target
        while current != self.root.parent:
            if current.is_symlink():
                fail('SYMLINK_IN_LIBRARY')
            current = current.parent
        return target

    def _write(self, relative, text):
        dest = self._path(relative)
        dest.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix='.writing-', dir=str(dest.parent))
        try:
            with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, dest)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    @contextmanager
    def _db(self, write=False):
        dbfile = self._path('knowledge.sqlite3')
        if not dbfile.is_file():
            fail('NOT_INITIALIZED')
        db = sqlite3.connect(str(dbfile), timeout=8, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA busy_timeout=8000')
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('PRAGMA secure_delete=ON')
            try:
                version = db.execute("SELECT value FROM meta WHERE key='schema'").fetchone()
            except sqlite3.DatabaseError:
                fail('INVALID_LIBRARY')
            if not version or version[0] != '1':
                fail('UNSUPPORTED_SCHEMA')
            db.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
            yield db
            db.execute('COMMIT')
        except BaseException:
            if db.in_transaction:
                db.execute('ROLLBACK')
            raise
        finally:
            db.close()

    def init(self, owner):
        owner = clean_text(owner, 256)
        if self.root.is_symlink():
            fail('SYMLINK_IN_LIBRARY')
        dbfile = self._path('knowledge.sqlite3')
        if dbfile.exists():
            with self._db() as db:
                if self._owner(db) != owner:
                    fail('OWNER_MISMATCH')
            return self.render(owner)
        if self.root.exists() and any(self.root.iterdir()):
            fail('NONEMPTY_ROOT')
        self.root.mkdir(parents=True, exist_ok=True)
        if os.name != 'nt':
            self.root.chmod(0o700)
        # Exclusive create prevents two initializers replacing each other's owner.
        try:
            fd = os.open(str(dbfile), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        except FileExistsError:
            fail('INITIALIZATION_IN_PROGRESS')
        db = sqlite3.connect(str(dbfile))
        try:
            db.executescript('''
              CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
              CREATE TABLE spaces(id TEXT PRIMARY KEY,title TEXT NOT NULL);
              CREATE TABLE grants(space TEXT NOT NULL REFERENCES spaces(id),principal TEXT NOT NULL,role TEXT NOT NULL,PRIMARY KEY(space,principal));
              CREATE TABLE entries(id TEXT PRIMARY KEY,space TEXT NOT NULL REFERENCES spaces(id),category TEXT NOT NULL,title TEXT NOT NULL,body TEXT NOT NULL,kind TEXT NOT NULL,status TEXT NOT NULL,confidence REAL NOT NULL,source TEXT NOT NULL,tags TEXT NOT NULL,event_id TEXT,supersedes TEXT,attachment TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,fingerprint TEXT NOT NULL);
              CREATE UNIQUE INDEX events ON entries(space,event_id) WHERE event_id IS NOT NULL;
              CREATE TABLE tombstones(id TEXT PRIMARY KEY,deleted_at TEXT NOT NULL,event_hash TEXT);
            ''')
            db.executemany('INSERT INTO meta VALUES(?,?)', [('schema', '1'), ('owner', owner), ('created_at', now())])
            db.execute('INSERT INTO spaces VALUES(?,?)', ('personal', 'Personal Knowledge Base'))
            db.commit()
        finally:
            db.close()
        self._write('library.json', dump({'schema_version': 1, 'root': str(self.root), 'storage': 'SQLite + original files + regenerated local views', 'network': False}) + '\n')
        return self.render(owner)

    @staticmethod
    def _owner(db):
        return db.execute("SELECT value FROM meta WHERE key='owner'").fetchone()[0]

    def _owner_only(self, db, principal):
        if not principal or principal != self._owner(db):
            fail('ACCESS_DENIED')

    def _permit(self, db, principal, space, write=False):
        if not db.execute('SELECT 1 FROM spaces WHERE id=?', (space,)).fetchone():
            fail('SPACE_NOT_FOUND')
        if principal and principal == self._owner(db):
            return
        role = db.execute('SELECT role FROM grants WHERE space=? AND principal=?', (space, principal)).fetchone()
        if not role or (write and role[0] != 'writer'):
            fail('ACCESS_DENIED')

    def create_space(self, principal, space, title):
        if not isinstance(space, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}', space):
            fail('INVALID_SPACE')
        title = clean_text(title, 240)
        with self._db(True) as db:
            self._owner_only(db, principal)
            db.execute('INSERT INTO spaces VALUES(?,?)', (space, title))
            self._render_locked(db)
        return {'space': space, 'title': title}

    def grant(self, principal, space, member, role):
        member = clean_text(member, 256)
        if role not in {'reader', 'writer', 'revoke'}:
            fail('INVALID_ROLE')
        with self._db(True) as db:
            self._owner_only(db, principal)
            self._permit(db, principal, space)
            if role == 'revoke':
                db.execute('DELETE FROM grants WHERE space=? AND principal=?', (space, member))
            else:
                db.execute('INSERT OR REPLACE INTO grants VALUES(?,?,?)', (space, member, role))
        return {'space': space, 'principal': member, 'role': role}

    @staticmethod
    def _decode(row):
        item = dict(row)
        for key in ('source', 'tags', 'attachment'):
            item[key] = json.loads(item[key]) if item[key] is not None else None
        item.pop('fingerprint', None)
        return item

    def _remember_locked(self, db, data, principal, space, attachment=None):
        self._permit(db, principal, space, True)
        fingerprint = hashlib.sha256(dump({**data, 'attachment': attachment}).encode('utf-8')).hexdigest()
        if data['event_id']:
            event_hash = hashlib.sha256(dump([space, data['event_id']]).encode('utf-8')).hexdigest()
            if db.execute('SELECT 1 FROM tombstones WHERE event_hash=?', (event_hash,)).fetchone():
                fail('EVENT_FORGOTTEN')
            old = db.execute('SELECT * FROM entries WHERE space=? AND event_id=?', (space, data['event_id'])).fetchone()
            if old:
                if old['fingerprint'] != fingerprint:
                    fail('EVENT_CONFLICT')
                return self._decode(old)
        if data['supersedes']:
            old = db.execute('SELECT * FROM entries WHERE id=? AND space=?', (data['supersedes'], space)).fetchone()
            if not old or old['status'] == 'superseded':
                fail('SUPERSEDES_NOT_CURRENT')
            # Shared-space contributors may add observations; changing the owner's
            # personal profile requires the owner route.
            self._owner_only(db, principal)
            db.execute("UPDATE entries SET status='superseded',updated_at=? WHERE id=?", (now(), old['id']))
        identity, stamp = str(uuid.uuid4()), now()
        status = 'unconfirmed' if data['kind'] == 'inference' else 'active'
        values = (identity, space, data['category'], data['title'], data['body'], data['kind'], status,
                  data['confidence'], dump(data['source']), dump(data['tags']), data['event_id'], data['supersedes'],
                  dump(attachment) if attachment else None, stamp, stamp, fingerprint)
        db.execute('INSERT INTO entries VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', values)
        return self._decode(db.execute('SELECT * FROM entries WHERE id=?', (identity,)).fetchone())

    def remember(self, record, principal, space='personal'):
        data = normalize(record)
        with self._db(True) as db:
            item = self._remember_locked(db, data, principal, space)
            self._render_locked(db)
            return item

    def get(self, identity, principal, offset=0, max_chars=6000):
        if not isinstance(offset, int) or offset < 0 or not isinstance(max_chars, int) or not 100 <= max_chars <= 24000:
            fail('INVALID_READ_BUDGET')
        with self._db() as db:
            row = db.execute('SELECT * FROM entries WHERE id=?', (identity,)).fetchone()
            if not row:
                fail('NOT_FOUND')
            self._permit(db, principal, row['space'])
            item = self._decode(row)
            body = item['body']
            item['body'] = body[offset:offset + max_chars]
            item['body_total_chars'] = len(body)
            item['offset'] = offset
            item['next_offset'] = offset + max_chars if offset + max_chars < len(body) else None
            return item

    def list_entries(self, principal, space='personal', offset=0, limit=50, include_history=True):
        if not 1 <= limit <= 200 or offset < 0:
            fail('INVALID_PAGINATION')
        with self._db() as db:
            self._permit(db, principal, space)
            condition = 'space=?' + ('' if include_history else " AND status='active'")
            total = db.execute('SELECT count(*) FROM entries WHERE ' + condition, (space,)).fetchone()[0]
            rows = db.execute('SELECT * FROM entries WHERE ' + condition + ' ORDER BY created_at,id LIMIT ? OFFSET ?', (space, limit, offset)).fetchall()
            return {'total': total, 'items': [self._decode(row) for row in rows], 'next_offset': offset + limit if offset + limit < total else None}

    def search(self, query, principal, space='personal', limit=8, max_chars=6000, include_unconfirmed=False):
        query = clean_text(query, 800)
        if not 1 <= limit <= 30 or not 600 <= max_chars <= 24000:
            fail('INVALID_SEARCH_BUDGET')
        # Bigrams let a natural Chinese question match a shorter stored term.
        terms = re.findall(r'[a-z0-9_-]+|[\u3400-\u9fff]+', query.lower())
        terms += [word[i:i+2] for word in terms[:] if re.search(r'[\u3400-\u9fff]', word) and len(word) > 2 for i in range(len(word)-1)]
        terms = list(dict.fromkeys(terms))[:40] or [query.lower()]
        with self._db() as db:
            self._permit(db, principal, space)
            statuses = "('active','unconfirmed')" if include_unconfirmed else "('active')"
            matches = []
            for row in db.execute('SELECT * FROM entries WHERE space=? AND status IN ' + statuses, (space,)):
                hay = ' '.join([row['title'], row['body'], row['tags']]).lower()
                score = sum((4 if term in row['title'].lower() else 1) * len(term) for term in terms if term in hay)
                if score:
                    matches.append((score, row['updated_at'], row['id']))
            matches.sort(reverse=True)
            result = {'query': query[:min(200, max_chars // 4)], 'space': space, 'items': [], 'total_matches': len(matches), 'truncated': False}
            for _, _, identity in matches[:limit]:
                row = db.execute('SELECT * FROM entries WHERE id=?', (identity,)).fetchone()
                text = row['body']
                positions = [text.lower().find(t) for t in terms if t in text.lower()]
                start = max(0, min(positions or [0]) - 120)
                body = text[start:start + min(900, max_chars // 2)]
                item = dict(id=row['id'], category=row['category'], title=row['title'][:160], body=body,
                            kind=row['kind'], status=row['status'], confidence=row['confidence'],
                            source=json.loads(row['source']), updated_at=row['updated_at'], excerpt=len(body) < len(text))
                # Bound metadata as well as body; full provenance is available via get.
                item['source'] = {k: v[:180] for k, v in item['source'].items()}
                candidate = {**result, 'items': result['items'] + [item], 'truncated': True}
                while len(dump(candidate)) > max_chars and len(item['body']) > 80:
                    item['body'] = item['body'][:max(80, len(item['body']) // 2)]
                    item['excerpt'] = True
                if len(dump(candidate)) > max_chars:
                    break
                result['items'].append(item)
            result['truncated'] = len(result['items']) < len(matches) or any(x['excerpt'] for x in result['items'])
            return result

    def import_file(self, file, principal, space='personal', source=None, extracted_text=None, event_id=None, title=None):
        original = Path(file).expanduser()
        if not original.is_file():
            fail('SOURCE_FILE_NOT_FOUND')
        if original.name.lower().startswith('.env') or original.suffix.lower() in {'.pem', '.key', '.p12', '.pfx', '.kdbx'}:
            fail('CREDENTIAL_FILE_REFUSED')
        # Authorize before opening the original or any supplied extracted text.
        with self._db() as db:
            self._permit(db, principal, space, True)
        with original.open('rb') as handle:
            raw = handle.read(MAX_FILE + 1)
        if len(raw) > MAX_FILE:
            fail('FILE_TOO_LARGE')
        extraction, body = 'attachment_only', 'Original file archived. Text has not been extracted. Ask the host agent to run an available PDF, Office, or OCR tool.'
        if original.suffix.lower() in TEXT_SUFFIXES:
            try:
                body = raw.decode('utf-8-sig')
            except UnicodeDecodeError:
                try:
                    body = raw.decode('gb18030')
                except UnicodeDecodeError:
                    fail('UNSUPPORTED_TEXT_ENCODING')
            extraction = 'text'
            if len(body) > MAX_TEXT:
                fail('TEXT_TOO_LARGE_USE_CHUNKS')
        elif extracted_text is not None:
            with Path(extracted_text).expanduser().open('rb') as handle:
                text_bytes = handle.read(MAX_TEXT * 4 + 1)
            try:
                body = text_bytes.decode('utf-8-sig')
            except UnicodeDecodeError:
                fail('EXTRACTED_TEXT_MUST_BE_UTF8')
            extraction = 'host_extracted_text'
        if not body.strip():
            body = 'Empty original file archived.'
        data = normalize(dict(category='reference', title=title or original.name, body=body,
                              kind='reference', source=source, event_id=event_id))
        # Refuse recognizable secrets in text files, including the bytes beyond
        # the excerpt, rather than copying an unredacted original into the store.
        if SECRET.search(body):
            fail('SECRET_DETECTED')
        digest = hashlib.sha256(raw).hexdigest()
        # Store as .bin: imported HTML/scripts/executables cannot become active
        # content inside the offline knowledge viewer.
        relative = 'library/' + digest + '.bin'
        attachment = dict(path=relative, original_name=original.name, sha256=digest,
                          size=len(raw), extraction=extraction)
        if extracted_text:
            attachment['extracted_text_sha256'] = hashlib.sha256(body.encode('utf-8')).hexdigest()
        with self._db(True) as db:
            self._permit(db, principal, space, True)
            dest = self._path(relative)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                if hashlib.sha256(dest.read_bytes()).hexdigest() != digest:
                    fail('ATTACHMENT_HASH_MISMATCH')
            else:
                fd, temporary = tempfile.mkstemp(prefix='.import-', dir=str(dest.parent))
                try:
                    with os.fdopen(fd, 'wb') as handle:
                        handle.write(raw)
                        handle.flush()
                        os.fsync(handle.fileno())
                    os.replace(temporary, dest)
                finally:
                    if os.path.exists(temporary):
                        os.unlink(temporary)
            try:
                item = self._remember_locked(db, data, principal, space, attachment)
            except BaseException:
                references = db.execute('SELECT attachment FROM entries WHERE attachment IS NOT NULL').fetchall()
                if not any(json.loads(r[0])['path'] == relative for r in references):
                    dest.unlink()
                raise
            self._render_locked(db)
            return item

    def forget(self, identity, principal):
        with self._db(True) as db:
            self._owner_only(db, principal)
            row = db.execute('SELECT * FROM entries WHERE id=?', (identity,)).fetchone()
            if not row:
                fail('NOT_FOUND')
            db.execute('DELETE FROM entries WHERE id=?', (identity,))
            event_hash = hashlib.sha256(dump([row['space'], row['event_id']]).encode('utf-8')).hexdigest() if row['event_id'] else None
            db.execute('INSERT INTO tombstones VALUES(?,?,?)', (identity, now(), event_hash))
            if row['attachment']:
                relative = json.loads(row['attachment'])['path']
                remaining = db.execute('SELECT attachment FROM entries WHERE attachment IS NOT NULL').fetchall()
                if not any(json.loads(r[0])['path'] == relative for r in remaining):
                    self._path(relative).unlink(missing_ok=True)
            self._render_locked(db)
        return {'forgotten': identity, 'original_source_unchanged': True, 'external_backups_not_managed': True}

    def render(self, principal):
        with self._db(True) as db:
            self._owner_only(db, principal)
            return self._render_locked(db)

    def _render_locked(self, db):
        rows = [self._decode(row) for row in db.execute('SELECT * FROM entries ORDER BY category,created_at,id')]
        notes = self._path('views/notes')
        notes.mkdir(parents=True, exist_ok=True)
        active_ids = {row['id'] for row in rows}
        for note in notes.glob('*.md'):
            if re.fullmatch(r'[0-9a-f-]{36}\.md', note.name) and note.stem not in active_ids:
                self._path('views/notes/' + note.name).unlink()
        chunks = []
        for item in rows:
            # The database is authoritative; these files are readable snapshots.
            markdown = '# ' + item['title'] + '\n\n' + item['body'] + '\n\n---\n\n' + '\n'.join([
                'ID: ' + item['id'], 'Space: ' + item['space'], 'Category: ' + CATEGORIES[item['category']],
                'Kind: ' + item['kind'], 'Status: ' + item['status'], 'Source: ' + dump(item['source']),
                'Created: ' + item['created_at'], 'Updated: ' + item['updated_at'],
            ]) + ('\nOriginal file: ' + dump(item['attachment']) if item['attachment'] else '') + '\n'
            self._write('views/notes/' + item['id'] + '.md', markdown)
            escape = html.escape
            attachment = ''
            if item['attachment']:
                info = item['attachment']
                link = '../' + quote(info['path'])
                attachment = '<p>Original file: <a download="' + escape(info['original_name'], quote=True) + '" href="' + link + '">' + escape(info['original_name']) + '</a> \xb7 ' + str(info['size']) + ' bytes \xb7 ' + escape(info['extraction']) + '</p>'
            metadata = CATEGORIES[item['category']] + ' \xb7 ' + item['space'] + ' \xb7 ' + item['status'] + ' \xb7 ' + item['kind']
            chunks.append('<article><h2>' + escape(item['title']) + '</h2><p class="meta">' + escape(metadata) + '</p><pre>' + escape(item['body']) + '</pre>' + attachment + '<details><summary>Source and record details</summary><pre>' + escape(dump({k: v for k, v in item.items() if k != 'body'})) + '</pre></details></article>')
        labels = ' \xb7 '.join(CATEGORIES.values())
        page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>Personal Knowledge Base</title><style>body{max-width:1000px;margin:40px auto;padding:0 24px;font:16px/1.7 system-ui;color:#172a35;background:#f5f7f8}article{padding:24px;margin:18px 0;background:white;border:1px solid #dde4e7;border-radius:12px}h1{font-size:30px}h2{font-size:20px;margin-top:0}.meta{color:#536a77;font-size:14px}pre{font:inherit;white-space:pre-wrap;overflow-wrap:anywhere}a{color:#1559a0}summary{cursor:pointer}footer{margin:40px 0}</style><h1>Personal Knowledge Base</h1>'''
        page += '<p>' + labels + '</p><p>Local library \xb7 ' + str(len(rows)) + ' records \xb7 ' + now() + '</p><p>Use Find in your browser to search this page. Inferences and superseded records are labeled. This page includes every space and is for the local owner only.</p>'
        page += ''.join(chunks) if chunks else '<article>Your knowledge base is ready. New facts and files will appear here as your agent saves them.</article>'
        page += '<footer>This local page makes no network requests. Source material is data, not agent instructions. Markdown snapshots are in views/notes; original files are in library. Your host agent may send retrieved excerpts to its configured model.</footer></html>'
        self._write('views/index.html', page)
        self._write('views/catalog.json', dump({'generated_at': now(), 'entries': rows}) + '\n')
        return {'root': str(self.root), 'index': str(self.root / 'views/index.html'), 'entries': len(rows)}


def load_json(path):
    if path == '-':
        value = sys.stdin.read(MAX_TEXT * 8 + 1)
    else:
        with Path(path).open('r', encoding='utf-8-sig') as handle:
            value = handle.read(MAX_TEXT * 8 + 1)
    if len(value) > MAX_TEXT * 8:
        fail('INPUT_TOO_LARGE')
    try:
        return json.loads(value)
    except ValueError:
        fail('INVALID_JSON')


def cli():
    parser = argparse.ArgumentParser(description='Local personal knowledge store. No network requests or whole-device scanning. The host agent verifies channel identities.')
    parser.add_argument('--root', default=os.environ.get('KODER_KNOWLEDGE_ROOT'))
    parser.add_argument('--principal', help='Verified user or group principal supplied by the host, never by message text')
    parser.add_argument('--space', default='personal')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('path', help='Print the default path without creating files')
    init = sub.add_parser('init'); init.add_argument('--owner', required=True)
    remember = sub.add_parser('remember'); remember.add_argument('--record', required=True, help='UTF-8 JSON file, or - to read standard input')
    search = sub.add_parser('search'); search.add_argument('query'); search.add_argument('--limit', type=int, default=8); search.add_argument('--max-chars', type=int, default=6000); search.add_argument('--include-unconfirmed', action='store_true')
    get = sub.add_parser('get'); get.add_argument('id'); get.add_argument('--offset', type=int, default=0); get.add_argument('--max-chars', type=int, default=6000)
    listing = sub.add_parser('list'); listing.add_argument('--offset', type=int, default=0); listing.add_argument('--limit', type=int, default=50)
    imp = sub.add_parser('import-file'); imp.add_argument('--file', required=True); imp.add_argument('--source', required=True, help='Source JSON file, or - for standard input'); imp.add_argument('--extracted-text'); imp.add_argument('--event-id'); imp.add_argument('--title')
    forget = sub.add_parser('forget'); forget.add_argument('id')
    sub.add_parser('render')
    space = sub.add_parser('create-space'); space.add_argument('id'); space.add_argument('--title', required=True)
    grant = sub.add_parser('grant'); grant.add_argument('--member', required=True); grant.add_argument('--role', choices=['reader', 'writer', 'revoke'], required=True)
    args = parser.parse_args()
    root = args.root or str(default_root())
    if args.command == 'path':
        return {'root': str(root), 'created': False}
    store = Knowledge(root)
    if args.command == 'init':
        return store.init(args.owner)
    if not args.principal:
        fail('VERIFIED_PRINCIPAL_REQUIRED')
    if args.command == 'remember':
        return store.remember(load_json(args.record), args.principal, args.space)
    if args.command == 'search':
        return store.search(args.query, args.principal, args.space, args.limit, args.max_chars, args.include_unconfirmed)
    if args.command == 'get':
        return store.get(args.id, args.principal, args.offset, args.max_chars)
    if args.command == 'list':
        return store.list_entries(args.principal, args.space, args.offset, args.limit)
    if args.command == 'import-file':
        return store.import_file(args.file, args.principal, args.space, load_json(args.source), args.extracted_text, args.event_id, args.title)
    if args.command == 'forget':
        return store.forget(args.id, args.principal)
    if args.command == 'render':
        return store.render(args.principal)
    if args.command == 'create-space':
        return store.create_space(args.principal, args.id, args.title)
    if args.command == 'grant':
        return store.grant(args.principal, args.space, args.member, args.role)


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        print(dump(cli()))
    except KnowledgeError as error:
        print(dump({'error': str(error)}), file=sys.stderr)
        sys.exit(2)
    except (OSError, sqlite3.Error, UnicodeError):
        # Do not echo record bodies, tokens, raw OS paths or database payloads.
        print(dump({'error': 'LOCAL_IO_FAILED', 'hint': 'Check directory permissions, disk space, and file locks. This tool does not escalate privileges.'}), file=sys.stderr)
        sys.exit(3)
