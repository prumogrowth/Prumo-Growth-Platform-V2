# Auditoria transversal — D-ORG-01 (18/10/2026)

**Escopo:** pacote original de 55 documentos Markdown (17/10/2026), consolidação conceitual v0.2, 49 documentos/textos do PR #1 e 27 do PR #2 examinados em busca de vínculo organizacional, equipe, gestor, operador, empregador e escopo. Sem alteração de normas de Meta/Banco.

**Constatação:** a visão original 01 prevê empresa independente com **pessoal próprio**, inclusive atuação sem vínculo empregatício com concessionária; 03 distingue gestor da empresa gestora de funcionários da loja; 41 admite gestor da equipe com **múltiplas lojas autorizadas** e autoatribuição operacional de caso. Não apareceu diretriz válida dizendo que gestores e operadores humanos sejam empregados das concessionárias. O desvio ocorreu na **redação e modelagem simplificada** da S1: “gestor da loja”, “operador da mesma loja” e `shopId` único por pessoa podem ser interpretados equivocadamente como vínculo de trabalho com a concessionária.

**Correção normativa:** `docs/D_ORG_01_EQUIPE_PRUMO_2026_10_18.md` registra que equipe gestora/operadora pertence à Prumo, com escopos por concessionária, possível dedicação exclusiva e múltiplas concessões explícitas. Foram revisados índice, decisões/gates, especificação/aceite S1, guia da demo e mapa mental. Não reescrever relatórios históricos nem confundir a titularidade Meta da DEC-WA-05 com contratação da equipe.

**Implementação atual:** a S0 separa identidade e concessão loja; a S1-001 tem seletores de perfil e `shopId` único somente na fixture. Não é uma autorização real. A S1-002 precisa projetar concessões múltiplas e autoatribuição gerencial D41-04 no backend, sem conceder D3/D4 por supervisão.

**Acervo revisado:** cópia preservadora do ZIP histórico, com 13 emendas datadas e nova norma, fornecida separadamente ao responsável; não substitui contratos ou aprovações externas. Esta auditoria não instala migrations, não mescla PR, não altera Supabase hospedado nem conecta Meta/Banco.

## Fechamento validado — D-ORG-01

**Commit de código testado:** `806d6465c1ec28c64cc67cc5154977a49b48f538`. [**GitHub Actions S1 #39136909717 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39136909717), **28 testes PASS, 0 FAIL**, incluindo `AUD-ORG-01`: os cinco atores fictícios da S1 declaram `organizationId: "prumo"` e permanecem associados a concessionárias **somente por escopo da demonstração**. Nenhum acesso adicional concedido, nenhum token, dado real ou recurso de produção.

**Resultado:** documentação ativa e fixture S1 padronizadas. A S1-002 continua obrigada a implementar equipe Prumo multi-escopo, atribuições por caso e autoatribuição gerencial D41-04; a S1-001 **não** passa a oferecer essas funcionalidades apenas por esta correção. PR #1/#2 Draft, sem merge nem migrações hospedadas.
