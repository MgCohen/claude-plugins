---
name: unity-field-notes
description: Tested rules and results for Unity Editor automation with the unity CLI and com.unity.pipeline on Windows - start, compile check, Safe Mode, dialogs, stop, focus, command queue, freezes, crashes, Play Mode input, logs, captures and players. Use with the unity-cli skill when you start, stop or drive a Unity Editor or player from automation, or when a command fails with exit 6, 14, 17 or 18. These results come before the docs where they differ.
---

# Unity field notes

These are results of real tests on Windows 11. Where the docs and these results differ, the results win until a new test says otherwise.

| Item | Tested versions |
|---|---|
| unity CLI | 1.0.0 (2026-11-14), 1.0.1 (from 2026-11-17) |
| com.unity.pipeline | 1.0.0 |
| Unity Editor | 6000.7.0b9 (2026-11-14 to 11-16), 6000.6.6f1 (from 2026-11-17) |
| Input System | 6.7.0 |

If your versions are newer, test a note again before you trust it.

## Rules

1. Start each automation Editor with `unity open <project> --args "-automated" --until-ready`. Without `-automated`, an Editor with no focus never runs `EditorApplication.delayCall`.
2. Before you start an Editor on code that can fail to compile, run a batch compile: `Unity.exe -batchmode -quit -nographics -projectPath <p> -logFile <f>`, with no Editor open on the project. Exit 1 and `error CS...` or `error UMP...` lines in the log mean: fix the code first.
3. An `-automated` start with a compile error enters Safe Mode with no dialog. The pipeline server does not run, and `--until-ready` waits until its time-out. Close it with `(Get-Process -Id <pid>).CloseMainWindow()`, fix the code, then start again. A restart with the same code enters Safe Mode again.
4. On a running Editor, find compile errors with `unity recompile` (about 7 s, file, line and code). The old domain stays loaded.
5. Act on an Editor only by the PID that you started. Never act on Unity by process name. In each command pass `--pid` or `--project-path`, never rely on the current folder.
6. Answer native dialogs with `scripts/answer-dialog.ps1 -ProcessId <pid> -Title <title> -Button <label>`. The CLI cannot answer dialogs on Unity 6000.6 or 6000.7. Always pass `-Title`: Unity's busy window is also a `#32770` window with a "Cancel" button.
7. Stop an Editor in this order: `unity command editor quit --save` or `--discard`, then `CloseMainWindow()` by PID, then a stop by PID.
8. Save or discard dirty scenes by API before a test run. Otherwise `test run` waits on a hidden save prompt and fails with exit 14 and no text.
9. Use `http://127.0.0.1:<port>`, not `localhost` (HTTP 400). Take the port and the bearer token (`evalToken`) from `Library/Pipeline/.unity-pipeline-port`. Never print the token.
10. One `unity command` call costs about 4.5 s on this computer. For a fast loop, call the HTTP API (about 20 ms) or keep one `unity mcp --pid <pid>` process open (5 to 15 ms for each call).
11. One Editor runs one command at a time. Keep commands short. For long work, use a detached job with an async command that checks its cancellation token, or `job wait --async true`.
12. `/api/status`, the descriptor heartbeat and `unity status` stay `ready` during a frozen main thread. To find a freeze, use a main-thread beacon or a probe with a short `timeout`, and read `/api/progress` or `/api/job` before you call a slow probe a freeze.
13. Check that the descriptor `pid` and `projectPath` match your Editor before you trust it.
14. Never use `capture editor_window`: it hung and crashed the Editor 2 times out of 2. Always pass `--output-path` to a capture.
15. In Editor Play Mode, a key event must reach the game through the player loop: queue it, and do not call `InputSystem.Update()`. `runtime simulate_key` does not work there.

## Start and compile

