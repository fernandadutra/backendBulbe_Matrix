/**
 * Componentes Web Reutilizáveis da Bulbe
 * Elementos personalizados nativos criados para a marca Bulbe.
 */

// 1. Componente de Cabeçalho (<bulbe-header>)
// Use o atributo variant="app" para o cabeçalho do app logado (sino + avatar).
class BulbeHeader extends HTMLElement {
  connectedCallback() {
    const variante = this.getAttribute('variant'); // 'app' ou nulo

    const menu = `
        <button class="icon-btn topbar__menu" aria-label="Abrir menu">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M3 6h18M3 12h18M3 18h18" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
          </svg>
        </button>`;

    const logo = `
        <a href="index.html" class="topbar__logo" aria-label="Bulbe — Início">
          <img src="../public/logo.png" alt="Bulbe Logo" style="height: 32px;" />
        </a>`;

    // Ações do app logado: sino de notificação (com bolinha de não-lido) + avatar.
    const acoesApp = `
        <div class="topbar__acoes">
          <button class="icon-btn topbar__sino" aria-label="Notificações" type="button">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M13.7 21a2 2 0 0 1-3.4 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="topbar__sino-badge" aria-hidden="true"></span>
          </button>
          <span class="topbar__avatar" aria-hidden="true"></span>
        </div>`;

    if (variante === 'app') {
      this.innerHTML = `
      <header class="topbar topbar--app">
        ${menu}
        ${logo}
        ${acoesApp}
      </header>
    `;
    } else {
      this.innerHTML = `
      <header class="topbar">
        ${menu}
        ${logo}
      </header>
    `;
    }
  }
}
customElements.define('bulbe-header', BulbeHeader);

