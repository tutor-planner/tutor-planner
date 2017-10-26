Generated plans
===============

.. seealso:: Module :py:mod:`tutorplanner.input.plan`


The generated plans consist of three pickled files.

``personalPlans.pickle``
  tutor's last name → task type → day index → hour → bool (if the tutor has a task at the slot)

``personalPlans_Rooms.pickle``
  tutor's last name → task type → day index → hour → room name or empty string

``plan.pickle``
  task type → day index → hour → number of tutors


``personalPlans.pickle`` and ``plan.pickle`` can be generated from ``personalPlans_Rooms.pickle``
as it contains all data. In most cases, the latter fits best for reading.

.. note::
  The task type in ``personalPlans_Rooms.pickle`` is a bit redundant since it can be read from the settings.
  It could be removed in the future. Additionally, the other files could be removed, as well as the day index could be
  replaced by a :py:class:`datetime.date`.


There is a folder that contains all output plans (``settings.paths.plans``). A subfolder is created in every planner
run. The name of the subfolder is determined by using the date, an incremental number and a label (``initial``,
``rolling`` or ``manual-updates``). For details see :py:func:`tutorplanner.input.plan.get_new_plan_folder`.

In this folder, the generated plans are saved to several folders named as ``Level_1`` up to ``Level_7``
(initial planning) or ``Level_9`` (rolling wave planning). Additionally, a happiness plot and a LP and a solution file
are saved for each level.
