# Array

## Two Sum

### Statement

Given an array of integers `nums` and an integer `target`, return _indices of
the two numbers such that they add up to`target`_.

You may assume that each input would have **_exactly_ one solution**, and you
may not use the _same_ element twice.

You can return the answer in any order.

**Example 1:**

```
**Input:** nums = [2,7,11,15], target = 9
**Output:** [0,1]
**Explanation:** Because nums[0] + nums[1] == 9, we return [0, 1].
```

**Example 2:**

```
**Input:** nums = [3,2,4], target = 6
**Output:** [1,2]
```

**Example 3:**

```
**Input:** nums = [3,3], target = 6
**Output:** [0,1]
```

**Constraints:**

- `2 <= nums.length <= 10\textsuperscript{4}`
- `-10\textsuperscript{9} <= nums[i] <= 10\textsuperscript{9}`
- `-10\textsuperscript{9} <= target <= 10\textsuperscript{9}`
- **Only one valid answer exists.**

\*\*Follow-up: \*\*Can you come up with an algorithm that is less than
`O(n\textsuperscript{2})` time complexity?

**Tags:** Array, Hash Table

### Hints

- A really brute force way would be to search for all possible pairs of numbers but that would be too slow. Again, it's best to try out brute force solutions for just for completeness. It is from these brute force solutions that you can come up with optimizations.
- So, if we fix one of the numbers, say <code>x</code>, we have to scan the entire array to find the next number <code>y</code> which is <code>value - x</code> where value is the input parameter. Can we change our array somehow so that this search becomes faster?
- The second train of thought is, without changing the array, can we use additional space somehow? Like maybe a hash map to speed up the search?

### Solution Summary

Video Solution Solution Article Approach 1: Brute Force Algorithm The brute
force approach is simple. Loop through each element x and find if there is
another

### Solution Article

______________________________________________________________________

#### Approach 1: Brute Force

**Algorithm**

The brute force approach is simple. Loop through each element $x$ and find if there is another value that equals to $target - x$.

**Implementation**

```cpp
class Solution {
public:
    vector<int> twoSum(vector<int> &nums, int target) {
        for (int i = 0; i < nums.size(); i++) {
            for (int j = i + 1; j < nums.size(); j++) {
                if (nums[j] == target - nums[i]) {
                    return {i, j};
                }
            }
        }
        // Return an empty vector if no solution is found
        return {};
    }
};
```

**Complexity Analysis**

- Time complexity: $O(n^2)$.
  For each element, we try to find its complement by looping through the rest of the array which takes $O(n)$ time. Therefore, the time complexity is $O(n^2)$.

- Space complexity: $O(1)$.
  The space required does not depend on the size of the input array, so only constant space is used.

______________________________________________________________________

#### Approach 2: Two-pass Hash Table

**Intuition**

To improve our runtime complexity, we need a more efficient way to check if the complement exists in the array. If the complement exists, we need to get its index. What is the best way to maintain a mapping of each element in the array to its index? A hash table.

We can reduce the lookup time from $O(n)$ to $O(1)$ by trading space for speed. A hash table is well suited for this purpose because it supports fast lookup in *near* constant time. I say "near" because if a collision occurred, a lookup could degenerate to $O(n)$ time. However, lookup in a hash table should be amortized $O(1)$ time as long as the hash function was chosen carefully.

**Algorithm**

A simple implementation uses two iterations. In the first iteration, we add each element's value as a key and its index as a value to the hash table. Then, in the second iteration, we check if each element's complement ($target - nums[i]$) exists in the hash table. If it does exist, we return current element's index and its complement's index. Beware that the complement must not be $nums[i]$ itself!

**Implementation**

```cpp
class Solution {
public:
    vector<int> twoSum(vector<int> &nums, int target) {
        unordered_map<int, int> hash;
        for (int i = 0; i < nums.size(); i++) {
            hash[nums[i]] = i;
        }
        for (int i = 0; i < nums.size(); i++) {
            int complement = target - nums[i];
            if (hash.find(complement) != hash.end() && hash[complement] != i) {
                return {i, hash[complement]};
            }
        }
        // If no valid pair is found, return an empty vector
        return {};
    }
};
```

**Complexity Analysis**