// 2. Componente de Banner (<bulbe-banner>)
class BulbeBanner extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <a class="referral" href="#" aria-label="Indique e ganhe R$50 mais prêmios especiais">
        <img src="../public/banner.png" alt="Banner Indique e Ganhe" style="width: 100%; height: auto; display: block;" />
      </a>
    `;
  }
}
customElements.define('bulbe-banner', BulbeBanner);

// 2b. Componente de Barra de Instalação (<bulbe-instalacao>)
// Barra "Instalação: 0000000000 ▾" exibida sobre o fundo azul nas telas do app logado.
class BulbeInstalacao extends HTMLElement {
  connectedCallback() {
    const valor = (this.getAttribute('valor') || '3013588579').replace(/[^0-9]/g, '');
    this.innerHTML = `
      <div class="barra-instalacao">
        <span class="barra-instalacao__label">Instalação:</span>
        <button class="barra-instalacao__seletor" type="button" aria-label="Selecionar instalação">
          <span class="barra-instalacao__valor">${valor}</span>
          <svg class="barra-instalacao__caret" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M6 9l6 6 6-6z"/>
          </svg>
        </button>
      </div>
    `;
  }
}
customElements.define('bulbe-instalacao', BulbeInstalacao);

// 3. Componente de Folha (Área de Conteúdo Principal) (<bulbe-sheet>)
class BulbeSheet extends HTMLElement {
  connectedCallback() {
    // Adiciona classe de estilo de bloco padrão
    const tipo = this.getAttribute('tipo');
    if (tipo === 'resultado') {
      this.classList.add('sheet--result');
    }
    if (tipo === 'consumo') {
      this.classList.add('sheet--consumo');
    }
    if (tipo === 'beneficios') {
      this.classList.add('sheet--beneficios');
    }
    if (tipo === 'pre-fatura') {
      this.classList.add('sheet--pre-fatura');
    }
    if (tipo === 'faturas') {
      this.classList.add('sheet--faturas');
    }
    if (tipo === 'consumo-app') {
      this.classList.add('sheet--consumo-app');
    }
    if (tipo === 'placeholder') {
      this.classList.add('sheet--placeholder');
    }
    if (tipo === 'beneficios') {
      this.classList.add('sheet--beneficios');
    }
  }
}
customElements.define('bulbe-sheet', BulbeSheet);

// 4. Componente de Rodapé (<bulbe-footer>)
class BulbeFooter extends HTMLElement {
  connectedCallback() {
    const activeTab = this.getAttribute('active-tab') || 'consumo';
    this.innerHTML = `
      <nav class="tabbar" aria-label="Navegação principal">
        <a href="pre-fatura.html" class="tab ${activeTab === 'faturas' ? 'is-active' : ''}" ${activeTab === 'faturas' ? 'aria-current="page"' : ''}>
          <svg class="tab__icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M7 3h8l4 4v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/>
            <path d="M14 3v4h4" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/>
            <path d="M9 12h7M9 16h7" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
          </svg>
          <span>Faturas</span>
        </a>
        <a href="faturas.html" class="tab ${activeTab === 'consumo' ? 'is-active' : ''}" ${activeTab === 'consumo' ? 'aria-current="page"' : ''}>
          <svg class="tab__icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M13.5 2L5 13h6l-1.5 9L19 11h-6l.5-9z"/>
          </svg>
          <span>Consumo</span>
        </a>
        <a href="indique-ganhe.html" class="tab ${activeTab === 'indicacoes' ? 'is-active' : ''}" ${activeTab === 'indicacoes' ? 'aria-current="page"' : ''}>
          <svg class="tab__icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="9" cy="8" r="3.2" stroke="currentColor" stroke-width="1.7"/>
            <path d="M3.5 19c.7-3 3-4.5 5.5-4.5s4.8 1.5 5.5 4.5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
            <circle cx="17.5" cy="9" r="2.6" stroke="currentColor" stroke-width="1.7"/>
            <path d="M17.5 14c2.2 0 3.8 1.2 4.5 3M19 5v3M17.5 6.5h3" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
          </svg>
          <span>Indicações</span>
        </a>
      </nav>
    `;
  }
}
customElements.define('bulbe-footer', BulbeFooter);

// 5. Componente de Cabeçalho Desktop (<bulbe-header-desktop>)
class BulbeHeaderDesktop extends HTMLElement {
  connectedCallback() {
    const activeTab = this.getAttribute('active-tab') || 'consumo';
    this.innerHTML = `
      <header class="topbar-desktop">
        <div class="topbar-desktop__container">
          <a href="index.html" class="topbar-desktop__logo" aria-label="Bulbe — Início">
            <img src="../public/logo.png" alt="Bulbe Logo" style="height: 32px;" />
          </a>
          <nav class="topbar-desktop__nav" aria-label="Navegação desktop">
            <a href="pre-fatura.html" class="topbar-desktop__link ${activeTab === 'faturas' ? 'is-active' : ''}" ${activeTab === 'faturas' ? 'aria-current="page"' : ''}>
              Faturas
            </a>
            <a href="simular-desconto.html" class="topbar-desktop__link ${activeTab === 'consumo' ? 'is-active' : ''}" ${activeTab === 'consumo' ? 'aria-current="page"' : ''}>
              Consumo
            </a>
            <a href="#" class="topbar-desktop__link ${activeTab === 'indicacoes' ? 'is-active' : ''}" ${activeTab === 'indicacoes' ? 'aria-current="page"' : ''}>
              Indicações
            </a>
          </nav>
          <div class="topbar-desktop__actions">
            <a href="#" class="btn-desktop-cta">Fale Conosco</a>
          </div>
        </div>
      </header>
    `;
  }
}
customElements.define('bulbe-header-desktop', BulbeHeaderDesktop);

// 6. Componente de Card de Métrica (<bulbe-metric-card>)
class BulbeMetricCard extends HTMLElement {
  connectedCallback() {
    const label = this.getAttribute('label') || '';
    const value = this.getAttribute('value') || '';
    const sub = this.getAttribute('sub') || '';
    const dataResult = this.getAttribute('data-result') || '';

    // Se tiver o atributo data-result, envolvemos a parte numérica em um span com data-result para que o script de simulação JS possa atualizá-la.
    const valueHtml = dataResult
      ? `R$ <span data-result="${dataResult}">${value}</span>`
      : value;

    this.innerHTML = `
      <div class="metric-card__container">
        <p class="metric-card__label">${label}</p>
        <p class="metric-card__value">${valueHtml}</p>
        ${sub ? `<p class="metric-card__sub">${sub}</p>` : ''}
      </div>
    `;

    // Remove o atributo data-result do elemento customizado para que o script.js 
    // atualize apenas o span interno e não destrua a estrutura do card.
    if (this.hasAttribute('data-result')) {
      this.removeAttribute('data-result');
    }
  }
}
customElements.define('bulbe-metric-card', BulbeMetricCard);

// 7. Componente de Card de Fatura (<bulbe-fatura-card>)
class BulbeFaturaCard extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <form id="simulador" class="card" novalidate>
        <label class="card__label" for="fatura">Valor da sua fatura atual</label>

        <div class="field">
          <span class="field__currency">R$</span>
          <input id="fatura" name="fatura" class="field__input" type="text" inputmode="decimal" autocomplete="off"
            value="0,00" aria-describedby="discountHint" />
        </div>

        <p id="discountHint" class="discount-hint" aria-live="polite">
          Desconto Bulbe: até 15% na sua fatura
        </p>
      </form>
    `;
  }
}
customElements.define('bulbe-fatura-card', BulbeFaturaCard);

// Efeito de Blur
const tooltipImg = document.querySelector('img[src="../public/tooltip.png"]');
let blurOverlay = null;
let modalImage = null;

const imageUrl = location.pathname.includes('status-pedido')
  ? '../public/Camada Bulbinho2.png'
  : '../public/Camada Bulbinho.png';

if (tooltipImg) tooltipImg.addEventListener('click', function (event) {
  event.stopPropagation();

  if (!blurOverlay) {
    // Cria o overlay de blur
    blurOverlay = document.createElement('div');
    blurOverlay.className = 'blur-overlay';
    document.body.appendChild(blurOverlay);

    // Cria a imagem modal
    modalImage = document.createElement('img');
    modalImage.src = imageUrl;
    modalImage.className = 'modal-image';
    document.body.appendChild(modalImage);
  }
});

// Clique em QUALQUER LUGAR = DESATIVA blur e remove imagem
document.addEventListener('click', function () {
  if (blurOverlay) {
    blurOverlay.remove();
    blurOverlay = null;
  }
  if (modalImage) {
    modalImage.remove();
    modalImage = null;
  }
});

// Opcional: fechar ao pressionar ESC
document.addEventListener('keydown', function (event) {
  if (event.key === 'Escape' && blurOverlay) {
    blurOverlay.remove();
    blurOverlay = null;

    if (modalImage) {
      modalImage.remove();
      modalImage = null;
    }
  }
});