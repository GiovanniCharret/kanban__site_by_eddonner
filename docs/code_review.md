# Code Review — Kanban Board MVP

**Data:** 2026-03-29
**Revisão de:** Todo o repositório (`backend/`, `frontend/`, `Dockerfile`, configurações)
**Total de issues:** 34 (2 críticos · 8 altos · 10 médios · 14 baixos)

---

## Resumo Executivo

O projeto está funcional e bem estruturado para um MVP. A gestão de segredos está correta: `.env` está no `.gitignore` e a API key nunca chegou ao repositório remoto.

As preocupações reais são de **segurança de sessão e resiliência**: o cookie de sessão pode ser falsificado trivialmente (qualquer um que defina `kanban_session=user` tem acesso total), não há rate limiting nos endpoints de login e chat, e o cliente DNS-over-HTTPS desabilita verificação SSL. Esses pontos devem ser endereçados antes de qualquer exposição pública.

Para uso estritamente local — que é o escopo declarado deste MVP — a maioria dos issues de segurança (A1–A5) é aceitável como débito técnico consciente. Os críticos C2 e C3 são de baixo custo para corrigir e valem independentemente do ambiente.

---

## Críticos

### C1 — ~~API Key exposta no controle de versão~~ ✅ Não aplicável
**Arquivo:** `.env`
**Status:** Falso positivo. `.env` está na linha 1 do `.gitignore` e nunca foi commitado. A chave nunca chegou ao GitHub.

---

### C2 — Cookie de sessão sem flag `Secure`
**Arquivo:** `backend/app/main.py`, linha ~114
**Problema:** O cookie `kanban_session` é definido com `httponly=True` mas sem `secure=True`, permitindo transmissão em HTTP claro (suscetível a MITM).
**Ação:**
```python
response.set_cookie(
    key=SESSION_COOKIE,
    value=VALID_USERNAME,
    httponly=True,
    secure=True,        # adicionar
    samesite="strict",  # considerar "strict" em vez de "lax"
    path="/",
)
```

---

### C3 — Verificação SSL desabilitada no cliente DNS-over-HTTPS
**Arquivo:** `backend/app/ai.py`, linha ~109
**Problema:** O resolver DOH usa `verify=False`, desabilitando verificação de certificado SSL — abre brechas para MITM na resolução DNS.
**Ação:** Remover `verify=False`. O padrão do httpx (`verify=True`) é correto para produção.

---

## Altos

### A1 — Autenticação bypassável via manipulação de cookie
**Arquivo:** `backend/app/main.py`, linhas ~43–44
**Problema:** A verificação de autenticação compara o valor do cookie com a string `"user"`. Qualquer pessoa pode definir `kanban_session=user` manualmente e ter acesso total.
**Ação:** Implementar tokens de sessão criptograficamente seguros (UUIDs aleatórios) armazenados server-side com expiração.

---

### A2 — Credenciais hardcoded no código-fonte
**Arquivo:** `backend/app/main.py`, linhas ~25–26
**Problema:** `VALID_USERNAME = "user"` e `VALID_PASSWORD = "password"` estão no código. Não podem ser alteradas sem modificar o código.
**Ação:** Carregar de variáveis de ambiente com fallback para valores padrão apenas em dev.

---

### A3 — Sem limites de tamanho na entrada do chat / board
**Arquivo:** `backend/app/ai_board.py` e `main.py`
**Problema:** Mensagens e histórico de chat ilimitados podem causar esgotamento de memória ou custos excessivos de API.
**Ação:**
```python
class AIChatRequest(BaseModel):
    message: str = Field(..., max_length=2000)
    history: list[ChatMessageModel] = Field(default_factory=list, max_length=50)
```

---

### A4 — Sem rate limiting
**Arquivo:** `backend/app/main.py`
**Problema:** Endpoints de login e chat não têm rate limiting — permite força bruta nas credenciais e abuso do endpoint de IA gerando custos.
**Ação:** Usar `slowapi` (wrapper de `limits` para FastAPI) para limitar tentativas de login por IP e requisições de chat por usuário.

---

### A5 — Sem configuração de CORS
**Arquivo:** `backend/app/main.py`
**Problema:** FastAPI sem `CORSMiddleware` definido explicitamente. Em alguns contextos pode bloquear o frontend legítimo ou, pior, aceitar qualquer origem.
**Ação:**
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)
```

---

### A6 — Parsing de resposta AI não diferencia tipos de erro
**Arquivo:** `backend/app/ai_board.py`, linhas ~113–116
**Problema:** `except Exception` captura tudo, mascarando erros inesperados como erros de validação normais.
**Ação:**
```python
from pydantic import ValidationError
try:
    return AIBoardResponseModel.model_validate(data)
