Command line interface
======================

All commands can be executed by using the ``tutor-planner`` script if you have installed the project using ``setup.py``
(via pip) as written :doc:`here </contents/install>`. Otherwise you have to run the command line interface
by using ``python -m tutorplanner`` (this will run the ``__main__`` module of the ``tutorplanner`` package).

You can show the help of the cli by running:

.. code-block:: bash

  tutor-planner --help

It prints a list of commands, descriptions and arguments. You can also get the help of single commands and
sub-commands, e.g.

.. code-block:: bash

  tutor-planner planning --help

If not all arguments are given, the cli prints the help automatically.


List of commands
----------------

+------------------------------------+--------------------------------------------------------------------------------+
| Command                            | Description                                                                    |
+====================================+================================================================================+
| ``check-plan``                     | check if a generated plan is consistent                                        |
+------------------------------------+--------------------------------------------------------------------------------+
| ``check-tutor-responses``          | check if tutor responses are valid                                             |
+------------------------------------+--------------------------------------------------------------------------------+
| ``export-plan``                    | export plan to xlsx (see :doc:`/contents/target_plan`)                         |
+------------------------------------+--------------------------------------------------------------------------------+
| ``find-available-tutors``          | find available tutors at a given time                                          |
+------------------------------------+--------------------------------------------------------------------------------+
| ``lsf-to-csv``                     | convert LSF files to CSV (see :doc:`/contents/rooms_csv`)                      |
+------------------------------------+--------------------------------------------------------------------------------+
| ``lsf-to-xlsx``                    | convert LSF and CSV files to XLSX (see :doc:`/contents/rooms_csv`)             |
+------------------------------------+--------------------------------------------------------------------------------+
| ``output``                         | generate PDFs and other output formats (like HTML) of plans, tickets etc.      |
|                                    | (see :doc:`/contents/output`)                                                  |
+------------------------------------+--------------------------------------------------------------------------------+
| ``output-diff-of-plans``           | output the difference of two plans                                             |
+------------------------------------+--------------------------------------------------------------------------------+
| ``planning``                       | execute planning algorithm, either initial or rolling wave                     |
|                                    | (see :doc:`/contents/planning`)                                                |
+------------------------------------+--------------------------------------------------------------------------------+
| ``room-info``                      | show room information like room type, number of seats, availability of a       |
|                                    | projector                                                                      |
+------------------------------------+--------------------------------------------------------------------------------+
| ``show-working-tutors``            | show the working tutors at a given time                                        |
+------------------------------------+--------------------------------------------------------------------------------+
| ``state``                          | handle active and working plans                                                |
+------------------------------------+--------------------------------------------------------------------------------+
| ``tutor-mail-addresses``           | show the mail addresses of the tutors                                          |
+------------------------------------+--------------------------------------------------------------------------------+
| ``tutorial-seat-overview``         | overview of tutorial seats                                                     |
+------------------------------------+--------------------------------------------------------------------------------+
| ``update-plan``                    | update plan manually (see :doc:`/contents/manual_updates`)                     |
+------------------------------------+--------------------------------------------------------------------------------+
