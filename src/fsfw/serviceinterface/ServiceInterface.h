#ifndef FSFW_SERVICEINTERFACE_SERVICEINTERFACE_H_
#define FSFW_SERVICEINTERFACE_SERVICEINTERFACE_H_

#include <string>

class ServiceInterfaceStream {
 public:
  explicit ServiceInterfaceStream(const char* name) : name(name) {}

 private:
  const char* name;
};

#endif // FSFW_SERVICEINTERFACE_SERVICEINTERFACE_H_
