from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

from app.repository_tool import GitHubError, LLMError, RepositoryService, parse_repository

app = FastAPI(title='Repository Story', version='0.1.0')


class AnalyzeRequest(BaseModel):
    url: str = Field(max_length=300)
    reference: str | None = Field(default=None, max_length=200)
    allow_private_llm: bool = False


class PostRequest(AnalyzeRequest):
    tone: Literal['profissional', 'conversacional'] = 'profissional'
    length: Literal['curto', 'medio'] = 'medio'
    hashtags: bool = False
    author_context: str | None = Field(default=None, max_length=2000)
    confirmed_author: bool = False
    max_characters: int = Field(default=2200, ge=300, le=3000)


async def service():
    return RepositoryService()


@app.get('/health')
async def health():
    return {'status': 'ok'}


@app.post('/api/v1/repositories/analyze')
async def analyze(request: AnalyzeRequest, svc: RepositoryService = Depends(service)):
    try:
        parse_repository(request.url)
        return await svc.analyze(request.url, request.reference, request.allow_private_llm)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except (GitHubError, LLMError) as exc:
        raise HTTPException(getattr(exc, 'status', 502), str(exc)) from exc


@app.post('/api/v1/posts/linkedin')
async def linkedin(request: PostRequest, svc: RepositoryService = Depends(service)):
    try:
        parse_repository(request.url)
        analysis = await svc.analyze(request.url, request.reference, request.allow_private_llm)
        return await svc.post(analysis, request.tone, request.length, request.hashtags, request.author_context, request.confirmed_author, request.max_characters)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except (GitHubError, LLMError) as exc:
        raise HTTPException(getattr(exc, 'status', 502), str(exc)) from exc
