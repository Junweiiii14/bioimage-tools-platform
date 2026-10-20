set pagination off
set confirm off
set print frame-arguments none
set print entry-values no
set print thread-events off
set disable-randomization off
handle all nostop noprint pass
handle SIGSEGV SIGABRT SIGBUS SIGILL SIGFPE SIGINT SIGTERM stop print pass
python
import gdb
import os

faults = {"SIGSEGV", "SIGABRT", "SIGBUS", "SIGILL", "SIGFPE"}
cancellations = {"SIGINT", "SIGTERM"}

def capture_fault(event):
    if not isinstance(event, gdb.SignalEvent) or event.stop_signal not in faults | cancellations:
        return
    marker = "NATIVE_CANCEL" if event.stop_signal in cancellations else "NATIVE_FAULT"
    print(marker + " signal=" + event.stop_signal, flush=True)
    try:
        selected = gdb.selected_thread()
        threads = [selected] + [t for t in gdb.selected_inferior().threads() if t != selected]
        captured = threads if os.environ.get("BIOIMAGE_NATIVE_DIAGNOSTIC") == "1" else threads[:64]
        print("NATIVE_THREADS total=" + str(len(threads)) + " truncated=" + str(len(threads) - len(captured)), flush=True)
        for thread in captured:
            thread.switch()
            print("NATIVE_THREAD " + str(thread.num), flush=True)
            gdb.execute("bt 24")
        selected.switch()
        gdb.execute("info sharedlibrary")
        print("NATIVE_CAPTURE_COMPLETE signal=" + event.stop_signal, flush=True)
    finally:
        # Observation must forward the original signal even when stack collection fails.
        gdb.execute("handle SIGSEGV SIGABRT SIGBUS SIGILL SIGFPE SIGINT SIGTERM nostop print pass")

gdb.events.stop.connect(capture_fault)
end
run
python
if gdb.selected_inferior().pid:
    gdb.execute("continue")
end