- `-automated` starts the normal Editor with its window (not batch mode, `Application.isBatchMode` false). The log line is `BatchMode: 0, IsHumanControllingUs: 0, StartBugReporterOnCrash: 0`. The descriptor `info` field is empty.
- In `-automated`, `EditorUtility.DisplayDialog` returns at once (2 ms) with `false` (the cancel button), and no dialog shows.
- Batch compile check: good code exits 0 in 13 to 17 s. Broken code exits 1 in about 8.5 s, with "Scripts have compiler errors." No Safe Mode in batch mode, and no process stays. Unity can hold the log for a moment after the exit: read it with shared access. It also finds analyzer errors with severity error.
- A package that cannot resolve (a bad `manifest.json` entry): with `-automated`, no dialog; the Editor logs "An error occurred while resolving packages" and exits with code 1 after about 5 s. The batch check gives the same lines.
- Warm start with `unity open --until-ready`: `Unity.exe` appears after about 6 s, `ready` after 18 to 22 s. A worktree Editor with a cache seed was ready in 70 s.
- Cold start: `/api/status` says `settling`, and main-thread commands get HTTP 503 with `busyReason: "settling"`, `retryable: true`. Wait for `ready`, not for the descriptor file.
- A second `Unity.exe -projectPath <same>` exits by itself with code 0 and no dialog. The first Editor is not affected. A launcher must check for a running Editor first, because the second start gives no error.
- `-logFile <path>` through `unity open . --args "-automated -logFile <path>"` works for that process only.

## Safe Mode

- In Safe Mode, the pipeline server does not run, so `status`, `recompile`, `unity close` and all commands fail. The window title has "SAFE MODE", and the log says "Safe Mode: Only loading a subset of assemblies".
- Without `-automated`, Unity shows the "Enter Safe Mode?" dialog. Press `Quit`, never "Enter Safe Mode".
- The Editor did not leave Safe Mode after a fix, also with window focus. The docs say that it does.
- `-ignoreCompilerErrors` does not prevent Safe Mode.

## Dialogs

| Step | Works? | How |
|---|---|---|
| Detect at start (6000.7) | Yes | `unity open --until-ready` fails in 3 to 11 s with `OPEN_BLOCKED_BY_DIALOG*`, the title and the buttons |
| Detect while running (6000.7) | Yes | `GET /api/status` gives `blocked_by_dialog`. `GET /api/dialog` gives the id, the title and the buttons. |
| Command while blocked | Fails fast | Exit 18 (`AWAITING_INPUT`) in about 6 s, with the dialog text |
| `unity status` | Wrong | Shows `starting` |
| Answer with the CLI | No | `editor dialog` and `editor.dialog` give "No command named..." (exit 13). The docs call it a Unity 7 feature, "probably not backported". |
| Answer with Win32 | Yes | `scripts/answer-dialog.ps1` sends `BM_CLICK` to the button |

- The dialog server API needs Unity 6000.7 or later. On 6000.6, only the Win32 script can see dialogs: a visible `#32770` window of the Editor PID.
- The script finds only native message boxes of that PID. It cannot answer an Editor window opened with `ShowModal`.
- After an answer, read `/api/dialog` again. A second dialog can open.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/answer-dialog.ps1 -ProcessId <pid> -List
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/answer-dialog.ps1 -ProcessId <pid> -Title "<title>" -Button "<label>"
```

Exit codes of the script: 0 pressed, 3 no dialog, 4 no such button.

Dialog policy:

| Dialog | Answer |
|---|---|
| "Enter Safe Mode?" | `Quit`, fix the code, start again |
| "Scene Backup Detected" | `Delete` for clean runs. "Keep Backups" does not load the backup. |
| Your own `DisplayDialog` | The button that the test expects. The Editor is `ready` again at once. |
| "URP Material upgrade" (from the docs) | OK. It blocks each command in a new URP project. |
| Software Terms (from the docs) | Run `unity terms accept <version> --yes` before the first open |

- Unity's busy window (progress bar) is a `#32770` window with the buttons "Cancel" and "Skip Transcoding". Its title gives the phase ("Importing", "Reloading Domain", "Hold on...", "Running managed callbacks (busy for 31s)..."). It is not a dialog.
- No scene backup dialog showed after a crash with a dirty scene and Play Mode, in `-automated` (3 of 3).
- Not tested: license, Hub sign-in and Software Terms dialogs.

## Stop an Editor

| Command | Unsaved changes | Result |
|---|---|---|
| `unity command editor quit` | Refuses, exit 6 | Lists the dirty scenes |
| `unity close <project> --if-saved` | Refuses | `reason: unsaved_changes` |
| `editor quit --save` or `--discard` | Saves or drops them | Exits in 2 to 9 s. The server goes down just before the exit. |
| `CloseMainWindow()` by PID | n/a | Works when the pipeline does not run. No effect while the main thread is frozen. |

A clean quit also deletes the scene backups, so the next start has no backup dialog.

## Focus

