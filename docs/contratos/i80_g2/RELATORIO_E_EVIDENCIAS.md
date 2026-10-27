# I80/G2 — entrega experimental de regularização do legado

27/10/2026, America/Sao_Paulo. Continuação do PR #26, não reconstrução da I79.
Contrato: [CONTRATO_REGULARIZACAO_V1.md](CONTRATO_REGULARIZACAO_V1.md).

## Implementado e reaproveitado

- Inventário administrativo paginado e minimizado, sob Diretor GoTrue real.
- Proposta explícita de cargo/chefia, prévia persistida e imutável com impacto,
  validade e contexto autoritativo; nenhuma aplicação implícita de READY.
- APPLY separado, CAS de estado/autoridade, idempotência, concorrência e auditoria.
- Regularização possível sem ativar pendentes, mudar estado, transferir casos,
  alterar histórico, intake ou concessões. Chefia obrigatória segue I79.
- Preservação de exceção I61 válida quando a chefia não muda; revogação durável
  de exceções incompatíveis ou ligadas à chefia substituída, conforme a prévia.
- Negativas para ambiguidade, dados incompletos, cargo já classificado, chefia
  incompatível, sessão/competência revogada, snapshot obsoleto e perfil incompleto.

Reuso físico: identidade/verificador/DSN/chave/nonce S0, construção da porta I79,
equipe/cargo/chefia existentes, constraints I79, barreira de atribuição S0, fila
I54/G1 e auditoria I61. Os arquivos executáveis I54–I79 permanecem byte a byte;
o workflow novo executa suas regressões antes de instalar o delta I80.

## Arquivos e checkpoints

| Arquivo novo | Finalidade |
| --- | --- |
| `backend/s1_legacy_regularization_local.py` | DTOs estritos, transporte autenticado e validação precommit; Python de laboratório |
| `supabase/tests/s1_i80_regularizacao_local_only.sql` | inventário, snapshot/contexto, plano, locks, prévias/recibos/auditoria privados e aplicação SQL |
| `integration/i80/install_local.py` | opt-in e fronteira loopback descartável existentes |
| `integration/i80/test_regularization.py` | 33 provas reais reaproveitando fixtures e portas I79/G1 |
| `backend/tests/test_s1_legacy_regularization_contract.py` | oito testes de compatibilidade/recusa |
| `.github/workflows/exp-s0-s1-i80-regularization.yml` | integração real completa + regressão histórica S1 separada |

Branch: `exp/s0-s1-i80-regularizacao-legado-20261027`, baseada exatamente em
`8068db1c42216fb1da6855401146eab257f3eff1`. Original S1 rechecado em `8780b576`,
sem avanço antes de implementar. CI da base I79 `40484344324` SUCCESS confirmada.
Nenhuma branch original foi modificada.

- `fbd40e9b34680369891dccb2d2c5dabdd248a15b`: inventário/prévia/aplicação, 32
  provas iniciais e oito unitários novos.
- `1daa307f6f831323e4da4b72d288c76d44c73230`: código certificado final; contexto
  vinculado às versões da competência do Diretor, pré-lock dos pares usados
  pelo validador I79 e impacto explícito da barreira técnica de intake.

## CI e resultados verificáveis

[Run 40497534544](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40497534544)
**SUCCESS**, commit executado `1daa307f6f831323e4da4b72d288c76d44c73230`.
Job integrado `122166665473` e job histórico `122166665913`, ambos SUCCESS.
Início `2026-10-27T11:37:27Z`, término `11:42:16Z`, **289 segundos**. Cleanup
confirmado; sem ResourceWarning. O commit posterior só acrescenta documentação.

| Camada | Resultado e limite |
| --- | --- |
| Unitários S0/F02/G1/I79/I80 | 288/288; oito novos I80 |
| Unitários S1 | 179/179 originais + 6 I75B + 8 I75C |
| Perfil I80 após delta | **33/33**, GoTrue/PG17/PostgREST reais |
| Perfil I79 preservado | **62/62**, incluindo seus 36 G1 herdados |
| G1 anterior ao delta I79 | 36/36, sem contar como testes novos |
| CFI/F02 e histórico | 56/56 + 19/19 S0 + 19/19 I63, reais |
| SQL I54/I56/I57/I58/I61 | 34/34, sujeitos sintéticos, separados dos GoTrue |
| S1 histórico PG17 | regressões I54–I74, I78 8/8 e I46/I48/I75B/I75C PASS |

Nomes, tempos, marcadores e SHA-256 dos seis executáveis estão em
[evidencias.json](evidencias.json). Não há percentual de conclusão de produto
deduzido desses números; I75D/I76 e demais históricos não são apresentados como
novos ensaios operacionais apenas por reutilizar o código certificado.

### Tentativa anterior

[40496658442](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40496658442),
commit `fbd40e9`, terminou FAILURE: 31/32 I80 passaram. O último teste esperava
`check_violation`, mas o guard imutável existente corretamente respondeu
`42501 / CFI01_IMMUTABLE_FACT`. Corrigida a asserção para `InsufficientPrivilege`,
sem alterar o guard, seus grants ou permitir UPDATE. A execução parcial não
certifica a entrega final. O segundo run também inclui a prova nova de revogação
e reconcessão da competência do Diretor.

