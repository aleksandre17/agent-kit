"""The served-setting gate -- a surface whose product runs its served files only once a setting
outside the tree names them is read on every check as ACTIVE, INACTIVE, ELSEWHERE or UNREADABLE.

A served hook the product never runs is the silence this exists to name: the files are present,
the record is whole, every projection gate is green, and nothing is guarded. The reading states
the moment it was taken and is never cached, because the setting's one home is the product's
configuration and anyone may change it there.
"""

from __future__ import annotations

import activation

KIND = "served-setting-active"


def _active(ctx, params):
    failures = []
    moment = ctx.clock.now()
    for surface, declared in sorted(activation.served(ctx).items()):
        state, value, detail = activation.reading(ctx, declared)
        where, setting = declared["points_at"], declared["setting"]
        if state == activation.INACTIVE:
            failures.append(f"{surface}: INACTIVE, read at {moment} -- {setting} is unset, so the "
                            f"product never runs what is served at {where}. The door: "
                            f"`activate --surface {surface} --approve <who>`.")
        elif state == activation.ELSEWHERE:
            failures.append(f"{surface}: ELSEWHERE, read at {moment} -- {setting} names {value!r}, "
                            f"not {where}, so what is served there never runs. The kit does not "
                            f"overwrite a setting it did not make; its owner changes it.")
        elif state == activation.UNREADABLE:
            failures.append(f"{surface}: UNREADABLE, read at {moment} -- {setting} could not be "
                            f"read ({detail}); an unread setting is not an active one.")
        else:
            idle = activation.unexecutable(ctx, declared)
            if idle:
                failures.append(f"{surface}: ACTIVE, read at {moment}, but {', '.join(idle)} under "
                                f"{where} lack(s) the execute bit, so the product skips them.")
            else:
                print(f"  {surface}: ACTIVE, read at {moment} -- {setting} = {value}")
    return failures


KINDS = {KIND: _active}
