# D-ORG-01 — Equipe Prumo, papéis e escopos por concessionária

**Decisão expressa do responsável — 18/10/2026.** Documento normativo de produto, sem comprovação de vínculo formal de trabalho ou autorização externa.

## Regra aprovada

**Todos os gestores e operadores da operação comercial são profissionais da Prumo, não funcionários das concessionárias clientes.** Uma escala, carteira ou dedicação **exclusiva** a uma concessionária não altera seu vínculo com a Prumo. A concessionária é o cliente atendido e o **escopo operacional** dos registros, não a empresa empregadora da equipe.

Os conceitos são distintos: **(1) identidade e pertencimento à equipe Prumo; (2) papel de gestor/operador; (3) concessões expressas de acesso a concessionárias; (4) designação/atribuição a casos; (5) escala ou dedicação preferencial/exclusiva.** É possível uma pessoa autorizada atuar em várias concessionárias, sem concessão global implícita; revogar uma loja não apaga a identidade do colaborador ou outras concessões.

**Gestor da Prumo:** supervisiona o conjunto de concessionárias explicitamente autorizado; lê conversas completas D2 das lojas concedidas conforme D41-01, sem obter por isso acesso irrestrito a D3/D4. Pode distribuir/remanejar caso entre profissionais da Prumo elegíveis, **inclusive autoatribuir-se** um caso para atuar nele como operador, conforme D41-04, sem poderes operacionais automáticos sobre casos não atribuídos.

**Operador da Prumo:** acessa e atua somente em casos atribuídos na(s) concessionária(s) em que está autorizado. Um operador exclusivo de determinada concessionária continua profissional da Prumo e está sujeito às mesmas verificações de papel, escopo, caso e revogação.

## Linguagem e modelagem

Preferir “gestor da Prumo com acesso à concessionária A”, “operador da Prumo designado ao caso da concessionária A” e “equipe da Prumo dedicada à concessionária A”. A expressão histórica “gestor/operador da loja” significa apenas **escopo funcional**, nunca vínculo empregatício com a concessionária.

Em S0, `public.atores` é a identidade individual e `public.vinculos_papel_escopo` é a concessão por concessionária; isso é compatível com vários escopos, mas **não constitui registro de emprego**. Na S1-001, `actor.shopId` identifica **um único escopo ativo na demonstração**; não é empresa empregadora nem modelo definitivo de autorização. Para S1-002 separar organização, ator, concessões múltiplas, contexto de loja selecionado, escala exclusiva/opcional e atribuição vigente de caso, com revalidação no servidor e trilha de auditoria. Concessionária não pode conceder direitos à equipe Prumo por simples atributo na interface.

## Fronteiras preservadas

DEC-WA-05 define a **titularidade de App Meta/WABA/emissor pela concessionária**, independentemente do vínculo dos atendentes. Não confundir titularidade de canal com empregador. Atos de cadastro/fechamento junto à instituição financeira continuam sujeitos às autorizações formais. Esta diretriz não cria contratos trabalhistas, usuários, migrations, grants nem credenciais, e não libera produção.

**Precedência:** decisão organizacional de 18/10/2026 prevalece sobre redações ambíguas dos textos antigos. Mantêm-se D41-01..06, isolamento de dados, oito estados comerciais e demais decisões não conflitantes.


## Evidência S0 após D-ORG-01

A [auditoria profunda S0 × D-ORG-01](./AUDITORIA_S0_DORG01_ESTRUTURA_2026_10_18.md) comprovou em [PG17 #39138178030 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39138178030) que **uma identidade única** pode ter concessões A+B e ser revogada só em B, com gestor multiloja, autoatribuição e operador vinculado ao caso. **Não** se deve reestruturar `atores` ou fixar empregado em `concessionaria_id`. Antes de S1-002 conectada, a arquitetura ainda precisa de **registro confiável de vínculo Prumo** (não fornecido pelo navegador) e de redistribuição auditada de casos no desligamento/revogação. Nenhuma migração foi autorizada por esta observação.
