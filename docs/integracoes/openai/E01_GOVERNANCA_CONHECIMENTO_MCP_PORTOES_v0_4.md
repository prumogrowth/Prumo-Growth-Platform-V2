# E01-KH/MCP v0.4 — Matriz de autoridade, consultas e mutações permitidas

**Data:** 22/10/2026. **Estado:** [DN] decisões AL-IA-02/03, [P/R] interfaces/controles ainda não ratificados pelos titulares. **Proposta documental de fronteiras**, não endpoint, grants, ACL física, ferramentas MCP novas, operação SQL, infraestrutura ou teste. Complementa [E01-KH v0.3](./E01_CONHECIMENTO_HABILIDADES_E_MCP_OPERACIONAL_v0_3.md) e [E01-INT v0.4](./E01_CONTRATO_TIPADO_ADAPTADOR_FALHAS_v0_4.md). Esta frente OpenAI não implementa políticas da S0.

## 1. Decisões de produto que não exigem nova escolha

**[DN] Governança exclusiva de conhecimento:** **somente a Prumo** cadastra, aprova, edita, pausa, reativa, versiona e organiza bases, fatos e habilidades configuráveis, inclusive de concessionárias. Lojistas podem submeter material à Prumo, mas **não administram a base diretamente**. Um Diretor autorizado pode solicitar a mudança via MCP sujeito à confirmação e aos serviços pré-existentes. A concessão de consulta a um fato **não** concede poder de edição.

**[DN] Fontes fechadas:** F01/F02/F03 **não fazem pesquisa aberta na internet como comportamento padrão** para ofertar, financiar, cadastrar ou definir estado. Usam fatos, histórias e fontes controlados/autorizados pela S0. Qualquer pesquisa externa futura exige função, fonte, finalidade e ferramenta realmente permitidas, com projeto separado; texto de skill ou prompt não habilita navegação livre.

**[DN] Quatro configurações globais e nenhuma local:** instruções F01, comportamento F01, instruções F02 e instruções F03. A descrição da concessionária fica em dados de conhecimento e contexto de operação, não em override do prompt. Guias de MCP são textos separados para o agente administrativo externo.

**[DN] Restrições estruturais:** Prumo não muda por instruções a ACL, status, provas bancárias, tenants, regras Meta, gatilhos de F03, handoff, código ou proteção de auditoria. LiberaCred é produto da instituição financeira; o software é plataforma de atendimento sem nome comercial definido.

## 2. Matriz de decisões por superfície — sem supor permissão física

| Superfície | Quem pode propor | Quem autoriza/aplica | Quem não pode administrar | Evidência mínima [P/R] |
|---|---|---|---|---|
| Instruções/comportamento globais | Prumo/Diretor autorizado via UI ou MCP existente | Backend S0 com versão, prévia, confirmação individual quando mutação MCP e auditoria | Concessionária, Consultor, F01/F02/F03, cliente | Ator, operação, versão antiga/nova, confirmação ligada à mudança |
| Base/fato institucional | Prumo com revisão de fonte e legitimidade | S0/Prumo; escopo institucional explícito e fonte homologada | Concessionária diretamente; IA operacional | Conteúdo, fonte, data, aprovação, ACL por IA, vigência, versão |
| Base/fato de concessionária | Prumo; material de loja é **solicitação**, não gravação | S0/Prumo, propriedade vinculada à loja desde criação | Outra concessionária, cliente, F01/F02/F03 | ID de loja, proprietário, base, fato, estado, `pausar_em`, fontes |
| Contexto histórico de campanha pausada | F01/F02/F03 quando S0 autorizar interpretação de período anterior | S0 filtra por tenant/finalidade; modelo **não pode ofertar como vigente** | Busca global/fallback de outro tenant | Fonte datada, estado real, modo histórico, ausência de oferta atual |
| Contexto transacional de cliente | Fluxo atribuído, F03 apenas após conclusão expressa | S0 resolve identidade, loja, cutoff, consentimento e proveniência | Bases empresariais por dedução sem guardas; loja B; F01 após handoff | Caso, autor, tempo, fontes, evento de fecho e recheck |
| Habilidades de IA operacional | Prumo/Diretor via MCP existente | S0: ação **já implementada**, com ACL/finalidade/limites atuais | F01/F02/F03 que queiram instalar tool, gerente de loja | `tool_ref` existente e versionado, modelos elegíveis, conhecimento vinculado |
| Guias semânticos MCP | Prumo sob governança de configuração | S0 publica texto aprovado que referencia operações existentes | Guia que reivindique endpoint, cargo ou nova permissão | Guia/versão, allowlist e revisão de injeção |
| Mutação de dados operacionais MCP | Diretor Prumo autenticamente autorizado | S0 prepara prévia, recebe **segunda confirmação por operação**, revalida e executa | Agente sozinho, outro Diretor usando confirmação alheia, pessoa de loja não autorizada | Ator, escopo, versão, hash da prévia/nonce/expiração [P], resultado/auditoria |
| Histórico protegido do próprio MCP | Leitura por Diretor quando autorizada | Subsistema de auditoria anexa **eventos legítimos** | MCP não cria artificialmente, altera, apaga ou reescreve, **mesmo confirmado** | Política estrutural/credenciais segregadas, trilha append-only auditável |

