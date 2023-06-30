==============================================
Explaining Apache Kafka® using Python concepts
==============================================

...or, 'Writing a "toy" Kafka'

(Do I actually have any intent of *writing* such a thing, or should this just
talk through it? Having code may make it easier to talk about, and will make
it easier to spot mistakes.)


Reference

* `The Log: What every software engineer should know about real-time data's unifying abstraction`_
  which introduces the idea that tables and events are a dual, and leads to
  Apache Kafka® as an implementation of that idea.

* Olena Kutsenko's blog post `Apache Kafka® simply explained`_

  Maybe reference her high points (from the start) of what Kafka is, and note
  which one's we aren't going to address:

  * **an event streaming platform** - well, we'll sort of provide a toy
    version
  * **a platform to handle transportation of messages** - ditto
  * **distributed** - nope
  * **scalable** - oh my, no
  * **community** and **wide ecosystem** - of course not

.. _`The Log: What every software engineer should know about real-time data's unifying abstraction`:
  https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying
.. _`Apache Kafka® simply explained`: https://aiven.io/blog/kafka-simply-explained

The proposal here is to explain the ideas of Kafka using Python datatypes.
This is *not* an implementation of Kafka - it is purely a "toy" to illustrate
the ideas, and there will be approximations and things left out.

Mechanism
=========

I was thinking of having a "monolithic" Textual program, much as I did with
the Fish & Chips & Kafka talk. However, I wonder if having the "kafka" bit be
a FastAPI prgram would be simpler - I can then have the producer(s) be in a
separate program (maybe with simple ``__repr__`` to display what they're
doing) and consumers the same. This would actually *look* more like actual
Kafka. It's also more flexible for playing with the parts, and doesn't
introduce the complexity of a Textual GUI.

  **Note:** Why yes, if the "mock kafka" is in a FastAPI application, we will
  be storing a class instance as a global, so it persists. I hope it's obvious
  we'll only want one worker.

  And any audience member who asks if we shouldn't be using Redis to persist
  the data instead will deserve brownie points!

Notes
-----

* Let's not forget https://www.gentlydownthe.stream/

* FastAPI for the win

* Use httpx instead of requests (it's better maintained, more modern, supports
  asyncio)

  https://www.python-httpx.org/

