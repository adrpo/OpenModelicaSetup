#include <windows.h>
#include <stdio.h>
#include <process.h>
#include <stdlib.h>

// Build from a Visual Studio Command Prompt with:
// "cl /O2 /Gy /Femt.exe mt-retry.cpp"
// or
// "g++ -g c:/dev/mt-retry.cpp -o mt.exe -municode"

int __cdecl wmain(int argc, WCHAR **argv, WCHAR **env)
{
    WCHAR **myargv = (WCHAR**)malloc((argc+1)*sizeof(WCHAR*));
    for(int  i = 0; i < argc; i++)
       myargv[i] = argv[i];
    // set to NULL as expected by _wspawnve!
    myargv[argc] = NULL;

    // Run the original mt.exe, which has been renamed to mt-orig.exe .
    for (int i = 0; i < 50; i++)
    {
        // Try to run the original mt.
        intptr_t iStatus = _wspawnve(_P_WAIT, L"C:\\Program Files (x86)\\Windows Kits\\8.1\\bin\\x86\\mt-orig.exe", myargv + 1, env);
        if (iStatus == 0) {
            break;
        } else {
            fprintf(stderr, "%d\n", iStatus);
            perror("Error: ");
        }
        
        // Try again, after a short wait.
        ::Sleep(500);
    }

    return 0;
}
