"""
min_heap.py  -  Binary min-heap written from scratch (Student 2)

Used as the priority queue inside Dijkstra's algorithm.
We do NOT use Python's heapq, because the project rules say library
functions must not replace the algorithm.

How it is stored
----------------
The heap is a normal Python list `a`. For the element at index i:
    left child  = 2*i + 1
    right child = 2*i + 2
    parent      = (i - 1) // 2
Heap property: every parent is <= its children, so the smallest
element is always at a[0].

Each entry is a tuple (priority, item), e.g. (12.5, "City Hospital").
Only the priority (entry[0]) is compared, so items never need to be
comparable with each other.
"""


class MinHeap:
    def __init__(self):
        self.a = []      # the list that stores the heap
        self.ops = 0     # number of comparisons, used in the analysis

    def __len__(self):
        return len(self.a)

    def is_empty(self):
        return len(self.a) == 0

    def peek(self):
        """Return the smallest entry without removing it. O(1)."""
        if not self.a:
            raise IndexError("peek from empty heap")
        return self.a[0]

    def push(self, entry):
        """Insert a (priority, item) tuple.  O(log n).

        Put the new entry at the end, then 'sift it up': swap it with
        its parent while it is smaller than the parent.
        """
        self.a.append(entry)
        i = len(self.a) - 1
        while i > 0:
            parent = (i - 1) // 2
            self.ops += 1
            if self.a[i][0] < self.a[parent][0]:
                self.a[i], self.a[parent] = self.a[parent], self.a[i]
                i = parent
            else:
                break

    def pop(self):
        """Remove and return the smallest entry.  O(log n).

        Take the root, move the last element to the root, then
        'sift it down': swap it with its smaller child until both
        children are larger (or it has no children).
        """
        if not self.a:
            raise IndexError("pop from empty heap")
        top = self.a[0]
        last = self.a.pop()
        if self.a:                      # heap still has elements
            self.a[0] = last
            i, n = 0, len(self.a)
            while True:
                left, right, smallest = 2 * i + 1, 2 * i + 2, i
                if left < n:
                    self.ops += 1
                    if self.a[left][0] < self.a[smallest][0]:
                        smallest = left
                if right < n:
                    self.ops += 1
                    if self.a[right][0] < self.a[smallest][0]:
                        smallest = right
                if smallest == i:
                    break
                self.a[i], self.a[smallest] = self.a[smallest], self.a[i]
                i = smallest
        return top