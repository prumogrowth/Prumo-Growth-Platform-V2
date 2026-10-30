# OPS-02 — execução exclusivamente offline e sintética

30/10/2026. Este runbook não nomeia, revoga, reativa ou recupera Diretor.
Não executar SQL I86 de laboratório em Supabase hospedado.

## Pré-condições

Conferir branch exp/s0-s1-ops02-evidence-contract-20261030 e base exata
a0c4eaf2720bd6cf2bd756544498f8f185f005fc, árvore
977c4ed302b9dd14e459575abbbc718eaa8ca920. Usar worktree isolado.
Não alterar checkout/branch CM-01. Não aceitar main como base substituta.

Preparar somente documentos fictícios fora do checkout, em diretório privado
normal sem links. Nunca usar identidades, credenciais, contas ou dados reais.
O contrato é uma gramática candidata; operator_ref não autentica ninguém.

## Validação

1. Preparar intenção segundo contract_v1.json. Não adicionar credenciais, flags de
   aprovação ou campos de execução. CAS e referências são dados sintéticos opacos.
2. Calcular seu digest com a serialização e domínio normativos. É um hash público,
   sem chave, não uma assinatura. O helper document_digest não emite autorização.
3. Se houver recibo candidato, criar outro objeto que vincule o digest da intenção;
   registrar estado declarado e tentativa distinta. Nunca tratar payload como COMMIT.
4. Executar, substituindo o diretório de exemplo por um diretório sintético real:

```sh
python3 -B -m ops.s0s1_authority.validate --input-root /tmp/ops02-synthetic intention.json receipt.json
```

5. Exit 0 e FORMALLY_VALID_UNTRUSTED permitem apenas afirmar validade formal.
   authorizes_action=false e todos os indicadores de confiança permanecem false.
   Exit 2 indica falha tipada. Não executar ato, retry SQL, concessão ou recuperação
   como consequência de qualquer saída. Não há opção CLI para essas capacidades.

A CLI abre só documentos enumerados. Evidências referenciadas não são lidas.
Uma execução não conhece documentos anteriores; duplicidade global continua não
comprovada. Falha ou interrupção não gera recibo, reversão nem alteração de estado.

## Ensaios locais da implementação

Manter PYTHONDONTWRITEBYTECODE=1 ou -B para não criar arquivos ignorados no checkout.
Guardar logs e inventários fora dele. Testes Git criam somente repositórios temporários.

```sh
python3 -B -m integration.s0s1_ops02.scope --candidate
python3 -B -m unittest integration.s0s1_ops02.test_contract -v
python3 -B -O -m unittest integration.s0s1_ops02.test_contract -v
```

Após o único commit atômico, usar o gate sem --candidate. Conferir independentemente
parent, árvore, oito adições, modos 100644, blobs e SHA-256; comparar todos os arquivos
herdados com a base. Reconfirmar remoto antes do push; se a branch existir/avançar
inesperadamente, interromper sem sobrescrever. Nunca force push, merge ou deploy.

## Evidências e parada

Workflow exclusivo exp-s0-s1-ops02-evidence-contract.yml: gate inicial/final,
contrato/caminhos, Git adversarial, capacidades, bateria otimizada e inventário externo.
Logs reais e JSON são artifacts vinculados ao SHA/árvore, sem serviços PG/GoTrue/
Supabase. Upload/download é transporte de CI, não função do verificador offline.
Conferir run, testes, ausência de skips e integridade dos artifacts independentemente.
Sucesso CI não equivale a presença humana nem a LAB_CLOSED sem auditoria posterior.

Parar diante de teste obrigatório falho, arquivo fora dos oito, mudança herdada,
base divergente, necessidade de credenciais/SQL/rede administrativa ou escopo adicional.
Preservar evidências e retornar à orquestração. Indisponibilidade de CI é bloqueio de
evidência; não substituir execução por expectativa. Não iniciar OPS-03.

Rollback futuro: decisão específica e revert normal em nova missão, sem reescrever
histórico. O gate de um commit não aprova automaticamente outro commit de reversão.
O checkpoint CM-01 fica intacto e utilizável independentemente desta branch.
