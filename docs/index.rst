.. Active Boxes documentation master file.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Active Boxes
============

Tiny `ActivityPub <https://www.w3.org/TR/activitypub/>`_ framework written
in Python, both database and server agnostic.

Active Boxes is a modernized fork of
`Little Boxes <https://github.com/tsileo/little-boxes>`_ (relicensed from
ISC to MIT), updated to current Python packaging standards and Python 3.10+
features with an async-first API.


Features
--------

* Database and server agnostic: implement a backend that responds to
  activity side-effects — you're responsible for serving the
  activities/collections and receiving them
* ActivityStreams helper classes
  * with Outbox/Inbox abstractions
* Content helper using Markdown
  * with helpers for parsing hashtags and linkify content
* Key (RSA/Ed25519) helper
* HTTP signature helper (draft-cavage and RFC 9421)
* JSON-LD signature and Data Integrity proof helpers
* Webfinger helper


API Reference
-------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules


Project docs
------------

* `README <https://github.com/cwt/active-boxes>`_
* `Knowledge bundle <https://github.com/cwt/active-boxes/tree/master/documents>`_


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