- Time complexity: $O(n)$.
  We traverse the list containing $n$ elements exactly twice. Since the hash table reduces the lookup time to $O(1)$, the overall time complexity is $O(n)$.

- Space complexity: $O(n)$.
  The extra space required depends on the number of items stored in the hash table, which stores exactly $n$ elements.

______________________________________________________________________

#### Approach 3: One-pass Hash Table

**Algorithm**

It turns out we can do it in one-pass. While we are iterating and inserting elements into the hash table, we also look back to check if current element's complement already exists in the hash table. If it exists, we have found a solution and return the indices immediately.

**Implementation**

```cpp
class Solution {
public:
    vector<int> twoSum(vector<int> &nums, int target) {
        unordered_map<int, int> hash;
        for (int i = 0; i < nums.size(); ++i) {
            int complement = target - nums[i];
            if (hash.find(complement) != hash.end()) {
                return {hash[complement], i};
            }
            hash[nums[i]] = i;
        }
        // Return an empty vector if no solution is found
        return {};
    }
};
```

**Complexity Analysis**

- Time complexity: $O(n)$.
  We traverse the list containing $n$ elements only once. Each lookup in the table costs only $O(1)$ time.

- Space complexity: $O(n)$.
  The extra space required depends on the number of items stored in the hash table, which stores at most $n$ elements.

# Heap

## Merge k Sorted Lists

### Statement

You are given an array of `k` linked-lists `lists`, each linked-list is sorted
in ascending order.

_Merge all the linked-lists into one sorted linked-list and return it._

**Example 1:**

```
**Input:** lists = [[1,4,5],[1,3,4],[2,6]]
**Output:** [1,1,2,3,4,4,5,6]
**Explanation:** The linked-lists are:
[
  1->4->5,
  1->3->4,
  2->6
]
merging them into one sorted list:
1->1->2->3->4->4->5->6
```

**Example 2:**

```
**Input:** lists = []
**Output:** []
```

**Example 3:**

```
**Input:** lists = [[]]
**Output:** []
```

**Constraints:**

- `k == lists.length`
- `0 <= k <= 10\textsuperscript{4}`
- `0 <= lists[i].length <= 500`
- `-10\textsuperscript{4} <= lists[i][j] <= 10\textsuperscript{4}`
- `lists[i]` is sorted in **ascending order**.
- The sum of `lists[i].length` will not exceed `10\textsuperscript{4}`.

**Tags:** Linked List, Divide and Conquer, Heap (Priority Queue), Merge Sort

## Find Median from Data Stream

### Statement

The **median** is the middle value in an ordered integer list. If the size of
the list is even, there is no middle value, and the median is the mean of the
two middle values.

- For example, for `arr = [2,3,4]`, the median is `3`.
- For example, for `arr = [2,3]`, the median is `(2 + 3) / 2 = 2.5`.

Implement the MedianFinder class:

- `MedianFinder()` initializes the `MedianFinder` object.
- `void addNum(int num)` adds the integer `num` from the data stream to the data structure.
- `double findMedian()` returns the median of all elements so far. Answers within `10\textsuperscript{-5}` of the actual answer will be accepted.

**Example 1:**

```
**Input**
["MedianFinder", "addNum", "addNum", "findMedian", "addNum", "findMedian"]
[[], [1], [2], [], [3], []]
**Output**
[null, null, null, 1.5, null, 2.0]

**Explanation**
MedianFinder medianFinder = new MedianFinder();
medianFinder.addNum(1);    // arr = [1]
medianFinder.addNum(2);    // arr = [1, 2]
medianFinder.findMedian(); // return 1.5 (i.e., (1 + 2) / 2)
medianFinder.addNum(3);    // arr[1, 2, 3]
medianFinder.findMedian(); // return 2.0
```

**Constraints:**

- `-10\textsuperscript{5} <= num <= 10\textsuperscript{5}`
- There will be at least one element in the data structure before calling `findMedian`.
- At most `5 * 10\textsuperscript{4}` calls will be made to `addNum` and `findMedian`.

**Follow up:**

- If all integer numbers from the stream are in the range `[0, 100]`, how would you optimize your solution?
- If `99%` of all integer numbers from the stream are in the range `[0, 100]`, how would you optimize your solution?

**Tags:** Two Pointers, Design, Sorting, Heap (Priority Queue), Data Stream