- Without `-automated` and with no focus, the `delayCall` queue never ran: it grew from 55 to 70 items in 20 s. `EditorApplication.update` ran about 62 000 times each second. `editor set_auto_tick` does not fix it. The docs call it a known bug of Pipeline 1.0.0.
- With `-automated` and no focus, `delayCall` runs normally.
- Commands run on the main thread with no focus. `unity recompile` works with no focus.

## Several Editors, ports and descriptors

- Each Editor takes the first free port in 7800-7849 and writes it to its own `Library/Pipeline/.unity-pipeline-port`. Follow the descriptor, never a fixed port.

| How you call `unity command` | Result |
|---|---|
| From a project folder or a subfolder | Goes to the Editor of that project |
| From a folder outside all projects | Fails, exit 6, `AMBIGUOUS_EDITOR`, with the list of Editors |
| `--project-path <path>` | Goes to that project, from any folder |
| `--pid <pid>` or `--port <port>` | Goes to that Editor, from any folder |

- If all ports 7800-7849 are taken, the Editor starts with no HTTP server and no descriptor, and `unity status` says `STATUS_NO_INSTANCES`. The server does not try again when the ports become free. Only a restart helps.
- `--seed full` and `--seed cache` do not copy the descriptor. A descriptor copied from another live Editor sends commands to that Editor until the own Editor writes its descriptor (about 12 s after its start).
- The descriptor is deleted before each domain reload. A reload stops each running command and job, and sets active `job wait` calls to `interrupted`.
- After a crash or a stop by PID, the descriptor stays with the dead PID for about 1 to 4 s, then the CLI parent removes it.

## Command cost and the HTTP API

- `unity command` takes about 4.5 s for each call, also for `editor status`: about 1.4 s to start the CLI and 3 s of Editor discovery (`tasklist`, then a new `powershell.exe`), also with `--pid`. `unity status` takes about 5 s. The docs say 118 to 600 ms, so this is probably this computer.
- `unity shell --protocol ndjson` does not help: each command still takes about 4.6 s.
- `unity mcp --pid <pid>` (MCP over stdio): `tools/list` took 2.7 s once, then each `tools/call` took 5 to 15 ms. Custom `[CliGroupCommand]` commands show as tools.
- Direct HTTP: `POST /api/exec` with `Authorization: Bearer <evalToken>` and `{"argv":["<group>","<command>"],"timeout":<ms>}` takes about 20 ms. `GET /api/status` takes less than 10 ms.
- The default time-out of `unity command` is about 60 s. A 40 s command completed with `--timeout 120`.
- Exit codes: 6 refused, busy or `success:false`; 13 no such command; 14 time-out; 17 `UNAVAILABLE` (busy or reloading, try again); 18 blocked by a dialog.

## The command queue

One Editor runs one command at a time, in arrival order:

| Command kind | Holds the queue? | Notes |
|---|---|---|
| Sync `ExitCode` | Yes, and it blocks the main thread | Cannot stop from outside |
| Async `Task<ExitCode>` | Yes, for its full time | The Editor draws frames, but a ping waits behind it |
| `MainThreadRequired = false` | Yes | Two of them ran one after the other |
| Detached job (`"job": true`) | Yes, while it runs | Returns `jobId` at once (`result.jobId`) |
| `job wait --async true` | No | Returns `waitId` at once. Other commands run meanwhile. |
| Sync `job wait` | Yes | A ping waited until the wait timed out |

- Off the queue: `GET /api/status`, `/api/job?id=`, `/api/progress`, `/api/dialog`.
- `POST /api/job/cancel {"id":"<jobId>"}` sets the token. An async command that checks `cmd.CancellationToken` stops at once. A sync command runs to the end, but its job state is `canceled`.
- The `timeout` field of `/api/exec` cancels the token of a running command. A queued request that does not start within its `timeout` gets HTTP 504 "did not start within" and never runs, so a probe never fills the queue.
- 110 parallel requests behind a 20 s command: 98 waited, 12 got HTTP 429. A probe with a short `timeout` gets 504, not 429.
- A command that times out on the CLI side is not cancelled. It keeps the queue busy.
- `script eval` and `script run`: a time-out does not stop the script, and each call loads an assembly that cannot unload.
- `job batch` takes up to 200 operations in one transaction. It refuses waits, tests, Play Mode, scripts, builds and runtime commands, and it blocks the main thread.

## Freezes and status signals

Signals that lie during a frozen main thread (sleep or busy loop, 75 to 90 s):