except ValidationError as exc:
    raise AIBoardError(f"Resposta AI inválida: {exc.error_count()} erros") from exc
except Exception as exc:
    raise AIBoardError(f"Erro inesperado: {type(exc).__name__}") from exc
```

---

### A7 — Sem controle de acesso ao board por usuário
**Arquivo:** `backend/app/main.py` e `db.py`
**Problema:** Existe autenticação, mas não há verificação de que o usuário autenticado é o dono do board. Se a sessão for forjada (ver A1), qualquer board fica acessível.
**Ação:** Garantir que todas as queries ao board filtrem por `username` obtido exclusivamente da sessão server-side, nunca de input do cliente.

---

### A8 — Operações AI aplicadas parcialmente sem rollback
**Arquivo:** `backend/app/ai_board.py`, linhas ~119–136
**Problema:** Se a 2ª operação de uma lista falha, a 1ª já foi aplicada — o board fica em estado inconsistente.
**Ação:** Validar todas as operações antes de aplicar qualquer uma; só persistir se todas forem bem-sucedidas.

---

## Médios

### M1 — Respostas de erro sem formato padronizado
**Arquivos:** `backend/app/main.py`, `ai.py`
**Problema:** Alguns erros retornam `{"detail": ...}`, outros expõem `str(exc)` diretamente ao cliente.
**Ação:** Criar um `ErrorResponse` model e usá-lo consistentemente em todos os endpoints.

---

### M2 — Board sem validação de integridade no PUT
**Arquivo:** `backend/app/main.py`, linhas ~137–140
**Problema:** `PUT /api/board` aceita qualquer `BoardModel` sem verificar IDs duplicados, colunas faltando, etc.
**Ação:** Adicionar função `validate_board_integrity(board)` que rejeite boards malformados antes de persistir.

---

### M3 — Race condition em atualizações do board no frontend
**Arquivo:** `frontend/src/components/AppShell.tsx`, linhas ~216–250
**Problema:** Mudanças locais feitas enquanto um save está em progresso podem ser sobrescritas pela resposta de volta.
**Ação:** Enfileirar mudanças ou bloquear a UI durante saves; implementar updates otimistas com rollback.

---

### M4 — `getNextCardId` com O(n) em cards
**Arquivo:** `frontend/src/lib/kanban.ts`, linhas ~211–219
**Problema:** Varre todos os cards a cada novo card adicionado.
**Ação:** Usar `crypto.randomUUID()` ou manter um contador incremental ao invés de escanear.

---

### M5 — Board deletado do DB não tem fallback
**Arquivo:** `backend/app/db.py`, linhas ~99–102
**Problema:** Se o board de um usuário sumir do banco, a API lança `RuntimeError` genérico em vez de recriar um board padrão.
**Ação:** Recriar board padrão automaticamente se não encontrado, ou retornar 404 com mensagem clara.

---

### M6 — IDs de coluna/card da AI não são validados antes de aplicar
**Arquivo:** `backend/app/ai_board.py`, linhas ~123–135
**Problema:** A AI pode referenciar IDs inexistentes; o erro é re-lançado expondo detalhes internos ao cliente.
**Ação:** Validar existência dos IDs antes de qualquer mutação; logar detalhes internamente e retornar mensagem genérica ao cliente.

---

### M7 — Variáveis de ambiente não validadas na inicialização
**Arquivo:** `backend/app/main.py`
**Problema:** `OPENROUTER_API_KEY` ausente só é detectada quando o primeiro request de chat é feito.
**Ação:**
```python
@asynccontextmanager
async def lifespan(_: FastAPI):
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise RuntimeError("OPENROUTER_API_KEY não definida")
    init_db()
    yield
```

---

### M8 — Sem logging no backend
**Arquivos:** Todos os arquivos de backend
**Problema:** Não há sistema de logging; erros e operações importantes são silenciosos em produção.
**Ação:** Usar `logging.getLogger(__name__)` nos módulos críticos (`main.py`, `ai.py`, `db.py`).

---

### M9 — Cobertura de teste: autenticação não é verificada nos testes de AI
**Arquivo:** `backend/tests/test_ai_api.py`
**Problema:** Os testes de chat não verificam que o endpoint retorna 401 sem sessão.
**Ação:**
```python
def test_ai_chat_requer_autenticacao(client: TestClient) -> None:
    response = client.post("/api/ai/chat", json={"message": "teste", "history": []})
    assert response.status_code == 401
