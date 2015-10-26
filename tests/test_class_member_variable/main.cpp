class Base {
  public:
    int getValue() const { return m_value; }
    void setValue(int value) { m_value = value; }

  protected:
    int m_value;
};

int main(int, char *[])
{
    Base *b = new Base;
    const int value = 3;
    b->setValue(value);
    const int returned_value = b->getValue();

    return 0;
}
