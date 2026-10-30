# OPS-02 — contrato offline de declarações sintéticas, versão 1

30/10/2026, America/Sao_Paulo. Autorização: missão S0S1-OPS-02 do responsável,
restrita aos oito arquivos enumerados. Não homologa administração humana real.

## Checkpoint e independência

Base imutável: a0c4eaf2720bd6cf2bd756544498f8f185f005fc; árvore
977c4ed302b9dd14e459575abbbc718eaa8ca920; branch anterior
exp/s1-i86-manual-director-20261028. Certificação técnico-laboratorial I86/CM-01:
https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41087043183

A orquestração ratificou LAB_CLOSED exclusivamente nesse alcance após auditoria
dos quatro ZIPs, 22 casos do observador, 31 manuais, jornada I85 e três descartes.
Documentos anteriores LAB_BLOCKED continuam snapshots históricos intactos.
OPS-02 não reabre CM-01 nem afirma equivalência com árvores privadas anteriores.

Branch exclusiva: exp/s0-s1-ops02-evidence-contract-20261030, um commit atômico
imediatamente após a base. O checker I86 não foi ampliado para esta branch.

## Semântica de saída

O único sucesso é FORMALLY_VALID_UNTRUSTED. Falhas: INVALID_UNTRUSTED com
errors.code e errors.location. Sempre authorizes_action=false, commit_proven=false,
human_identity_verified=false, organizational_authorization_verified=false,
origin_authenticated=false e referenced_evidence_bytes_verified=false.

Sucesso significa estrutura, digest do documento e correspondência no conjunto
fornecido. Não comprova pessoa, autorização, origem, custódia, evidência externa,
estado real, horário ou COMMIT. Qualquer consumidor futuro deve preservar isso.
Não existe token, comando ou ramo positivo que execute operações administrativas.
O próprio processo não solicita nem aceita credenciais como campos do contrato.

## Objetos distintos

O formato normativo legível por máquina é ops/s0s1_authority/contract_v1.json.
O verificador compila a mesma gramática; teste compara seus campos e constantes.
Importá-lo não lê implicitamente o contrato nem outros arquivos.

INTENTION declara um ato ainda não executado: version, kind, data_classification,
authorizes_action, act_id, action, target_id, environment, cas, operator_ref,
authorization_ref, evidence e digest. action é APPOINT, REVOKE ou REACTIVATE.
act_id e target_id são UUIDs canônicos minúsculos não nulos RFC4122.
Não há nome, CPF, email, JWT, token, senha, SQL ou texto pessoal livre.

environment contém somente kind=SYNTHETIC_OFFLINE e id sintético. cas contém
scheme=i86.snapshot.sha256 e observed_sha256. Este CAS é uma declaração opaca:
não consulta o SQL I86, não verifica frescor, não concede competência.
operator_ref e authorization_ref são referências declaradas, sem autenticação.
evidence contém ref e sha256. Somente sintaxe desses dois campos é conferida;
o arquivo da evidência não é procurado, aberto ou autenticado implicitamente.

RECEIPT tem os campos comuns e intention_digest, attempt_id UUID, state,
commit_claim, posterior_evidence e digest. Não repete operador nem autorização.
Vincula act_id, ação, alvo, ambiente, CAS e digest da intenção presente na mesma
invocação. posterior_evidence usa o mesmo formato ref/sha256 e os mesmos limites.
Recibo é logicamente posterior à intenção, sem certificar ordem temporal real.

| state declarado | commit_claim permitido | Significado limitado |
| --- | --- | --- |
| INTENTION_RECORDED | NOT_CLAIMED | Registro declarado da intenção |
| PROVISIONAL_RESULT | UNPROVEN | Resultado provisório declarado |
| COMMIT_NOT_PROVEN | UNPROVEN | COMMIT não comprovado |
| RECONCILED_DECLARED | DECLARED_COMMITTED | Alegação de conciliação; COMMIT continua não comprovado pelo verificador |
| FAILURE | UNPROVEN ou DECLARED_NOT_COMMITTED | Falha alegada, sem inferência adicional |
| CONFLICT | DECLARED_NOT_COMMITTED | Conflito alegado |

