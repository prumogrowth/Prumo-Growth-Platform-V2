# S1-002/I26 — GoTrue revalidado independentemente pelo assinador HMAC (20/10/2026)

**Estado: protótipo local candidato, sem produção.** Somente `feat/s1-002-equipe-prumo`, PR #5 Draft; não alterar Supabase hospedado, nem fazer deploy/merge/produzir chaves reais.

## Problema e fronteira de confiança

I25 demonstrou **40/40 testes unitários e 60/60 cenários E2E** de processo assinador em `multiprocessing` isolado logicamente da borda HTTP. O processo assinava qualquer material que estivesse estruturalmente correto e dentro da janela temporal, mesmo sem autenticar independentemente o usuário. Um atacante com a pipe de SIGN e credencial SQL de conexão poderia forjar claims GoTrue (ator/sessão) e executar um comando como gestor. O gateway externo validava GoTrue, mas o **assinador não possuía uma prova própria**.

I26 é a contramedida de laboratório: **o processo que possui a chave faz uma nova chamada própria a GoTrue** com o Bearer, recusa assinaturas com identidade ou sessão divergente e nunca fornece HMAC para chamadas sem token. A função PostgreSQL I22 continua revalidando `auth.sessions` a partir das claims assinadas e exige nonce exclusivo; os grants gerenciais I14 continuam aplicados.

## Implementação, compatibilidade e prova

- `backend/s1_signer_process_local.py`: `LocalSignerSupervisor(independent_auth_url=API_URL, publishable_key=ANON_KEY)` inicia worker `spawn` com `SupabaseGoTrueVerifier` próprio configurado para **URL loopback exclusivamente**. Nesse modo, o IPC de operações exige `SIGN` com quatro elementos: comando, key ID, material canônico, Bearer. Qualquer formato anterior sem token é negado. O validador consulta `GET /auth/v1/user` em GoTrue, extrai identificador e session ID ligado ao JWT validado e confronta exatamente com o material HMAC. O segredo continua no filho, fornecido pelo canal separado de controle do runner. 
- `backend/s1_signer_independent_gotrue_local.py`: `LocalIndependentlyAuthenticatedGateway` confere GoTrue no gateway, constrói somente argumentos autorizados e solicita segunda validação dentro do assinador. A assinatura resultante vincula operação, ator, sessão, destino, motivo, timestamp e nonce à prova no banco. O objeto gateway não tem o segredo nem canal de controle.
- Se GoTrue do filho ficar indisponível, o IPC devolve `UNAVAILABLE` e a borda HTTP falha fechada (503). Se token não corresponder ao ator/sessão no material, o IPC recusa assinatura; não informa segredo ou token ao cliente. O timeout de IPC foi elevado apenas nesse modo para contemplar a consulta GoTrue; o processo é encerrado em timeout para impedir que uma resposta tardia seja confundida com outra requisição.
- O caminho legado I25 `LocalSignerSupervisor()` sem GoTrue permanece para regressão histórica, não sendo autorizado para operação real. Novos consumidores devem usar **somente o modo I26**, sem fallback automático.
[TRECHO COMERCIAL INTERNO EXCLUÍDO DA VERSÃO PÚBLICA]

## Cenários planejados

O job unitário repete 30 testes HTTP e 10 testes I25, somados a 10 testes novos I26 com autoridade GoTrue sintética HTTP apenas no loopback: token válido, token ausente/malformado, ator falso, sessão falsa, timestamp vencido, isolamento de processo novo, configuração da autoridade insegura, indisponibilidade da autoridade e gateway exigindo Bearer. **O servidor sintético não verifica criptografia JWT**: esta validação é ensaio do contrato de integração, não evidência de segurança de GoTrue.

O job E2E `scripts/test_s1_002_i26_dual_gotrue_local.py` reaplica 50 migrations reais S0/S1 e as fixtures locais I20–I24, mantém os 60 cenários I25 com GoTrue real e adiciona S1AUTH-61..70: provisionamento da chave separada, operação legítima com GoTrue duplo, recusa de uso do canal SIGN sem token, token falso, ator inventado, sessão inventada, token legítimo de outra pessoa, token legítimo da outra equipe negado por RBAC S1, GoTrue do filho indisponível e queda do assinador preservando o domínio.

## Limites e NO-GO

**Esta implementação não protege contra um atacante que rouba um Bearer válido de gerente e detém acesso ao canal de assinatura e à credencial SQL**; ele ainda poderá usar a sessão legítima até sua revogação, respeitadas as verificações do banco. O GoTrue do assinador e do gateway compartilham a mesma infraestrutura de autoridade e o mesmo usuário Unix do runner; portanto não são dois fatores criptográficos nem duas entidades operacionais isoladas. Um atacante que comprometa o sistema operacional pode alcançar chaves/descritores/controle. Não foram implementados mTLS entre workloads, identidade própria de serviço, OAuth client audience/DPoP, enclaves/HSM/KMS/Vault, replay de requisição na camada de assinatura, auditoria inviolável ou implantação segura.

**NO-GO para produção e merge.** Continuam como gates: isolamento da identidade e do runtime do assinador em infraestrutura independente, autenticação mútua da workload, custódia externa, TLS/controle de origem, auditoria operacional, procedimentos de chave comprometida e integração com UI e conclusão humana S0.

## Resultado inspecionado e aceito apenas no CI

**[GitHub Actions #39362965397 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39362965397)**, SHA testado `590cf7ca8444b047b3c28315ce1bf51bf07fe6b3`. Os dois jobs encerraram em sucesso:

- `http-policy-unit` (job `118433150113`): **50/50 unittest PASS**. Logs confirmam três saídas separadas: `Ran 30 tests ... OK` (HTTP I23), `Ran 10 tests ... OK` (processo I25), `Ran 10 tests ... OK` (GoTrue independente I26, mock local).
- `e2e-gerencia-local` (job `118433150420`): **70/70 identificadores S1AUTH-01..70 PASS**, sem duplicação. Aplicadas **50 migrations reais S0/S1** em GoTrue/PostgreSQL descartáveis e fixtures de teste I20–I24. I26-61..70 foram confirmados em logs de operações GoTrue reais, prova HMAC, anti-forja de sub/sessão e negação RBAC, indisponibilidade de autoridade e pane do assinador.

Também foi verificada a regressão I25 histórica depois da alteração do modo de assinador: [GitHub Actions #39362715347 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39362715347). Esse fluxo mantém o modo anterior exclusivamente para preservar os testes, sem fallback automático a partir de I26.

**Parecer restrito: GO para continuar o desenvolvimento isolado. NO-GO produção, merge ou deploy.** Os testes de IPC com pipe e o login SQL de teste em conjunto demonstram limites dos contratos, mas **não representam um teste de penetração de infraestrutura nem segurança contra o roubo simultâneo de token válido, IPC ou identidade OS**. A custódia e o canal continuam no mesmo runner.

**Integridade de evidência:** as atualizações de `docs/` e `tests/S1_ACEITE.md` são posteriores ao SHA de código efetivamente testado, sem mudanças no caminho de execução aprovado.
