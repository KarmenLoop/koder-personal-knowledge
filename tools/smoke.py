"""Run a synthetic, temporary end-to-end CLI walkthrough. No network."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    repo = Path(__file__).resolve().parents[1]
    script = repo / 'koder-personal-knowledge/scripts/knowledge.py'
    calls = []
    with tempfile.TemporaryDirectory(prefix='koder-knowledge-smoke-') as temporary:
        root = Path(temporary) / 'library'

        def run(args, principal='local-owner', expected=0):
            argv = [sys.executable, '-B', str(script), '--root', str(root), '--principal', principal] + args
            result = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8', timeout=25)
            if result.returncode != expected:
                raise AssertionError((args, result.returncode, result.stdout, result.stderr))
            calls.append({'command': args[0], 'exit_code': result.returncode})
            return json.loads(result.stdout or result.stderr)

        run(['init', '--owner', 'local-owner'])
        run(['remember', '--record', str(repo / 'examples/preference.json')])
        result = run(['search', 'summary', '--max-chars', '2000'])
        assert result['items'] and 'summary' in result['items'][0]['body']
        run(['import-file', '--file', str(repo / 'examples/field-notes.txt'), '--source', str(repo / 'examples/file-source.json')])
        result = run(['search', 'delivery window'])
        assert result['items'] and result['items'][0]['category'] == 'reference'
        run(['grant', '--member', 'group:synthetic:team', '--role', 'reader'])
        assert run(['search', 'summary'], principal='group:synthetic:team')['items']
        run(['grant', '--member', 'group:synthetic:team', '--role', 'revoke'])
        assert run(['search', 'summary'], principal='group:synthetic:team', expected=2)['error'] == 'ACCESS_DENIED'
        view = run(['render'])
        page = Path(view['index']).read_text(encoding='utf-8')
        assert 'lang="en"' in page and 'Personal Knowledge Base' in page
        assert 'Source and record details' in page
        assert view['entries'] == 2
    print(json.dumps({'result': 'PASS', 'synthetic_only': True, 'processes': len(calls), 'calls': calls}, indent=2))


if __name__ == '__main__':
    main()
