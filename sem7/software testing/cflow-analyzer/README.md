# cflow-analyzer

C control-flow-graph visualizer + cyclomatic complexity calculator.

## Run it

**1. Build the analyzer (needs flex + bison + gcc):**
```
cd parser && make
```

**2. Start the backend** (wraps the compiled binary as an HTTP API on :3001):
```
cd backend && npm install && npm start
```

**3. Start the frontend** (:5173, talks to the backend at localhost:3001):
```
cd frontend && npm install && npm run dev
```

Open the frontend URL. It loads `test-programs/sample1.c` by default; use
"Upload .c file" to analyze your own.

## Known limitations (v1)
- No `typedef` support (and so no lexer hack yet either)
- No explicit type casts, e.g. `(int)x`
- `#include`d headers are stripped before parsing, not resolved - only your
  own function bodies are analyzed
- Global variable declarations only support a single declarator per line
