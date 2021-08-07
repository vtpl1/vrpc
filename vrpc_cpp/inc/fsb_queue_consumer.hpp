#pragma once
#ifndef fsb_queue_consumer_H
#define fsb_queue_consumer_H
#include <deque>

#include "vrpc.hpp"

namespace vrpc {
// CLASS TEMPLATE queue
template <class _Ty>
class fsb_queue {
   public:
    fsb_queue(int queue_id) {}
    /**
     *  @brief  Add data to the end of the %queue.
     *  @param  __x  Data to be added.
     *
     *  This is a typical %queue operation.  The function creates an
     *  element at the end of the %queue and assigns the given data
     *  to it.  The time complexity of the operation depends on the
     *  underlying sequence.
     */
    void push(const _Ty& __x) {
        // c.push_back(__x);
    }

    void push(_Ty&& __x) {
        //   c.push_back(std::move(__x));
    }

    /**
     *  @brief  Removes first element.
     *
     *  This is a typical %queue operation.  It shrinks the %queue by one.
     *  The time complexity of the operation depends on the underlying
     *  sequence.
     *
     *  Note that no data is returned, and if the first element's
     *  data is needed, it should be retrieved before pop() is
     *  called.
     */
    void pop() {}

    /**
     *  Returns a read/write reference to the data at the first
     *  element of the %deque.
     */
    _Ty& front() {
        _Ty x;
        return x;
    }

    /**
     *  Returns a read-only (constant) reference to the data at the first
     *  element of the %deque.
     */
    const _Ty& front() const {
        _Ty x;
        return x;
    }
};
}  // namespace vrpc
#endif