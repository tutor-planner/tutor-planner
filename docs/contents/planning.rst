Planning
========

.. seealso:: Module :py:mod:`tutorplanner.planning`

The tutor planner uses two types of planning: `initial planning` and `rolling wave planning` (short: rolling planning).
Each planner consists of multiple phases, so called levels. The main difference between initial and rolling wave
planning is that the rolling wave uses an existing plan as input.

After each planning level, the resulting plans are written to a new folder as described in
:doc:`/contents/generated_plans`.


Initial planning
----------------

The initial planning starts from scratch. It uses the project data, including the target plan, and tries to find
suitable tasks for each tutor.

You can call initial planning by:

.. code-block:: bash

   tutor-planner planning initial

The initial planner uses the following seven planning levels:

#. minimize deviation from plan
#. minimize work spread
#. maximize min happiness
#. maximize cube happiness
#. minimize hoppings between buildings
#. select best rooms
#. maximize tutor--room stability


Rolling wave planning
---------------------

The rolling wave planning starts from an existing plan. It uses the project data, including the target plan, and tries
to find suitable tasks for each tutor. It also tries to minimize the number of changes in comparison to the existing
input plan.

You can call rolling wave planning by:

.. code-block:: bash

  tutor-planner planning rolling NEXT_DAY

where ``NEXT_DAY`` is the date of the next day to plan (``YYYY-MM-DD`` or ``MM-DD``).

The rolling wave planner uses the following nine planning levels:

#. minimize deviation from plan
#. maximize task contingency
#. minimize work spread
#. maximize min happiness
#. maximize cube happiness
#. minimize hoppings between buildings
#. select best rooms
#. maximize tutor--room stability
#. maximize task--room contingency
