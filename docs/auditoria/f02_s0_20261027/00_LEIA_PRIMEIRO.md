# Auditoria auxiliar de integração F02/S0

27/10/2026, America/Sao_Paulo. Repositório `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`.

**Resultado: G01–G06 parcialmente atendidos; G07 pendente. Nenhum dos sete bloqueios foi removido ou ratificado.** Há código físico descartável aproveitável, além dos testes puros; falta conectar as fontes e formalizar as decisões operacionais.

A evolução mais recente encontrada é a I79/G2 do PR Draft #26, HEAD `8068db1c42216fb1da6855401146eab257f3eff1`, posterior aos PRs #16/#18/#20. Ela entrega cargo/chefia/administração autenticada sobre o mesmo S0/S1, sem implementar ratificação F02 ou lookup de binding. O Codex principal continua responsável conjuntamente por S0/S1 e mantém a prioridade I79/G2.

## Entregas

- [Matriz G01–G07](01_MATRIZ_G01_G07.md), com sete campos por gate e separação laboratório/físico/operação; [JSON](MATRIZ_G01_G07.json).
- [Evidências e lacunas](02_EVIDENCIAS_E_LACUNAS.md), com SHAs, arquivos, CIs e limites; [inventário verificável](EVIDENCIAS.json).
- [Próximas implementações S0](03_PRIORIZACAO_S0.md), sem implementar portas nesta etapa.
- [Encaminhamentos necessários](04_ENCAMINHAMENTOS_PROPOSTOS.md), propostas para revisão do principal, não enviadas a outras frentes.
- [Resposta objetiva à F02](05_RESPOSTA_F02.md).
- [Decisões reservadas](06_DECISOES_RESERVADAS.md).
- [Verificador documental](verificar_auditoria.py) e [resultado local](VERIFICACAO_LOCAL.json).

## Limites da entrega

Branch exclusiva `aux/f02-s0-auditoria-integracao-20261027`, baseada em `main` no SHA `dace737ab7afb7ae3f5a3a6f5cb522e6def8b43a`. A base documental evita incorporar experimentalmente código de qualquer frente. Somente novos arquivos neste diretório; nenhuma alteração nas branches S0/S1/F02/Meta/Frontend. Sem merge, deploy, banco hospedado, credenciais reais, chamadas comerciais ou mensagens a outras frentes.

Foram inspecionados contratos, código crítico, árvores Git e metadados/jobs/logs de CI, com reexecução local de 197 testes puros F02 e verificação de integridade de 102 referências de arquivos coletadas. Os stacks físicos não foram reexecutados nesta auditoria: sua evidência vem dos CIs identificados. Não é auditoria integral linha a linha de todo o inventário, pentest ou homologação operacional.

Antes de executar qualquer proposta, reler os HEADs das frentes. O snapshot de branches e os limites temporais da consulta estão em `EVIDENCIAS.json`; avanço posterior invalida as conclusões afetadas, não autoriza transplantar contratos antigos.

## Reprodução documental

Em clone que já contenha os commits pinados das fontes, sem executar aplicação ou SQL:

```sh
python3 docs/auditoria/f02_s0_20261027/verificar_auditoria.py --git-repo CAMINHO_DO_CLONE
```

Alternativamente, usar `--sources-root CAMINHO_DOS_SNAPSHOTS` com arquivos organizados por `snapshot/path` conforme `EVIDENCIAS.json`. O verificador não busca rede e falha se faltar fonte ou houver drift. A saída prova integridade documental, não autenticação/ratificação operacional. O comando e os nove módulos F02 reexecutados estão em `VERIFICACAO_LOCAL.json`.
