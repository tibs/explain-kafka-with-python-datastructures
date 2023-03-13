===============================================
Explaiining Apache Kafka® using Python concepts
===============================================

...or, 'Writing a "toy" Kafka'

(Do I actually have any intent of *writing* such a thing, or should this just
talk through it? Having code may make it easier to talk about, and will make
it easier to spot mistakes.)


Reference *the paper*

Apache Kafka® is an implementation of that idea.

The proposal here is to explain the ideas of Kafka using Python datatypes.
This is *not* an implementation of Kafka - it is purely a "toy" to illustrate
the ideas, and there will be approximations and things left out.

Let's start with a simple list.

The producer, P, adds items to the end of the list. The consumer, C, reads
them. In line with Kafka and the paper, we will term our items "events".

1. The events on the list are ordered, as P placed them onto the list
2. C does not *remove* events from the list - they stay there.

One P, one C
============

::

  P -> [ 0 1 2 3 4 5 ] -> C

C can ask for the earliest event - event ``[0]`` in Python terms.

It can ask for the most recent/latest event - event ``[-1]``

And it can ask for a particular event - for instance event ``[3]`` is ``3``

This is important because P writes to (appends to) the list at its own speed,
and C reads independently.

So C needs to maintain a note of which event it last read, so that it can make
sure not to miss any.

Note that if we ask directly for ``[-1]`` we'll need to do a little bit more
work to make sure that the offset recorded by C is the actual index, and not
``-1``.

Adding more P
=============

More producers just means that more events get added. So maybe we see P1
adding integer events, and P2 adding lowercase alphabetic events::

  P1
    \
     [ 0 1 2 3 4 5 a 6 7 b 8 c ] -> C(5)
    /
  P2

C will continue to work just the same.

Adding more C
=============

Since each C has an idea of where it last read from, we can add more
consumers::

  P1                             C1(5)
    \                           /
     [ 0 1 2 3 4 5 a 6 7 b 8 c ]
    /                           \
  P2                             C2(0)

and the new consumer can choose whether to start reading from the beginning of
the event stream, the end, or some other value.

More...
=======

The list of items will eventually grow too big, so allow dropping some off the
start. For this, we want to move to a Deque.

https://docs.python.org/3/library/collections.html?highlight=deque#collections.deque

In a real Kafka application, we'd likely move old events to a data lake of
some kind (for instance, Cassandra). In our simple example, we might say that
when we get more than N (perhaps 20 - we're staying small) events in the
stream, we'll drop the first 10 off the Deque, and put them as a record in a
CSV file. Python has good support for CSV files, and they're easy to read into
Pandas for later analysis.

But now we have a problem with C and its index.

Starting a new C and asking for ``[0]`` will do the right thing - give us the
oldest "current" entry. ``[-1]`` will do what we expect as well.

However, if we recorded the index as ``12``, and the first 10 items have now
gone, that won't work. So we need to add a bit more infrastructure:

* Alongside the Deque we need to keep the actual index of the first event
* When C asks for ``[12]`` we actually need to subtract that actual index from
  the request, so that we give back ``[2]``

In Python, we could make a subclass of Deque, add the new "offset" value, and
either override the method backing ``[]``, or provide a new method that we use
instead.

Or (mad idea) we could use a dictionary. Or, more specifically, a new class
with a dictionary ABC.  The access syntax is the same: ``[n]``. We'd need to
record the "last" index, to enable us to do ``[-1]``. We'd also need to record
the "earliest" index, to allow for removing the first N events. But actually
access would be simpler (C will always be able to use the correct index
directly, as they are now dictionary keys), and we get interesting semantics
if C tries to access an event that has "gone away" - either a index exception,
or (perhaps) ``None``.

While a deque or a dictionary might be the best choice here, using a new class
is definitely the way to go - it would also allow us to *change* the
implementation without P or C needing to know.

-----

Multiple topics

Consumer groups

Compaction

Threading/multiple processes/etc.

What else?

Schemas using Pydantic?

Flink???
