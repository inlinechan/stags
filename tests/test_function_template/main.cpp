class Base {
public:
    template <typename T>
    void method(T) {}
};

int main(int, char *[])
{
    Base b;
    int integer;
    char character;
    void *void_ptr;

    b.method(integer);
    b.method(character);
    b.method(void_ptr);

    return 0;
}
