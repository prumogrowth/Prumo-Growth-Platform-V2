# I79/G2 — relatório de implementação e continuidade S0/S1

27/10/2026. Fonte normativa, DTO interno, locks e limites estão em
[CONTRATO_E_CHECKPOINT.md](CONTRATO_E_CHECKPOINT.md). Esta é uma continuação da
I78, não reinicialização da S1 ou incorporação automática de PRs.

## O que mudou efetivamente

1. Cargo explícito na equipe existente. Gestor sem subordinados é identificável;
   grants de loja não concedem cargo nem competência do Diretor.
2. REGISTER/ACTIVATE de Gestor/Consultor sobre UUID GoTrue existente, sob Diretor
   autenticado. Consultor só ativa com uma chefia principal ativa no COMMIT.
3. TRANSFER de chefia autenticado, CAS do vínculo anterior, relação sucessora,
   idempotência durável, auditoria e validação antes de confirmar a resposta.
4. Barreira no caminho canônico S0 de atribuições e no G1, incluindo replay.
   I54 filtra registros ainda não classificados, sem reimplementar sua fila.
5. Revogação I61 durável na perda da chefia que concedeu a exceção. Retorno ao
   Gestor anterior não ressuscita a autorização. Sem transferência de casos,
   grants gerais ou reinicialização de intake/indicadores.

## Reuso e fronteiras de arquivo

| Área | Arquivo/delta |
| --- | --- |
| S1 — backend | `backend/s1_professionals_local.py`, porta administrativa interna |
| S1 — banco | `supabase/tests/s1_i79_profissionais_local_only.sql`, cargo, constraints, chefia, recibos e auditoria |
| S0/S1 — adaptação I54 | `integration/i79/install_local.py`, função original conferida por hash e uma condição de elegibilidade; instalação atômica |
| S0/G1 — fixtures de integração | `integration/g1/test_manual_handoff.py`, apenas dois hooks de preparação/mudança de equipe; 36 asserções originais preservadas |
| Fontes S1 | `integration/g1/s1_sources.json`, novo ref I78 após igualdade de 34 hashes |
| Compatibilidade pura | `backend/tests/test_s1_professionals_contract.py`, oito testes novos |
| Provas reais | `integration/i79/test_professionals.py`, 36 G1 herdados + 26 I79 |
| CI própria | `.github/workflows/exp-s0-s1-i79-professionals.yml`, integração e regressão histórica pinada em jobs separados |

Não se reescreveram GoTrue, CFI-01, HMAC, login SQL, cofres, nonce, fila I54,
intake I52, guarda I57, exceção I61, revogador I62 ou catálogo RLS I63. A nova
barreira complementa os guards, preservando-os. O cadastro administrativo não é
o convite/criação da conta GoTrue e não usa service_role ou credencial produtiva.

## Recuperação e commits

- S1 `8780b576`, I78 `f8268bc3`, CI `40475205913` SUCCESS conferidos antes de editar.
  Relatórios I77/I78 e checkpoint da frente consultados integralmente.
- PRs #16/#18/#20 recuperados; base desta branch `4775091` do PR #20.
- `e634a26347c9239a524e87a8b1a5b729039a4563`: primeira implementação I79.
- `bf2021f757dcdba9763c48b176e27e7bc3c41862`: diagnóstico SQL fixo de bootstrap,
  sem segredo, e provas de Gestor sem subordinados/seletor legado.
- `9eac7337db37b46fa53799af19dd3313728f6c7e`: constraint adiada privada valida sob
  owner fixo; login continua sem EXECUTE dos helpers ou SELECT privado.
- `ab96b5d2d2aae293e239b38bccec82c29dd72a15`: revogação durável I61, ordem sem
  espera bloqueante inversa e regressões unitárias S1 pinadas.

## Tentativas anteriores, sem certificado indevido

- CI [40482243885](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40482243885):
  regressões S1 históricas, S0/CFI/F02, histórico e G1 36 passaram. I79 recusou
  bootstrap; zero cenários I79 certificados nessa tentativa.
- CI [40482932356](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40482932356):
  confirmou `42501 permission denied for function s1_i79_validar_profissional`
  no COMMIT diferido. Causa: retorno da função DEFINER restaura login restrito
  antes de avaliar a constraint. Corrigido no contexto da constraint; não se
  concederam privilégios privados ao login para mascarar a falha.
- CI [40483535241](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40483535241):
  59/60 cenários I79/G1 passaram. O último recusou corretamente o Gestor como
  destinatário Consultor, mas a asserção esperava `DENIED` genérico; o resultado
  real foi `DESTINATION_INELIGIBLE`. Corrigida a expectativa para esse resultado
  explícito, sem mudar a autorização. A execução inteira permanece FAILURE.

## Cobertura e interpretação

**Execução final: [40484344324](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40484344324)
SUCCESS**, código `ab96b5d2d2aae293e239b38bccec82c29dd72a15`. Jobs
`122122262229` (integração real) e `122122262376` (S1 histórico), ambos SUCCESS.
Início `2026-10-27T09:54:20Z`, término `09:58:29Z`, 249 segundos; stacks removidas.

