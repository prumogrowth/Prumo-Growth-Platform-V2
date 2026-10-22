/** FV-UI-020 — apresentação CONSERVADORA de cenários técnicos sintéticos.
 * Estados candidatos não são códigos HTTP, resultados reais de S0/S1,
 * aprovação bancária, prova de envio Meta ou autorização de reprocessamento.
 * Nenhuma mensagem externa, detalhe de rejeição ou PII entra na cópia visual.
 */
export const DEMO_OPERATION_STATES=Object.freeze([
  'accepted','partial','failed','stale','uncertain','denied','unavailable'
]);
const STATES=Object.freeze({
  accepted:{
    title:'Solicitação registrada — somente na simulação',
    description:'Não há confirmação S0 de conclusão, execução F03 ou gravação cadastral.',
    nextStep:'Aguardar uma projeção autenticada do núcleo, quando a integração existir.'
  },
  partial:{
    title:'Resultado parcial fictício, não persistido',
    description:'Campos propostos, lacunas e conflitos não equivalem a dados validados.',
    nextStep:'Não atualizar a ficha pelo navegador nem iniciar contato automático.'
  },
  failed:{
    title:'Falha técnica simulada',
    description:'Não há resultado de extração nem atualização cadastral confirmada.',
    nextStep:'Exibir incidente e aguardar orientação ou reprocessamento autorizado pelo S0.'
  },
  stale:{
    title:'Versão incompatível simulada',
    description:'Um resultado antigo não pode ser aplicado sobre outra versão do atendimento.',
    nextStep:'Uma nova leitura autorizada pelo S0 seria necessária; não reenviar automaticamente.'
  },
  uncertain:{
    title:'Confirmação externa incerta · simulação',
    description:'Tempo esgotado ou ausência de resposta não prova falha nem execução concluída.',
    nextStep:'Consultar o estado autoritativo; não repetir a solicitação por conta própria.'
  },
  denied:{
    title:'Operação negada · cenário sintético',
    description:'Nenhuma informação protegida ou causa detalhada é exposta nesta demonstração.',
    nextStep:'Não executar ação nem contornar permissões. A validação real pertence ao S0.'
  },
  unavailable:{
    title:'Serviço indisponível · simulação',
    description:'A interface não pode confirmar processamento, persistência ou efeito comercial.',
    nextStep:'Preservar o estado anterior e aguardar restauração ou confirmação autorizada.'
  }
});
const fallback=Object.freeze({
  kind:'untrusted',title:'Resultado técnico não verificável',
  description:'Nenhum efeito ou dado pode ser confirmado a partir desta resposta.',
  nextStep:'Exigir projeção minimizada e autenticada do núcleo.',
  effectConfirmed:false,automaticRetryAllowed:false,commercialTransition:false
});
/** Somente nomes constantes da cena local; não ingerir response.outcome
 * de rede aqui. O S0 será a origem da futura projeção minimizada.
 */
export function projectDemoOperationFeedback(kind){
  if(typeof kind!=='string' || !Object.hasOwn(STATES,kind))return fallback;
  const info=STATES[kind];
  return Object.freeze({
    kind,title:info.title,description:info.description,nextStep:info.nextStep,
    effectConfirmed:false,automaticRetryAllowed:false,commercialTransition:false
  });
}
