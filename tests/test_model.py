import tempfile
import unittest
from pathlib import Path

from sessionglow.model import SessionStore
from sessionglow.motion import Motion, TARGETS


def row(sid="main", state="running", started=100, updated=110, parent=None):
    return {"id": sid, "parent_id": parent, "title": sid, "project": "/project",
            "state": state, "last_started": started, "updated_at": updated, "detail": ""}


def packet(rows, seq=1, instance="test", **kwargs):
    return {"instance_id": instance, "sequence": seq, "sessions": rows, **kwargs}


class SessionTest(unittest.TestCase):
    def test_mru_ignores_tools_and_heartbeats(self):
        store = SessionStore()
        store.receive(packet([row("a", started=100), row("b", started=200)]), 0)
        store.receive(packet([row("a", started=100, updated=300), row("b", started=200)], 2), 5)
        self.assertEqual([r["id"] for r in store.rows()], ["b", "a"])
        store.receive(packet([row("a", started=400, updated=400)], 3), 6)
        self.assertEqual([r["id"] for r in store.rows()], ["a", "b"])

    def test_children_wait_and_run_belong_to_root(self):
        store = SessionStore()
        roots = [row(), row("other", started=50)]
        child = row("child", "waiting", parent="main")
        store.receive(packet(roots + [child]), 0)
        visible = store.rows(now=0)
        self.assertEqual(len(visible), 2)
        self.assertEqual(visible[0]["state"], "waiting")
        self.assertEqual(visible[0]["children"], 1)
        store.receive(packet(roots + [dict(child, state="done", updated_at=120)], 2), 1)
        self.assertEqual(store.rows(now=1)[0]["state"], "running")
        store.receive(packet([row(state="done", updated=130), dict(child, state="running", updated_at=125)], 3), 2)
        self.assertEqual(store.rows(now=2)[0]["state"], "running")

    def test_old_child_wait_does_not_override_new_task(self):
        store = SessionStore()
        store.receive(packet([row(started=300, updated=300), row("child", "waiting", parent="main")]), 0)
        self.assertEqual(store.rows(now=0)[0]["state"], "running")

    def test_sequences_multi_instance_and_stale_connection(self):
        store = SessionStore()
        store.receive(packet([row()], instance="a"), 0)
        self.assertFalse(store.receive(packet([row(state="done")], instance="a"), 1))
        store.receive(packet([row(updated=120)], instance="b"), 15)
        self.assertTrue(store.rows(now=22)[0]["connected"])
        self.assertFalse(store.rows(now=36)[0]["connected"])
        self.assertEqual(store.rows(now=36)[0]["state"], "running")

    def test_history_survives_restart_without_claiming_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / "history.json"
            store = SessionStore(cache)
            store.receive(packet([row(state="failed")]), 0)
            store.save()
            restored = SessionStore(cache)
            result = restored.rows(now=1)[0]
            self.assertEqual(result["state"], "failed")
            self.assertFalse(result["connected"])
            self.assertEqual(result["last_started"], 100)

    def test_delete_and_malformed_payload(self):
        store = SessionStore()
        store.receive(packet([row()]), 0)
        self.assertFalse(store.receive(packet([dict(row(), state=[])], 2), 1))
        self.assertFalse(store.receive(packet([dict(row(), updated_at=float("nan"))], 2), 1))
        store.receive(packet([], 2, removed=["main"]), 2)
        self.assertEqual(store.rows(), [])

    def test_diagnostics_identify_separate_server_sources_and_expire(self):
        store = SessionStore()
        store.receive(packet([row()], source={"endpoint": "127.0.0.1:4096", "directory": "/demo", "pid": 10}), 0)
        store.receive(packet([row("other")], instance="managed", source={"endpoint": "127.0.0.1:39195", "directory": "/other"}), 5)
        self.assertEqual({s["endpoint"] for s in store.sources(now=6)}, {"127.0.0.1:4096", "127.0.0.1:39195"})
        self.assertEqual(len(store.sources(now=21)), 1)
        self.assertEqual(store.sources(now=26), [])


class MotionTest(unittest.TestCase):
    def test_all_transitions_start_at_exact_current_frame(self):
        motion = Motion(0)
        now = 0.0
        for state in ("running", "waiting", "failed", "done", "running"):
            now += 0.21  # Interrupt previous transitions while they are still in flight.
            before = motion.values(now)
            phase, travel = motion.phase, motion.travel
            motion.change(state, now)
            self.assertEqual(before, motion.values(now))
            self.assertEqual((phase, travel), (motion.phase, motion.travel))
        self.assertEqual(motion.values(now + 1), TARGETS["running"])

    def test_failure_stops_particle_travel_and_green_has_no_electricity(self):
        motion = Motion(0)
        motion.change("failed", 0)
        motion.advance(1)
        before = motion.travel
        motion.advance(1.1)
        self.assertEqual(motion.travel, before)
        self.assertEqual(motion.values(1)[3], 0)
        motion.change("done", 2)
        values = motion.values(3)
        self.assertEqual(values[6], 0)
        self.assertEqual(values[7], 1)


if __name__ == "__main__":
    unittest.main()
