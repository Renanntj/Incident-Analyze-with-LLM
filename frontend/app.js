const form = document.querySelector('#repository-form');
const notice = document.querySelector('#notice');
const resultContent = document.querySelector('#result-content');
const analyzeButton = document.querySelector('#analyze-button');
const postButton = document.querySelector('#post-button');
const copyButton = document.querySelector('#copy-button');
let latestPost = '';

function setNotice(message, type = '') {
  notice.textContent = message;
  notice.className = `notice ${type}`.trim();
}
function text(tag, value, className = '') {
  const node = document.createElement(tag);
  node.textContent = value ?? '';
  if (className) node.className = className;
  return node;
}
function payload() {
  const data = new FormData(form);
  return {
    url: data.get('url').trim(),
    reference: data.get('reference').trim() || null,
    tone: data.get('tone'),
    length: data.get('length'),
    max_characters: Number(data.get('max_characters')),
    author_context: data.get('author_context').trim() || null,
    confirmed_author: document.querySelector('#confirmed-author').checked,
    hashtags: document.querySelector('#hashtags').checked,
    allow_private_llm: document.querySelector('#private-consent').checked,
  };
}
async function request(endpoint, body) {
  const response = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  let data;
  try { data = await response.json(); } catch { throw new Error('O servidor retornou uma resposta inesperada.'); }
  if (!response.ok) {
    const detail = data.detail;
    throw new Error(typeof detail === 'string' ? detail : 'Confira os dados informados e tente novamente.');
  }
  return data;
}
function showTab(tab) {
  const isPost = tab === 'post';
  document.querySelector('#analysis-view').hidden = isPost;
  document.querySelector('#post-view').hidden = !isPost;
  document.querySelector('#tab-analysis').setAttribute('aria-selected', String(!isPost));
  document.querySelector('#tab-post').setAttribute('aria-selected', String(isPost));
}
function renderAnalysis(data) {
  resultContent.hidden = false;
  const link = document.querySelector('#result-repo');
  link.textContent = data.repository;
  link.href = data.repository;
  document.querySelector('#result-purpose').textContent = data.purpose || data.description || 'Finalidade não identificada com segurança.';
  document.querySelector('#result-ref').textContent = `Referência: ${data.reference}`;
  document.querySelector('#result-commit').textContent = `Commit: ${data.commit.slice(0, 10)}`;
  document.querySelector('#claim-count').textContent = `${data.claims.length} afirmação(ões)`;
  const claims = document.querySelector('#claims');
  claims.replaceChildren();
  const labels = { observed: 'Observado no código', documented: 'Documentado', intended: 'Intenção', inferred: 'Inferência' };
  if (!data.claims.length) claims.append(text('p', 'Nenhuma afirmação com referência válida foi encontrada nesta seleção.', 'empty'));
  for (const claim of data.claims) {
    const card = text('article', '', 'claim');
    const top = text('div', '', 'claim-top');
    top.append(text('span', labels[claim.kind] || claim.kind, `tag ${claim.kind}`), text('span', claim.category || '', 'claim-category'));
    card.append(top, text('p', claim.text), text('div', `${claim.path || 'Fonte não informada'}${claim.line ? ` · linha ${claim.line}` : ''} · ${claim.commit?.slice(0, 10) || ''}`, 'claim-source'));
    claims.append(card);
  }
  const coverage = document.querySelector('#coverage-content');
  coverage.replaceChildren();
  const examined = data.coverage?.examined || [];
  const ignored = data.coverage?.ignored || [];
  coverage.append(text('p', `${examined.length} arquivo(s) examinado(s), ${ignored.length} ignorado(s).${data.coverage?.tree_truncated ? ' A árvore do GitHub foi truncada.' : ''}`));
  if (data.coverage?.context_truncated?.length) coverage.append(text('p', `Contexto truncado: ${data.coverage.context_truncated.join(', ')}`));
  const messages = [...(data.warnings || []), ...(data.uncertainties || []), ...ignored.slice(0, 20).map(item => `${item.path}: ${item.reason}`)];
  if (messages.length) { const list = document.createElement('ul'); for (const message of messages) list.append(text('li', message)); coverage.append(list); }
  showTab('analysis');
  setNotice('Análise concluída. Revise as fontes e os limites da coleta.');
}
function renderPost(data) {
  renderAnalysis(data.analysis);
  latestPost = data.post;
  document.querySelector('#post-text').textContent = latestPost;
  document.querySelector('#post-count').textContent = `${data.characters} caracteres`;
  showTab('post');
  setNotice('Texto gerado. Revise antes de copiar ou publicar.');
}
async function run(action) {
  if (!form.reportValidity()) return;
  const body = payload();
  analyzeButton.disabled = postButton.disabled = true;
  setNotice(action === 'post' ? 'Analisando o repositório e preparando o texto…' : 'Analisando o repositório…', 'busy');
  try {
    if (action === 'post') renderPost(await request('/api/v1/posts/linkedin', body));
    else renderAnalysis(await request('/api/v1/repositories/analyze', body));
  } catch (error) { setNotice(error.message || 'Não foi possível concluir a solicitação.', 'error'); }
  finally { analyzeButton.disabled = postButton.disabled = false; }
}
form.addEventListener('submit', event => { event.preventDefault(); run('analyze'); });
postButton.addEventListener('click', () => run('post'));
document.querySelector('#tab-analysis').addEventListener('click', () => showTab('analysis'));
document.querySelector('#tab-post').addEventListener('click', () => showTab('post'));
copyButton.addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(latestPost); copyButton.textContent = 'Texto copiado'; setTimeout(() => { copyButton.textContent = 'Copiar texto'; }, 2200); }
  catch { setNotice('Não foi possível copiar automaticamente. Selecione o texto e copie manualmente.', 'error'); }
});