```

---

### M10 — Operações do board com tipos verificados por string literal
**Arquivo:** `backend/app/ai_board.py`
**Problema:** O dispatch de operações usa `if operation.type == "create_card"` em cadeia — frágil e propenso a erros silenciosos.
**Ação:** Usar dict de handlers: `handlers = {"create_card": _apply_create, ...}` com erro explícito para tipos desconhecidos.

---

## Baixos

### B1 — Endpoints de API como magic strings no frontend
**Arquivo:** `frontend/src/components/AppShell.tsx`
**Ação:** Centralizar em um objeto `const API = { BOARD: '/api/board', ... } as const`.

---

### B2 — Board padrão duplicado em backend e frontend
**Arquivos:** `backend/app/board.py` e `frontend/src/lib/kanban.ts`
**Ação:** Definir estrutura padrão em um único lugar (ex: endpoint `GET /api/board/default` ou constante compartilhada).

---

### B3 — Título de coluna pode ser string vazia
**Arquivo:** `frontend/src/components/KanbanBoard.tsx`, linha ~228
**Ação:** Validar `title.trim().length > 0 && title.length <= 100` antes de chamar `onBoardChange`.

---

### B4 — Sem paginação no histórico de chat
**Arquivo:** `frontend/src/components/AppShell.tsx`, linhas ~311–321
**Ação:** Limitar renderização a últimas N mensagens ou usar virtualização.

---

### B5 — Timeout ausente na conexão SQLite
**Arquivo:** `backend/app/db.py`
**Ação:** `sqlite3.connect(db_path, timeout=10.0)` para evitar travamentos indefinidos em lock contention.

---

### B6 — Sem headers de segurança no Next.js
**Arquivo:** `frontend/` (ausência de `next.config.js`)
**Ação:** Configurar `X-Content-Type-Options`, `X-Frame-Options` e `Content-Security-Policy` via `next.config.js`.

---

### B7 — Sem atributos de acessibilidade (ARIA)
**Arquivos:** `KanbanBoard.tsx`, `AppShell.tsx`
**Ação:** Adicionar `aria-label` em botões de drag handle, botões de ação de card e inputs sem label visível.

---

### B8 — Sem teste de integridade do board após operações AI
**Arquivo:** `backend/tests/test_ai_board.py`
**Ação:** Verificar ausência de IDs duplicados e presença de todas as colunas após `apply_board_operations`.

---

### B9 — Sem testes para edge cases de `moveCard`
**Arquivo:** `frontend/src/lib/kanban.test.ts`
**Ação:** Testar card ID inválido, coluna inválida e mover para a mesma posição.

---

### B10 — Erros de async inconsistentes no frontend
**Arquivo:** `frontend/src/components/AppShell.tsx`
**Ação:** Padronizar tratamento de erro em todos os `catch` blocks (logar e/ou exibir feedback ao usuário).

---

### B11 — Imports não utilizados
**Arquivo:** `frontend/src/components/KanbanBoard.tsx`, linha 3
**Ação:** Remover imports não utilizados do React.

---

### B12 — Sem documentação em funções complexas
**Arquivo:** `frontend/src/lib/kanban.ts`
**Ação:** Adicionar JSDoc em `moveCard` e `applyOperation` descrevendo parâmetros e comportamento em edge cases.

---

### B13 — Sem tratamento de erro visual em operações de board
**Arquivo:** `frontend/src/components/AppShell.tsx`
**Ação:** Exibir feedback visível ao usuário quando save de board falha (atualmente silencioso).

---

### B14 — Sem paginação: chat history enviado inteiro para AI
**Arquivo:** `backend/app/ai_board.py`
**Problema:** Todo o histórico de chat é enviado ao OpenRouter sem limite, aumentando custo e latência com o tempo.
**Ação:** Limitar histórico enviado às últimas N mensagens (ex: 10).

---

## Priorização Recomendada

| Prioridade | Issues | Justificativa |
|-----------|--------|---------------|
| **Imediato** | C2, C3, A1, A2 | Segurança fundamental — corrigir antes de qualquer uso externo |
| **Curto prazo** | A3, A4, A5, A6, A7, A8, M7 | Robustez e proteção contra abuso |
| **Médio prazo** | M1–M10 | Qualidade e estabilidade |
| **Backlog** | B1–B14 | Melhoria incremental |

---

*Revisão gerada por Claude Code (claude-sonnet-4-6) em 2026-03-29.*
