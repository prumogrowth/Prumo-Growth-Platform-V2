# Impacto previsto antes das correções — auditoria independente I85

28/10/2026, America/Sao_Paulo. HEAD encontrado 0d3beb4; I84 3bf948f preservada.

A leitura integral de I85 e do CLI Supabase 2.84.2 confirmou dois problemas que
exigem tratamento explícito de componentes herdados, sem editar a branch I84.

1. `local_admin.boundary.save` usa nome fixo `.next` e O_EXCL. SIGKILL entre fsync
   e replace deixa resíduo que impede novas escritas. O código I84 será mantido;
   a I85 adotará escrita privada e recuperação explícita de seus próprios
   journals. Resíduos nunca serão apagados silenciosamente nem tratados como
   prova de rollback. O teste também reproduzirá o comportamento herdado.
2. `supabase functions serve` injeta SUPABASE_SERVICE_ROLE_KEY, SUPABASE_DB_URL
   de instalação e SUPABASE_INTERNAL_JWT_SECRET no container. O template oficial
   encaminha service_role/DB_URL ao user worker. Logo, as declarações anteriores
   de exclusividade do instalador são inexatas, mesmo se runtime.ts não usa as
   variáveis. Fontes: supabase/cli v2.84.2, internal/functions/serve/serve.go e
   templates/main.ts. A I85 precisa de perfil local restrito, sem essas variáveis
   desde a criação. Será reutilizado o mesmo Edge Runtime e template oficial
   fixado, as mesmas funções I82, rede/credencial I83 e ciclo I84. Uma seleção
   explícita no worker I84 da branch I85 delegará somente o perfil I85 opt-in.
   Sem opt-in, comportamento anterior preservado para regressão; sem alteração
   de TypeScript I82, SQL, grants, owners ou protocolo HTTP.

Outros achados a reproduzir: trava apenas na CLI, init/dispose interrompidos,
revogação com ordem de locks inversa à sessão→ator→equipe→competência I79,
revogação sem retomada após rollback, confirmação/descarte que confiam em
journal sem validar novamente a autoridade global, diagnóstico argparse com eco.
Não são autorizações de mudança comercial ou de criação de Diretor real.

O perfil restrito é adaptação de infraestrutura descartável para corrigir uma
exposição anterior; não é runtime hospedado, nova autenticação ou I86. Seu aceite
exige Edge/GoTrue/PG17/PostgREST reais, ausência física das credenciais e todas
as regressões pertinentes. Se não passar, fechamento I85 permanece bloqueado.
