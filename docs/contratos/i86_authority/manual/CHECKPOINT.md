# I86 manual — checkpoint de desenvolvimento

28/10/2026, America/Sao_Paulo. LAB_BLOCKED provisório: testes físicos pendentes.
Base exata dbf49ab19b73766d60678c4ce6f7dea56cd66c9b, tree
9d2f54b8753d4afadf5175ee5b332510890f1772.
Branch exclusiva exp/s1-i86-manual-director-20261028, sem alterar I86 histórica.

Implementado procedimento SQL INVOKER com APPOINT/REVOKE/REACTIVATE, CAS,
evidência manual vinculada, auditoria atômica, reconciliação sem reaplicação e
retirada de sessões. Nenhuma API/CLI operacional nova ou permissão comum.
Múltiplos Diretores permitidos; substituição automática não implementada.

Unidades locais: 13 testes de escopo, cinco do contrato v1 preservado e quatro
da política manual. Isso não comprova SQL real, presença humana ou implantação.
São 31 casos reais planejados, mais regressões independentes I85/I86 em runners
distintos. Código, CI, artefatos, descarte e classificação serão registrados
somente depois da execução efetiva.

D01–D05 reclassificadas conforme a instrução do responsável. Identidade nominal,
custódia produtiva, validação externa da evidência e continuidade não decidida
permanecem limites operacionais. Sem merge, deploy, usuários reais ou Meta.