| Signal | Result |
|---|---|
| `GET /api/status` and `unity status` | `ready` |
| Descriptor `lastHeartbeat` | Keeps moving (every 15 s, from another thread) |
| CPU time of the Editor | Background threads use CPU, also during a start hang |
| `CloseMainWindow()` | No effect while the main thread sleeps |

Signals that work:

| State | Signal | Time to detect |
|---|---|---|
| Frozen main thread | A beacon file written from `EditorApplication.update` stops moving | about 2.7 s (3 s age limit) |
| Frozen main thread | `IsHungAppWindow(main window)` is true | about 5 s, only when Unity shows no busy window |
| Busy queue, not frozen | Probe 504, and the beacon still moves | first sample |
| Native dialog | A visible `#32770` window of the Editor PID that is not the busy window | first sample |
| Hang in game code (Play Mode) | The beacon stops, `IsHungAppWindow` true after about 4.8 s | Unity shows no busy window in Play Mode |

- A command to a frozen Editor fails with exit 14 after its time-out (about 9.5 s with `--timeout 5`). A command to a second Editor still works.
- During a hang in a domain reload: the server and the descriptor are gone, `IsHungAppWindow` stays false, the beacon is still, and the busy window counts up ("busy for 01:01" after 60 s).
- A stall rule must not count CPU time. A start hang stalled at about 127 s with a 120 s stall window, and the Editor was ready about 180 s after a restart.
- The pipeline server can be stopped and started natively (`Unity.Pipeline.Editor.PipelineServerStartup.StopServer()` and `EnsureServerStarted()`, internal static, by reflection). While it is off, the beacon moves and `/api/status` refuses. The rule "no server, beacon moves, no Unity event for 10 s (30 s at a start)" finds it in 2 to 15 s.

Progress, readable from outside with Win32 (no focus):

- Startup window: class `UnitySplashWindow`, title "Opening project...". Child `msctls_progress32` (range 0 to 100): read it with `SendMessageTimeout` `PBM_GETPOS` (0x0408) and `PBM_GETRANGE` (0x0407). The status text on the image is drawn, so read the log for it. The bar can stand still for 30 s or more during a healthy open.
- In-Editor busy window: child `msctls_progress32` (range 0 to 1000) and a `Static` control with the step text, for example the asset path that is importing.
- The "busy for Ns" counter is not progress. Use the bar position, the step text and the log growth.

## Crashes

- After `Utils.ForceCrash`, the log has `Crash!!!` at once, but the process stays alive 24 to 31 s to write the dump, then exits with `0xC0000005`. No UnityBugReporter started. Use the log line, not the PID, to see a crash at once.
- `Unity.dll` has the undocumented environment variable `UNITY_DONOTSTARTBUGREPORTER`.
- A hang in a domain reload, escalated: a 120 s cap, `CloseMainWindow()` (no effect), a stop by PID, a new start: ready about 60 s later.

## Play Mode and input

- `unity command editor.playmode start` turns on Run In Background, so the Editor runs frames with no focus. It stops the pipeline listener for about 8 s.
- Wait for frames: `unity command job wait --condition '{"member":"UnityEngine.Time.frameCount","op":"greaterThan","value":<n>}' --on-met '{"capture":{"view":"game","output-path":"Temp/x.png"}}'`.
- From the docs, not tested: in Play Mode, `/api/status` has `playerLoopTicking` and `frameCount`.

| Command | Editor Play Mode, no focus | Windows development player |
|---|---|---|
| `runtime simulate_pointer --action click` on a uGUI button | Works | Works |
| `runtime simulate_key --key Space` | Does not reach the game, also with focus, `IgnoreFocus` or `AllDeviceInputAlwaysGoesToGameView` | Works |
| Own command: `InputSystem.QueueStateEvent(Keyboard.current, new KeyboardState(Key.Space))`, no `InputSystem.Update()` | Works | Not tested |
| The same, then `InputSystem.Update()` | Does not reach the game | Not tested |

The cause (from the source and the tests): `runtime simulate_key` calls `InputSystem.Update()` inside the command, and in Editor Play Mode that update goes to the Editor input state.

## Logs and captures

- `console get` (Editor and player, off the main thread) takes 1 to 20 ms over HTTP. Reply keys: `entries`, `cursor`, `session`, `returned`, `dropped`, `reset`, `counts`, `groundTruth`. Entry keys: `seq`, `timestampUtc`, `level`, `logType`, `message`, `stackTrace`.
- Follow the log with `--since <cursor> --since-session <session>` from the last reply. A wrong session gives `reset=true` and the tail. `--level error` filters.
- `console status` gives `counts` and `groundTruth` (`compilationFailed`, `compiling`, `consoleErrors`). `groundTruth` is null in a player.

