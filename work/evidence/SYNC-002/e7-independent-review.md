# E7 WB core independent review

Initial frozen review e09ba014..f99a294ef4e530bcec4ed950c5cfffa4fe6439ee found one P2: WBWindow._completed clears the current reference without deleting the window-parented RunSession, retaining runner and result bytes per analysis until close. Non-author independently verified original product byte identity, seven receipt bytes/ancestry and frozen rule check;14pure core/.92s0. No reviewer Qt/wheel claim.

All four server checks passed on f99 (quality39322766358/rules39322766267), but this did NOT permit merge because the P2 remained. Final lifecycle correction and three real-process success/failure/cancel regressions must pass and receive bound final review plus fresh exact-head checks.
