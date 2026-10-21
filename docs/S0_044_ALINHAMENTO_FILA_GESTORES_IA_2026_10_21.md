> **Terminologia atualizada [S0-045], 21/10/2026:** “responsável da plataforma” passa a **Diretor**; “operador” passa a **Consultor**; **Gestor** permanece. Somente nomenclatura, sem mudança de função ou código. Consultar [S0-045](./S0_045_NOMENCLATURA_DIRETOR_GESTOR_CONSULTOR_2026_10_21.md). Referências abaixo podem usar nomes anteriores por terem sido redigidas antes.

# S0-044 — Contrato documental de alinhamento: novos leads, fila dos gestores e IA
**Data:** 21/10/2026. **Natureza:** registro de **decisões de produto [D]**, para coordenação S0↔S1↔Frontend. **Não** confirma SQL, endpoint, RLS, Auth, integrações nem operação real. Registro complementar à [S0-043](./S0_043_PAUSA_SELETIVA_E_INDICADOR_CONVERSA_2026_10_20.md). A fonte detalhada do frontend é [FV-DOC-01/D-AL-01..10](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/frontend-plataforma-visual/frontend/docs/35_FV_DOC_01_DECISOES_VIGENTES_ALINHAMENTO_2026_10_21.md).

## Separação que não pode voltar a ser confundida
| Tipo | Destino automático válido | Sem receptor | Regra de titularidade |
| --- | --- | --- | --- |
| **Caso ativo já atribuído ao operador que foi pausado**, sem primeiro contato humano comprovado | Outro operador **da mesma equipe**, com conta ativa, intake habilitado e concessão à concessionária | **Manter atribuído ao operador pausado**, sem nova fila sem titular | Não deslocar por ausência de substituto |
| Caso existente **com** contato humano comprovado ou evidência desconhecida | Nenhuma mudança automática | Preservar titular | Transferência somente manual individual e autorizada |
| **Lead novo**, distribuição normal | **Qualquer equipe**, se operador elegível com concessão regular à loja, conta ativa e recebendo leads | **Fila sem titular** compartilhada por gestores autorizados à concessionária | Não atribuir automaticamente a gestores |
| Lead pendente **sem titular** na fila quando algum operador volta a ser elegível | Voltar automaticamente à distribuição normal, inclusive entre equipes | Continua pendente | Não retirar caso já assumido manualmente por gestor/operador |
| Gestor assume/encaminha **lead pendente sem titular** | Gestor autorizado à loja assume ou envia a **membro da própria equipe**; eventual falta de grant de loja exige **exceção estritamente por caso** | Mantém na fila | Apenas um vencedor transacional; evitar dupla titularidade |

**Autorização:** gestor gerencia equipe e vê fila pendente somente das concessionárias às quais tenha autoridade reconhecida; não recebe automaticamente concessão de todas as lojas. O responsável configura contas e grants gerais; gestor não bloqueia conta nem concede lojas. Se o gestor for titular designado, executa operações normais de operador somente no caso. Profissional **pausado** mantém leitura e respostas nos casos que conserva.

## Prova de contato humano — decisão expressa
Contar **mensagem efetiva de operador com evento de envio confirmado pela plataforma**. Não contar leitura, abertura, recebimento da atribuição, tentativa sem comprovação ou interação exclusiva da IA. **Não criar registro manual** de ligação externa/visita para provar contato humano. Ligação oficial WhatsApp poderá contar **futuramente** se a API oferecer suporte, existir integração construída e evento confiável de **chamada atendida**; chamada somente tentada não conta. Capacidade Meta e contrato de prova permanecem [V/T], não demanda de implantação imediata.

## IA Vendedora — fronteira de dados
A IA que atende o cliente **não conhece nem consulta** quantidade/identidade de operadores, suas equipes, permissões, disponibilidade, concessionárias concedidas ou regras de distribuição. Seu contexto contém o necessário à conversa comercial; ela continua atendendo mesmo sem operador disponível. No handoff, o **núcleo operacional** decide alocar humano ou fila; a IA não decide destinatário. Não usar prompts, memória da IA ou modelo como autorizador de fila, RLS ou grants. Preservar interrupção da IA Vendedora após handoff no caso.

## Regras já aprovadas preservadas
- Pausa com confirmação simples, **sem motivo, data, atestado ou prazo**; não suspende login e só impede novos leads.
- Transferência manual dentro da equipe para destinatário sem concessão geral à loja cria, após confirmação, autorização **somente daquele caso**, revogável quando titular muda; nenhuma concessão geral ou D3/D4 bruto por supervisão.
- Um indicador de conversa: número de não lidas ou bolinha sem número após leitura sem resposta, nunca dois badges; supervisor não marca leitura em nome do titular. Sem SLA/cronômetros operacionais.
- Núcleo **Supabase**; “Firebase” foi erro de transcrição.
- **DEC-WA-05** documentada nesta branch permanece referência de titularidade de canal Meta por concessionária, com Prumo integradora, e não deve ser confundida com pessoal da Prumo.

## Fronteiras técnicas e checklist ainda [T]
1. Evento assinado/autorizado e versionado da primeira mensagem humana; tratamento de chamadas Meta futuras sem prova inventada.
2. Separar estado `intake` de estado de conta, grants gerais, carteira ativa e status comercial.
3. Contratos S1 para distribuição regular **cross-team** de leads novos e redistribuição restrita à **mesma equipe** de casos do pausado.
4. Fila pendente por concessionária e gestores explicitamente autorizados, com prova de escopo; assunção manual, prioridade da atribuição automática, CAS/serialização, idempotência, audit trail e corrida entre gestores.
5. Exceção por caso cobrindo **mensagens, leitura D2, operação, D3/D4 permitidos e anexos** sem vazamento para outros casos/lojas, com revogação segura.
6. Sem API/SQL/Meta/OpenAI produtivos antes de GoTrue/RLS/PostgREST e testes concorrentes. Nada disso é automaticamente liberado pelo presente documento.

## Estado e precedência
O [S0-043](./S0_043_PAUSA_SELETIVA_E_INDICADOR_CONVERSA_2026_10_20.md) continua vigente para **casos existentes de operador pausado**. A presente S0-044 **acrescenta** decisões sobre **leads novos, fila compartilhada, retomada, fronteira da IA e prova de ligação**, que não estavam resolvidas no S0-043. A branch S1-002 já contém retificações na issue #10 para intake e caso excepcional, mas a implementação operacional ponta a ponta permanece sujeita a revisão própria da S1. **Nenhum código S0/S1/Meta/Frontend foi modificado por este registro.** FV-UI-013 não homologada, 19F 69/100 preservado.