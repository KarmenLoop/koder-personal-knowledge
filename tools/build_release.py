"""Build a source-only installable skill ZIP and SHA-256 checksum."""
import hashlib
from pathlib import Path
import zipfile


def main():
    root = Path(__file__).resolve().parents[1]
    version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    skill = root / 'koder-personal-knowledge'
    output = root / 'dist'
    output.mkdir(exist_ok=True)
    files = sorted(p for p in skill.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    allowed = {'.md', '.py', '.yaml'}
    for p in files:
        if p.name not in {'LICENSE', 'NOTICE'} and p.suffix not in allowed:
            raise ValueError('Unexpected skill resource: ' + p.name)
        if p.is_symlink():
            raise ValueError('Symlink resource refused')
    archive = output / ('koder-personal-knowledge-' + version + '.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for p in files:
            info = zipfile.ZipInfo(p.relative_to(root).as_posix(), date_time=(2026, 10, 19, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, p.read_bytes())
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise ValueError('Archive integrity check failed')
        for p in files:
            assert bundle.read(p.relative_to(root).as_posix()) == p.read_bytes()
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = output / (archive.name + '.sha256')
    checksum.write_text(digest + '  ' + archive.name + '\n', encoding='utf-8')
    print(str(archive))
    print(digest)


if __name__ == '__main__':
    main()
