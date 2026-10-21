# WA-01B — revisão cruzada Meta ↔ S0/028/029 | 18/10/2026 | v0.1

> **[LEITURA_ORIENTADA_2026_10_21] Documento de referência histórica ou de engenharia, NÃO substitui decisões funcionais recentes.** Consulte o [LEIA PRIMEIRO](./README.md), a [especificação vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e o [mapa de conflitos por origem](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Apenas trechos expressamente substituídos perdem vigência; evidências offline não significam serviços reais homologados.

**Estado: PARECER E CONTRATO CANDIDATO [P] — não homologado pela frente principal.**
Base auditada no GitHub: PR #1 `feat/s0-fundacao-prumo`, HEAD `1ed4bab627a6f1977c3c1889eed6ada03c456a69`; PR #2 `docs/whatsapp-meta-concessionária de demonstração-poc-20261017` após WA-01A e DEC-WA-05. Nenhum merge, migration hospedada, webhook real ou canal comercial foi alterado.

## 1. Evidência real versus intenção de integração

| Área | Evidência de implementação na S0 | Limite para a Meta real |
| --- | --- | --- |
| Identidade | 028 cria `aliases_identidade_s0` e resolvedor com prova móvel **fictícia** | `p_mobile_confirmado` NÃO pode vir de payload Meta nem virar prova de titularidade civil; não conectar C02 real ainda |
| Ingresso | 029 `aceitar_lote_ingresso_s0(p_canal,p_itens)` insere inbox + tarefa atomicamente por **um** canal simulado, com duplicatas, hash e rollback integral | Não autentica app Meta, não resolve WABA/Phone Number ID, só opera com `current_user='postgres'`; não é interface para webhook |
| Payload | 029 grava `tipo`, `chave_evento`, `fingerprint_sintetico` e escopo; **não persiste conteúdo/referência protegida de replay** | Com esses dados não há recuperação de texto/mídia/status completo para C02/C07; jamais usar resultado 029 como ACK real |
| Lote | 029 recebe `p_canal` único, até 20 itens; WA-01A pode extrair múltiplos `entry[]` e emissores | Precisamos de aceite **atômico de todo o POST**, inclusive se houver canais distintos; não fazer duas RPCs e retornar 200 após só uma |
| Saída | 029 registra C03/C06/C12 apenas `BLOQUEADA_GATES` | Não existe adaptador autorizado de Graph ou revalidação final |
| Segurança | 029 restringe EXECUTE a uso interno SQL em PostgreSQL descartável | Não inventar acesso `service_role`; credencial de serviço e RLS/GRANT dependem da frente principal |
| Titularidade Meta | PR #2 documenta **DEC-WA-05 [D]: cada concessionária controla seu App/WABA/número/segredos** | Confirmação cadastral, permissões e onboarding são pendências [V]; não copiar premissa antiga de titularidade da gestora |

**Nota de precedência:** documentos antigos da S0 e da interface v0.1 que mencionam DEC-WA-05 como pendente ou canais pertencentes à gestora precisam conciliação explícita. DEC-WA-05 foi aprovada **como titularidade**, não como autorização operacional.

## 2. Mínimo exigido para interface verdadeira [P]

Proposta de operação privada e autenticada **em lote único** pelo núcleo, sem nome de RPC definido:

1. Receber referência de app **selecionada por contexto confiável** e confirmação HMAC sobre bytes brutos (WA-01A), sem aceitar `concessionaria_id` do remetente como autoridade.
2. Conferir app/WABA/phone_number_id em mapeamento cadastral válido; unknown/revogado deve ter destino seguro sem vinculação arbitrária.
3. Persistir **payload original ou referência protegida, íntegra e recuperável** sob retenção/segurança aprovada, junto aos identificadores necessários; não enviar PII bruta a logs ou CI.
4. Em **uma transação**, gravar todas as unidades relevantes, dedupe por identidade de evento apropriada, tarefas duráveis e eventual quarentena restrita; erro de um item não autoriza sucesso parcial.
5. Retornar recibo confiável somente após commit: `outcome`, `commit_state='COMMITTED'`, `total`, `accepted`, `duplicates`, `quarantined`. O total deve bater com itens do POST. O recibo é **proposto**, não resultado atual da função 029.
6. A distinção de `status_callback` não pode usar apenas `statuses[].id` como chave única de callback: é o ID da mensagem de saída, que admite sucessivos status.
7. O ACK HTTP 200 só pode ocorrer após todos os itens obterem decisão durável e **política aprovada de ACK/quarentena**. Até DEC-WA-06, a guarda experimental retém ACK se houver quarentena.

A guarda sintética `integrations/whatsapp-meta/durable-receipt.ts` **apenas valida a consistência estrutural de um recibo hipotético**; não emite HTTP, não atesta banco, não possui transporte nem aceita diretamente o retorno incompleto da 029. O código chamador futuro deverá confiar exclusivamente em serviço interno autenticado e comprovadamente transacional. A decisão de 503 para quarentena é provisória, **não é política de produção homologada**.

## 3. Pedidos objetivos à frente principal (PR #1)

1. **Escopo atômico de lote:** a interface definitiva aceitará um POST com mais de um `phone_number_id`? Se sim, como fará commit único (não múltiplas chamadas 029 por canal)?
2. **Payload recuperável:** onde ficará o conteúdo/media/status íntegro, criptografado/referenciado, com retenção e DLQ, para worker C02/C07?
3. **Identidade de serviço:** qual operação interna, privilégio mínimo, contrato de versionamento e autorização para resolver `Meta app + WABA + sender → canal_id + concessionaria_id`?
4. **Dedupe/status:** qual chave/observação para callback sem event ID, replay de mesmo `wamid` com formatação de telefone variante e conflito verdadeiro?
5. **Recibo/gates:** resultados de transação, quarentena, ACK/replay e estados de erro; qual ensaio sintético comprova rollback do lote completo?
6. **DEC-WA-05:** conciliar o novo modelo de propriedade por concessionária nas referências S0, sem nenhuma alteração dos ativos Meta existentes.

**Dependências abertas:** DEC-WA-04 (ambiente definitivo), DEC-WA-06 (operação/segredos/retencão/backups), validação do cadastro Meta por concessionária (parte [V] da DEC-WA-05), serviço/DDL de ingressão aprovado. WA-01B não concede aprovação a nenhuma dessas decisões.

## 4. Testes executados e lacunas

`node --experimental-strip-types --test integrations/whatsapp-meta/durable-receipt.test.ts` — **WA-ACK-01..10 PASS** localmente em Node 22.16.0; checagem TypeScript sem emissão aprovada. Estes testes provam **somente a regra pura de ACK**, não transaction commit, integração com a S0, HMAC real Meta ou webhook em produção.

Também permanece válido o ensaio isolado WA-01A de parser/HMAC, mas a integração entre `inbound.ts` e um port de persistência é **posterior à revisão cruzada**.

**Proibições preservadas:** sem migrations, sem deploy, sem assinatura de apps, sem Graph API, sem alteração de concessionária de demonstração ou números comerciais, sem contratação paga, PRs Draft e sem merge.
