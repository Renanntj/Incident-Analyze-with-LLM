import asyncio
import json

import httpx
import pytest

from app.repository_tool import Findings, GeminiProvider, LLMError, PostOutput


def run_provider(monkeypatch, handler, schema=Findings):
    monkeypatch.setenv('GEMINI_API_KEY', 'private-test-key')
    monkeypatch.setenv('GEMINI_MODEL', 'test-model')
    provider = GeminiProvider(httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    return asyncio.run(provider.complete('private-prompt', schema))


@pytest.mark.parametrize('status,reason,kind', [(400, 'API_KEY_INVALID', 'authentication'), (403, 'PERMISSION_DENIED', 'permission'), (404, 'MODEL_NOT_FOUND', 'model'), (429, 'QUOTA_EXCEEDED', 'quota')])
def test_permanent_http_errors_are_specific_and_not_retried(monkeypatch, status, reason, kind):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(status, json={'error': {'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': reason}]}})
    with pytest.raises(LLMError) as error:
        run_provider(monkeypatch, handler)
    assert error.value.kind == kind
    assert len(calls) == 1
    assert 'private-test-key' not in str(error.value)


@pytest.mark.parametrize('body,kind', [({}, 'missing_candidates'), ({'candidates': [{}]}, 'missing_content'), ({'candidates': [{'content': {}}]}, 'missing_parts'), ({'candidates': [{'content': {'parts': [{'text': 'not json'}]}}]}, 'invalid_json'), ({'candidates': [{'content': {'parts': [{'text': '{}'}]}}]}, 'schema')])
def test_response_shape_errors_are_specific(monkeypatch, body, kind):
    with pytest.raises(LLMError) as error:
        run_provider(monkeypatch, lambda request: httpx.Response(200, json=body), PostOutput)
    assert error.value.kind == kind


def test_structured_request_and_valid_schemas(monkeypatch):
    def handler(request):
        body = json.loads(request.content)
        assert body['generationConfig']['responseMimeType'] == 'application/json'
        assert body['generationConfig']['responseSchema']['required'] == ['purpose', 'claims', 'uncertainties']
        return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': '{"purpose":"teste","claims":[],"uncertainties":[]}'}]}}]})
    assert run_provider(monkeypatch, handler).purpose == 'teste'


def test_post_output_schema_is_sent(monkeypatch):
    def handler(request):
        schema = json.loads(request.content)['generationConfig']['responseSchema']
        assert schema['required'] == ['text']
        return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': '{"text":"Olá"}'}]}}]})
    assert run_provider(monkeypatch, handler, PostOutput).text == 'Olá'


def test_transient_error_waits_and_retries(monkeypatch):
    calls, delays = [], []
    async def fake_sleep(seconds): delays.append(seconds)
    monkeypatch.setattr(asyncio, 'sleep', fake_sleep)
    def handler(request):
        calls.append(request)
        if len(calls) == 1: return httpx.Response(503, headers={'Retry-After': '2'})
        return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': '{"text":"ok"}'}]}}]})
    assert run_provider(monkeypatch, handler, PostOutput).text == 'ok'
    assert delays == [2]


def test_long_retry_after_does_not_retry_early(monkeypatch):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(429, headers={'Retry-After': '120'}, json={'error': {'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'RATE_LIMIT_EXCEEDED'}]}})
    with pytest.raises(LLMError) as error:
        run_provider(monkeypatch, handler)
    assert error.value.kind == 'rate_limit'
    assert len(calls) == 1


def test_timeout_retries_with_progressive_wait(monkeypatch):
    delays, calls = [], []
    async def fake_sleep(seconds): delays.append(seconds)
    monkeypatch.setattr(asyncio, 'sleep', fake_sleep)
    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout('timeout')
    with pytest.raises(LLMError) as error:
        run_provider(monkeypatch, handler)
    assert error.value.kind == 'timeout'
    assert len(calls) == 3
    assert delays == [0.5, 1.0]


def test_logs_do_not_include_key_or_prompt(monkeypatch, caplog):
    with pytest.raises(LLMError):
        run_provider(monkeypatch, lambda request: httpx.Response(400, json={'error': {'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID'}]}}))
    assert 'category=authentication status=400' in caplog.text
    assert 'private-test-key' not in caplog.text
    assert 'private-prompt' not in caplog.text
