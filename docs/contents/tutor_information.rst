Tutor information
=================

.. seealso:: Module :py:mod:`tutorplanner.input.tutor`


The planner needs to know when a tutor is available. Therefore, there is a form that the tutors answer.
Besides the availability, there are also some personal questions:

* last name
* first name
* email address
* university department
* mobile phone number
* monthly working hours
* maximum working hours without break
* maximum tutorials without break
* knowledge in the programming language (0=none, 3=expert)
* unsureness of availability of second week (number of two-hour slots)

After one week, the tutors have to fill in a second form that only requests the last name and the availabililty of the
second week. This is necessary for our course because the tutors are students themselves and have courses and
especially tutorials of other courses that start in the second week. Often, the tutors only know about their other
tutorials after a few days. This is also a reason for having a rolling wave planner.

The format of the form is CSV (rather: TSV=tab-separated values). The first lines contain the personal questions
in the first column, and the answers in the second column. After the personal questions, there is an empty line
(containing no text or just tabs). After that, there is an availability table that starts in the second column
(because it looks better in text editors). The table contains a single week with the dates in the column header and
the time slots in the row headers (with a resolution of two hours, in our case).

In the rest of the table, the tutor has to fill in the availability:

* 0 = not available
* 1 = available but bad time slot
* 2 = available
* 3 = available and preferred

The planner tries to maximize the happiness of tutors that depends on the availability value when they have to work.

If there is more than one week, there is a table for each week separated by an empty line.

For details of the format, take a look at the empty form files or at the tests of :py:class:`tutorplanner.input.tutor.Tutor`.

You can check if the tutor responses can be parsed by using:

.. code-block:: bash

  tutor-planner check-tutor-responses