**Nota:** permissões físicas, shape da prévia e API/tool existente precisam ser ratificados por S0/Prumo. A tabela mostra **intenção funcional e guardas candidatos**, não delegação técnica executada.

## 3. Governança das fontes e revisão de bases [P/R]

A sequência proposta para uma informação comercial (sem implicar schema SQL) é: **receber material → avaliar origem/veracidade/direitos → escolher escopo institucional ou loja → registrar gatilho semântico declarativo e fato canônico sem instrução conversacional → revisar condições, valores, exceções, fontes e vigência → prévia → confirmar por mutação MCP, se usada → registrar versão aprovada → ativar após validação S0**.

Regras que o validador futuro precisa provar:
1. **Semelhantes não são iguais:** nomes, slogans, códigos ou embeddings de A e B podem coincidir; a busca deve **filtrar por tenant e função antes de ranquear**, bem como depois de recuperar. Nenhum fallback 'tente outra loja'. Acesso institucional depende de classificação explícita, não de `owner_concessionaria_ref` vazio por engano.
2. **Fonte não vira autorização:** dados de campanha, conversa, documentos enviados por concessionária, notas de Consultor e texto de guia MCP são material a avaliar, jamais prompt de sistema, SQL ou grant. Injeções como 'ignore tenant' ficam inertes.
3. **Vigências independentes:** `estado` da base, `pausar_em` (opcional), datas por fato/campanha, hora com fuso e aprovação precisam ser avaliados separadamente. Job atrasado não permite oferta pós-pausa; reativação da base não ressuscita fato expirado.
4. **Histórico sem reoferta:** contexto de base pausada pode interpretar o que o cliente mencionou; condição antiga não pode ser dada como atual. Campo descritivo com fim **previsto** não comprova fim **ocorrido** nem prorrogação.
5. **Versão atual no ponto de uso:** edição, pausa, revogação, opt-out, mudança de função e handoff após recuperação têm de impedir emissão/uso indevido mesmo com resultado em cache.
6. **Política de fonte financeira:** dado de instituição financeira, taxa/aprovação, recusa, remessa e comprovantes exigem fonte/fluxo apropriados; fato semântico isolado nunca substitui estado/evidência S0.

A Prumo é o **governante do conteúdo**; S0 é o **aplicador das guardas**. Concessionária e cliente são fornecedores potenciais de dados, não autorizadores de conteúdo.

## 4. Ciclo de uma mutação MCP [P/R]

Proposta de estados **lógicos**, não enums homologados: `REQUESTED` → `PREVIEW_READY` → `AWAITING_SPECIFIC_CONFIRMATION` → `RECHECKING` → `COMMITTED`, ou `DENIED / EXPIRED / STALE / UNAVAILABLE / REJECTED`.

