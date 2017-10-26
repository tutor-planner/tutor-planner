Room bookings from LSF
======================

.. seealso:: Module :py:mod:`tutorplanner.input.lsf_parser`


At the TU Berlin, there is a system called LSF_ (Lehre, Studium, Forschung) that contains the course catalog and the
room bookings of a course. The course owners can export the bookings in an XML format. The bookings might be in
multiple files.

.. The setting of the LSF path is ``paths.lsf``.


Parsing details
---------------

An excerpt of a LSF XML file looks like:

.. code-block:: xml

  <Terms>
    <TerID>123456</TerID>
    <TerBeginn>10:00</TerBeginn>
    <TerEnde>12:00</TerEnde>
    <TerBeginDat>18.10.2016</TerBeginDat>
    <TerEndeDat>18.10.2016</TerEndeDat>
    <TerRhyth>Einzel</TerRhyth>
    <VerID>23456</VerID>
    <MaxTeil />
    <TerRaumID>1907</TerRaumID>
    <TermBemerkung />
    <WoTag>Di</WoTag>
    <k_wochentag.wochentagid>2</k_wochentag.wochentagid>
    <k_wochentag.sort>2</k_wochentag.sort>
    <Rooms>
      <RaumBez>MAR 4.062</RaumBez>
    </Rooms>
  </Terms>

Although it is named ``<Terms>``, the tag contains a single event. The same applies to ``<Rooms>``.
As you can see, the language of the XML file is a mix of German and English with many abbreviations.
The fields we use are:

* ``TerBeginn``: start time
* ``TerEnde``: end time
* ``TerBeginDat``: start date
* ``TerEndeDat``: end date
* ``TerRhyth``: rhythm/frequency of the event:

  * ``Einzel``: single event
  * ``wöchentl``: weekly event
  * ``14tägl``: biweekly event
  * ``Block``: day period

* ``WoTag``: weekday

  * ``Mo``, ``Di``, ``Mi``, ``Do``, ``Fr``, ``Sa``, ``So`` for Monday to Sunday

* ``RaumBez``: room name


We expect the weekday to be set for weekly and biweekly events.


.. note::

  You should never write the LSF files by hand. Instead, use the :doc:`CSV format </contents/rooms_csv>` directly.



.. _LSF: https://www.tu-berlin.de/lsf/home/
