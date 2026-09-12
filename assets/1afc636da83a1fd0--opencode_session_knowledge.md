# OpenCode Session Knowledge — galbot_s1_SDK_learning

Extracted: 2026-08-20
Source workspace: `/home/lsy03/Lsy03_document/galbot_s1_SDK_learning`
Raw session store: `/home/lsy03/.local/share/opencode/opencode.db`

## Scope and handling

Five OpenCode sessions were found whose stored working directory exactly matches the source workspace:

1. `长期任务支持功能初始化`
2. `模型provider是否官方`
3. `8_15 继续对话`
4. `当前是否使用deepseekharness`
5. `继续8_15对话`

The raw database is not copied into this repository. It may contain tool output, provider/account metadata, and unrelated operational details. This document keeps only durable project knowledge. Credentials and authentication material are deliberately excluded.

Historical chat is the lowest-priority evidence source. When it conflicts with current source code, current real-robot observation, or accepted project documentation, report the conflict and use the stronger evidence.

## Workspace and knowledge-system decisions

- `VERIFIED`: The source workspace is a Git repository and contains a file-based knowledge system under `docs/`, plus `AGENTS.md`, `README.md`, an OpenCode configuration, commands, module directories, SDK examples, and `third_party/GalbotSDK`.
- `VERIFIED`: Its intended startup path is `AGENTS.md` → `docs/00_KNOWLEDGE_INDEX.md` → `PROJECT_CONTEXT.md` + `CURRENT_STATE.md` → task-specific documents/code.
- `VERIFIED`: OpenCode sessions are stored in the user-level SQLite database, not in `docs/sessions/`. The source `docs/sessions/` directory was empty when inspected on 2026-08-20.
- `ACCEPTED HISTORICAL DECISION`: Git-tracked Markdown, not one chat/session, is the long-term source of truth.
- `ACCEPTED HISTORICAL DECISION`: `third_party/` is reference code and is not edited by default.
- `ACCEPTED HISTORICAL DECISION`: Load a small core context and retrieve other documentation/code on demand.

## Source workspace state observed on 2026-08-20

- `VERIFIED`: Git history contains commits for workspace initialization, SDK reference import, read-only robot verification, head micro-movement, left-arm micro-movement, and visible head movement.
- `VERIFIED`: `third_party/GalbotSDK` is described by the source repository as a reference snapshot containing type stubs/examples rather than a complete locally runnable robot installation.
- `VERIFIED`: The following scripts exist locally and were untracked in the source repository when inspected:
  - `sdk_examples/restore_pre_example2_pose.py`
  - `sdk_examples/restore_torso_home.py`
  - `sdk_examples/restore_arms_pre_example2.py`
- `HISTORICAL`: The source `CURRENT_STATE.md` was last dated 2026-08-15 and does not include the later `example2`/torso incident. It must not be treated as a complete current state without reconciliation.

## Reported real-robot experiments

The following results come from OpenCode session text and the source Git history. They are historical evidence and should be revalidated if the current robot/software environment matters.

- `VERIFIED (historical run)`: SSH access to the robot endpoint succeeded during the 2026-08-15 work, and Galbot SDK `1.9.0` was reported importable on the robot.
- `VERIFIED (historical run)`: Robot/device and arm joint state were read without commanding motion.
- `VERIFIED (historical run)`: A head `+0.05 rad` micro-movement and return was reported with final error around `0.0025 rad`.
- `VERIFIED (historical run)`: A left-arm joint-1 `+0.1 rad` micro-movement and return was reported with error around `0.00017 rad`.
- `VERIFIED (historical run)`: A head movement of approximately `±0.4 rad` was reported to return with error around `0.00005 rad`.
- `HISTORICAL`: An SDK message later advertised version `1.9.1`. This proves only that an update was advertised at that time, not the currently installed or appropriate version.

## Critical safety incident and correction

### What happened

