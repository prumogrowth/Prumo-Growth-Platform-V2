# S1-002/I25 — recuperação após falha do assinador HMAC isolado (19/10/2026)

**Estado: incremento exclusivamente CI/loopback; aceite somente após logs.** Branch `feat/s1-002-equipe-prumo`, PR #5 Draft. Não há migration operacional, deploy, Supabase hospedado, usuários reais, gateway público ou chaves persistentes.

## Problema

O I24 confirmou **50/50 casos E2E e 30/30 HTTP**, com CAS e revogação auditável dentro de um PostgreSQL descartável. No entanto, o protótipo `LocalSignedTeamGateway` guardava a chave HMAC nos mesmos atributos do objeto que recebia o HTTP. Essa arquitetura dificulta distinguir falhas da borda HTTP, perda do assinador e recuperação. I25 ensaia uma barreira **entre objetos/processos locais**, não uma barreira criptográfica entre domínios de infraestrutura.

## Design do experimento

- `backend/s1_signer_process_local.py`: processo Python filho iniciado por `multiprocessing.get_context('spawn')`, sem listener TCP/HTTP. O processo armazena, somente em memória, um conjunto de chaves HMAC sintéticas com UUIDs; possui duas pipes com descritores diferentes. Uma é para **controle** `LOAD/REVOKE/STOP` somente pelo supervisor do runner; a outra é para `SIGN` no cliente entregue ao gateway. Nenhuma resposta retorna chave, e reatribuição silenciosa do mesmo ID é negada.
- `LocalSeparatedSignerGateway`: valida formato do comando antes de chamar GoTrue, consulta o GoTrue de confiança para a identidade/sessão e só então solicita assinatura ao processo, usando o mesmo protocolo `prumo-s1-i20-v1`, epoch/nonce, operação e argumento do I20–I24. Não recebe `signing_key` nem canal de controle. O banco continua validando HMAC via custódio I22 e `auth.sessions` I15; a role SQL permanece sem EXECUTE de gestão de chaves.
- O processo assinador aceita somente material com estrutura canônica, comando allowlisted e janela curta; essa checagem **não comprova** que ele verificou GoTrue. Ela reduz falhas de formato, não impede que um atacante capaz de usar a pipe de assinatura peça HMAC para identidades arbitrárias.
- Em falha do processo assinador, a requisição HTTP retorna 503, nenhum nonce novo é consumido e o domínio comercial não sofre alteração. Um processo novo **não recupera automaticamente** os segredos do anterior. O runner, atuando como administrador sintético, provisiona no banco uma nova chave com novo UUID e novo segredo, carrega-a no processo de reposição, troca o ID do assinador e testa novas operações. A chave anterior é revogada no PostgreSQL via CAS, e uma HMAC correta para chave revogada continua recusada pelo banco.
- O processo filho não dispõe de credenciais SQL, não executa chamadas HTTP e não conhece tokens GoTrue. O gateway conhece apenas identificador de chave, conexão SQL restrita e pipe de assinatura. A preparação da chave e o controle da pipe permanecem no **runner administrativo sintético**.

## Plano de validação

O job rápido repete os **30 testes HTTP** I23 e adiciona **10 testes sem Supabase** do assinador: HMAC canônica, chave desconhecida, chave curta, ID duplicado, timestamp vencido, material arbitrário, revogação no processo, queda do processo, ausência de `signing_key`/pipe administrativa no gateway e novo processo sem chave herdada.

O job integrado `scripts/test_s1_002_i25_signer_recovery_local.py` reaplica **50 migrations reais S0/S1** e fixtures de teste I20–I24; mantém **S1REC-01..50** do I24 e acrescenta:
- S1REC-51: processo separado e gateway sem chave/canal de controle;
- S1REC-52: operação GoTrue real assinada via pipe;
- S1REC-53: perda do processo bloqueia HTTP sem afetar equipe;
- S1REC-54: processo novo inicia sem chave antiga;
- S1REC-55: recuperação com chave nova e retomada autorizada;
- S1REC-56: revogação de chave antiga bloqueia HMAC legítima no banco;
- S1REC-57: token inválido não alcança assinador;
- S1REC-58: revogação no processo bloqueia nova assinatura;
- S1REC-59: ID carregado não pode ser sobrescrito com segredo distinto;
- S1REC-60: histórico mínimo e preservação do estado da equipe.

## Limites de segurança e próximos gates

**Este experimento NÃO estabelece isolamento operacional forte.** Gateway e assinador são processos do **mesmo usuário do runner**; um atacante com os privilégios dessa conta pode acessar os descritores/segredos de ambos. As pipes usam mensagens Python locais, não autenticação entre workloads. Não existe contêiner separado, serviço com identidade própria, permissões OS/Kubernetes, KMS/Vault/HSM, autenticação mTLS, gestão de quotas por usuário ou segredo fora do runner. O cliente com acesso à pipe `SIGN` pode solicitar assinaturas para mensagens válidas sem autenticação GoTrue independente **dentro do assinador** — portanto roubo da credencial SQL **e** da pipe pode contornar a separação. A revogação `NOLOGIN` do I24 não equivale a auditoria WORM contra o administrador DB.

**NO-GO produção, merge e deploy.** Próximo passo exige contrato de autenticação ponta a ponta entre gateway e serviço assinador/secret manager, segregação de identidades de processo, controle de acesso ao canal, provisionamento externo e auditoria durável. A execução de gerenciamento de equipe, escalas e fluxo humano S0 ainda tem os gates anteriores.

**Resultado CI:** pendente; preencher apenas após inspeção dos dois jobs e seus logs.