| Capture | Time | Result |
|---|---|---|
| `capture game_view` (`source=screen`, default) | 40 to 110 ms | 1280x720 PNG, with Screen Space Overlay UI in Play Mode |
| `capture game_view --source camera` | 40 to 60 ms | Main Camera. `--overlay auto` adds the overlay UI with URP. |
| `--max-resolution 256`, no `--output-path` | 30 ms | Inline base64, about 21 000 characters |
| No `--output-path`, full size | 75 ms | Inline base64, about 161 000 characters: too large for an agent |
| `capture scene_view` | 60 to 90 ms | Works |
| `capture editor_window --window Inspector` | | Hung, then the Editor crashed (2 of 2) |

- `capture runtime_element` and `capture editor_element` need 6000.7 or later. The default `source` differs between `capture game_view` and `job wait --on-met`, so always pass it.

## Players: the runtime pipeline

- Turn it on: `unity command settings.runtime_pipeline set --settings '{"enable-in-development-builds":true}' --confirm`. Play Mode follows this setting. The docs call it experimental, for desktop players.
- Build: `unity command build run --target StandaloneWindows64 --output-path Builds/Win/Lab.exe --options '["Development"]' --confirm`, then poll `build status`. An IL2CPP build took 119 s. `unity build` through an open Editor changes its active target.
- The player writes `.unity-pipeline-runtime-port` beside the exe and takes the first free port from 7900 (the docs give 7900-7949 and 7900-7999: scan to 7999).
- Reach it with `unity command --runtime-path <build folder> <command>` or `--runtime Lab.exe <command>`.
- Start each player from its own folder. A second player from the same folder listens on 7901 but cannot write the descriptor, so the CLI cannot reach it, and `--runtime Lab.exe` fails as ambiguous.
- A player serves only 23 commands: no `capture game_view` and no `job wait`. Players need their own screenshot and wait commands.
- `runtime quit` only schedules the quit: once the player did not exit in 9 s. Check the PID, then use `CloseMainWindow()` and a stop by PID.
- Android players get no Roslyn, so no `script eval`. The Android descriptor goes to `Application.persistentDataPath`.

## Custom commands and scripts

- A `[CliGroupCommand]` static method in an Editor script is enough. The package references `Unity.Pipeline.Attributes`, so no asmdef is necessary. A new script needs `unity recompile` before the Editor lists it.
- The command name is snake case: a method `FreezeNow` in group `lab` is `lab.freeze_now`.
- A command that opens a modal dialog must schedule it with `EditorApplication.delayCall`, so the command returns first.
- A custom command in `Assets/Scripts` (no asmdef) runs in an IL2CPP development player.
- `script eval --code` from PowerShell loses the inner double quotes. Put the code in a `.cs` file and pass `--file <path>`.
- `unity command --query <term> --detail full` lists the parameters of each matching command.
- `test run --async-tests` with `test status --detail failures`. `unity test` exits 8 on failed tests and writes NUnit and JUnit reports.

## Windows process facts

- The `unity` CLI is also named `unity.exe` (in `WindowsApps\UnityTechnologies.UnityCLI_*`), and its command line holds the `--args` text. Find the Editor with `ExecutablePath -like '*\Editor\Unity.exe'`.
- The Editor from `unity open` is a child of that CLI process. The CLI stays alive with two helper children (`--internal-auth-broker-serve`, `--internal-identity-serve`).
- Asset import workers are `Unity.exe -batchMode -name AssetImportWorkerN -projectPath <project>`. Leave them out of a "foreign Editor" check.

## CLI output shapes (1.0.1)

- `unity status --format json`: `data.items[]` with `pid` and `state`. It lists all Editors on the computer, so pick the row with your PID.
- `unity pipeline editors --format json`: `data.items[]` with `pid`, `isRunning`, `pipelineServer.isReachable` and `safeMode` (null or an object). The docs give a `phase` field, but 1.0.1 has none.

## Other facts from the docs

- MPPM clones serve no HTTP, only the pipeline TCP protocol. Reach them with `--instance`.
- Linux CI: `open --batchmode` runs with no graphics when no display is set. The CLI needs glibc 2.34 or later.
- The `unity-pipeline` agent skill comes from the Unity-Technologies/skills repository through `unity skill install`, not from the package. Its text is older than 1.0.0.
