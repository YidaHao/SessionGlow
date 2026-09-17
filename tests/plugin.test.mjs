import assert from "node:assert/strict";
import { createServer } from "node:http";
import test from "node:test";
import SessionGlow from "../plugin/sessionglow.mjs";

test("explicit lifecycle, child metadata, task ordering and terminal errors over real HTTP", async (t) => {
  const packets = [];
  const server = createServer((req, res) => {
    let raw = "";
    req.on("data", part => { raw += part; });
    req.on("end", () => { packets.push(JSON.parse(raw)); res.writeHead(204).end(); });
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  process.env.SESSIONGLOW_PORT = String(server.address().port);
  const main = { id: "main", title: "Main task", directory: "/demo", time: { updated: 100 } };
  const child = { id: "child", parentID: "main", title: "Child" };
  const client = { session: {
    list: async () => ({ data: [main] }),
    get: async ({ path }) => ({ data: path.id === "child" ? child : main }),
    status: async () => ({ data: {} }),
    messages: async () => ({ data: [] }),
  } };
  const hooks = await SessionGlow({ client, directory: "/demo", serverUrl: new URL("http://user:secret@127.0.0.1:4096/?token=secret") });
  let replacement;
  const event = (type, properties = {}) => hooks.event({ event: { type, properties } });
  t.after(async () => {
    await event("server.instance.disposed");
    if (replacement) await replacement.event({ event: { type: "server.instance.disposed", properties: {} } });
    await new Promise(resolve => setTimeout(resolve, 20));
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
    delete process.env.SESSIONGLOW_PORT;
  });
  async function waitFor(predicate) {
    const deadline = Date.now() + 3000;
    while (Date.now() < deadline) {
      const packet = packets.at(-1);
      if (packet && predicate(packet)) return packet;
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    assert.fail("Expected plugin snapshot not received: " + JSON.stringify(packets.at(-1)));
  }
  const latest = id => packets.at(-1)?.sessions.find(row => row.id === id);
  await waitFor(p => p.sessions[0]?.state === "unknown");
  assert.equal(packets.at(-1).source.endpoint, "127.0.0.1:4096");
  assert.equal(packets.at(-1).source.directory, "/demo");
  assert.equal(JSON.stringify(packets).includes("secret"), false);
  await hooks["chat.message"]({ sessionID: "main" }, { message: { time: { created: 1000 }, content: "private prompt" } });
  await waitFor(p => p.sessions[0]?.state === "running");
  const started = latest("main").last_started;
  await hooks["tool.execute.before"]({ sessionID: "main", tool: "bash" });
  await event("session.status", { sessionID: "main", status: { type: "retry" } });
  await waitFor(p => p.sessions[0]?.detail === "重试中");
  assert.equal(latest("main").last_started, started);
  await event("message.updated", { info: { sessionID: "main", role: "user", time: { created: Date.now() } } });
  await new Promise(resolve => setTimeout(resolve, 25));
  assert.equal(latest("main").last_started, started, "Late shell transcript must not reorder the active task");
  await event("permission.asked", { sessionID: "child", id: "p1" });
  await event("question.asked", { sessionID: "child", id: "p2" });
  await event("permission.replied", { sessionID: "child", requestID: "p1" });
  await waitFor(p => p.sessions.some(r => r.id === "child" && r.state === "waiting"));
  assert.equal(latest("child").parent_id, "main");
  await event("question.replied", { sessionID: "child", requestID: "p2" });
  await waitFor(p => p.sessions.some(r => r.id === "child" && r.state === "running"));
  await event("session.idle", { sessionID: "child" });
  await waitFor(p => p.sessions.some(r => r.id === "child" && r.state === "done"));
  assert.equal(latest("main").state, "running");
  await event("session.error", { sessionID: "main", error: { name: "APIError", data: { message: "private error" } } });
  await event("session.status", { sessionID: "main", status: { type: "idle" } });
  await event("session.idle", { sessionID: "main" });
  await waitFor(p => p.sessions.find(r => r.id === "main")?.state === "failed");
  assert.equal(latest("main").detail, "APIError");
  assert.equal(JSON.stringify(packets).includes("private"), false);
  await hooks["chat.message"]({ sessionID: "main" }, { message: { time: { created: 2000 } } });
  await waitFor(p => p.sessions[0]?.state === "running");
  assert.equal(latest("main").last_started, 2000);
  await event("session.idle", { sessionID: "main" });
  await waitFor(p => p.sessions[0]?.state === "done");
  // Terminal sessions remain in snapshots, including after a heartbeat.
  assert.equal(latest("main").title, "Main task");

  // A server's large history must not delay a new task or overwrite its live state.
  let releaseHistory;
  client.session.messages = async () => new Promise(resolve => { releaseHistory = resolve; });
  const originalID = packets.at(-1).instance_id;
  replacement = await SessionGlow({ client, directory: "/demo", serverUrl: "http://127.0.0.1:4096" });
  await replacement["chat.message"]({ sessionID: "main" }, { message: { time: { created: 3000 } } });
  const live = await waitFor(p => p.instance_id !== originalID && p.sessions[0]?.state === "running");
  assert.equal(live.sessions[0].last_started, 3000);
  assert.equal(typeof releaseHistory, "function");
  releaseHistory({ data: [{ info: { role: "user", time: { created: 1000 } } },
    { info: { role: "assistant", time: { created: 1100, completed: 1200 }, finish: "stop" } }] });
  await waitFor(p => p.instance_id === live.instance_id && p.sequence > live.sequence);
  assert.equal(latest("main").state, "running");
  assert.equal(latest("main").last_started, 3000);
});
