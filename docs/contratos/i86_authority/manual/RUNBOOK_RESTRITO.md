# I86 — roteiro do operador, exclusivamente ensaio local

Este documento descreve a utilização humana futura do instrumento. Não é
automação de nomeação, comando MCP ou autorização de produção. O SQL contém
guard de laboratório e não deve ser instalado no Supabase hospedado.

## Preparação e revisão

Um humano autorizado deverá possuir acesso administrativo restrito e referência
verificável do ato. A política de custódia, a identidade nominal e a fonte dessa
autorização ainda precisam de configuração operacional. Não fornecer credenciais
postgres/SQL Editor a agentes, MCPs, APIs, frontend ou Edge.

No ensaio, somente a infraestrutura I84 cria uma stack nova. O perfil I85 mantém
a Edge sem credenciais do instalador. A fixture procedure.sql é instalada
atomicamente pelo contexto técnico local. Nenhum usuário comum recebe EXECUTE.

Obter UUID da fonte canônica Auth. Não converter cargo por metadados nem alterar
as três tabelas manualmente para satisfazer precondições. Antes de decidir,
consultar inspect_subject(target). A consulta não autoriza ação e devolve CAS.
Preparar act_id novo e os códigos de referência do operador/ato e digest da
evidência. Os exemplos abaixo usam parâmetros, nunca credenciais ou pessoas reais.

## Transação explícita

~~~sql
BEGIN ISOLATION LEVEL READ COMMITTED;
SET LOCAL lock_timeout = '8s';
SET LOCAL statement_timeout = '20s';
SELECT prumo_i86_manual.apply_act(
    :act_id, :action, :target_uuid, :expected_sha256,
    :operator_record_ref, :manual_record_ref, :evidence_sha256
);
COMMIT;
~~~

O resultado do SELECT é provisório. Constraints e auditoria podem falhar no
COMMIT. Não declarar nomeação concluída pela impressão anterior à confirmação.
Depois, em transação nova READ COMMITTED:

~~~sql
SELECT prumo_i86_manual.reconcile_act(:act_id, :evidence_sha256);
~~~

Somente COMMITTED_CURRENT_STATE_VERIFIED comprova confirmação e contexto
coincidente naquela leitura. Não é permissão futura nem assinatura do humano.
COMMITTED_STATE_CHANGED registra que o ato existiu, mas o estado já mudou;
não repetir ato antigo para restaurá-lo.

## Falhas e repetição

- Timeout/conexão perdida: manter act_id/evidência e consultar reconciliação.
- NOT_PROVEN: não é autorização de retry automático. Investigar a transação,
  conflitos e estado atual; um novo envio exige decisão humana explícita.
- COMMIT_NOT_PROVEN: transação própria ainda não confirmada; não anunciar sucesso.
- STALE/conflito: revisar estado/evidência. Nunca trocar CAS por conveniência.
- NOWAIT/lock timeout: rollback integral. A contenção não autoriza remover locks.
- Falha de auditoria/constraint: não há sucesso. Confirmar ausência com consultas.
- Alvo já vinculado a outro cargo/incompleto: manter bloqueio, sem editar tabelas
  relacionadas para contornar o instrumento.

REVOKE conserva cargo Diretor/estado ativo como classificação histórica e
inativa competência. Retira sessões existentes no corte, sem banir conta:
novo login é possível, mas não recupera administração. REACTIVATE exige novo
ato manual; nunca recria as sessões apagadas. Não inferir suspensão de carteira,
mudança de intake, transferência de casos ou política comercial.

## Simulação de laboratório e descarte

Somente os testes chamam o instrumento automaticamente para representar o
contexto privilegiado em uma VM descartável. Os registros usam referências
I86M_SYNTHETIC e não comprovam um ato humano. Não copiar lab_support/crash_probe
para um backend, job produtivo ou ferramenta MCP.

O laboratório inteiro é retirado pelo operador I84/I86 já existente, com prova
de recursos ausentes e material sensível removido. A criação de usuários é
somente fixture Auth em memória; não usa grant ou journal de bootstrap I85.
Uma jornada I85 independente preserva a certificação anterior. Não há promessa
de destruição forense de RAM/WAL ou de defesa contra infraestrutura comprometida.
