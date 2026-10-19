# Estratégia de implementação sem credenciais reais — APIs no gate de integração

**19/10/2026 — proposta de execução [P], não decisão de negócio nem homologação.** Aplica-se à plataforma **Prumo**; **LiberaCred é produto da instituição financeira**, não o nome da plataforma.

## Resposta operacional

Podemos construir quase toda a estrutura sem conectar credenciais reais de Meta/WhatsApp, OpenAI ou integrações bancárias. **Não** podemos afirmar que o sistema está concluído ou pronto para operar sem integrar, observar e homologar esses serviços. Separar **API real no fim do desenvolvimento** de **contrato de API e testes durante o desenvolvimento**.

## Sequência e gates

| Fase | Entrega aceita para engenharia | O que não depende de API externa real | O que permanece bloqueado |
|---|---|---|---|
| 1 — Contratos agora | Eventos/campos/versões, erros, idempotência, escopo loja/App/WABA/emissor, autenticação, recibo pós-commit, janela 24h, timestamps, `sent` confirmado, limites por agente | Documentação; esquemas de entrada/saída; fixtures sintéticas com negativas; adaptadores por interface; testes de conformidade offline | Regras oficiais da Meta e onboarding de contas ainda carecem de verificação; DEC-WA-04/06 continuam abertas |
| 2 — Núcleo real, sem fornecedores | SQL da **S0** com testes PostgreSQL 17 descartável, concorrência, rollback/recuperação, RLS/menor privilégio, trilha e C02/C07/C08/C09/C04 | Banco local real; processos e simulação explícita da recepção de eventos; fluxo IA Vendedora → humano, atribuição Prumo, não retorno arbitrário à IA | Integração HTTP Meta real, autenticação de provedor, dados de cliente e qualquer aprovação comercial |
| 3 — Adaptadores desacoplados | Portas/interfaces substituíveis; transporte Meta e chamadas OpenAI atrás de gateways; autorização de envio **somente S0**, observabilidade; testes automáticos com servidor falso controlado | Desenvolvimento do aplicativo, painel humano, IA Planejadora propondo parâmetros permitidos da IA de atendimento, automações e tratamento de erro | Qualidade/latência/custo e correspondência 1:1 dos serviços reais não comprovadas |
| 4 — Integração real autorizada | Credenciais de teste, sandbox ou conta autorizada **por concessionária**, validação de assinatura, eventos reais de webhook, janelas, templates aprovados, `sent` oficial, política de retenção, auditoria de custos; integração OpenAI e banco apenas conforme contratos/autorizações específicos | Praticamente nada disso deve ser inferido a partir de mocks | Produção até passagem dos testes end-to-end e aprovações legais/comerciais |
| 5 — Homologação e implantação | Segurança, testes intersessões, falha de conexão/COMMIT_UNKNOWN, replay, isolamento multi-tenant, handoff, opt-out, template após 24h, casos pré/pós-banco, monitoramento e rollback | Checklist pode ser redigido antecipadamente | Operar, cobrar/enviar mensagens ou afirmar funcionamento completo antes das evidências |

## Particularidades fundamentais já estabelecidas

- **Meta** é dona do transporte WhatsApp; cada concessionária possui App/WABA/números próprios (DEC-WA-05) e a Prumo age dentro da autorização. **S0**, não a Meta nem a IA, decide classificação comercial, janela e permissões.
- **IA Vendedora** atende no fluxo autorizado; **IA Planejadora/otimizadora** pode propor mudanças em parâmetros permitidos da IA Vendedora, nunca alterar sua própria política nem agir fora do controle humano/S0. O agente não recebe credenciais da Meta para envio direto.
- Mensagem inbound entregue após handoff pertence à **fila/operador humano autorizado**. Template só é enviado mediante autorização/catálogo e validação de janela/opt-out. Aceitação HTTP do provedor não basta para provar `sent`; C09 pós-silêncio jamais derruba `cadastro enviado ao banco`.
- **instituição financeira/LiberaCred**: desenhar interface e registros de evidência agora; não pressupor API pública, integração automática, autorização bancária ou resultado de crédito real. Decisões e envio ao banco seguem controle autorizado.
- A auditoria WA-06D-AUD2 identificou que os 6 cenários `WA06D-B` criam dados em **fixtures próprias**, sem executar o ingressor WA-06D/A ou S0. **0/20 SQL PostgreSQL realmente executados até esta data.** Não criar novos simuladores para aumentar uma contagem artificial.
- **Primeiro gate técnico obrigatório para prosseguir com confiança:** executar PostgreSQL 17 descartável e a suíte já publicada; a seguir provar o caminho S0 real. Isso **não exige credencial de nenhuma API externa**. Se o ambiente local não oferece PG17, registrar bloqueio e trabalhar apenas em contrato/arquitetura até obter execução legítima e autorizada.

## Política de evidências e custo

- A existência de uma interface, mock, fixture ou documentação **não equivale à integração homologada**. Relatar separadamente: proposta, código revisado, teste offline, teste PostgreSQL e teste real do fornecedor.
- Não ativar API Graph/Meta, OpenAI, Banco, Supabase hospedado, números reais da concessionária de demonstração, deploy, CI pago ou secrets sem aprovação explícita. PRs permanecem Draft; não alterar metas/percentuais de planejamento só por preparar gateways.
- **Próxima ação recomendada [R S0/Meta]:** validar o PG17 local já pendente; só depois atravessar fronteira Meta→S0 por uma transação demonstrável, com identidade de serviço real e recibo depois do COMMIT. Real API fica para gate separado de integração, não para dimensionar o domínio.
