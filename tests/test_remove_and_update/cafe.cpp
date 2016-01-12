#include "cafe.h"
#include "person.h"

Cafe::Cafe()
{
    for (int i = 0; i < N; i++)
        persons[i] = nullptr;
}

void Cafe::enter(Person* person)
{
    person->talk();

    for (int i = 0; i < N; i++) {
        if (!persons[i])
            persons[i] = person;
    }
}

void Cafe::leave(Person* person)
{
    person->talk();

    for (int i = 0; i < N; i++) {
        if (persons[i] == person)
            persons[i] = nullptr;
    }
}
