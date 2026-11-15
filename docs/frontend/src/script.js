(function () {
  'use strict';

  const DISCOUNT_RATE = 0.15;
  const STORAGE_KEY = 'bulbe.fatura';

  const formatBRL = (n) =>
    n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const parseCurrency = (str) => {
    const digits = String(str).replace(/\D/g, '');
    if (!digits) return 0;
    return parseInt(digits, 10) / 100;
  };

  function setupEntryForm() {
    const form = document.getElementById('simulador');
    const input = document.getElementById('fatura');
    if (!form || !input) return;

    const render = (value) => { input.value = formatBRL(value); };

    input.addEventListener('input', () => {
      const value = parseCurrency(input.value);
      render(value);
      input.setSelectionRange(input.value.length, input.value.length);
    });

    input.addEventListener('focus', () => {
      if (parseCurrency(input.value) === 0) input.select();
    });

    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const value = parseCurrency(input.value);
      if (value <= 0) {
        input.focus();
        input.style.outline = '2px solid #C73C2D';
        setTimeout(() => (input.style.outline = ''), 1200);
        return;
      }
      try { sessionStorage.setItem(STORAGE_KEY, String(value)); } catch (_) { }
      window.location.href = 'resultado.html';
    });
  }

  function setupResultScreen() {
    const targets = document.querySelectorAll('[data-result]');
    if (!targets.length) return;

    let value = 0;
    try { value = parseFloat(sessionStorage.getItem(STORAGE_KEY)) || 0; } catch (_) { }

    if (!value) {
      // valores padrão de demonstração de acordo com o design
      value = 350;
    }

    const monthlySavings = value * DISCOUNT_RATE;
    const bulbePrice = value - monthlySavings;
    const annualSavings = monthlySavings * 12;

    const map = {
      monthlySavings,
      fullPrice: value,
      bulbePrice,
      annualSavings,
    };

    targets.forEach((el) => {
      const key = el.getAttribute('data-result');
      if (key in map) el.textContent = formatBRL(map[key]);
    });

    const isLogado = sessionStorage.getItem('bulbe.logado') === '1';
    const detalhamento = document.getElementById('resultado-detalhamento');
    const ctaStart = document.getElementById('ctaStart');
    if (detalhamento) detalhamento.style.display = isLogado ? 'block' : 'none';
    if (ctaStart) ctaStart.style.display = isLogado ? 'none' : '';
  }

  function setupFlowRouting() {
    const btnEntrar = document.getElementById('btn-entrar');
    if (btnEntrar) {
      btnEntrar.addEventListener('click', () => {
        sessionStorage.setItem('bulbe.logado', '1');
      });
    }
    const btnNovo = document.querySelector('.btn-quero-economizar');
    if (btnNovo) {
      btnNovo.addEventListener('click', () => {
        sessionStorage.removeItem('bulbe.logado');
      });
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    setupEntryForm();
    setupResultScreen();
    setupFlowRouting();
  });
})();

// ─── Oculta detalhamento para novos usuários (?novo=1) ───
if (new URLSearchParams(location.search).get('novo') === '1') {
  const hideDetalhe = () => {
    const d = document.querySelector('.sim-detalhe');
    if (d) d.classList.add('sim-detalhe--oculto');
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', hideDetalhe);
  } else {
    hideDetalhe();
  }
}

// ─── Detalhamento das simulações (accordion) ───
;(function () {
  function initAccordion() {
    const items = document.querySelectorAll('.sim-detalhe__item');
    if (!items.length) return;

    items.forEach((item) => {
      const btn = item.querySelector('.sim-detalhe__header');
      if (!btn) return;

      btn.addEventListener('click', () => {
        const isOpen = item.classList.contains('is-open');

        // Fecha todos
        items.forEach((i) => {
          i.classList.remove('is-open');
          const h = i.querySelector('.sim-detalhe__header');
          if (h) h.setAttribute('aria-expanded', 'false');
        });

        // Abre o clicado (toggle: se já estava aberto, fica fechado)
        if (!isOpen) {
          item.classList.add('is-open');
          btn.setAttribute('aria-expanded', 'true');
        }
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAccordion);
  } else {
    initAccordion();
  }
})();
