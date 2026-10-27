# S0/S1 — checkpoint I83 — provisionamento Edge dedicado

Estado: **certificada em laboratório descartável**, CI40595963445 SUCCESS; G2 e operação hospedada permanecem bloqueados/parciais.

## Continuidade

- Base PR Draft #35 / I82: código c8817429184d4fb3d5bef29cb9e99d6f2b970f63,
  checkpoint 3dec252e5711c075781984d899d6c46b66b8ec74, CI40554841552 SUCCESS.
- I79, I80, I81 e S1 original 8780b576aa18bd3983c063339e2e42d2452af22c preservados.
- Branch própria `exp/s0-s1-i83-edge-provisionamento-20261027`, PR Draft #38,
  empilhado somente na I82, sem merge ou incorporação de outro PR experimental.
- Código certificado: 462b23a78618eb98f6f986dd2ff8e81c15bd4ce8.
- CI certificado: [40595963445](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40595963445).

## Implementação

Login `prumo_s1_admin_edge_local`, sem privilégios gerais, com apenas duas portas
SQL administrativas. HMAC independente no cofre privado do novo NOLOGIN
`prumo_s1_edge_custodian_local`. Owners de domínio/validador I81 e executor HMAC
existente preservados. Nenhuma identidade humana é concedida pela credencial.

O nonce e os recibos antigos continuam canônicos. Anchor inativo sem material
real no cadastro antigo mantém FK sem permitir chave Edge em outros domínios.
Validade, substituição atômica, revogação com SHARE até COMMIT e limpeza do segredo
antigo são responsabilidades do provisionador local confiável, nunca do navegador.

Contrato HTTP prumo.admin.v1, seis comandos e identidade GoTrue inalterados.
O perfil dedicado recusa login incorreto e não faz fallback. Python prepara
provisionamento/testes; TypeScript executa a Edge e SQL mantém a autoridade.

## Artefatos

- [Contrato de provisionamento/custódia](contratos/i83_edge/CONTRATO_PROVISIONAMENTO_V1.md).
- [Mapa legível por máquina](contratos/i83_edge/provisionamento_v1.json).
- [Relatório, arquivos, tentativas e reprodução](contratos/i83_edge/RELATORIO_E_EVIDENCIAS.md).
- [Evidências e hashes](contratos/i83_edge/evidencias.json).

## Evidência certificada

Preflight de logging PASS, inclusive erros reais de senha e de CHECK com bytes,
sem valores nos erros/logs e sem alterar limiar de erro ou conceder parâmetro.
Suíte dedicada **35/35**: os 20 HTTP originais I82 e 15 provas de credenciais,
rotação, revogação/concorrência, expiração durante espera e nonce global.
3 recusas de instalação, I79/G1 62/62, I80 33/33, I81 14/14 após delta aprovados.
14 Deno, 1 teste/7 vetores, 288 S0 e 193 S1/catálogo, CFI/F02 56 e demais
regressões anteriores preservados. Repetições por perfil não são testes novos.

Jobs122511819193/122511818765/122512740733 SUCCESS no mesmo commit de código.
Catálogo after=final: 107 funções, 57 triggers; apenas novo cofre, 2 policies e
4 constraints. Owners originais e ACLs de dados preservados, somente duas portas
EXECUTE para o login dedicado. Novo cofre owned pelo custodiante NOLOGIN.
Defaults públicos CONNECT/TEMP inventariados; sem CREATE de schema/DB.

Material zerado no cofre, login NOLOGIN/senha NULL, zero sessões; arquivo/env e
container do worker retirados. Logs reais sem matches de credenciais. Artefatos
12776997229/12776346252, metadados/hashes duráveis em evidencias.json. Nenhum
ResourceWarning; stop --no-backup confirmado. Commit documental posterior não
altera os executáveis certificados.

## Próxima execução segura

Preparar operação local reproduzível fora do
harness: comandos para emitir/rotacionar/revogar credenciais e iniciar/retirar o
worker, reutilizando o provisionador I83, sem exibir material. Conservar o mesmo
contrato HTTP e repetir as provas reais. Revisão do DTO com o Frontend em paralelo,
sem aceitar prévias visuais ou modificar sua branch.

Continuam pendentes custódia/homologação produtivas, TLS, rotação operacional sem
downtime, controle distribuído de abuso, governança DDL ampla, bootstrap/convite
Auth e aceite operacional. Não há implantação, migração hospedada ou clientes reais.

Decisões de cargo/chefia continuam do Diretor, sem inferência e sem novos poderes
de Gestor. F02 G01–G06 parciais/G07 pendente. CFI continua captura/recheck técnicos;
não há venda, agendamento/envio ou ratificação humana comercial nesta entrega.
