// Thin fetch wrapper. Throws Error(message) with a human-readable message.
async function req(method, path, body) {
  const res = await fetch('/api' + path, {
    method,
    credentials: 'same-origin',
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    let msg = data?.detail;
    if (Array.isArray(msg)) msg = msg.map((d) => `${d.loc?.at(-1) ?? 'field'}: ${d.msg}`).join('. ');
    const err = new Error(msg || `Something went wrong (${res.status}). Try again.`);
    err.status = res.status;
    if (res.status === 401 && path !== '/login' && path !== '/me') location.hash = '#/login';
    throw err;
  }
  return data;
}

export const api = {
  me: () => req('GET', '/me'),
  login: (b) => req('POST', '/login', b),
  register: (b) => req('POST', '/register', b),
  logout: () => req('POST', '/logout'),
  bikes: () => req('GET', '/bikes'),
  bike: (id) => req('GET', `/bikes/${id}`),
  createBike: (b) => req('POST', '/bikes', b),
  patchBike: (id, b) => req('PATCH', `/bikes/${id}`, b),
  deleteBike: (id) => req('DELETE', `/bikes/${id}`),
  addKm: (id, b) => req('POST', `/bikes/${id}/odometer`, b),
  addTask: (id, b) => req('POST', `/bikes/${id}/tasks`, b),
  patchTask: (id, tid, b) => req('PATCH', `/bikes/${id}/tasks/${tid}`, b),
  deleteTask: (id, tid) => req('DELETE', `/bikes/${id}/tasks/${tid}`),
  addLogs: (id, b) => req('POST', `/bikes/${id}/logs`, b),
  deleteLog: (id, lid) => req('DELETE', `/bikes/${id}/logs/${lid}`),
  export: () => req('GET', '/export'),
};
