#ifndef CAFE_H
#define CAFE_H

class Person;

class Cafe {
  public:
    Cafe();
    void enter(Person* person);
    void leave(Person* person);

    static const int N = 10;

  private:
    Person* persons[N];
};

#endif /* CAFE_H */
