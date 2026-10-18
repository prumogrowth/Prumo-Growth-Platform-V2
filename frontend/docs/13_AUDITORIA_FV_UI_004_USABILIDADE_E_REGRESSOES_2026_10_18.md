# FV-UI-004 — Qualidade da interface, navegação e regressões | 18/10/2026

**Situação:** incremento de frontend sintético na branch exclusiva. Não há decisão nova de produto, autorização de integração, autenticação real nem implantação.

## Correções

- Os botões de **Equipe** ficam ocultos para operadores e perfis suspensos, inclusive no celular. O quadro do gestor identifica membros fictícios suspensos sem tratá-los como elegíveis.
- Ao abrir diálogos de **Concluir** e **Selecionar template**, o retorno da confirmação anterior é limpo. Fechar com Escape não reaproveita um aceite antigo.
- As abas de detalhes possuem `aria-controls` / `aria-labelledby` e preservam o foco quando selecionadas. O perfil suspenso recebe mensagem própria de acesso demonstrativo indisponível.
- O script de teste de navegador foi atualizado para CF-OP-02, opção Equipe oculta para operadores, Escape no diálogo, gestor no celular e bloqueio de profissional suspenso.
- Seis verificações estáticas novas estão em `tests/source-contract.test.mjs`: responsividade, ações separadas, diálogos, acesso à equipe, abas e ausência de rede/relógios no browser.

## Evidência

- **24/24** testes de regras sintéticas executados em harness JavaScript V8 sobre módulos recuperados da branch: **PASS**.
- Sintaxe dos sete arquivos JavaScript de lógica/testes verificados: sem erros.
- Inspeção estática de fontes: confirma limpeza de diálogo, controles de equipe, relação das abas, ausência de chamadas HTTP e cálculo de relógios C09/Meta pelo navegador.
- **Pendente:** execução Node direta de todos os testes (inclusive os seis novos), execução do navegador Playwright após FV-03/FV-UI-004, auditoria por leitor de tela e testes em dispositivo físico. Script de navegador preparado ≠ teste executado.
- Autorização e regras reais continuam de propriedade S0, OpenAI, Meta e S1-002. Os filtros client-side NÃO autenticam ou protegem dados reais.

**Gate:** segue permitido desenvolver a UI sintética; homologação funcional real e apresentação visual final permanecem pendentes. Não alterar a pontuação do documento 19F automaticamente; 69/100 permanece.