1. An official/example workflow moved the whole body to a home-like pose in which both arms appeared raised.
2. OpenCode attempted to construct a “restore previous pose” script.
3. The earlier snapshot included arm values but did **not** include the prior torso value.
4. OpenCode guessed `torso=0` and described it as a zero/home target.
5. Running the script drove the torso lift downward. The user reported that the waist moved toward its lowest position.
6. Further motion was stopped and state was read. The torso value was reported around `0.4331`.
7. A separate torso-only script moved it to `0.74`; the user-provided terminal output reported `ControlStatus.SUCCESS` and final torso `[0.74]`.

### Evidence classification

- `VERIFIED (historical source code)`: `restore_pre_example2_pose.py` contains the unjustified target `"torso": [0.0]` while its own comments call the entire target “VERIFIED.” That label is false for torso.
- `VERIFIED (historical run)`: The user observed unintended torso descent after running it.
- `HISTORICAL / NEEDS_CONFIRMATION`: The later script records a `torso_lift_joint1` range of `0` to `0.75` and interprets `0` as lowest, `0.75` as highest. Reconfirm against the exact robot model/version configuration before future use.
- `OBSERVATION, NOT A SAFE TARGET`: The arm joint vectors captured before `example2` were real measured values, but only prove the pose observed at that moment. They do not prove a factory, natural, home, or otherwise correct pose. The user explicitly questioned the restored result.

### Binding lessons

- Never move an unmeasured group as part of a recovery operation.
- “Zero,” “home,” “initial,” and “safe” are distinct concepts and must not be treated as synonyms.
- A recovery pose requires a complete pre-motion snapshot for every affected group, or an authoritative configuration matching the exact robot and software version.
- Preview every affected group and numeric target before motion.
- Use one group at a time, low speed, bounded range, clear workspace, available physical emergency stop, and post-command state verification.
- A successful SDK return code proves command execution, not that the chosen target was semantically correct or safe.
- Do not use `restore_pre_example2_pose.py`. Do not treat `restore_arms_pre_example2.py` as a canonical recovery script without the user visually validating the intended pose.

## User authorization boundary

The user ended the earlier work by requiring that OpenCode not unexpectedly control the robot and that its own SSH activity be disconnected.

For this project:

- Do not initiate or retain a robot SSH session without explicit authorization in the current task.
- Read-only inspection is preferable, but remote access itself still requires the current task to place the robot in scope.
- Never send a real motion command automatically.
- Obtain fresh, step-specific confirmation after stating the device, exact expected motion, affected arm/gripper/lift/base, numeric target or bound, collision zone, speed, stopping method, and physical emergency-stop readiness.
- Do not interpret approval for one motion as approval for another.

## Configuration/provider discussions

- `HISTORICAL`: OpenCode reported that the active model/provider was `deepseek/deepseek-v4-flash` through its built-in DeepSeek provider and that no DeepSeek Harness integration was detected.
- These provider claims are unrelated to S1 behavior and may now be stale. Reinspect current OpenCode configuration before relying on them.

## Known conflicts and stale records

- Source `CURRENT_STATE.md` says the local SDK reference lacks a runtime `.so`, while historical runs succeeded on the robot. These are compatible only if the SDK runtime existed remotely but not in the local reference checkout.
- Source `HARDWARE_SOFTWARE.md` leaves robot IP, SDK version, and OS as `NEEDS_CONFIRMATION`, while later session/source history contains partial observations. Reconcile rather than silently overwriting.
- The historical OpenCode assistant sometimes upgraded its own statements to `VERIFIED` without adequate evidence. Every imported claim in this document therefore names its evidence boundary.

## Next safe use

Use the source workspace primarily as a read-only reference. Before any further real-robot experiment:

1. reconcile its `CURRENT_STATE.md` with the later session history;
2. quarantine or clearly deprecate unsafe recovery scripts in that repository only if the user explicitly asks to modify it;
3. confirm robot identity, SDK version, joint-group semantics, limits, current full-state snapshot, and physical emergency-stop procedure;
4. begin with a local/static or read-only task rather than motion.