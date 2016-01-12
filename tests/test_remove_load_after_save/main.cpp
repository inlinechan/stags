#include "cafe.h"
#include "person.h"

int main()
{
    Cafe c;
    Person* p = new Person;
    c.enter(p);
    c.leave(p);

    delete p;

    return 0;
}
