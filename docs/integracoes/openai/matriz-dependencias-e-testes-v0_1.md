# OAI-03 — Matriz de dependências, autonomia e testes | v0.1

**Estado [P]:** proposta de planejamento e verificações futuras. Nenhuma suíte, conexão real ou integração executada nesta branch.

## Matriz de titularidade não competitiva

| Item | Dono | Esta branch faz | Esta branch NÃO faz |
|---|---|---|---|
| Credencial OpenAI | Responsável humano | Orientação e contrato de consumo futuro | Gerar, coletar, persistir ou testar credencial |
| Secret Supabase da Prumo | Responsável humano | Nome lógico e instrução documental | Consultar plugin de outro projeto, alterar secrets, usar banco remoto |
| Estado/caso, permissões, RLS, versão, auditoria | S0 / PR #1 | Especificar campo e validação esperados; revisão cruzada | Migrar esquema, alterar funções, abrir API pública ou modificar fluxo |
| IA Vendedora / intenção C03 | S0 + adaptador OpenAI [P] | Formatar proposta sem efeito | Decidir status ou enviar Meta |
| IA Planejadora C05 | S0 + adaptador OpenAI [P] | Sugerir itens existentes, sujeito ao domínio | Criar template, publicar/agendar sozinho |
| Transportes WhatsApp C02/C06/C07/C12 | Meta / PR #2 e S0, segundo contrato | Receber apenas referência ao destino da intenção | Implementar Graph, callback, HMAC, worker ou alterar o PR #2 |
| Handoff C10 e resultado Banco | S0 + humano | Recusar geração/saída após bloqueio | Retomar IA, registrar venda/recusa ou operar Banco |
| MCP administrativo | Fluxo de governança | Nada nesta fase | Substituir MCP ou retirar segunda confirmação |

## Testes propostos para a futura porta de OpenAI — NÃO executados

- OAI-T01: cliente na loja A e mesmo telefone na B -> contexto de A não aparece no envelope B, nem pela referência de conhecimento.
- OAI-T02: estado com handoff já ativo -> nenhuma geração autorizada; se handoff ocorre durante chamada, resultado tardio não vai para outbox.
- OAI-T03: resposta do modelo solicitando atualização de status 'vendido'/'perdido' -> tratada como texto não autorizado, sem mutação.
- OAI-T04: oferta bancária, taxa ou limite inventados -> proposta recusada/escalada, sem publicação.
- OAI-T05: planejadora escolhe template inexistente ou versão não aprovada -> S0 recusa sem agendar.
- OAI-T06: instruções maliciosas em mensagem/anexo -> não obtêm segredo, acesso interloja nem execução de ferramentas.
- OAI-T07: versões incompatíveis de contrato/prompt/contexto -> rejeição determinística com código seguro.
- OAI-T08: timeout, 401, 429, cota esgotada ou corpo do provedor inválido -> nenhuma duplicação Meta, nenhuma mudança de domínio, auditoria mínima.
- OAI-T09: pedido de MCP ou exclusão em massa por porta de atendimento -> rejeição; não confundir com confirmação administrativa.
- OAI-T10: logs/resultados nunca contêm API key, JWT, segredo Meta, dados bancários brutos ou mensagens pessoais sem autorização.
- OAI-T11: status técnico delivered/read ou texto de modelo não altera estado comercial; pós-venda ou pós-remessa continua humano.
- OAI-T12: idem request_id reenviado -> a política S0 impede criar intenção comercial duplicada, independentemente de repetição de chamada ao provedor.

## Portões de coordenação

**Abertura da branch:** concluída. **Documentação candidata:** presente, sem aceite normativo. **Revisão cruzada:** PENDENTE da frente S0; a Meta revisa apenas quando a fronteira de saída afeta seu contrato. **Segredo manual:** PENDENTE; **teste pago:** NÃO AUTORIZADO; **dados reais, deploy e merge:** NO-GO.

Não usar resultados futuros desses testes para elevar o percentual auditado do planejamento sem critérios, execução e evidências conforme controle 19.
