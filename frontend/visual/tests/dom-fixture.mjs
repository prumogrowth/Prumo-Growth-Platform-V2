/** DOM mínimo para testar INTERAÇÃO de UI em Node sem dependências.
 * Não emula CSS/layout, navegador real, segurança ou acessibilidade de leitor de tela.
 */
export function installMockDOM({ mobile = false, tablet = false, prefersDark = false } = {}) {
  class MockNode {
    constructor(tag = 'div') {
      this.tagName = tag.toUpperCase(); this.children = []; this.parent = null;
      this._text = ''; this.attrs = {}; this.events = {}; this.dataset = {};
      this.style = {}; this.hidden = false; this.disabled = false;
      this.value = ''; this._class = ''; this._open = false; this.returnValue = '';
      this.scrollTop = 0; this.scrollHeight = 1000;
    }
    set className(v) { this._class = String(v); }
    get className() { return this._class; }
    get classList() {
      const node = this;
      const tokens = () => node._class.split(/\s+/).filter(Boolean);
      return {
        add(v) { node._class = [...new Set([...tokens(), v])].join(' '); },
        remove(v) { node._class = tokens().filter(x => x !== v).join(' '); },
        toggle(v) { const a = tokens(); const on = !a.includes(v); node._class = (on ? [...a,v] : a.filter(x => x !== v)).join(' '); return on; },
        contains(v) { return tokens().includes(v); }
      };
    }
    set textContent(v) { this.children = []; this._text = String(v); }
    get textContent() { return this._text + this.children.map(n => n.textContent ?? '').join(''); }
    get innerText() { return this.textContent; }
    append(...children) {
      for (const child of children) {
        if (typeof child === 'string') { this._text += child; continue; }
        if (!child) continue;
        child.parent = this;
        this.children.push(child);
      }
    }
    replaceChildren(...children) {
      this.children = []; this._text = ''; this.append(...children);
      if (this.tagName === 'SELECT') this.value = this.children[0]?.value ?? '';
    }
    setAttribute(k,v) { this.attrs[k] = String(v); }
    getAttribute(k) { return this.attrs[k] ?? null; }
    addEventListener(k,fn) { (this.events[k] ??= []).push(fn); }
    fire(k, opts={}) {
      for (const fn of (this.events[k] ?? []))
        fn({ target:this, currentTarget:this, preventDefault(){}, key:'', ...opts });
    }
    click() { this.fire('click'); }
    focus() { document.activeElement = this; }
    blur() { if (document.activeElement === this) document.activeElement = null; }
    showModal() { this._open = true; }
    show() { this._open = true; }
    close(value) { if (value !== undefined) this.returnValue = value; this._open = false; this.fire('close'); }
    get open() { return this._open; }
    set open(value) { this._open=Boolean(value); }
    get options() { return this.children; }
    contains(node) {
      for (let cursor=node; cursor; cursor=cursor.parent) if(cursor===this) return true;
      return false;
    }
    querySelector(selector) {
      if (selector === '.detail-tab.active') return descendants(this).find(n =>
        n.classList.contains('detail-tab') && n.classList.contains('active')) ?? null;
      if (selector.startsWith('#')) return descendants(this).find(n => n.id === selector.slice(1)) ?? null;
      return null;
    }
  }
  const descendants = node => node.children.flatMap(n => [n, ...descendants(n)]);
  const ids = [
    'bank-dialog','bank-content','bank-ready-empty','bank-title','bank-nav','bank-nav-mobile','bank-close','bank-case-select','conversations-nav',
    'list-extra','filter-toggle','filter-panel','followup-actions','thread-bottom','communication-tools','composer-demo-guidance',
    'thread-actions','terminal-banner','commercial-filter','filter-summary','demo-dialog','demo-open','demo-close','demo-list-state',
    'visual-app', 'actor-select', 'shop-select', 'search-input', 'status-filter',
    'list-count', 'list-context', 'queue-summary', 'filter-reset-controls', 'clear-list-filters', 'conversation-items', 'thread-title',
    'thread-meta', 'thread-body', 'workflow-bar', 'message-input',
    'detail-content', 'detail-pane', 'thread-pane', 'message-preview-dialog',
    'message-preview-body', 'completion-dialog',
    'completion-form', 'template-dialog', 'template-select', 'intake-dialog',
    'intake-dialog-title', 'intake-dialog-copy', 'team-dialog','team-title',
    'team-list', 'team-monitor', 'team-batches', 'team-queue', 'team-action-announcement',
    'queue-action-dialog', 'queue-action-title', 'queue-action-copy', 'queue-assignee-area', 'queue-assignee', 'team-show-queue',
    'team-show-members', 'team-show-monitor', 'team-show-batches',
    'context-announcement', 'toast', 'team-nav', 'team-nav-mobile', 'team-close',
    'reset-app', 'composer', 'thread-back', 'detail-back', 'detail-close',
    'theme-light', 'theme-dark', 'emoji-toggle', 'emoji-picker', 'audio-record',
    'audio-draft', 'audio-preview', 'audio-status', 'audio-duration', 'audio-stop',
    'audio-attach', 'audio-delete', 'composer-availability', 'ui-settings'
  ];
  const nodes = new Map(ids.map(id => {
    const tag=id.endsWith('dialog') ? 'dialog' :
      id==='clear-list-filters' ? 'button' :
      ['search-input','message-input'].includes(id) ? 'input' :
      id.includes('select') || ['status-filter','queue-assignee'].includes(id) ? 'select' :
      'div';
    return [id,new MockNode(tag)];
  }));
  for (const [id, node] of nodes) node.id = id;
  // Reproduzir o HTML inicial: o seletor de emoji começa fechado, e
  // não depende da antiga limpeza incondicional ao reabrir o mesmo caso.
  nodes.get('emoji-picker').hidden = true;
  // Fiel à árvore básica do painel para testes de foco/contains em tablet.
  nodes.get('detail-pane').append(nodes.get('detail-content'));
  const inbox = ['active','history','all'].map(value => {const n=new MockNode('button'); n.dataset.inbox=value; return n;});
  const filters = ['all','unread','mine','pending'].map(value => {const n=new MockNode('button'); n.dataset.filter=value; return n;});
  const send = new MockNode('button'); send.className = 'send-button';
  const document = {
    activeElement:null, events:{},
    createElement:tag=>new MockNode(tag),
    createElementNS:(ns,tag)=>new MockNode(tag),
    getElementById:id=>nodes.get(id) ?? null,
    querySelector(s) {
      if (s === '.send-button') return send;
      if (s === 'dialog[open]') return [...nodes.values()].find(n=>n.tagName==='DIALOG' && n._open) ?? null;
      return null;
    },
    querySelectorAll(s) { return s === '[data-inbox]' ? inbox : s === '[data-filter]' ? filters : []; },
    addEventListener(k,fn) { (this.events[k] ??= []).push(fn); },
    fire(k,opts={}) { for(const fn of this.events[k]??[])fn({preventDefault(){}, ...opts}); }
  };
  globalThis.document = document;
  // Mock de eventos do viewport: testes DOM não simulam layout nem reflow real.
  // O comportamento de foco sob resize é verificado no Chromium.
  const systemColorScheme={
    matches:Boolean(prefersDark), listeners:[],
    addEventListener(type,listener){if(type==='change')this.listeners.push(listener);}
  };
  globalThis.window = {
    events:{},
    matchMedia(query) {
      if(query.includes('prefers-color-scheme: dark'))return systemColorScheme;
      if (query.includes('760px')) return {matches:mobile};
      return {matches:(mobile || tablet) && /max-width/.test(query)};
    },
    addEventListener(k,fn) { (this.events[k] ??= []).push(fn); }
  };
  return {
    document, nodes, inbox, filters, descendants,
    get:id=>nodes.get(id),
    setSystemDark(dark){
      systemColorScheme.matches=Boolean(dark);
      for(const listener of systemColorScheme.listeners) listener({matches:systemColorScheme.matches});
    },
    cards:()=>descendants(nodes.get('conversation-items')).filter(n=>n.classList.contains('conversation-card')),
    openCase(fragment) {
      if(nodes.get('bank-dialog').open) nodes.get('bank-dialog').close();
      const node=this.cards().find(n=>(n.attrs['aria-label']??'').includes(fragment));
      if (!node) throw new Error('case not found in rendered list: '+fragment);
      node.click();
    },
    caseContent() {return nodes.get('bank-dialog').open ? nodes.get('bank-content') : nodes.get('detail-content');},
    openArea(title) {
      if(['Extração','Banco'].includes(title)) {
        const target=descendants(nodes.get('detail-content')).find(n=>
          n.id==='registration-diagnostics' && title==='Extração' ||
          n.classList.contains('prior-bank-history') && title==='Banco');
        if(!target)throw new Error('Resumo não contém diagnóstico solicitado: '+title);
        target.open=true;return;
      }
      const target=['Novo contato','Recontatos'].includes(title)?'Histórico':title;
      const button=descendants(nodes.get('detail-content')).find(n=>n.attrs.role==='tab' && n.textContent===target);
      if(!button)throw new Error('Aba não encontrada: '+target);
      button.click();
    },
    selectActor(id) { nodes.get('actor-select').value=id;nodes.get('actor-select').fire('change'); },
    selectShop(id) { nodes.get('shop-select').value=id;nodes.get('shop-select').fire('change'); }
  };
}
