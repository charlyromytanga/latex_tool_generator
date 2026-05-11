/**
 * secure_delete.js — Intercepte les formulaires de suppression du frontend
 * et demande le mot de passe avant de soumettre.
 */
(function () {
  const MODAL_HTML = `
  <div id="sd-overlay" style="
      display:none; position:fixed; inset:0;
      background:rgba(0,0,0,0.55); z-index:99999;
      align-items:center; justify-content:center;">
    <div style="
        background:var(--bg-card,#fff); border:1px solid var(--border,#dee2e6);
        border-radius:10px; padding:2rem;
        max-width:420px; width:90%; box-shadow:0 12px 48px rgba(0,0,0,0.35);">
      <h4 style="margin:0 0 0.5rem; color:var(--danger-text,#c0392b); font-size:17px;">
        ⚠️ Confirmer la suppression
      </h4>
      <p id="sd-item-label" style="color:var(--text-secondary,#555); font-size:13px; margin-bottom:1.25rem;"></p>
      <input id="sd-input" type="password"
             placeholder="Mot de passe ou code numérique"
             style="
               width:100%; padding:9px 12px;
               border:2px solid var(--border-strong,#dee2e6);
               border-radius:5px; font-size:14px; margin-bottom:0.5rem;
               box-sizing:border-box; font-family:var(--font,inherit);
               background:var(--bg-card,#fff); color:var(--text-primary,#111);"
             autocomplete="off"/>
      <div id="sd-error"
           style="color:var(--danger-text,#c0392b); font-size:13px; margin-bottom:1rem; display:none;">
        ❌ Mot de passe incorrect. Veuillez réessayer.
      </div>
      <div style="display:flex; gap:0.75rem; justify-content:flex-end;">
        <button id="sd-cancel" class="btn btn-secondary">Annuler</button>
        <button id="sd-confirm" class="btn btn-danger">Supprimer</button>
      </div>
    </div>
  </div>`;

  document.addEventListener('DOMContentLoaded', function () {
    document.body.insertAdjacentHTML('beforeend', MODAL_HTML);

    const overlay    = document.getElementById('sd-overlay');
    const input      = document.getElementById('sd-input');
    const errMsg     = document.getElementById('sd-error');
    const itemLabel  = document.getElementById('sd-item-label');
    const btnCancel  = document.getElementById('sd-cancel');
    const btnConfirm = document.getElementById('sd-confirm');

    let pendingForm = null;

    function showModal(form) {
      pendingForm = form;
      input.value = '';
      errMsg.style.display = 'none';
      // Try to extract item name from button data-label or form action
      var label = form.dataset.deleteLabel || form.action.split('/').filter(Boolean).pop() || '?';
      itemLabel.textContent = 'Élément : ' + label;
      overlay.style.display = 'flex';
      setTimeout(function () { input.focus(); }, 80);
    }

    function hideModal() {
      overlay.style.display = 'none';
      pendingForm = null;
    }

    function submitForm() {
      if (!pendingForm) return;
      var hidden = pendingForm.querySelector('input[name="delete_password"]');
      if (!hidden) {
        hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = 'delete_password';
        pendingForm.appendChild(hidden);
      }
      hidden.value = input.value;
      pendingForm.dataset.sdDone = '1';
      overlay.style.display = 'none';
      pendingForm.submit();
      pendingForm = null;
    }

    btnCancel.addEventListener('click', hideModal);
    btnConfirm.addEventListener('click', submitForm);

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); submitForm(); }
      if (e.key === 'Escape') hideModal();
    });

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) hideModal();
    });

    // Intercept all delete form submissions (capture phase = runs before onsubmit)
    document.addEventListener('submit', function (e) {
      var form = e.target;
      if (form.dataset.deleteForm && !form.dataset.sdDone) {
        e.preventDefault();
        e.stopImmediatePropagation();
        showModal(form);
      }
    }, true);
  });
})();
