import pytest
import base64
import asyncio
import httpx

from app.repository_tool import parse_repository, select_files, redact, GitHubClient, GitHubError, RepositoryService, Settings, Findings, PostOutput, GeminiProvider, LLMError
from app.main import app, service


def test_url_validation():
    assert parse_repository('https://github.com/acme/demo.git/') == ('acme', 'demo')
    for url in ('https://evil.com/a/b', 'https://u:p@github.com/a/b', 'http://github.com/a/b', 'https://github.com/a/b/tree/main'):
        with pytest.raises(ValueError):
            parse_repository(url)


def test_selection_and_redaction():
    entries = [{'path': 'README.md', 'type': 'blob', 'size': 10, 'sha': 'a'}, {'path': '.env', 'type': 'blob', 'size': 10, 'sha': 'b'}, {'path': 'src/main.py', 'type': 'blob', 'size': 10, 'sha': 'c'}]
    chosen, ignored = select_files(entries, 1, 100)
    assert [x['path'] for x in chosen] == ['README.md']
    assert {x['path'] for x in ignored} == {'.env', 'src/main.py'}
    assert 'SECRET' not in redact('API_KEY=SECRET')


class FakeLLM:
    def __init__(self): self.prompts = []
    async def complete(self, prompt, schema):
        self.prompts.append(prompt)
        if schema is Findings:
            return Findings(purpose='API de exemplo', claims=[{'text': 'Possui rota HTTP', 'kind': 'observed', 'path': 'main.py', 'line': 1}])
        return PostOutput(text='Ao explorar este projeto, encontrei uma rota HTTP. Conheça https://github.com/acme/demo')


def fixture_github(request):
    path = request.url.path
    if path == '/repos/acme/demo': return httpx.Response(200, json={'default_branch': 'main', 'description': 'demo', 'private': False})
    if path == '/repos/acme/demo/commits/main': return httpx.Response(200, json={'sha': 'a' * 40})
    if path == '/repos/acme/demo/git/trees/' + 'a' * 40:
        return httpx.Response(200, json={'truncated': True, 'tree': [{'path': 'main.py', 'type': 'blob', 'size': 40, 'sha': 'blob'}]})
    if path == '/repos/acme/demo/git/blobs/blob':
        return httpx.Response(200, json={'encoding': 'base64', 'content': base64.b64encode(b'API_KEY=SECRET\n@app.get("/")').decode()})
    if path == '/repos/acme/demo/commits': return httpx.Response(200, json=[{'sha': 'a' * 40, 'commit': {'message': 'Initial'}}])
    return httpx.Response(404)


def test_complete_flow():
    async def run():
        transport = httpx.MockTransport(fixture_github)
        github = GitHubClient(httpx.AsyncClient(transport=transport, base_url='https://api.github.com'))
        llm = FakeLLM()
        svc = RepositoryService(github, llm, Settings())
        async def fake_service(): return svc
        app.dependency_overrides[service] = fake_service
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                analysis = (await client.post('/api/v1/repositories/analyze', json={'url': 'https://github.com/acme/demo'})).json()
                assert analysis['commit'] == 'a' * 40
                assert analysis['coverage']['tree_truncated'] is True
                assert analysis['claims'][0]['commit'] == 'a' * 40
                assert 'SECRET' not in '\n'.join(llm.prompts)
                post = (await client.post('/api/v1/posts/linkedin', json={'url': 'https://github.com/acme/demo'})).json()
                assert post['characters'] == len(post['post'])
                assert 'não diga que desenvolvi' in llm.prompts[-1]
                assert (await client.get('/health')).json() == {'status': 'ok'}
        finally:
            app.dependency_overrides.clear()
    asyncio.run(run())


def test_github_errors_and_missing_reference():
    async def run(status):
        client = GitHubClient(httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(status)), base_url='https://api.github.com'))
        with pytest.raises(GitHubError) as error:
            await client.get('/repos/a/b')
        return error.value.status
    assert asyncio.run(run(404)) == 404
    assert asyncio.run(run(403)) == 403
    assert asyncio.run(run(409)) == 422


def test_empty_repo_and_invalid_llm_json():
    async def run():
        def handler(request):
            if request.url.path.endswith('/repos/acme/demo'):
                return httpx.Response(200, json={'default_branch': 'main', 'private': False})
            if '/commits/main' in request.url.path:
                return httpx.Response(200, json={'sha': 'a' * 40})
            if '/git/trees/' in request.url.path:
                return httpx.Response(200, json={'tree': [], 'truncated': False})
            return httpx.Response(200, json=[])
        github = GitHubClient(httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url='https://api.github.com'))
        llm = FakeLLM()
        result = await RepositoryService(github, llm, Settings()).analyze('https://github.com/acme/demo')
        assert result['claims'] == [] and 'README ausente ou não selecionado' in result['warnings']
        assert llm.prompts == []
        provider = GeminiProvider(httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': '{}'}]}}]}))))
        from unittest.mock import patch
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'fake', 'GEMINI_MODEL': 'gemini-2.5-flash'}):
            with pytest.raises(LLMError):
                await provider.complete('x', PostOutput)
    asyncio.run(run())
