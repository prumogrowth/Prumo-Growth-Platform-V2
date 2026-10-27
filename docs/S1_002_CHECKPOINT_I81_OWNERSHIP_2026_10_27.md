# S0/S1 — checkpoint I81, ownership administrativo restrito

27/10/2026, America/Sao_Paulo. Continuidade do PR Draft #30/I80, sem reinício.

- Branch: `exp/s0-s1-i81-ownership-administrativo-20261027`.
- [PR Draft #32](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/32), base exata I80 `cfeca5f39d9744340f5f362c2f65a4b201e2d5f5`.
- Código certificado: `4ba266d04b47fcb8036352970456d0dd5b2d09a7`.
- Tree do código: `e3865ca4a5fb8fc76d43c0fb98b20a737854a049`.
- [CI 40543117528 SUCCESS](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40543117528), ambos os jobs SUCCESS.
- Checkpoint documental: commit que contém este arquivo; não muda executáveis.
- S1 original `8780b576`, I79 `8068db1` e I80 preservados.

## O que funciona no laboratório

I79 REGISTER/ACTIVATE/TRANSFER e I80 INVENTORY/PREVIEW/APPLY executam com owner
administrativo NOLOGIN/NOBYPASSRLS. A constraint profissional diferida usa outro
owner de leitura/locks. A aplicação não assume esses owners nem ganha DML privado.
A prévia I80 anterior à troca permanece válida. Diretor GoTrue, sessão viva,
HMAC/nonce, CAS/idempotência, concorrência e auditoria continuam os certificados.

I46 mantém negação de DML direto com whitelist apenas do owner inacessível;
I57/I61, triggers, constraints e RLS preservados. Auth fica nos helpers mínimos
privados, não em grants de credencial/dados Auth ao domínio. Não se cria caso,
atribuição, nova exceção, grant de loja ou alteração de intake pela regularização.

PG17 mantém membership ADMIN-only de instalação para postgres, concedida por
supabase_admin: INHERIT=false/SET=false. SET temporário da troca foi revogado;
nenhum login de aplicação recebeu SET/INHERIT do domínio ou do validador.

## Evidências

**21 novos cenários**: 6 instalação/rollback, 1 cutover e 14 probes/fluxos reais.
Após troca: I79/G1 **62/62** e I80 **33/33**. CFI captura/recheck real integrado
à admissão restrita; outra identidade e revogação recusadas. Baseline unitário
288/288, S1 193/193, CFI/F02 56/56, histórico 38/38 e SQL canônico 34/34.
Não somar repetições como testes novos nem confundir I78 original com I79.

Catálogo: funções 105→106; triggers **57** e constraints **418** preservados;
policies 108→145 exclusivas dos owners. **After = final**, sem resíduo de probes,
novos privilégios para consumidores, mudança de owner de tabela ou flags RLS.

- [Contrato técnico v1](contratos/i81_ownership/CONTRATO_OWNERSHIP_V1.md).
- [Relatório, arquivos, reprodução, tentativas e limites](contratos/i81_ownership/RELATORIO_E_EVIDENCIAS.md).
- [Evidências, ACL antes/depois, testes e hashes](contratos/i81_ownership/evidencias.json).

## Bloqueios e próxima execução

Ownership administrativo demonstrado somente em PG17/GoTrue/PostgREST
**descartáveis**. G2 operacional continua parcial: faltam borda/API/UI,
provisionamento/homologação, custódia/rotação/retenção e rollout autorizado.
Outros owners postgres de casos/G1/I54/I55/I62 não foram generalizados para o
domínio; helpers Auth privados mínimos continuam postgres-owned. DDL futuro nas
tabelas metadata-only exige revisão de ACL (o guard de formato é de instalação).

Decisões administrativas de cargo/chefia e conflitos legados continuam com o
Diretor. F02 G01–G06 parciais/G07 pendente, sem repetir auditoria ou H01; nenhuma
ratificação comercial. Contratos UI/comerciais pendentes não são promovidos.

**Próxima execução segura:** preparar a borda administrativa em Edge Functions
local, reutilizando contratos I79/I80 e autenticação GoTrue, com nova prova física
da fronteira e de custódia. Não hospedar, migrar produção ou chamar APIs
comerciais. ADR backend Supabase + servidor→OpenAI respeitada.

Nenhum merge, deploy, Supabase hospedado, credencial/cliente real ou alteração
de branch de outra frente. Issue #23 permanece aberta como coordenação de G2.
