set pagination off
set confirm off
set print frame-arguments none
set print entry-values no
set print thread-events off
set startup-with-shell off
set disable-randomization off
handle all nostop noprint pass
handle SIGSEGV SIGABRT SIGBUS SIGILL SIGFPE stop print pass
python
import gdb

faults = {"SIGSEGV", "SIGABRT", "SIGBUS", "SIGILL", "SIGFPE"}

def capture_fault(event):
    if not isinstance(event, gdb.SignalEvent) or event.stop_signal not in faults:
        return
    print("NATIVE_FAULT signal=" + event.stop_signal, flush=True)
    selected = gdb.selected_thread()
    threads = [selected] + [t for t in gdb.selected_inferior().threads() if t != selected]
    for thread in threads[:64]:
        thread.switch()
        print("NATIVE_THREAD " + str(thread.num), flush=True)
        gdb.execute("bt 24")
    selected.switch()
    gdb.execute("info sharedlibrary")
    # Pass the original fault onwards, including faulthandler's repeated signal.
    gdb.execute("handle SIGSEGV SIGABRT SIGBUS SIGILL SIGFPE nostop print pass")

gdb.events.stop.connect(capture_fault)
end
run
python
if gdb.selected_inferior().pid:
    gdb.execute("continue")
end
