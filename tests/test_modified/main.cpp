#include "derived.h"

int main(int argc, char *argv[])
{
    Derived *d = new Derived;
    d->method1("hello");

    return 0;
}
