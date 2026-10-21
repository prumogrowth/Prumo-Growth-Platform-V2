# WA-21 — Nomenclatura de papéis e assinatura visível de mensagens humanas

**Data da decisão:** 21/10/2026. **Tipo:** decisão expressa do responsável, registrada para implementação futura. **Escopo:** nomenclatura do projeto/WhatsApp e formato visível da autoria nas mensagens. **Estado:** documentação aprovada; código, interfaces, permissões e migrations NÃO alterados. Este registro **complementa e prevalece** sobre a apresentação ainda aberta na [WA-20](./wa20-identificacao-visivel-atendente-assinatura-mensagem-2026-10-21.md).

## 1. Nomes oficiais dos papéis — DECISÃO

| Denominação usada anteriormente | Denominação de produto aprovada em 21/10/2026 | Interpretação |
|---|---|---|
| `responsável` como nome do papel superior/administrativo | **DIRETOR** | Nome visível e de domínio da posição anteriormente chamada responsável |
| `gestor` | **GESTOR** | Nome mantido, sem mudança de atribuições presumida |
| `operador` | **CONSULTOR** | Nome visível e de domínio do papel humano de atendimento anteriormente chamado operador |

**Precedência:** em especificações, interface, comunicação, documentação nova e futuramente nomes de exibição, usar **Diretor, Gestor, Consultor**. Nos documentos antigos, expressões como “operador humano”, “caso do operador”, “gestor” e “responsável atual” são interpretadas conforme o papel ao qual se referiam na época, **sem apagar o texto original**. “Responsável pela decisão”, “responsável legal”, “responsável técnico” e outros usos de “responsável” como substantivo genérico **não são automaticamente renomeados como cargo Diretor**. Isso evita transformar toda menção a responsabilidade em privilégio de diretor.

**Importante para segurança:** a mudança é **terminológica e de apresentação**, não uma autorização para mexer em perfis, permissões/RLS, contas MCP, autenticação nem tabelas legadas automaticamente. Os identificadores físicos existentes (ex.: `operador_id`, `casos_humanos`, `actor_tipo=OPERADOR`, enum de status `em atendimento pelo operador`) podem permanecer durante uma migração compatível; os textos visíveis poderão dizer **consultor** quando a interface for atualizada. A hierarquia/permissão de Diretor, Gestor e Consultor e a ampliação do MCP precisam preservar a matriz autorizada e a dupla confirmação já decididas. **Não inferir que Gestor ou Consultor passam a ter MCP administrativo** pela troca de nomes; a frente MCP/global deverá conciliar acesso com a nomenclatura nova.

## 2. Formato OBRIGATÓRIO de autoria nas mensagens humanas — DECISÃO

O cliente deverá receber **o papel e o nome da pessoa identificados antes do texto**, gerados pela plataforma, sem que ela digite repetidamente o próprio nome. O responsável aprovou as três formas:

```text
Consultor Fulano:
Bom dia! Como posso ajudar?
```

```text
Gestor Ciclano:
Vou conferir sua solicitação.
```

```text
Diretor Beltrano:
Estamos acompanhando seu atendimento.
```

**Esquema aprovado:** `<Cargo de exibição> <Nome de exibição>:\n<Mensagem original>`. Nome dos cargos com inicial maiúscula, seguido de espaço, nome do usuário, **dois pontos** e mensagem em seguida, idealmente na próxima linha para reproduzir a referência do cliente de nome acima do texto. **Não utilizar “Mariana — Atendimento” como padrão vigente.**

A aplicação é para **mensagens textuais livres enviadas por humanos** que atuem como Consultor, Gestor ou Diretor, dentro da janela e das regras WhatsApp. O comportamento padrão desejado é a composição automática quando um humano desses perfis enviar a mensagem; política de exceções (ex.: mídia, legenda, um único cabeçalho por conversa, outros formatos) só pode ser alterada mediante decisão explícita posterior. **Não atribuir assinatura humana a texto originado exclusivamente por IA ou sistema.**

Para templates aprovados, o prefixo NÃO pode ser concatenado arbitrariamente à estrutura aprovada Meta; se a identidade humana precisar aparecer, ela deve estar contida no conteúdo ou em parâmetro/slot aprovado, cuja fonte é congelada por versão e preenchida pela plataforma. A assinatura não contorna a janela de mensagens livres de 24h, nem consentimento/opt-out, handoff, escopo da concessionária ou autorização de envio.

## 3. Separar identidade interna e texto visível — PROPOSTA TÉCNICA para auditoria posterior

- O backend valida **identidade da sessão**, papel vigente e atribuição ao caso, sempre no tenant da concessionária, ao compor o texto final; **não confia em papel/nome enviados pelo cliente, pela IA ou pelo navegador sem autenticação**.
- Manter autoria real e imutável com ator estável, tipo humano/IA/sistema, `role_snapshot`, `nome_snapshot`, conteúdo digitado e conteúdo efetivamente transmitido, sem falsificar histórico quando pessoa muda de nome ou cargo.
- Prévia no painel precisa refletir o texto exato recebido pelo cliente. Uma única etapa de composição evita duplicar assinatura em retries/idempotência; respeitar limites de caracteres.
- Consultor, Gestor ou Diretor **não são remetentes Meta separados**. O WhatsApp permanece exibindo o número/perfil empresarial da concessionária como origem técnica; o cabeçalho é texto construído pela plataforma.
- Se o humano trocar durante o caso, a mensagem seguinte usará o papel e nome do **autor real do envio**, sem reescrever mensagens anteriores.

## 4. Pontos de auditoria e coordenação

1. Atualizar especificações de UI, telas, trilhas de autoria, filtros, nomenclaturas de perfis, matriz de permissões e textos operacionais nas frentes correspondentes. **Não** substituir cegamente cada string `responsável` nos históricos.
2. Ajustar documentos de MCP e gestão de templates de “responsável” como cargo para **Diretor**, onde o papel corresponder ao antigo papel superior; política concreta de contas/perfis permanece sob revisão da frente MCP/global.
3. Conferir o status comercial `em atendimento pelo operador` e identificadores de banco **antes** de cogitar renomear o estado físico; atualização de UI não pressupõe migration.
4. Criar testes futuros: cada cargo/nome correto, ausência de autorização, handoff/troca de cargo, rascunho sem prefixo duplo, envio/retry com assinatura idempotente, mensagens IA sem identificação humana, template Meta aprovado sem adulteração e segregação por loja.
5. A documentação histórica de 17/10, WA-20 e os PRs existentes continuam preservados; esta decisão determina **precedência terminológica**, não conclusão técnica.

**Status final:** alinhamento registrado para desenvolvimento posterior; não implementado, sem Meta real, CI, Supabase hospedado, MCP, merge ou deploy. Referências: [00 — decisões WDC](./00-decisoes-vigentes-precedencia-documental-2026-10-21.md), [01 — especificação funcional](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md), [WA-20](./wa20-identificacao-visivel-atendente-assinatura-mensagem-2026-10-21.md) e [índice principal](./README.md).