| Camada | Resultado |
| --- | --- |
| Unitários S0/F02/G1/I79 | 280/280, sendo 8 novos I79 |
| Unitários S1 originais | 179/179 + 6 I75B + 8 I75C |
| G1 anterior ao delta | 36/36 GoTrue/PG/PostgREST |
| Perfil I79 depois do delta | 62/62 = 36 G1 herdados + 26 novos |
| CFI/F02 preservados | 56/56 reais |
| Histórico S0 e S1/I63 | 19/19 + 19/19 reais |
| SQL I54/I56/I57/I58/I61 | 34/34, identidades sintéticas |
| S1 PG17 histórico | regressão I54–I74, I78 8/8, I46/I48/I75B/I75C PASS |
| Conexões/cleanup | sem ResourceWarning; descarte confirmado |

Hashes dos executáveis, nomes dos cenários e marcadores de prova estão em
[evidencias.json](evidencias.json). O próximo commit só acrescenta documentação,
sem alterar o código executado nessa CI.

G1 é executado antes do delta I79 para preservar o checkpoint legado e novamente
depois dele com as mesmas 36 asserções. No segundo perfil, os profissionais são
cadastrados/ativados pela porta autenticada do Diretor; a mudança temporária de
equipe usa transferência CAS real, sem deixar/reabrir vínculo órfão.

Os 26 cenários I79 (40–65) cobrem Diretor real; Gestor sem competência; cadastro
pendente; ativação órfã proibida; Gestor sem subordinados; dupla chefia; comandos
concorrentes e stale CAS; chave repetida; logout/expiração; revogação antes/depois
de espera; preservação de intake pausado, caso e grants; mudança de supervisão
com JWT existente e PostgREST; rollback parcial/COMMIT adiado e fechamento de
conexão; MAC/nonce; resposta corrompida; legado sem cargo; ACL; seleção I54;
assunção pessoal do Gestor sem subordinados; não reativação I61; conflito físico
com lock de exceção e retentativa.

As regressões históricas I54–I78 são executadas no checkout S1 fixado, antes da
nova semântica de ativação. O teste I78 que demonstra órfão é corretamente
preservado como evidência da lacuna antiga, não reinterpretado como aceite do
novo comportamento. Depois do delta, a prova I79-41 verifica o oposto: não pode
confirmar Consultor classificado ativo sem chefia.

Não se somam 36 G1 herdados duas vezes como testes novos. Aceites SQL antigos
com identidade sintética não são apresentados como testes GoTrue. Os tempos,
nomes e resultados da execução final estarão no JSON de evidências.

## Pendências sem falsa decisão comercial

Reprodução: seguir `.github/workflows/exp-s0-s1-i79-professionals.yml` em checkout
próprio e stack **nova, desvinculada**, CLI 2.84.2, PG17, psycopg 3.2.9. Depois
do bootstrap S0, histórico/CFI/F02 e fonte S1 fixada, o workflow aplica o delta G1,
roda os cinco aceites SQL e os 36 G1 originais; então executa, com os opt-ins já
definidos pelo workflow:

```bash
PYTHONPATH=. python3 integration/i79/install_local.py
PYTHONPATH=. python3 integration/i79/test_professionals.py
```

O perfil I79 cria usuários no GoTrue descartável e inicializa a competência do
Diretor no banco de teste; depois usa a porta assinada para admitir os demais.
Esse bootstrap não é uma rota cliente nem procedimento de produção. Ao terminar,
usar o cleanup `supabase stop --no-backup`, como no workflow. Não copiar chaves,
senhas, dados da fixture ou SQL para o Supabase hospedado.

- **Técnicas S0/S1:** regularização administrativa do legado sem inferência,
  serviço HTTP/autenticação na borda, fluxo de identidade/convite, provisionamento
  com owner restrito e evolução completa de desligamento/chefia.
- **Consumidores:** contrato API/UI de administração e UX de conflito, revogação
  e continuidade dos casos cuja exceção perdeu validade. Não reabrir D1/A2.
- **Produto/outros gates:** mídia/D3/D4/retencão; prova física de primeiro contato
  humano e entrega; conclusão/F03 e homologação multiloja. Não criar status
  comercial, autorização de envio, agenda, Banco ou Meta para completar um teste.

Próximo avanço sob o mesmo responsável S0/S1: comando de regularização de cargo
e chefia dos registros legados, com prévia de impacto e CAS, preservando acervo;
depois contrato de borda administrativa com Frontend. G1/G2/G3 permanecem parciais
como operação, e G4–G6 não são liberados por esta certificação de laboratório.

Nenhuma escrita na branch original S1, S0 oficial, main, Frontend, F02/F03 ou Meta.
Sem merge, deploy ou migration hospedada. A antiga conversa S1 não precisa
implementar adaptação técnica desta integração: a responsabilidade já foi
transferida ao Codex principal pelo responsável.
