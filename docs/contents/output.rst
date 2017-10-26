Output plans and other stuff as PDF
===================================

.. seealso:: Module :py:mod:`tutorplanner.output`


You can use the ``output`` command to generate PDF files (and other formats) out of your data. There are plenty of
options, so it would be better for you to call the ``--help`` of the command line interface.

The subcommands of ``output`` are:

* ``badges``

  Output badges for tutors and course leaders with their names and roles on it.

* ``contact-list``

  Output a contact list of tutors and course leaders.

* ``tutor-plans``

  Output a plan for each tutor.

* ``tutor-schedule``

  Output a daily schedule for all tutors over all rooms.

* ``course-overview``

  Similar to ``tutor-schedule`` but for the students and without tutor names.

* ``tickets``

  Generate tickets for the students.

  For details, how many tickets are created for a tutorial, see :py:func:`tutorplanner.output.compute_tutorial_sizes`.
