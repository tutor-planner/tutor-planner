.. _active and working plans:

Plan states
===========

There are two states of plans: `active` and `working`. At the same time, at most one plan can be `active` and one plan
can be `working`. Other plans do not have a special state. The paths to the active and working plans are set in a file
``plan_paths.yaml`` in the plan output folder.

Initially, ``active`` and ``working`` are unset.

The active plan is used as input for the rolling wave planner. After running the planning (initial or rolling wave),
the active plan is set to the plan of the last level, e.g. ``active`` could be ``2016-10-12-1-initial/Level_7``.
The ``output`` command uses the active plan too.

The working plan is set by ``tutor-planner state``. You can create a working copy of the active plan. For example,
``working`` could be ``2016-10-12-2-manual-updates`` (note that manual updates don't have levels).
After doing manual updates, you can activate the working plan, so that the current working plan is now set as
``active`` and ``working`` is unset again. See :doc:`/contents/manual_updates` for details.

Of course, you can also edit ``active`` and ``working`` by hand, but it should not be necessary if you are working
linearly.


Show state
----------

.. code-block:: bash

  tutor-planner state show

Shows the current active and working plans. Also shows the number of manual changes on the working plan.

Create a working copy
---------------------

.. code-block:: bash

  tutor-planner state init-working

The working copy is saved in a new plan folder with label ``manual-updates`` (see :doc:`/contents/generated_plans`).
The pickle files are copied from the active plan.

Activate working plan
---------------------

.. code-block:: bash

  tutor-planner state activate-working

The active plan is set to the working plan and the working plan is unset.

Activate parent plan
--------------------

.. code-block:: bash

  tutor-planner state activate-parent

The active plan is set to the parent plan. The parent plan of a plan created by manual updates or rolling wave planning
is the plan it was derived from.
