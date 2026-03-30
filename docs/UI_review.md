# UI Review — Melhorias de Layout e Interação

Data: 2026-03-29

## Problemas identificados e corrigidos

### 1. Card invisível ao arrastar

**Problema:** A coluna tinha `overflow: hidden`, então o card sumia ao ser arrastado para fora dos limites da coluna.

**Solução:** Adicionado `DragOverlay` do `@dnd-kit/core`. O card original permanece no lugar como um "fantasma" (opacidade 35%, borda tracejada) e uma cópia flutuante levemente rotacionada (`rotate(1.5deg)`) acompanha o cursor. O `overflow: hidden` foi removido da coluna.

Arquivos: `KanbanBoard.tsx`, `globals.css`

---

### 2. Barra de rolagem horizontal no board

**Problema:** O grid usava `grid-template-columns: repeat(5, minmax(220px, 240px))` com `min-width: max-content`, forçando scroll horizontal em praticamente qualquer resolução.

**Solução:** Trocado para `repeat(5, minmax(0, 1fr))` — as 5 colunas se distribuem no espaço disponível. Removido `min-width: max-content` e `overflow-x: auto` do `.workspace-board`. O `max-width` do workspace foi aumentado de 1350px para 1600px para aproveitar melhor telas maiores.

Arquivos: `globals.css`

---

### 3. Botões de texto substituídos por ícones

**Problema:** Os botões "Drag" e "Delete" usavam texto, ocupando espaço e deixando o card visualmente carregado.

**Solução:**
- **Drag** → ícone de grip (6 pontos) SVG inline. O botão é transparente e só ganha cor ao hover.
- **Delete** → ícone de lixeira SVG inline. Fica **invisível por padrão** e aparece apenas ao passar o mouse no card (`:hover`), mantendo a interface limpa.
- Ambos os botões foram movidos para a mesma linha do título (`card-head`), eliminando o botão "Delete" solto no rodapé do card.

Arquivos: `KanbanBoard.tsx`, `globals.css`

---

### 4. Ajustes gerais de espaçamento e responsividade

- Padding interno das colunas e cards levemente reduzido para caber melhor no grid de 5 colunas.
- Título do card agora tem `overflow: hidden; text-overflow: ellipsis; white-space: nowrap` para não quebrar o layout em títulos longos.
- Breakpoints responsivos revisados:
  - `> 1200px`: 5 colunas (com sidebar lateral)
  - `<= 1200px`: 3 colunas (sidebar empilhada acima/abaixo)
  - `<= 860px`: 2 colunas
  - `<= 540px`: 1 coluna

Arquivos: `globals.css`

---

## Arquivos modificados

| Arquivo | O que mudou |
|---|---|
| `frontend/src/components/KanbanBoard.tsx` | Adicionado `DragOverlay`, `DragStartEvent`; ícones SVG `GripIcon` e `TrashIcon`; componente `CardDragPreview`; estado `activeCardId`; `PointerSensor` com `activationConstraint` |
| `frontend/src/app/globals.css` | Grid sem scroll, remoção de `overflow: hidden` da coluna, estilos de ícone para drag/delete, `.card-drag-preview`, `.card-item.is-dragging` com opacidade, breakpoints revisados |
