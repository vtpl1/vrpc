#pragma once
#ifndef fsb_queue_consumer_H
#define fsb_queue_consumer_H
#include <deque>

#include "vrpc.hpp"

namespace vrpc {
// CLASS TEMPLATE queue
template <class _Ty, class _Container = std::deque<_Ty>>
class fsb_queue {
   public:
    using value_type = typename _Container::value_type;
    using reference = typename _Container::reference;
    using const_reference = typename _Container::const_reference;
    using size_type = typename _Container::size_type;
    using container_type = _Container;

    static_assert(is_same_v<_Ty, value_type>, "container adaptors require consistent types");

    fsb_queue() = default;
};
}  // namespace vrpc
#endif