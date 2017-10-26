Creating a target plan
======================

The target plan is used in planning. It contains the desired number of tutors at each time slot.

You can create an empty target plan by using:

.. code-block:: bash

  tutor-planner export-plan --empty

There is an optional parameter for the output file (``--output FILENAME``). The output is saved in an XLSX file.
If the output file is unset, ``settings.paths.planner`` is used.

You can fill in the target plan in the worksheet ``Target``. The plan contains time slots and task types.
You have to enter the number of tutors that are targeted for the tasks at the time slots.

.. warning:: Use ``--empty`` only once as it deletes any existing worksheet named ``Target``.

.. warning:: Create backups of your planner file.


You can also export the generated plan, using:

.. code-block:: bash

  tutor-planner export-plan --pickled