Não existe estado COMMIT_PROVEN. Campos human_verified, approved, commit_confirmed,
signature ou execute são desconhecidos e recusados. Mesmo um recibo coerente
alegando conciliação nunca muda os indicadores de confiança da saída.

Conjunto: 1–32 documentos, pelo menos uma intenção. Recibos isolados são recusados.
Duplicatas idênticas são aceitas sem efeito; mesmo act_id com intenções diferentes
ou mesmo attempt_id com recibos diferentes conflitam. Nova observação exige outro
attempt_id. Não há armazenamento, memória entre execuções ou avaliação de ordem
entre tentativas distintas; não é idempotência transacional nem ledger operacional.

## Exemplo fictício completo: dois arquivos separados

intention.json (nenhum UUID ou referência representa pessoa real):

```json
{
  "version": "prumo.s0s1.authority.evidence.v1",
  "kind": "INTENTION",
  "data_classification": "SYNTHETIC",
  "authorizes_action": false,
  "act_id": "10000000-0000-4000-8000-000000000001",
  "action": "APPOINT",
  "target_id": "20000000-0000-4000-8000-000000000001",
  "environment": {"kind": "SYNTHETIC_OFFLINE", "id": "synthetic:lab-01"},
  "cas": {"scheme": "i86.snapshot.sha256", "observed_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
  "operator_ref": "synthetic:operator-01",
  "authorization_ref": "synthetic:record-01",
  "evidence": {"ref": "synthetic:intent-01", "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
  "digest": "807eef6bf57db70a021462b5a05f1bc27c1b1e0c4639baaf9e0557171ca05583"
}
```

receipt.json (alegação posterior de resultado incerto, sem execução):

```json
{
  "version": "prumo.s0s1.authority.evidence.v1",
  "kind": "RECEIPT",
  "data_classification": "SYNTHETIC",
  "authorizes_action": false,
  "act_id": "10000000-0000-4000-8000-000000000001",
  "action": "APPOINT",
  "target_id": "20000000-0000-4000-8000-000000000001",
  "environment": {"kind": "SYNTHETIC_OFFLINE", "id": "synthetic:lab-01"},
  "cas": {"scheme": "i86.snapshot.sha256", "observed_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
  "intention_digest": "807eef6bf57db70a021462b5a05f1bc27c1b1e0c4639baaf9e0557171ca05583",
  "attempt_id": "30000000-0000-4000-8000-000000000001",
  "state": "COMMIT_NOT_PROVEN",
  "commit_claim": "UNPROVEN",
  "posterior_evidence": {"ref": "synthetic:receipt-01", "sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"},
  "digest": "4299f1dbbab24d0f7497773753ec2bb8e41334233a96439bf435c75d57f6c88c"
}
```

## Bytes e integridade

Entrada JSON UTF-8 estrito, sem BOM, chaves duplicadas, NaN, números, arrays ou null.
Apenas objetos, strings e booleanos, sujeitos à gramática exata. Campos desconhecidos
são recusados em todos os níveis. Não há coerção de tipo, preenchimento ou trim.
Versão única: prumo.s0s1.authority.evidence.v1; versões futuras são recusadas.

1. Remover somente a chave digest no nível superior, sem modificar o objeto original.
2. Serializar como Python json.dumps(payload, sort_keys=True, separators=(',', ':'),
   ensure_ascii=True, allow_nan=False), UTF-8, sem quebra de linha.
3. Antepor UTF8(version + NUL + kind + NUL), separando os domínios INTENTION/RECEIPT.
4. SHA-256 dos bytes concatenados, em 64 caracteres hexadecimais minúsculos.