* When retrieving data, look at SSE. Do the normal POST to send stuff, but do
  a GET that specifies an offset and returns a stream from that point. This is
  now standard HTTP 2

  (This is Ben nerd-sniping me with a way to (a) learn interesting stuff, (b)
  show off interesting stuff, and (c) make the actual "toy" just *that bit* better.)

  FastAPI and SSE:

  * 2022 https://devdojo.com/bobbyiliev/how-to-use-server-sent-events-sse-with-fastapi
  * 2020 https://sairamkrish.medium.com/handling-server-send-events-with-python-fastapi-e578f3929af1
  * The starlette (https://github.com/encode/starlette) TestClient uses httpx
  * 2020 https://sysid.github.io/server-sent-events/

  HTTPX and SSE:

  * https://github.com/florimondmanca/httpx-sse
  * https://github.com/encode/httpx/issues/1278 has comments, and ends up
    referrring to httpx-sse. The HTTPX
    third part packages page (https://www.python-httpx.org/third_party_packages/)
    also now refers to it.

  Part 9
  (https://christophergs.com/tutorials/ultimate-fastapi-tutorial-pt-9-asynchronous-performance-basics/)
  of "The Ultimate FastAPI Tutorial" shows using httpx in the context of (the
  client for) a FastAPI service.

  **Using SSE** should let me support the ``async for <thing>: get next
  thing`` sort of loop in the Consumer. This may only be for the DevCenter
  variant of the text - for the talk I hadn't gone as far as thinking about
  writing the Consumer (or, indeed, Producer) classe, but only implementing
  the backend, the ``Kafkaesque`` FastAPI server itself. However, providing
  basic Producer and Consumer classes would be very nice, and actually
  probably isn't much work.

* *Do* write "stale messages" to a file, as this is an important principle of
  how kafka is used - and any Python programmer should understand how to get
  "old" messages from a file. (hmm - or perhaps even a local sqlite db???)

* At the end, if there's a DevCenter piece, implement one of the
  Fish&Chips&Kafka examples using the "toy" service - and that's when having
  simple Consumer and Producer classes would be especially useful.

  ...the more I think of it, the more that's probably a thing to do right from
  the start, so the user of the "toy" never has to worry about network
  POST/GET minutiae.

Note on naming: PyPi already lists https://pypi.org/project/kafkaesque/ as
"a flask style kafka consumer", an "extension of the KafkaConsumer from the
kafka-python package". The source code is at https://github.com/sankalpjonn/kafkaesque
and it was last touched 5 years ago.


One P, one C
============

Let's start with a simple Deque.

The producer, P, adds items to the start/left of the deque. The consumer, C, reads
them. In line with Kafka and the paper, we will term our items "events".

1. The events on the list are ordered, as P placed them onto the list
2. C does not *remove* events from the list - they stay there.
3. So C has an idea of where it last read from

Start with a Deque
------------------

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

Notes:

* Use ``append(x)`` or ``extend(iterable)`` to add new items to the deque -
  this seems the most natural way of thinking about "latest" items.
* ``len(deque)`` will give the length of the deque, which we can use to work out
  the index of entry ``[-1]``
* ``maxlen`` is the maximum length of the deque, or ``None`` if it's unbounded

But we don't have infinite storage
----------------------------------

Eventually, we'll "run out of room" in our deque. So we'll want to drop older
events.

This means that C won't be able to use its index directly any more - the
actual index ``[0]`` won't be the "theoretical" index ``[0]``.

  This "theoretical" index is the **offset** of the event, in Kafka terms.

So wrap the deque in a class. Let's call it ``Kafkaesque``. Create the deque with::

  collections.deque(maxlen=MAXLEN)

and provide some methods:

* ``get(n)`` to retrieve the entry at offset ```n``. Treats negative ``n`` as
  we'd expect (so ``-1`` means the last entry). Raises an exception if ``n``
  no longer exists in the deque.

* ``earliest()`` gets the earliest entry (the entry with *actual* index
  ``[0]``), and returns a tuple of the entry offset and its value: ``(offset,
  value)``

* ``latest()`` gets the latest/newest entry (the entry with *actual* index
  ``[-1]``), and returns a tuple of the entry offset and its value: ``(offset,
  value)``

We might as well also have ``put(value)`` for adding a value to the deque, so
that we don't need to access it directly.

  **Note:** This means old events are just discarded. Does *actual* Kafka have
  a mechanism to automatically push old events to backing/cold storage? I
  think worrying about that is beyond the scope of this discussion - or if
  not, something we would introduce in the "optional" stuff at the end.

Topics
------

With real Kafka, events can be sent to *topics* (add a brief discussion of why
this is useful <smile>).

  Topics allow us to organise events by what sort of event they are, what they
  represent or how they are to be managed.

We can do this ourselves by having an array of our deque-wrapper class (which
we should now rename as ``Topic``, and have a new top-level ``Kafkaesque``
class to contain that array).

The ``Topic`` access methods then have corresponding access methods in the top
level class, which take the topic index as their first argument. The producer
and consumer have to specify the topic they want to interact with.

  **Note:** The producer specifies the topic for each ``put``, so a single
  producer can write to multiple topics.

  The consumer decides on the topic when it is created, so a single
  consumer will not read from multiple topics.

  **(I haven't got that wrong, have I?)**

Topics and keys
---------------

Maybe also provide the ability to ``put`` an event and use a hash function to
decide which topic to write to, instead of being explicit about the topic index.


Adding more P
=============

More producers just means that more events get added. So maybe we see P1
adding integer events, and P2 adding lowercase alphabetic events::

  P1
    \
     [ 0 1 2 3 4 5 a 6 7 b 8 c ] -> C(5)
    /
  P2

or the different producers write to different topics.

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

Committing consumer positions
=============================

Kafka allows a consumer to *commit* its current position(s), so that if it
crashes it can resume from its last saved state.

Our equivalent would be to support a dictionary of::

  <some sort of consumer id> : <the necessary position information>

which should be easy enough.

Partitions
==========

Explain why partitions.

* A producer writes to a set of partitions (that constitute a topic or topics)
* A consumer reads from a set of partitions

In our terms, this is just pushing the actual deques down another level (so we
have one deque per partition) and adding in more management functionality to
make them work appropriately.

**TBD: Add in a proper description of partitions, to work out what we need.**



Consumer groups
===============

One or more consumers agree to "share" events from one or more topics.

Each consumer gets allocated particular partitions from the topics.

.. note:: So we can't do this until we've introduced partitions.

We need a ``ConsumerGroup`` class.

An instance of that class

* has a name - the name of the consumer group
* knows which topics it is managing, and what partitions they have
* contains a dictionary mapping consumers to partitions

This is a separate entity from the ``Kafkaesque`` class.

A consumer makes a request to join a consumer group.

1. It looks the consumer group up by name
2. It calls the ``join`` method
3. The partitions are shared out between the new and existing consumers
   (again). In "the real thing" there are mechanisms to cope with when that
   goes wrong, but we'll ignore that <smile>

To get a new event, the consumer now asks the consumer group for the next
event, and the consumer group will get the next event from the relevant
partition(s).

**TBD: Is this actually a correct description of the behaviour we want?**

Batching
========

Given the underlying use of deques, it's perfectly possible to add more than
one item at a time (to a particular deque) - that just uses the ``extend``
method.

So we could build batching into our classes if we wished (with a little bit of
care around hashing events).

And if we're doing the FastAPI thing, then it's not hard to see how we'd write
an API for that, as well.

So let's just mention the idea, but not actually bother doing it <smile>.

Brokers
=======

We shan't try to simulate brokers - they're not an obvious necessity with out
"in memory" model, and trying to provide them will, I think, add length to the
talk to no good purpose.

However, they should be mentioned, so I do need an understanding here of how
we *would* simulate them.

  Brokers allow replication of partitions across physical devices (???). Each
  broker will contain multiple partitions, and each partition will be on
  multiple brokers. So if a device goes down, the data is not lost.

**TBD: Work out how we'd do "brokers" if we did want to.**

Other things ignored
====================

Include (but there are probably more):

* Brokers - see above
* Compaction
* Safety / resiliency / reliability - all the points of the real thing!

Old notes
=========

?Consumer can register its offset with the queue class, so it doesn't have to
remember it itself (consumer doesn't necessarily do this all the time)

Multiple topics

Consumer groups

Compaction

Threading/multiple processes/etc.

Schemas using Pydantic?

What else?

Can we do anything with brokers, or is that really really just an
implementation detail?

Flink???
