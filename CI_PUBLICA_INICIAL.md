# Laboratorio inicial no GitHub Actions

Esta branch principal contem um acionador manual deliberadamente limitado para
laboratorios **offline** da integracao WhatsApp/Meta e da interface visual.

1. GitHub > Actions > **Liberacred - laboratorio offline inicial**.
2. **Run workflow** > escolha `meta` ou `frontend`.
3. Nenhuma chamada real a Meta, OpenAI, Supabase hospedado, banco de dados
   de producao ou cliente e realizada por este acionador.
4. A configuracao usa apenas `contents: read`, nao consome secrets do repositorio,
   nao implanta nada e nao executa codigo arbitrario informado por usuarios.

Este piloto **nao substitui** as suites fisicas PostgreSQL 17/GoTrue/S0-I86.
Elas exigem um workflow especifico, isolado e com verificacao de ambiente,
que deve ser preparado depois da importacao. Nao alegue sucesso desses testes
antes de existir uma execucao real confirmada no GitHub Actions.

O workflow fica na branch padrao (`main`) para que o acionamento manual apareca
no menu Actions; o codigo testado e obtido apenas das duas branches autorizadas.
