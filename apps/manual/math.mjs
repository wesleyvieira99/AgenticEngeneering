/** Pure educational mechanisms. No network, model, billing or production measurements. */
const finite = xs => xs.length > 0 && xs.every(Number.isFinite);
export function vectorMetrics(a, b) {
  if (!finite(a) || !finite(b) || a.length !== b.length) throw new Error('Use vetores finitos de mesma dimensão.');
  const dot = a.reduce((s, x, i) => s + x * b[i], 0);
  const an = Math.hypot(...a), bn = Math.hypot(...b);
  return { dot, cosine: an && bn ? Math.max(-1, Math.min(1, dot / (an * bn))) : null,
    distance: Math.hypot(...a.map((x, i) => x - b[i])), normA: an, normB: bn };
}
export function softmax(values, temperature = 1) {
  if (!(temperature > 0) || !Number.isFinite(temperature) || !values.length || values.some(x => Number.isNaN(x) || x === Infinity)) throw new Error('Distribuição ou temperatura inválida.');
  const top = Math.max(...values);
  if (!Number.isFinite(top)) throw new Error('Ao menos uma posição precisa estar disponível.');
  const exps = values.map(x => Math.exp((x - top) / temperature));
  const sum = exps.reduce((a, b) => a + b, 0);
  return exps.map(x => x / sum);
}
export function attention(q, keys, values, causal = false, temperature = 1) {
  if (keys.length !== values.length || !keys.length || values.some(v => v.length !== values[0].length || !finite(v))) throw new Error('Chaves e valores incompatíveis.');
  const scores = keys.map((k, i) => causal && i > 0 ? -Infinity : vectorMetrics(q, k).dot / Math.sqrt(q.length));
  const weights = softmax(scores, temperature);
  return { scores, weights, output: values[0].map((_, j) => values.reduce((sum, v, i) => sum + weights[i] * v[j], 0)) };
}
export function tokenEstimate(text, bytesPerToken = 4) {
  if (!(bytesPerToken > 0)) throw new Error('Fator deve ser positivo.');
  const bytes = new TextEncoder().encode(text);
  return { characters: Array.from(text).length, bytes: bytes.length, estimated: Math.ceil(bytes.length / bytesPerToken), binary: [...bytes].slice(0, 12).map(x => x.toString(2).padStart(8, '0')) };
}
export function contextBudget(capacity, parts) {
  if (!Number.isFinite(capacity) || capacity <= 0 || parts.some(x => !Number.isFinite(x) || x < 0)) throw new Error('Orçamento inválido.');
  const used = parts.reduce((s, n) => s + n, 0);
  return { used, remaining: capacity - used, overflow: Math.max(0, used - capacity), percentage: used / capacity * 100 };
}
export function costEstimate(input, output, inputRate, outputRate, calls, retries) {
  const values = [input, output, inputRate, outputRate, calls, retries];
  if (values.some(n => !Number.isFinite(n) || n < 0)) throw new Error('Use valores não negativos.');
  const perCall = (input * inputRate + output * outputRate) / 1e6;
  const attempts = calls * (1 + retries / 100);
  return { perCall, attempts, total: perCall * attempts };
}
export function concurrency(tasks, slots, duration) {
  if (![tasks, slots].every(Number.isInteger) || tasks < 1 || slots < 1 || duration <= 0) throw new Error('Use tarefas/slots inteiros positivos e duração positiva.');
  return { waves: Math.ceil(tasks / slots), total: Math.ceil(tasks / slots) * duration, slotsUsed: Math.min(tasks, slots), sequential: tasks * duration };
}
export function gradient(weight, rate, iterations = 1) {
  if (![weight, rate].every(Number.isFinite) || rate <= 0 || !Number.isInteger(iterations) || iterations < 1 || iterations > 30) throw new Error('Parâmetros de gradiente inválidos.');
  const points = [];
  for (let i = 0; i <= iterations; i++) {
    const loss = (2 * weight - 4) ** 2;
    points.push({ step: i, weight, loss, derivative: 4 * (2 * weight - 4) });
    weight -= rate * points[i].derivative;
  }
  return points;
}
