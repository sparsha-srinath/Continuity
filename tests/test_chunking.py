from dataclasses import replace

import pytest

from knowledge_assistant.ingestion import build_seed_documents
from knowledge_assistant.retrieval import split_chunks
from knowledge_assistant.workspace import LiveWorkspace
from knowledge_assistant.chunking import sql_regions


def source(text, filename, kind="code"):
    return replace(build_seed_documents()[0], text=text, source_file=filename, source_type=kind)


def test_python_decorators_classes_nested_functions_and_unicode():
    text = ('"""東京 module."""\r\nimport os\r\n\r\n'
            '@decorate\r\nclass Worker:\r\n    value = 1\r\n'
            '    @staticmethod\r\n    async def run():\r\n'
            '        def inner():\r\n            return "東京"\r\n'
            '        return inner()\r\n\r\n'
            'def stop():\r\n    pass\r\n')
    parts = split_chunks([source(text, "worker.py")])
    assert ''.join(p.text for p in parts) == text
    symbols = {p.symbol_name for p in parts}
    assert symbols == {'worker', 'worker.Worker', 'worker.Worker.run', 'worker.Worker.run.inner', 'worker.stop'}
    method = next(p for p in parts if p.symbol_name == 'worker.Worker.run')
    assert method.text.startswith('    @staticmethod')
    assert (method.line_start, method.line_end) == (7, 8)
    assert all(p.chunk_strategy == 'python-ast' for p in parts)
    assert next(p for p in parts if p.symbol_name == 'worker.Worker').symbol_kind == 'class'


def test_prose_keeps_headings_separate_and_packs_whole_paragraphs():
    text = '# Install\n\nFirst step.\n\nSecond step.\n\n# Run\n\nStart here.\n'
    parts = split_chunks([source(text, 'guide.md', 'doc')])
    assert [p.heading for p in parts] == ['Install', 'Run']
    assert ''.join(p.text for p in parts) == text
    limited = split_chunks([source(text, 'guide.md', 'doc')], max_chars=30)
    assert any('First step.' in p.text for p in limited)
    assert any('Second step.' in p.text for p in limited)


def test_prose_fences_and_underlined_headings():
    text = 'Install\n=======\n\n```python\n# not a heading\n\nx = 1\n```\n\nRun\n---\nStart.\n'
    parts = split_chunks([source(text, 'guide.md', 'doc')])
    assert [p.heading for p in parts] == ['Install', 'Run']
    assert ''.join(p.text for p in parts) == text


def test_sql_quoted_semicolons_comments_dollar_bodies_and_batches():
    statements = ["-- ignored ;\nSELECT 'it''s ;', \"a;b\", [x;y], `a;b`;\n",
                  '/* nested /* ; */ ; */ SELECT 2;\n',
                  'DO $body$ BEGIN PERFORM 1; PERFORM 2; END $body$;\n',
                  'SELECT 3\nGO\n', 'SELECT 4']
    text = ''.join(statements)
    assert [text[r.start:r.end] for r in sql_regions(text)] == statements
    parts = split_chunks([source(text, 'schema.sql')])
    assert [p.text for p in parts] == [''.join(statements[:-1]), statements[-1]]
    assert all(p.chunk_strategy == 'sql-statements' for p in parts)


def test_sql_packs_adjacent_whole_statements_as_limit_increases():
    statements = [f"SELECT {n}, '" + 'x' * 45 + "';\n" for n in range(10)]
    text = ''.join(statements)
    document = source(text, 'queries.sql')
    small = split_chunks([document], max_chars=200)
    large = split_chunks([document], max_chars=500)
    assert len(small) > len(large)
    boundaries = {sum(len(s) for s in statements[:i]) for i in range(1, len(statements) + 1)}
    for parts, limit in ((small, 200), (large, 500)):
        assert ''.join(p.text for p in parts) == text
        offset = 0
        for part in parts:
            offset += len(part.text)
            assert len(part.text) <= limit
            assert offset in boundaries


@pytest.mark.parametrize('filename,text', [
    ('broken.py', 'def incomplete(:\n'), ('broken.sql', "SELECT 'unclosed;"),
    ('component.ts', 'export function foo() { return 1; }'),
])
def test_invalid_or_unsupported_code_falls_back(filename, text):
    parts = split_chunks([source(text, filename)], max_chars=10)
    assert ''.join(p.text for p in parts) == text
    assert all(p.chunk_strategy == 'text-fallback' and len(p.text) <= 10 for p in parts)


@pytest.mark.parametrize('filename,text,kind', [
    ('large.py', 'def long_function():\n    return "' + 'x' * 1000 + '"\n', 'code'),
    ('large.sql', "SELECT '" + 'x' * 1000 + "';", 'code'),
    ('large.md', '# Heading\n\n' + '東京 ' * 1000, 'doc'),
])
def test_oversized_units_remain_exact_bounded_and_deterministic(filename, text, kind):
    document = source(text, filename, kind)
    parts = split_chunks([document], max_chars=200)
    assert ''.join(p.text for p in parts) == text
    assert all(0 < len(p.text) <= 200 for p in parts)
    assert len({p.chunk_id for p in parts}) == len(parts)
    assert parts == split_chunks([document], max_chars=200)
    if filename.endswith('.py'):
        assert all(p.symbol_name == 'large.long_function' for p in parts)


def test_symbol_metadata_survives_indexing_and_preview():
    document = source('import os\n\ndef run():\n    return 1\n', 'example.py')
    workspace = LiveWorkspace(documents=[document])
    assert workspace.document_chunks(document.chunk_id) == workspace.chunks
    records = workspace.store.collection.get()
    assert {m['symbol_name'] for m in records['metadatas']} == {'example', 'example.run'}
    assert all(m['chunk_strategy'] == 'python-ast' for m in records['metadatas'])


def test_invalid_chunk_limit_rejected():
    with pytest.raises(ValueError):
        split_chunks([], max_chars=0)
