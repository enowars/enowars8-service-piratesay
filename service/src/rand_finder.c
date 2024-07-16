#include <stdio.h>

static unsigned long int next = 1;

void advance_rand_state(unsigned long int *state, unsigned int a, unsigned int c, unsigned int m, unsigned int k)
{
    unsigned long int a_k = 1;
    unsigned long int c_k = 0;
    unsigned long int temp_a = a;
    unsigned long int temp_c = c;

    while (k > 0)
    {
        if (k & 1)
        {
            a_k = (a_k * temp_a) % m;
            c_k = (c_k * temp_a + temp_c) % m;
        }
        temp_c = (temp_c * (temp_a + 1)) % m;
        temp_a = (temp_a * temp_a) % m;
        k >>= 1;
    }

    *state = (a_k * (*state) + c_k) % m;
}

int main()
{
    unsigned long int state = 1; // Example initial state
    unsigned int a = 1103515245;
    unsigned int c = 12345;
    unsigned int m = 1 << 31; // 2^31
    unsigned int k = 1000;

    advance_rand_state(&state, a, c, m, k);

    printf("State after advancing 1000 steps: %lu\n", state);

    return 0;
}