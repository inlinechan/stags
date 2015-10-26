class Base {
  public:
    virtual void method1(const char*) {}
};

class Delegate {
  public:
    virtual void didStarted() = 0;
};

class Derived: public Base,
               public Delegate {
  public:
    virtual void method1(const char*) {}
    virtual void didStarted() {}
};

class MoreDerived: public Derived {
  public:
    virtual void method1(const char*) {}
};

void caller(const char *msg)
{
    MoreDerived *m = new MoreDerived;
    m->method1(msg);
}

int main(int, char *[])
{
    Base *b = new Derived;
    b->method1("hello");

    return 0;
}
