// Local session metadata only: no prompt text, tool arguments or answer contents.
import { randomUUID } from "node:crypto";

export default async function SessionGlow({ client, directory = "", serverUrl }) {
  const port = Number(process.env.SESSIONGLOW_PORT || 8790);
  if (!Number.isInteger(port) || port < 1 || port > 65535) return {};
  const instance = randomUUID();
  // Expose the actual server address, without userinfo or query parameters.
  let endpoint = "";
  try { endpoint = new URL(serverUrl).host; } catch { /* In-process clients may have no public address. */ }
  const source = { endpoint, directory, pid: process.pid };
  const registryKey = Symbol.for("sessionglow.projectRuntimes");
  const registry = globalThis[registryKey] ??= new Map();
  registry.get(directory)?.();
  const sessions = new Map();
  const requests = new Map();
  const removed = new Set();
  const observed = new Set();
  let sequence = 0;
  let online = true;
  let sending = false;
  let pending = null;
  let chain = Promise.resolve();
  const text = (value, fallback = "") => typeof value === "string" ? value.replace(/\s+/g, " ").slice(0, 180) : fallback;

  function changed(row) {
    row.updated_at = Math.max(Date.now(), row.updated_at + 1);
  }

  async function get(method, options = {}) {
    try {
      const result = await method({ ...options, signal: AbortSignal.timeout(2000) });
      return result?.data ?? result;
    } catch { return null; }
  }

  function metadata(info) {
    if (!info || typeof info.id !== "string") return null;
    let row = sessions.get(info.id);
    if (!row) {
      row = { id: info.id, parent_id: info.parentID || null, title: info.title || info.id.slice(0, 12),
        project: directory, state: "unknown", detail: "", last_started: 0, updated_at: 0 };
      sessions.set(row.id, row);
    }
    row.parent_id = info.parentID || null;
    row.title = text(info.title, row.title);
    row.project = text(info.directory, row.project);
    return row;
  }

  async function ensure(id, depth = 0) {
    if (typeof id !== "string") return null;
    let row = sessions.get(id);
    if (!row) {
      const info = await get(client.session.get.bind(client.session), { path: { id } });
      if (!info?.id) return null; // Do not accidentally display an unknown subagent as a root.
      row = metadata(info);
    }
    if (row.parent_id && depth < 8 && !sessions.has(row.parent_id)) await ensure(row.parent_id, depth + 1);
    return row;
  }

  function trim() {
    if (sessions.size <= 192) return;
    const candidates = [...sessions.values()].filter(r => !["running", "waiting"].includes(r.state))
      .sort((a, b) => a.last_started - b.last_started);
    for (const row of candidates) {
      if (sessions.size <= 192) break;
      if (![...sessions.values()].some(r => r.parent_id === row.id)) sessions.delete(row.id);
    }
  }

  async function drain() {
    if (sending) return;
    sending = true;
    try {
      while (pending) {
        const body = pending;
        pending = null;
        try {
          const response = await fetch(`http://127.0.0.1:${port}/opencode`, {
            method: "POST", headers: { "Content-Type": "application/json" }, body,
            signal: AbortSignal.timeout(600),
          });
          await response.body?.cancel();
        } catch { pending = null; }
      }
    } finally { sending = false; }
  }

  function send() {
    trim();
    pending = JSON.stringify({ instance_id: instance, sequence: ++sequence, online,
      source, sessions: [...sessions.values()], removed: [...removed] });
    void drain();
  }

  function enqueue(work) {
    // Plugin callbacks return immediately; metadata lookups never block Agent execution.
    chain = chain.then(() => online ? work() : undefined).catch(() => {});
  }

  function start(row, explicit = false, stamp = Date.now()) {
    if (explicit && stamp > row.last_started) row.last_started = stamp;
    if (!["running", "waiting"].includes(row.state)) {
      if (!explicit) row.last_started = Math.max(row.last_started, stamp);
      row.state = "running";
      row.detail = "";
    }
    changed(row);
  }

  function finish(row) {
    if (["running", "waiting"].includes(row.state)) {
      row.state = "done";
      row.detail = "";
      changed(row);
    }
    for (const [key, value] of requests) if (value === row.id) requests.delete(key);
  }

  async function bootstrap() {
    const list = await get(client.session.list.bind(client.session), { query: { directory, limit: 32 } });
    if (Array.isArray(list)) {
      for (const info of list.slice(0, 32)) {
        if (!observed.has(info.id) && !removed.has(info.id)) metadata(info);
      }
      // Read message metadata to recover the last user task, never forward its parts.
      await Promise.all([...sessions.values()].map(async row => {
        if (row.parent_id) return;
        const messages = await get(client.session.messages.bind(client.session), { path: { id: row.id }, query: { limit: 12 } });
        if (!online || observed.has(row.id) || !Array.isArray(messages)) return;
        const info = messages.map(m => m.info).filter(Boolean).sort((a, b) => (a.time?.created || 0) - (b.time?.created || 0));
        const user = info.filter(m => m.role === "user").at(-1);
        const assistant = info.filter(m => m.role === "assistant" && !m.summary).at(-1);
        row.last_started = user?.time?.created || 0;
        if (assistant && (assistant.time?.created || 0) >= row.last_started) {
          if (assistant.error) {
            row.state = "failed";
            row.detail = text(assistant.error.name, "任务失败");
          } else if (assistant.time?.completed && assistant.finish && !["tool-calls", "unknown"].includes(assistant.finish)) {
            row.state = "done";
          }
          row.updated_at = assistant.time?.completed || assistant.time?.created || 0;
        }
      }));
    }
    const statuses = await get(client.session.status.bind(client.session));
    if (statuses && typeof statuses === "object") {
      for (const [id, status] of Object.entries(statuses)) {
        if (["busy", "retry"].includes(status?.type)) {
          const row = await ensure(id);
          if (row && online && !observed.has(id)) { row.state = "running"; changed(row); }
        }
      }
    }
    // Restore outstanding confirmations when the plugin/server is restarted.
    for (const [api, detail] of [[client.permission, "等待授权"], [client.question, "等待回答"]]) {
      if (typeof api?.list !== "function") continue;
      const outstanding = await get(api.list.bind(api));
      for (const request of Array.isArray(outstanding) ? outstanding : []) {
        const row = await ensure(request.sessionID);
        if (row && online && !observed.has(row.id)) { requests.set(request.id, row.id); row.state = "waiting"; row.detail = detail; changed(row); }
      }
    }
    send();
  }

  const accepted = new Set(["session.created", "session.updated", "session.deleted", "session.status", "session.idle",
    "session.error", "message.updated", "permission.asked", "permission.replied", "question.asked", "question.replied",
    "question.rejected", "server.instance.disposed", "global.disposed"]);
  // History reads can be slow on a long-lived server. Live events must not wait
  // behind them, and late history responses must never overwrite live state.
  void bootstrap().catch(() => {});
  const heartbeat = setInterval(() => send(), 5000);
  heartbeat.unref?.();
  function stop() {
    if (!online) return;
    online = false;
    clearInterval(heartbeat);
    send();
    if (registry.get(directory) === stop) registry.delete(directory);
  }
  registry.set(directory, stop);

  async function handle(event) {
    const p = event.properties || {};
    if (["server.instance.disposed", "global.disposed"].includes(event.type)) {
      stop(); return;
    }
    if (["session.created", "session.updated"].includes(event.type)) {
      const row = metadata(p.info);
      if (row) { if (row.parent_id) await ensure(row.parent_id); changed(row); }
      send(); return;
    }
    const id = p.sessionID || p.info?.sessionID || (event.type === "session.deleted" ? p.info?.id : null);
    if (event.type === "session.deleted") {
      observed.add(id);
      sessions.delete(id); removed.add(id);
      if (removed.size > 192) removed.delete(removed.values().next().value);
      send(); return;
    }
    // Ignore assistant streaming deltas; session.status supplies task lifecycle.
    if (event.type === "message.updated" && p.info?.role !== "user") return;
    const row = await ensure(id);
    if (!row) return;
    observed.add(id);
    if (event.type === "message.updated") {
      const stamp = p.info.time?.created;
      // /shell creates its user message after the command exits. It must not move
      // an already running task to the top; chat.message records genuine new input.
      if (!["running", "waiting"].includes(row.state) && Number.isFinite(stamp) && stamp > row.last_started) {
        row.last_started = stamp; changed(row);
      }
    } else if (event.type === "session.status") {
      if (["busy", "retry"].includes(p.status?.type)) {
        // A fresh busy event starts a new attempt, while retries remain blue.
        start(row);
        if (p.status.type === "retry") row.detail = "重试中";
      } else if (p.status?.type === "idle") finish(row);
    } else if (event.type === "session.idle") finish(row);
    else if (event.type === "session.error") {
      row.state = "failed";
      row.detail = p.error?.name === "MessageAbortedError" ? "已取消" : text(p.error?.name, "任务失败");
      changed(row);
    } else if (["permission.asked", "question.asked"].includes(event.type)) {
      requests.set(p.id, id);
      row.state = "waiting";
      row.detail = event.type === "permission.asked" ? "等待授权" : "等待回答";
      changed(row);
    } else if (["permission.replied", "question.replied", "question.rejected"].includes(event.type)) {
      requests.delete(p.requestID);
      if (![...requests.values()].includes(id) && row.state === "waiting") {
        row.state = "running"; row.detail = ""; changed(row);
      }
    }
    send();
  }

  return {
    event: async ({ event }) => { if (accepted.has(event.type)) enqueue(() => handle(event)); },
    "chat.message": async (input, output) => {
      enqueue(async () => {
        const row = await ensure(input.sessionID);
        if (row) { observed.add(row.id); start(row, true, output.message?.time?.created || Date.now()); send(); }
      });
    },
    "tool.execute.before": async (input) => {
      enqueue(async () => {
        const row = await ensure(input.sessionID);
        if (row && row.state !== "waiting") { observed.add(row.id); start(row); send(); }
      });
    },
  };
}
