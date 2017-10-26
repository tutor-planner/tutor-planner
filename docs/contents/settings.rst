Settings file
=============

.. seealso:: Module :py:mod:`tutorplanner.util.settings`


At first, you have to create a project folder and a settings file. The project folder can be an empty folder, you
can add the data later. The central settings (paths, planning dates/times) are stored in ``settings.yaml``.
It is in YAML format and should contain the following data:

* ``paths``: file names and directories of data

  All paths are relative to the working directory (the ``settings.yaml`` is in the working directory too).

  * ``tutor_responses``: list of folders for tutor responses

    Example:

    .. code-block:: yaml

      tutor_responses:
      - tutor_availability/first_replies # first week
      - tutor_availability/second_replies # second week

  * ``bookings``: CSV file of room bookings

    Example:

    .. code-block:: yaml

      bookings: all_bookings.csv

  * ``bookings_additional``: CSV file of additional rooms that students can use

    This is only used in PDF output.

  * ``course_leaders``: CSV file of course leaders, see :ref:`course-leaders-file`

    Example:

    .. code-block:: yaml

      course_leaders: course_leaders.csv

  * ``planner``: XLSX file of target plan

    Example:

    .. code-block:: yaml

      planner: planner.xlsx

  * ``plans``: output folder of generated plans

    This also contains the plan paths file (``plan_paths.yaml``).

  * ``templates``: template folder

  * ``pdf_output``, ``html_output``, ``png_output``: folder for plan exports

    Example:

    .. code-block:: yaml

      pdf_output: pdf
      html_output: html
      png_output: png

* ``times``: list of times used in export and tutor parsing

  Note that some functions increase the resolution to 1 hour.

  Example:

  .. code-block:: yaml

    times: [10, 12, 14, 16]

* ``days``: list of dates for planning

  The dates have to be in ISO format.

  Example:

  .. code-block:: yaml

    days:
    - 2016-10-17
    - 2016-10-18
    - 2016-10-19
    - 2016-10-20
    - 2016-10-21
    - 2016-10-24
    - 2016-10-25
    - 2016-10-26
    - 2016-10-27
    - 2016-10-28

* ``forbidden_timeslots``: dict of date to list of forbidden time slots

  Forbidden time slots are used for slots that should not contain tutorials/exercises.

  Example:

  .. code-block:: yaml

    forbidden_timeslots:
      2016-10-17: [10, 12, 14, 16]
      2016-10-18: [12]
      2016-10-19: [14]
      2016-10-20: [16]
      2016-10-21: [14]
      2016-10-24: [16]
      2016-10-25: [12]
      2016-10-26: [14]
      2016-10-27: [16]
      2016-10-28: []

* ``expected_number_of_rooms``, ``expected_number_of_students``: the expected numbers are used for formatting in the planning file

* ``room_patterns``: list of room patterns that are used for getting room information, see :ref:`room-patterns`

* ``optimization_parameters``: parameters of the MIP

  Example:

  .. code-block:: yaml

    optimization_parameters:
      bounds:
        task_contingency: 0.95
        maximal_work_spread: 1.5
        min_happiness: 0.9
        cube_happiness: 0.95
        minimal_mar_tel_hopping: 1.05
        best_rooms: 0.98
        tutor_room_stability: 0.9
      time_limits:
        short: 360
        long: 1800

* ``specific_working_hours``: working hours regulations of tutors

  Example:

  .. code-block:: yaml

    specific_working_hours:
      Mustermann:
        total: {min: 16, max: 28}
        first_week: {min: 12, max: 20}
        second_week: {min: 4, max: 8}

  The tutor Mustermann has to work maximum 28 hours (instead of the half of the working hours per month that she
  has written in her :doc:`tutor information CSV </contents/tutor_information>`. She has to work 12 to 20 hours
  in the first week and 4 to 8 hours in the second week.

You can find a complete example in ``test_data``.


.. _course-leaders-file:

Course leaders file
-------------------

The course leaders file is a simple CSV (rather: TSV) file that contains the following columns:

* ``first_name``
* ``last_name``
* ``email``
* ``phone``


.. _room-patterns:

Room patterns
-------------

Room patterns are evaluated from top to bottom. If a room is matched, it sets or overwrites all attributes.

Room patterns contain the following attributes:

* ``pattern``: the pattern itself

  The pattern is matched on the room name using wildcards with ``*``.

  Example: ``MAR *`` matches every room starting with ``"MAR "``.

  Note that you have to enquote patterns that start with ``*`` due to the YAML syntax.

* ``type``: room type (tutorial, exercise, exerciseMAR, grading)

* ``capacity``: room capacity (number of seats)

* ``tutorial_size``: not used anymore

* ``projector``: 1 if the room has a projector, 0 otherwise
