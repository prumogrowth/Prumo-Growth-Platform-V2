# S0/S1 — checkpoint I84 — operação local da borda

27/10/2026, America/Sao_Paulo. Continuidade I83, sem reiniciar I79–I83.

- PR Draft #40: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/40
- Branch própria: `exp/s0-s1-i84-operacao-edge-local-20261027`.
- Base preservada PR #38: código `462b23a78618eb98f6f986dd2ff8e81c15bd4ce8`,
  checkpoint `df7ea64ea9490f70f553f5a02149dbfe96aacf76`.
- S1 original permanece em `8780b576aa18bd3983c063339e2e42d2452af22c`.
- Código certificado I84: `6852a4f509df8466e35da46ba995a4ac2ed5e1f7`.
- [CI40622136488 SUCCESS](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40622136488): quatro jobs aprovados.
- Jornada real com 16 pontos em 121,974s; 9 testes físicos/diagnósticos, também -O.
- I82 20/20; I83 35/35 (20 HTTP + 15 credenciais); I79/G1 62/62, I80 33/33, I81 14/14, regressões S1 nativas I54–I78 e CFI/histórico preservadas.
- Artefato operacional 12788177118; catálogo pós-prepare = final, network_loopback=true, material_removed/resources_absent/retirement_verified=true na stack completa e zero matches de material.
- Owners NOLOGIN preservados; app sem DML privado/Auth, SET de owners ou novos grants comerciais.
- Revisões intermediárias e suas CIs aprovadas estão no relatório.

## Estado funcional

`python3 -m local_admin` inicializa stack descartável própria, verifica fontes e
instala as dependências existentes sem executar testes ou criar humanos. Usa o
provisionador I83, o login/cofre dedicados e a Edge TypeScript/Deno I82. Oferece
status sem segredos, rotação/reinício, revogação, retirada de worker, recuperação
conservadora de pós-COMMIT e descarte com comprovação de recursos ausentes.

Rede Docker própria tem publicação somente loopback, com verificação física
dos bindings DB/Kong: não se presume isolamento a partir de API_URL. Nenhuma
mudança no daemon global, SQL comercial, owner ou grant para facilitar a borda.
Cargos, competência do Diretor, GoTrue, RLS, HMAC/nonce, CAS, idempotência,
auditoria e constraints diferidas I79/I80/I81 preservados.

## Retomada operacional

Ler primeiro [operação local](contratos/i84_operacao/OPERACAO_LOCAL_V1.md) e
[relatório/evidências](contratos/i84_operacao/RELATORIO_E_EVIDENCIAS.md).

```sh
export PRUMO_I84_DISPOSABLE=YES
python3 -m local_admin init
python3 -m local_admin prepare --s1-source /caminho/s1-no-commit-8780b576
python3 -m local_admin provision
python3 -m local_admin serve
python3 -m local_admin status
python3 -m local_admin rotate
python3 -m local_admin revoke
python3 -m local_admin worker-stop
python3 -m local_admin down
```

`recover` somente revoga e retira material incerto. Não repetir emissão ou
comando de negócio automaticamente. Uma resposta administrativa perdida deve
ser reconciliada pela mesma chave I82. `restart` exige credencial válida;
rotação tem indisponibilidade. Não iniciar o harness contra a stack do operador.

## Gates que permanecem

Exclusivamente laboratório Linux/Docker confiável. Identidade de recurso ou
configuração não comprovada bloqueia recuperação automática, sem adoção/remoção
de stack de terceiros. Escopo de falhas físicas e pontos não homologados consta
no relatório; não há promessa de crash recovery universal ou apagamento forense.

Bootstrap Auth/Diretor, revisão Frontend prumo.admin.v1, TLS, custódia produtiva,
abuso distribuído, homologação e rollout permanecem separados. Nenhum usuário
real, Supabase hospedado, merge, deploy ou chamada comercial. F02 G01–G06
parciais/G07 pendente; sem nova auditoria ou autorização de revisão comercial.

Próximo avanço: procedimento local explícito de bootstrap/recuperação Auth e
Diretor, respeitando o contrato vigente e decisões administrativas necessárias,
e revisão do consumo HTTP pelo Frontend. Retomar do HEAD documental deste PR,
conferindo avanços posteriores antes de implementar.
