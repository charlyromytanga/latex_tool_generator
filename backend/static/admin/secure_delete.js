/**
 * secure_delete.js — Intercepte toutes les soumissions de formulaires de suppression
 * dans l'admin Flask-Admin et demande le mot de passe de suppression via un popup.
 */
(function () {
  const MODAL_HTML = `
  <div id="sd-overlay" style="
      display:none; position:fixed; inset:0;
      background:rgba(0,0,0,0.55); z-index:99999;
      align-items:center; justify-content:center;">
    <div style="
        background:#fff; border-radius:10px; padding:2rem;
        max-width:420px; width:90%; box-shadow:0 12px 48px rgba(0,0,0,0.35);">
      <h4 style="margin:0 0 0.5rem; color:#c0392b; font-size:18px;">
        ⚠️ Confirmer la suppression
      </h4>
      <p style="color:#555; font-size:14px; margin-bottom:1.25rem;">
        Entrez le mot de passe ou le code numérique pour confirmer la suppression.
      </p>
      <input id="sd-input" type="password"
             placeholder="Mot de passe de suppression"
             style="
               width:100%; padding:9px 12px; border:2px solid #dee2e6;
               border-radius:5px; font-size:14px; margin-bottom:0.5rem;
               box-sizing:border-box; outline:none; transition:border-color .15s;"
             autocomplete="off"/>
      <div id="sd-error"
           style="color:#c0392b; font-size:13px; margin-bottom:1rem; display:none;">
        ❌ Mot de passe incorrect. Veuillez réessayer.
      </div>
      <div style="display:flex; gap:0.75rem; justify-content:flex-end;">
        <button id="sd-cancel" style="
            padding:8px 18px; border:1px solid #dee2e6; background:#f8f9fa;
            border-radius:5px; cursor:pointer; font-size:14px;">
          Annuler
        </button>
        <button id="sd-confirm" style="
            padding:8px 18px; background:#c0392b; color:#fff;
            border:none; border-radius:5px; cursor:pointer; font-size:14px;
            font-weight:600;">
          Supprimer
        </button>
      </div>
    </div>
  </div>`;

  document.addEventListener('DOMContentLoaded', function () {
    document.body.insertAdjacentHTML('beforeend', MODAL_HTML);

    const overlay   = document.getElementById('sd-overlay');
    const input     = document.getElementById('sd-input');
    const errMsg    = document.getElementById('sd-error');
    const btnCancel = document.getElementById('sd-cancel');
    const btnConfirm = document.getElementById('sd-confirm');

    let pendingForm = null;

    function showModal(form) {
      pendingForm = form;
      input.value = '';
      errMsg.style.display = 'none';
      input.style.borderColor = '#dee2e6';
      overlay.style.display = 'flex';
      setTimeout(function () { input.focus(); }, 80);
    }

    function hideModal() {
      overlay.style.display = 'none';
      pendingForm = null;
    }

    function submitForm() {
      if (!pendingForm) return;
      let hidden = pendingForm.querySelector('input[name="delete_password"]');
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

    input.addEventListener('focus', function () {
      input.style.borderColor = '#2980b9';
    });
    input.addEventListener('blur', function () {
      input.style.borderColor = '#dee2e6';
    });

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) hideModal();
    });

    // Intercept all delete form submissions (capture phase)
    document.addEventListener('submit', function (e) {
      var form = e.target;
      if (form.action && form.action.indexOf('/delete/') !== -1 && !form.dataset.sdDone) {
        e.preventDefault();
        e.stopImmediatePropagation();
        showModal(form);
      }
    }, true);
  });
})();
