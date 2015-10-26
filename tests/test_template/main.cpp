class Base {
  public:
    virtual void method1(const char*) {}
};

template <typename T>
class Delegate {
  public:
    void started(T* t) {
        t->didStarted();
    }
};

class Derived: public Base,
               public Delegate<Derived> {
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
    Derived *d = new Derived;
    d->method1("hello");
    d->started(d);

    return 0;
}
