Manual updates
==============

.. seealso:: Module :py:mod:`tutorplanner.update_plan`


Often, you want to make manual changes on the generated plans without changing the code or the tutor availability.
For doing this, you can use the ``update-plan`` command. The command is based on the concepts of
:ref:`active and working plans`.

The manual changes are logged to ``changes.log``.

Task descriptions of the following commands should be in quotes. Spaces in tutor and room names should be replaced
by underscores. The basic format is ``"TUTOR_NAME DATE HOUR ROOM_NAME"``, where ``TUTOR_NAME`` is the tutor's last
name and ``DATE`` is either ``YYYY-MM-DD`` or ``MM-DD``.

Make sure to activate the working plan before using rolling wave planning or generating output files (such as PDF).


Add a task
----------

.. code-block:: bash

  tutor-planner update-plan add NEW_TASK

Remove a task
-------------

.. code-block:: bash

  tutor-planner update-plan remove OLD_TASK

The room name is optional.

Switch a task
-------------

.. code-block:: bash

  tutor-planner update-plan switch OLD_TASK NEW_TASK

The old task is removed and the new task is added in a single operation. The room name of the old task is optional.

Undo the last change
--------------------

.. code-block:: bash

  tutor-planner update-plan undo
