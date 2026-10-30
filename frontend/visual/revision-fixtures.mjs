/** FV-REV-01/2: cenas ADICIONAIS inteiramente sintéticas, sem contratos/API S0.
 * Enriquecem cópias em memória; jamais alteram a fixture original ou os grants.
 */
export function withRevisionScenes(records) {
  return records.map(record => {
    const row = structuredClone(record);
    const explicit = {
      'A-102': ['aurora', 'rafael', 'cliente02-aurora-demo'],
      'A-108': ['aurora', 'rafael', 'client09-aurora-only'],
      'A-105': ['aurora', 'rafael', 'client15-aurora-only'],
      'A-114': ['aurora', 'rafael', 'client15-aurora-only'],
      'A-115': ['aurora', 'rafael', 'cliente16-aurora-demo'],
      'A-116': ['aurora', 'rafael', 'cliente16-aurora-demo'],
      'A-110': ['aurora', 'rafael', 'cliente11-aurora-demo'],
      'A-111': ['aurora', 'rafael', 'cliente12-aurora-demo'],
      'A-117': ['aurora', 'lia', 'cliente19-aurora-demo']
    }[row.id];
    if (!explicit || row.shopId !== explicit[0] || row.assignedTo !== explicit[1]) return row;
    const event = (id, kind, label, order, extra = {}) => ({id, kind, label, order,
      state:'confirmed', time:'Sequência fictícia · '+order, origin:'s0_fixture',
      confirmed:true, versionRef:row.id+'-'+id+'-v1-demo', ...extra});
    const continuation = ['A-114','A-116'].includes(row.id);
    const events = continuation ? [
      event('return', 'customer_return', 'Retorno do cliente após marco anterior', 10),
      event('cycle', 'human_cycle', 'Novo ciclo humano autorizado · F01 permanece silenciada', 20),
      event('assignment', 'assignment', 'Atribuição inicial a Rafael Lima', 30)
    ] : [
      event('lead', 'lead', 'Entrada do lead · origem demonstrativa', 10),
      event('f01', 'f01_started', 'Atendimento inicial pela F01', 20),
      event('handoff', 'handoff', 'Encaminhamento ao atendimento humano', 30),
      event('assignment', 'assignment', 'Atribuição inicial a '+(row.id==='A-117'?'Consultor da equipe de origem':'Rafael Lima'), 40)
    ];
    if(row.id==='A-117') events.push(event('transfer','transfer',
      'Transferência confirmada para Lia Martins · acesso somente a este caso',50));
    if(row.id==='A-105') events.push(event('bank','bank_submission',
      'Encaminhamento ao Banco Yamaha confirmado na fixture',60));
    if(row.id==='A-115') events.push(event('sale','sold','Venda confirmada na fixture',60,{resultConfirmed:true}));
    if(row.id==='A-111') events.push(event('loss','lost',
      'Perda confirmada na fixture · motivo: silêncio após template final comprovado',80,{resultConfirmed:true}));
    row.relationshipProjection = {origin:'s0_fixture', confirmed:true, caseId:row.id,
      shopId:row.shopId, customerRef:explicit[2], versionRef:'timeline-'+row.id+'-v1-demo', events};
    if(row.id==='A-114'){
      row.registrationProjection={state:'persisted',confirmedPersisted:true,formVersionRef:'live-form-v2-demo',
        fields:[{key:'demo_f01',label:'Informação inicial demonstrativa',safeDisplayValue:'Valor sintético coletado pela F01',
          sourceRef:'f01-form-v1-demo',sourceLabel:'F01 · coleta inicial fictícia',validationState:'applied'},
          {key:'demo_f03',label:'Informação atualizada demonstrativa',safeDisplayValue:'Valor sintético atualizado',
          sourceRef:'f03-form-v2-demo',sourceLabel:'F03 · atualização confirmada fictícia',validationState:'applied'}],missing:[],conflicts:[]};
      row.bankReadinessProjection={origin:'s0_fixture',confirmed:true,caseId:row.id,shopId:row.shopId,versionRef:'ready-a114-demo-v2',formVersionRef:'live-form-v2-demo'};
    }
    const publications = [];
    if(!continuation) publications.push({id:'f01-summary-'+row.id, source:'F01',
      content:'Resumo fictício: atendimento automatizado inicial e contexto encaminhados à equipe humana.',
      time:'Antes do atendimento humano · fictício', audience:'case', published:true, versionRef:'f01-'+row.id+'-v1-demo'});
    if(['A-108','A-110'].includes(row.id)) publications.push(
      {id:'f02-plan-1-'+row.id, source:'F02', content:'Comunicação fictícia anterior: planejamento de continuidade em análise.',
        time:'Primeiro planejamento · fictício', audience:'case', published:true, versionRef:'f02-'+row.id+'-v1-demo'},
      {id:'f02-plan-2-'+row.id, source:'F02', content:'Atualização fictícia: consultar os estados de cada tentativa no Histórico. Planejamento não comprova envio.',
        time:'Revisão do planejamento · fictício', audience:'case', published:true, versionRef:'f02-'+row.id+'-v2-demo'});
    row.aiCommunicationsProjection = {origin:'s0_fixture', caseId:row.id, shopId:row.shopId,
      versionRef:'communications-'+row.id+'-demo', entries:publications};
    if(row.id==='A-110') row.followupProjection.attempts.push(
      {label:'Tentativa anterior',state:'sent_confirmed',template:'Modelo demonstrativo',time:'Antes do plano atual · fictício'},
      {label:'Execução em curso',state:'executing',template:'Modelo demonstrativo',time:'Corte fictício T0'},
      {label:'Tentativa com falha',state:'failed',template:'Modelo demonstrativo',time:'Corte fictício T0'},
      {label:'Transporte sem confirmação',state:'uncertain',template:'Modelo demonstrativo',time:'Corte fictício T0'},
      {label:'Tentativa cancelada',state:'cancelled',template:'Modelo demonstrativo',time:'Cancelamento confirmado na fixture'});
    return row;
  });
}
