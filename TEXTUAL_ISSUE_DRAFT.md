# Draft issue for Textualize/textual

Not filed. Written after an incident in this repo and kept here so it can be
submitted by hand. Everything below was measured on this machine (macOS 15,
arm64, python 3.11.13, textual 7.3.0) and is ready to paste into a new issue.

---

**Title:** `run_input_thread` spins at 100% CPU after the terminal hangs up

**Body:**

An app whose controlling pty is closed under it does not exit. It keeps
running with its input thread in a tight loop, burning a full core for as
long as the process lives.

This is what a Textual app does when whatever launched it goes away without
killing it: a terminal emulator that crashes, an ssh session that drops, or a
harness that drives the app on a pty and then dies. The app is reparented to
init and stays there. I found 19 orphaned instances of one Textual app pinned
at 40-49% CPU each, the oldest about 10 hours old.

## Reproduction

`minapp.py`:

```python
from textual.app import App, ComposeResult
from textual.widgets import Static

class Min(App):
    def compose(self) -> ComposeResult:
        yield Static("hello")

if __name__ == "__main__":
    Min().run()
```

`orphan.py` starts it on a pty, drains the master for four seconds so the app
paints, then exits without killing the child. The kernel closes the master,
which is what a crashed parent does:

```python
import os, pty, subprocess, sys, time

master, slave = pty.openpty()
p = subprocess.Popen(
    [sys.executable, "minapp.py"],
    stdin=slave, stdout=slave, stderr=slave, start_new_session=True,
)
os.close(slave)
print(p.pid, flush=True)
os.set_blocking(master, False)
end = time.time() + 4
while time.time() < end:
    try:
        os.read(master, 65536)
    except BlockingIOError:
        time.sleep(0.05)
    except OSError:
        break
os._exit(0)
```

```
$ python orphan.py
54769
$ top -l 4 -pid 54769 -stats pid,cpu,time -n 1
54769  0.0   00:03.01
54769  81.5  00:04.09
54769  100.1 00:05.14
54769  99.7  00:06.19
$ ps -o pid,ppid,%cpu,time,etime -p 54769
  PID  PPID  %CPU      TIME ELAPSED
54769     1 100.0   0:06.20   00:10
```

The app sits at 0.0% CPU for as long as the master is open and reaches 100%
within a second of the parent exiting. It stays there indefinitely.

`sample` puts every tick of the hot thread in `select` and `read`:

```
1631 Thread_27139027
+ 383 os_read  (in libpython3.11.dylib)
+   366 _Py_read -> read  (in libsystem_kernel.dylib)
+ 377 select_select_impl -> __select  (in libsystem_kernel.dylib)
```

## Cause

`LinuxDriver.run_input_thread` in `textual/drivers/linux_driver.py`:

```python
for last, (_selector_key, mask) in loop_last(selector_events):
    if mask & EVENT_READ:
        unicode_data = decode(read(fileno, 1024 * 4), final=final and last)
        if not unicode_data:
            # This can occur if the stdin is piped
            break
        ...

while not self.exit_event.is_set():
    process_selector_events(selector.select(0.1))
```

Once the master is closed, the fd is permanently readable and `read` returns
`b""` every time. The empty read breaks the byte loop, `process_selector_events`
returns, and the `while` re-enters `select`, which returns immediately because
the fd is still readable. The `0.1` timeout never applies, so there is no
sleep anywhere in the cycle.

The comment beside the `break` shows EOF was anticipated. The handling leaves
the byte loop and lets the thread go around again, which is right for a pipe
that will deliver more later and wrong for a tty that has hung up.

## Suggested fix

Treat an empty read on a tty as a hangup and end the app rather than
re-entering `select`, along the lines of what a terminal-driven program does
on `SIGHUP`. Setting `exit_event` and letting the driver's normal shutdown run
would be enough to stop the spin. A backoff on repeated empty reads would cap
the CPU cost without changing the exit behavior, though it would leave the
process alive forever.

Same class of bug as [ranger#1367](https://github.com/ranger/ranger/issues/1367).

## Versions

- textual 7.3.0
- python 3.11.13
- macOS 15.6, arm64