## O que as provas cobrem

Os cenários usam usuários GoTrue reais, Diretor e Gestores existentes da fixture
I79, duas lojas por caso, SQL login restrito e RLS via PostgREST. Para representar
legado com carteira, o instalador de teste cria profissionais e atribuições
válidos pelas portas I79/G1 e **somente no banco descartável** remove a classificação
de cargo de registros sintéticos. Nenhum FK, trigger, RLS ou guard é desabilitado.
Não se afirma que um acervo real foi inventariado ou migrado.

01–10: inventário/negativa Gestor, prévia sem mutação, preservação byte a byte de
casos/atribuições/mensagens/grants/intake, exceção válida conservada, revogação
sem reativação, órfão sem escolha, vínculo incompatível, pendente e ordem explícita
de classificação Gestor/Consultor.

11–19: stale entre inventário/prévia, ABA, alteração de grant com mesma contagem,
intake pausado sem suspensão, alteração posterior de intake/atribuição/exceção,
logout e vínculo de sessão, revogação de competência.

20–29: mesma chave concorrente, consumo único da prévia, conflito de payload,
lock real ocupado e retry, rollback após cargo/chefia/I61 alterados, COMMIT
adiado, fechamento de conexão, resultado corrompido antes de confirmar, HMAC,
nonce, ACL, prévia vencida e G1 esperando a regularização confirmar.

30–33: Gestor escolhido revogado, ausência de equipe sem cadastro implícito,
funções/tabelas privadas e prévia imutável, competência do Diretor revogada e
reconcedida exigindo outra prévia.

O vencimento usa fixture persistida antiga, inserida pelo instalador confiável,
sem editar a prévia original ou trocar o relógio do servidor. Concorrência usa
conexões e locks PostgreSQL efetivos; não só uma ordenação de mocks.

## Reprodução

Usar o workflow próprio em checkout desta branch e stack nova/desvinculada,
CLI 2.84.2 / PG17 / psycopg 3.2.9. Ele preserva bootstrap, histórico, CFI/F02,
34 hashes S1, aceites SQL, G1 e I79 e só então executa os opt-ins I80:

```bash
PYTHONPATH=. python3 integration/i80/install_local.py
PYTHONPATH=. python3 integration/i80/test_regularization.py
```

O workflow define `PRUMO_I80_DISPOSABLE_TEST=YES` e conserva os opt-ins anteriores.
O instalador recusa ambiente não loopback por `local_env`; o SQL exige PG17,
I79 e opt-in explícito. O cleanup é `supabase stop --no-backup` no job integrado,
e remoção do serviço PG no job histórico. Não levar fixture/chaves/dados ao banco
hospedado nem tratar esses comandos como roteiro de produção.

## Decisões administrativas ainda necessárias

O Diretor deve selecionar cargo e chefia de cada pessoa, revisar a perda de
acesso por exceção indicada na prévia e enviar APPLY explicitamente. Não existe
aprovação em lote por inferência de papel de loja ou subordinados.

Permanecem para decisão/tratamento administrativo: pessoas simultaneamente
subordinadas e propostas como Gestor; Consultor proposto com subordinados;
cadastros sem equipe/Auth; chefias pendentes incompatíveis; perfis incompletos;
continuidade de casos cujo acesso excepcional será revogado. A porta recusa
esses casos quando não pode aplicar sem inventar uma reestruturação.

I80 não resolve criação/convite Auth, mudança arbitrária de cargo conhecido,
promoção a Diretor, suspensão/desligamento ou remoção automática de vínculos.
As decisões D1/A2 continuam vigentes e não precisam ser reaprovadas.

## Produção e próxima execução

G2 segue parcial como operação. A ponte ainda depende do owner técnico postgres
por causa de I46/I57/I61; login de aplicação não recebe esse papel nem DML geral.
Faltam owner de domínio restrito, borda administrativa/API/UI, runtime Edge local
e homologação, custódia/retencão/observabilidade e limites de escala.

Próxima execução recomendada: separar o ownership das operações administrativas
e reconciliar os guards I46/I57/I61 com privilégios mínimos em ambiente
descartável; depois compor a borda administrativa no runtime Edge Functions
local, usando os contratos I79/I80, sem migração hospedada antecipada.

## Coordenação preservada

Auditoria F02 `7c282df` e H01 `559b583` lidos, sem repetir a auditoria ou pedir
outro levantamento. F02 já avançou seu HEAD para `2171d9a`; a ADR foi consultada
nesse commit. Nenhum desses candidatos foi incorporado. G01–G06 ficam parciais,
G07 pendente. I80 não produz intenção/ratificação comercial F02 nem implementa
qualquer dos quatro produtores H01.

Não houve merge, deploy, migração hospedada, chamada comercial/OpenAI/Meta,
credencial real ou alteração nas branches de outras frentes.
