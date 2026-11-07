const nf = new Intl.NumberFormat('en');
export const km = (n) => (n == null ? '—' : `${nf.format(n)} km`);
export const num = (n) => (n == null ? '—' : nf.format(n));
const df = new Intl.DateTimeFormat('en', { day: 'numeric', month: 'short', year: 'numeric' });
const dfShort = new Intl.DateTimeFormat('en', { day: 'numeric', month: 'short' });
export const date = (s) => (s ? df.format(new Date(s + 'T00:00:00')) : '—');
export const dateShort = (s) => (s ? dfShort.format(new Date(s + 'T00:00:00')) : '—');
export const today = () => {
  const d = new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
};
export const money = (n) => (n == null ? '—' : nf.format(Number(n)));

export const STATE_LABEL = { ok: 'OK', soon: 'Due soon', overdue: 'Overdue', due: 'Not logged', none: 'Not tracked' };
export const STATE_ICON = { ok: '●', soon: '▲', overdue: '■', due: '◆', none: '○' };

/** "340 km or 12 days left" / "Overdue by 120 km" / "Never logged" */
export function describe(t) {
  if (!t) return 'Not tracked on this bike';
  if (t.state === 'due') return 'Never logged. Log it once to start tracking.';
  const parts = [];
  if (t.km_left != null) parts.push(t.km_left <= 0 ? `${num(-t.km_left)} km over` : `${num(t.km_left)} km`);
  if (t.days_left != null)
    parts.push(t.days_left <= 0 ? `${num(-t.days_left)} days late` : `${num(t.days_left)} days`);
  if (t.state === 'overdue') return parts.filter((p) => /over|late/.test(p)).join(' · ') || 'Overdue';
  return parts.join(' or ') + ' left';
}

/** Short mono readout for diagram labels */
export function readout(t) {
  if (!t) return 'NOT TRACKED';
  if (t.state === 'due') return 'NOT LOGGED';
  if (t.state === 'overdue') {
    if (t.km_left != null && t.km_left <= 0) return `OVER ${num(-t.km_left)} KM`;
    return `LATE ${num(-t.days_left)} D`;
  }
  const bits = [];
  if (t.km_left != null) bits.push(`${num(t.km_left)} KM`);
  if (t.days_left != null) bits.push(`${num(t.days_left)} D`);
  return bits.join(' / ');
}

export function interval(t) {
  const a = [];
  if (t.every_km) a.push(`${num(t.every_km)} km`);
  if (t.every_days) a.push(t.every_days % 365 === 0 ? `${t.every_days / 365} yr` : `${t.every_days} days`);
  return a.length ? 'Every ' + a.join(' or ') : 'No interval';
}

export const RANK = { overdue: 0, due: 1, soon: 2, ok: 3, none: 4 };

/** Share of the interval used, 0..1 (1 = due or past). null when never logged. */
export function wear(t) {
  if (!t || t.state === 'due') return null;
  const f = [];
  if (t.every_km && t.km_left != null) f.push(1 - t.km_left / t.every_km);
  if (t.every_days && t.days_left != null) f.push(1 - t.days_left / t.every_days);
  return f.length ? Math.min(1, Math.max(0, ...f)) : null;
}
