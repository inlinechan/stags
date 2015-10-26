#ifndef DERIVED_H
#define DERIVED_H

#include "base.h"

class Derived: public Base {
  public:
    virtual void method1(const char* param);
};

#endif /* DERIVED_H */
