#include <iostream>
#include <fstream>
#include <string>
#include "alu.hpp"

enum State { IDLE, CHECK, RUN, PAUSE, COMPLETE, BUZZ, ERROR_STATE };
enum Mode { DEFROST = 0, HEAT = 1, GRILL = 2 };

const char* stateStr[] = {"IDLE", "CHECK", "RUN", "PAUSE", "COMPLETE", "BUZZ", "ERROR"};
const char* modeStr[] = {"DEFROST", "HEAT", "GRILL"};
const uint8_t modeCycles[] = {3, 5, 7};

void logLine(std::ostream& out, int cycle, State state, bool door, bool food, bool temp,
             bool heater, bool turntable, bool light, bool buzzer, Mode mode, uint8_t timer) {
    out << "Cycle " << cycle
        << " | " << stateStr[state]
        << " | DOOR=" << door
        << " | HEATER=" << (heater ? "ON" : "OFF")
        << " TURNTABLE=" << (turntable ? "ON" : "OFF")
        << " LIGHT=" << (light ? "ON" : "OFF")
        << " BUZZER=" << (buzzer ? "ON" : "OFF")
        << " | " << modeStr[mode] << "-" << (int)timer
        << "\n";
}

int main() {
    std::ofstream trace("cpu_trace.txt");

    int modeInput, cycles;
    std::cout << "Mode (0=DEFROST 1=HEAT 2=GRILL): ";
    std::cin >> modeInput;
    Mode mode = (Mode)modeInput;

    std::cout << "Number of cycles: ";
    std::cin >> cycles;

    State state = IDLE;
    uint8_t timer = 0;

    trace << "Cycle | State | Inputs | Outputs | Display\n";
    trace << std::string(65, '-') << "\n";

    for (int cycle = 1; cycle <= cycles; cycle++) {
        int s, st, d, f, t;
        std::cin >> s >> st >> d >> f >> t;

        bool START = s, STOP = st, DOOR = d, FOOD = f, TEMP = t;

        if (state != ERROR_STATE) {
            if (state != IDLE && state != BUZZ) {
                if (TEMP) {
                    state = ERROR_STATE;
                } else if (!DOOR) {
                    state = PAUSE;
                } else if (STOP && state == RUN) {
                    state = PAUSE;
                }
            }

            switch (state) {
            case IDLE:
                if (START && DOOR && FOOD) {
                    state = CHECK;
                    timer = modeCycles[mode];
                }
                break;
            case CHECK:
                state = RUN;
                break;
            case RUN:
                {
                    ALUResult res = alu_sub(timer, 1);
                    timer = res.value;
                    if (res.Z) state = COMPLETE;
                }
                break;
            case PAUSE:
                if (START && DOOR) {
                    state = RUN;
                }
                break;
            case COMPLETE:
                state = BUZZ;
                break;
            case BUZZ:
                state = IDLE;
                timer = 0;
                break;
            case ERROR_STATE:
                break;
            }
        }

        bool heater    = (state == RUN);
        bool turntable = (state == RUN);
        bool light     = (state == CHECK || state == RUN || state == PAUSE ||
                          state == COMPLETE || state == ERROR_STATE);
        bool buzzer    = (state == BUZZ || state == ERROR_STATE);

        logLine(trace, cycle, state, DOOR, FOOD, TEMP, heater, turntable, light, buzzer, mode, timer);
        // logLine(std::cout, cycle, state, DOOR, FOOD, TEMP, heater, turntable, light, buzzer, mode, timer);
    }

    trace.close();
    std::cout << "\nTrace saved to cpu_trace.txt\n";
    return 0;
}
