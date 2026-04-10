#include <bits/stdc++.h>
using namespace std;

int main() {
    int steps = 1000;
    double loss_prob = 0.02;

    double cwnd_reno = 1;
    double cwnd_bic = 1;

    double bic_max = 1;
    double bic_min = 1;

    ofstream fout("output.dat");

    for (int t = 1; t <= steps; t++) {

        // random loss 
        bool loss = ((double)rand() / RAND_MAX) < loss_prob;

        // reno 
        if (loss) {
            cwnd_reno = max(1.0, cwnd_reno / 2.0);
        } else {
            cwnd_reno += 1.0 / cwnd_reno; // linear growth
        }

        // bic
        if (loss) {
            bic_max = cwnd_bic;
            cwnd_bic = max(1.0, cwnd_bic / 2.0);
            bic_min = cwnd_bic;
        } else {
            // binary search phase
            double target = (bic_max + bic_min) / 2.0;

            if (abs(cwnd_bic - target) < 0.1) {
                cwnd_bic += 1; // aggressive increase
            } else {
                cwnd_bic += (target - cwnd_bic) * 0.1;
            }
        }

        fout << t << " " << cwnd_reno << " " << cwnd_bic << "\n";
    }

    fout.close();
    return 0;
}
