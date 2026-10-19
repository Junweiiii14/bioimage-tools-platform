/* Fixed private-runtime entry. No command shell or developer Python lookup. */
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#include <windows.h>
#include <shellapi.h>
#include <wchar.h>

#define CAPACITY 32768
#ifndef RELEASE_CHANNEL
#define RELEASE_CHANNEL L"candidate"
#endif

static BOOL append(wchar_t *command, size_t *length, wchar_t value) {
    if (*length + 1 >= CAPACITY) return FALSE;
    command[(*length)++] = value;
    command[*length] = 0;
    return TRUE;
}

/* CommandLineToArgvW inverse: preserve quotes and trailing backslashes. */
static BOOL argument(wchar_t *command, size_t *length, const wchar_t *value) {
    if (*length && !append(command, length, L' ')) return FALSE;
    if (!append(command, length, L'"')) return FALSE;
    size_t slashes = 0;
    for (;;) {
        wchar_t character = *value++;
        if (character == L'\\') { slashes++; continue; }
        size_t count = (character == L'"' || character == 0) ? slashes * 2 : slashes;
        for (size_t index = 0; index < count; index++)
            if (!append(command, length, L'\\')) return FALSE;
        slashes = 0;
        if (character == L'"' && !append(command, length, L'\\')) return FALSE;
        if (character == 0) break;
        if (!append(command, length, character)) return FALSE;
    }
    return append(command, length, L'"');
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR line, int show) {
    (void)instance; (void)previous; (void)line; (void)show;
    wchar_t executable[CAPACITY], command[CAPACITY] = {0};
    DWORD path_length = GetModuleFileNameW(NULL, executable, CAPACITY);
    DWORD error = ERROR_BAD_PATHNAME;
    HANDLE job = NULL;
    PROCESS_INFORMATION process = {0};
    LPWSTR *arguments = NULL;
    if (!path_length || path_length >= CAPACITY) goto failed;
    wchar_t *separator = wcsrchr(executable, L'\\');
    if (!separator || (size_t)(separator - executable) + 21 >= CAPACITY) goto failed;
    wcscpy(separator, L"\\runtime\\python.exe");
    int count = 0;
    arguments = CommandLineToArgvW(GetCommandLineW(), &count);
    if (!arguments) goto failed;
    size_t length = 0;
    if (!argument(command, &length, executable) || !argument(command, &length, L"-I") ||
        !argument(command, &length, L"-X") || !argument(command, &length, L"utf8") ||
        !argument(command, &length, L"-m") || !argument(command, &length, L"bioimage_app"))
        goto failed;
    for (int index = 1; index < count; index++)
        if (!argument(command, &length, arguments[index])) goto failed;
    LocalFree(arguments); arguments = NULL;
    if (!SetEnvironmentVariableW(L"BIOIMAGE_RELEASE_CHANNEL", RELEASE_CHANNEL)) goto failed;
    job = CreateJobObjectW(NULL, NULL);
    if (!job) goto failed;
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits = {0};
    limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    if (!SetInformationJobObject(job, JobObjectExtendedLimitInformation, &limits, sizeof(limits)))
        goto failed;
    STARTUPINFOW startup = {0};
    startup.cb = sizeof(startup);
    startup.dwFlags = STARTF_USESTDHANDLES;
    startup.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    startup.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    startup.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    if (!CreateProcessW(executable, command, NULL, NULL, TRUE,
                        CREATE_NO_WINDOW | CREATE_SUSPENDED, NULL, NULL, &startup, &process))
        goto failed;
    if (!AssignProcessToJobObject(job, process.hProcess)) goto failed;
    if (ResumeThread(process.hThread) == (DWORD)-1) goto failed;
    CloseHandle(process.hThread); process.hThread = NULL;
    if (WaitForSingleObject(process.hProcess, INFINITE) != WAIT_OBJECT_0) goto failed;
    DWORD result = 1;
    if (!GetExitCodeProcess(process.hProcess, &result)) goto failed;
    CloseHandle(process.hProcess); CloseHandle(job);
    return (int)result;
failed:
    error = GetLastError();
    if (!error) error = ERROR_INVALID_PARAMETER;
    if (arguments) LocalFree(arguments);
    if (process.hProcess) {
        TerminateProcess(process.hProcess, 1);
        CloseHandle(process.hProcess);
    }
    if (process.hThread) CloseHandle(process.hThread);
    if (job) CloseHandle(job);
    wchar_t message[160];
    wsprintfW(message, L"无法启动候选版，请重新安装候选版。错误码：%lu", error);
    MessageBoxW(NULL, message, L"BioImage WB 候选版", MB_OK | MB_ICONERROR);
    return 1;
}
