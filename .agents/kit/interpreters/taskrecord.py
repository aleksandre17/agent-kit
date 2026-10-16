"""The task RECORD of one dispatch -- opened at `submitted` before anything is started, moved through
the A2A task states, and closed exactly once (ADR-017 decision 6).

A record written only at the end proves nothing about a dispatch that never reached the end; a
worker started by a process that then died leaves a tree full of changes that reads exactly like
finished work. So the record is the first write of a dispatch and its last, and this is its one
writer.
"""

from __future__ import annotations

import json

import dispatching
import ephemeral

class Record:
    """One task record, held open and rewritten at every transition -- the same life a run receipt
    and an install journal have, for the same reason. Every transition is FLUSHED: batching the
    writes for the end would make this document exactly the thing it exists to refute."""

    __slots__ = ("ctx", "workspace", "rel", "value")

    def __init__(self, ctx, workspace, rel: str, value: dict) -> None:
        self.ctx, self.workspace, self.rel, self.value = ctx, workspace, rel, value

    @staticmethod
    def opened(ctx, rel: str, *, packet, adapter, workspace, lease, now) -> "Record":
        value = {
            "schema_version": ctx.manifest.version_of(dispatching.TASK),
            "id": packet["id"],
            "state": dispatching.SUBMITTED,
            "packet": packet,
            "adapter": adapter,
            "workspace": workspace,
            "branch": packet["branch"],
            "lease": lease,
            "opened_at": now,
            "kit_version": ctx.manifest.version,
            "boundary": ctx.boundary(),
        }
        record = Record(ctx, ephemeral.scope(ctx), rel, value)
        record._flush("as this dispatch opens it")
        return record

    @staticmethod
    def reopened(ctx, rel: str) -> "Record":
        """A record that is already standing, read back so the SAME document goes on being
        rewritten. A resume that opened a second record would leave two accounts of one task, and
        each would be internally correct."""
        try:
            value = json.loads(ctx.workspace.path(rel).read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            raise dispatching.DispatchRefused(
                f"the task record at {rel} cannot be read back -- {exc}. What a worker was told and "
                f"what state it is in are that document's to say; nothing is re-entered on a "
                f"record this host cannot read") from exc
        return Record(ctx, ephemeral.scope(ctx), rel, value)

    def moment(self) -> str:
        """WHEN this record last said anything -- so a state is never reported without the moment
        it was taken at. A state with no moment goes on certifying for as long as it sits there."""
        turns = self.value.get(dispatching.HISTORY) or []
        return (self.value.get("ended_at") or (turns[-1]["at"] if turns else None)
                or self.value.get("started_at") or self.value["opened_at"])

    def reentry(self):
        """The way back into the worker standing at this record: the token of the LAST question it
        asked, or None. A worker resumed twice hands back a new one each time, and the earliest
        token would re-enter a turn that is already over."""
        for turn in reversed(self.value.get(dispatching.HISTORY) or []):
            if turn["role"] == dispatching.AGENT and turn.get(dispatching.REENTRY):
                return turn[dispatching.REENTRY]
        return None

    def asked(self, code: int, turn: dict, artifacts, admission) -> None:
        """The worker stopped and asked. NOT an ending: no `ended_at` is written, because the task
        has not ended and a moment written here would say it had. What the worker produced on the
        way to asking, and the verdict on what it left in its tree, are recorded exactly as they
        are at any other return."""
        self.value.update(state=dispatching.INPUT_REQUIRED, exit_code=code, artifacts=artifacts,
                          admission=admission)
        self.value.setdefault(dispatching.HISTORY, []).append(turn)
        self._flush("as this worker asks for input")

    def answered(self, at: str, text: str, by: str = None) -> None:
        """The operator's turn, written before the worker is re-entered with it."""
        self.value.setdefault(dispatching.HISTORY, []).append(
            dict({"role": dispatching.OPERATOR, "at": at, "text": text}, **({"by": by} if by else {})))
        self._flush("as an answer is carried back into it")

    def _flush(self, moment: str) -> None:
        errors = self.ctx.manifest.validate(self.value, dispatching.TASK)
        if errors:
            raise dispatching.VocabularyDrift(f"{self.rel} {moment} does not honour the kit schema {dispatching.TASK!r}, "
                                  f"and a task record that is not one is not written:\n  "
                                  + "\n  ".join(errors))
        self.workspace.write_json(self.rel, self.value)

    def move(self, state: str, **fields) -> None:
        self.value.update(state=state, **fields)
        self._flush(f"as it moves to {state}")

    def close(self, state: str, code: int, message: str = None, artifacts=None,
              admission=None) -> None:
        """The end, stated in the same act as its moment. A state without a moment goes on
        certifying for as long as it sits there and cannot be contradicted."""
        self.value.update(state=state, ended_at=self.ctx.clock.now(), exit_code=code)
        if artifacts is not None:
            self.value["artifacts"] = artifacts
        if admission is not None:
            self.value["admission"] = admission
        if message:
            self.value["status_message"] = message
        self._flush("as this dispatch closes it")