- **Vínculo forte à prévia:** a confirmação deve corresponder ao **mesmo ator**, verbo da operação, recurso, loja(s), IDs/alvos, contagem/limites, versão e prazo. Alterar qualquer item material **invalida a confirmação** e exige prévia nova. `"faça tudo"` não é uma confirmação genérica de N mutações.
- **Aplicação:** após a confirmação, S0 checa novamente grants/versão, escopo dos dados e travas de consistência; retorna efeito confirmado, quantidade de itens realmente afetados e referência de auditoria. Sem resultado confirmado, **não afirmar sucesso**. Operação irreversível exige prévia explícita de consequências.
- **Idempotência/retry:** repetir a mesma intenção confirmada não executa a mesma mutação novamente; confirmações expiradas, de outro Diretor ou reaproveitadas em lote diferente são negadas. Falha de rede sem recibo é estado **incerto**, não sucesso nem permissão para executar uma segunda operação.
- **Execução em massa:** o serviço S0 define escopo/atomicidade e retorno de operações parcialmente permitidas; MCP não escolhe implicitamente 'ignorar erros' para ultrapassar dados não autorizados. Cruzamento A/B requer grants para cada loja e alvos explícitos, nunca a soma de vizinhança de dados.
- **Auditoria:** registros próprios do MCP só aceitam **novos eventos reais** do serviço de auditoria protegido; não há `edit_audit_record` ou `delete_audit_history` administrativa. A confirmação específica não transforma a ação proibida em válida.
- **Limites técnicos:** MCP pode solicitar **proposta de integração/funcionalidade** para engenharia, mas **não** criar API, habilitar ferramenta inexistente, alterar esquema SQL, migrar dados estruturais ou instalar SDK. Guia escrito não concede capacidade.

## 5. Separação de erro de autorização e versão [P]

Se o mesmo pedido encontra **revogação de acesso e estado/versão alterados**, não responder ao ator revogado revelando diferença do caso, contagem, template ou dono. O laboratório sintético da ponte PR #8 demonstrou `DENIED` antes de `STALE`, mas a S0 ainda precisa ratificar seus estados físicos. Ordem específica de checks/locks é decisão S0; objetivo do contrato é **não divulgação**.

## 6. O que falta pactuar para virar critério executável

| Gate | Questão de aprovação | Responsável |
|---|---|---|
| KH-R01 | Quais operações de administração Prumo já existem, em qual catálogo e sob quais grants por escopo? | S0 + Prumo |
| KH-R02 | Como autorizar busca institucional/loja, mode histórico, revalidação, caching e relatórios sem cross-tenant? | S0 + OpenAI + segurança |
| KH-R03 | Qual schema/versionamento de base, fato, gatilho, estado, `pausar_em`, timezone, publicação e revogação? | S0 + Prumo + OpenAI |
| KH-R04 | Como provar fonte bancária/financeira aprovada e bloquear oferta com condição não confirmada? | Prumo + produto/financeiro + S0 |
| KH-R05 | Como o MCP autentica segundo ato, cria prévia, vincula identidade/escopo, invalida replay e reporta commit? | S0 + equipe MCP + segurança |
| KH-R06 | Como credenciais/serviços tornam trilha de auditoria efetivamente protegida, inclusive contra exclusão em massa? | S0 + segurança |
| KH-R07 | Quais habilidades já possuem operação implementada/autorizada, e como a proposta nova fica separada da ativação? | S0 + Prumo + OpenAI |
| KH-R08 | Política de privacidade, retenção, exportação, download/importação e dados sujeitos a obrigação legal? | Privacidade + S0 + Prumo |

**Saída exigida:** contrato/catálogo versionados de cada frente, dono identificado, aceite expresso com ressalvas e apontamento dos cenários adversariais. Texto desta branch e comentários de GitHub não são substitutos do aceite titular.

## 7. Continuidade E02/E04

Os cenários SYN-57..70 continuam **70 SYN no total**; devem ser suplementados pelo caderno [E02-KH/MCP — variações adversariais](./E02_MATRIZ_ADVERSARIAL_CONHECIMENTO_MCP_v0_1.md), que **não aumenta a contagem oficial de casos SYN**. Variações detalham ataques/negativas para revisão documental, sem schema, fixture executável ou testes rodados.

**Estado:** revisão/planejamento permitido, sem alterar outras frentes, sem chamada OpenAI/MCP/Meta real, sem senha/chave, sem commit de código. E02-REV e E02-FIX seguem **pendentes**. E04 exige liberação **expressa de implementação** conforme G-FASE-DO-PROJETO; E05 exige orçamento/credencial/ambiente aprovados separadamente.
