export const ui = $state({ toast: null, user: undefined });

let timer;
/** Show a toast. action = { label, run } for e.g. Undo. */
export function toast(message, action = null, ms = 5000) {
  clearTimeout(timer);
  ui.toast = { message, action, id: Date.now() };
  timer = setTimeout(() => (ui.toast = null), ms);
}
export function dismissToast() {
  clearTimeout(timer);
  ui.toast = null;
}
