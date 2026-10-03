#!/usr/bin/env python3
"""Read-only local Markdown link/anchor checker; no history or Mermaid validation."""
import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


def visible(text):
    """Exclude YAML and fenced code, retaining line positions."""
    output = []
    marker = None
    length = 0
    front = text.startswith('---\n') or text.startswith('---\r\n')
    for number, line in enumerate(text.splitlines(), 1):
        if front:
            output.append('')
            if number > 1 and line.strip() == '---':
                front = False
            continue
        fence = re.match(r'^\s*(`{3,}|~{3,})(.*)$', line)
        if fence:
            token, rest = fence.groups()
            if marker is None:
                marker, length = token[0], len(token)
            elif token[0] == marker and len(token) >= length and not rest.strip():
                marker = None
            output.append('')
        else:
            output.append('' if marker else line)
    return '\n'.join(output), marker is not None


def anchors(text):
    heads, blocks = set(), set()
    duplicates = {}
    for line in text.splitlines():
        match = re.match(r'^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$', line)
        if match:
            title = match.group(1).strip()
            # Conventional Markdown heading slugs; exact titles serve Obsidian.
            slug = re.sub(r'[^\w\s-]', '', title.lower()).replace(' ', '-')
            count = duplicates.get(slug, 0)
            duplicates[slug] = count + 1
            heads.update((title, slug if not count else f'{slug}-{count}'))
        blocks.update(re.findall(r'\^([\w-]+)\s*$', line))
        heads.update(re.findall(r'<a\s+(?:id|name)=[\"\']([^\"\']+)', line))
    return heads, blocks


def check(root, vault=None):
    root = Path(root).resolve()
    vault = Path(vault).resolve() if vault else root
    errors, warnings, cache = [], [], {}

    def content(path):
        if path not in cache:
            raw = path.read_text(encoding='utf-8-sig')
            cache[path] = visible(raw)
        return cache[path][0]

    def verify(src, number, destination, wiki=False):
        decoded = unquote(destination.strip())
        if wiki:
            decoded = decoded.split('|', 1)[0]
        parsed = urlsplit(decoded)
        if parsed.scheme or decoded.startswith('//'):
            return
        filepart, _, fragment = decoded.partition('#')
        if not filepart:
            target = src
        elif wiki:
            rel = Path(filepart)
            if not rel.suffix:
                rel = rel.with_suffix('.md')
            candidates = [vault / rel, src.parent / rel]
            found = list(dict.fromkeys(p.resolve() for p in candidates if p.is_file()))
            if not found and len(rel.parts) == 1:
                found = list(vault.rglob(rel.name))
            if len(found) > 1:
                errors.append(f'{src.relative_to(root)}:{number}: ambiguous wiki target {decoded}')
                return
            target = found[0] if found else candidates[0]
        else:
            target = (src.parent / filepart).resolve()
        label = f'{src.relative_to(root)}:{number}: {decoded}'
        if not target.is_file():
            errors.append(f'{label} — missing file')
            return
        if target.suffix.lower() != '.md':
            return
        body = content(target)
        substantive = re.sub(r'^\s*#{1,6}.*$', '', body, flags=re.M).strip()
        if not substantive:
            errors.append(f'{label} — empty or heading-only Markdown')
        if fragment:
            heads, blocks = anchors(body)
            valid = fragment[1:] in blocks if fragment.startswith('^') else fragment in heads
            if not valid:
                errors.append(f'{label} — missing anchor')

    for src in sorted(root.rglob('*.md')):
        body = content(src)
        if cache[src][1]:
            errors.append(f'{src.relative_to(root)}: unclosed code fence')
        for number, line in enumerate(body.splitlines(), 1):
            # Inline code does not create links. Mermaid/code blocks were removed above.
            line = re.sub(r'`+[^`]*`+', '', line)
            for match in re.finditer(r'\[\[([^\]]+)\]\]', line):
                verify(src, number, match.group(1), True)
            inline = re.sub(r'\[\[[^\]]+\]\]', '', line)
            for match in re.finditer(r'!?\[[^\]]*\]\((<[^>]+>|[^\s()]+)(?:\s+[\"\'][^\n]*?[\"\'])?\)', inline):
                verify(src, number, match.group(1).strip('<>'))
            if re.search(r'\[[^\]]+\]\s*\[[^\]]*\]|^\s*\[[^\]]+\]:', inline):
                warnings.append(f'{src.relative_to(root)}:{number}: reference-style link needs manual check')
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--vault-root', type=Path)
    args = parser.parse_args()
    if not args.root.is_dir() or (args.vault_root and not args.vault_root.is_dir()):
        parser.error('root and vault-root must be existing directories')
    errors, warnings = check(args.root, args.vault_root)
    for item in errors:
        print('ERROR:', item)
    for item in warnings:
        print('WARNING:', item)
    print(f'{len(errors)} error(s), {len(warnings)} warning(s). Structure only; facts and rendering not checked.')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