O digest é de integridade formal, não assinatura nem prova de autoria. Adversário
capaz de reescrever documento e digest pode criar outra declaração formalmente válida.
Intenção não referencia recibo; recibo referencia digest já calculado da intenção.
Cada objeto exclui somente o próprio digest, evitando ciclo de autorreferência.

declared_at é o único campo opcional: YYYY-MM-DDTHH:MM:SSZ, calendário válido.
Se ausente permanece ausente; se presente integra o digest; null é recusado.
Não impõe prazo, expiração, mandato ou horário confiável.

Referências: synthetic:[a-z0-9][a-z0-9_-]{0,63}. A etiqueta SYNTHETIC é obrigatória.
Isso reduz a superfície de dados, mas não descobre se alguém ocultou dados reais
num identificador aparentemente sintético. Quem prepara entradas deve usar somente
ficção. Não enviar documentos reais ao verificador desta missão.

## Limites de leitura e capacidades

Linux/POSIX, Python 3.12 na CI, biblioteca padrão. CLI estrita:
python3 -B -m ops.s0s1_authority.validate --input-root /diretorio/absoluto arquivo.json

Somente caminhos relativos .json explicitamente fornecidos, até 256 caracteres e
8 componentes; componentes ASCII seguros de até 128 caracteres. Root absoluto,
até 4096 caracteres, sem barra final, raiz /, componentes vazios, ponto ou traversal.
Sem symlink em root, pais ou arquivo; percurso por descritores O_NOFOLLOW,
O_DIRECTORY, O_CLOEXEC. Arquivos regulares de link único, sem FIFO, dispositivo,
socket, diretório, glob ou busca recursiva. Máximo 64 KiB/documento, 1 MiB/conjunto,
profundidade JSON 8. Alteração observável durante leitura é recusada; o digest
conferido continua sendo dos bytes efetivamente lidos, sem autenticar o armazenamento.

Não lê arquivos apontados por ref; não acessa rede, banco, SDK, shell, subprocesso,
usuários, papéis ou credenciais; não escreve documentos. Saída JSON em stdout,
exit 0 somente formalmente válido, exit 2 para falhas tratadas. Não reflete conteúdos
de entrada nos erros. Falha fatal de processo/SO não é sucesso nem autorização.

## D01–D05 e proteção herdada

Somente humano nominal autorizado poderá futuramente administrar Diretores.
Diretores comuns, Gestores, Consultores, IA, MCP, automações e Edge ordinárias
não recebem essa capacidade. JWT, metadata, cargo ou service_role não a inferem.
D01 identidade/custódia, D02 origem/preservação da evidência, D03 continuidade manual,
D04 recuperação humana sem rebootstrap e D05 resposta a incidentes permanecem
pendentes nos aspectos operacionais listados em DECISOES_E_TESTES.json.

Não se escolhem pessoas, provedor, segundo aprovador, quórum, prazo ou limite de
Diretores. Não há sucessão automática, recuperação automática ou reutilização I85.
Revogação existente de competência e sessões continua intocada. Nenhuma alteração
de SQL, bootstrap, Auth, backend, Frontend, OpenAI ou Meta é necessária/permitida.

O gate OPS-02 compara base/árvore/branch, oito adições regulares 100644, índice,
bytes locais, arquivos ignorados, cada commit intermediário e história de um commit.
--candidate só aceita as oito adições pendentes quando HEAD ainda é a base; não
certifica conteúdo não confirmado. Certificação padrão exige commit e worktree limpo.
Assume-unchanged/skip-worktree não escondem alterações, pois os bytes são conferidos.
O checker novo não é âncora independente: inventário externo do delta, modos, blobs,
SHA-256 e comparação do restante da árvore são obrigatórios na revisão/CI.

Próxima etapa possível: decisão humana de D01/D02 e especificação de um canal
administrativo nominal, sob nova autorização. OPS-02 não a inicia nem homologa.
