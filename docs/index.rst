Welcome to tutor-planner!
=========================

Welcome to tutor-planner's documentation. The tutor planner is a tool used by the department
`Internet Network Architectures (INET)`_ of Technische Universität Berlin (TU Berlin) for the
module *Einführung in die Programmierung* (introduction to programming). The module contains a two-week course to
introduce new students in programming in C. Each day is filled with lectures, tutorials and computer exercises.
This project is used for assigning the tutors to the tasks.

For the course, the tutor planner has a list of tutors, room bookings, target plans and much more information.
The project contains a planner that is using Gurobi_, a optimization solver for linear programming, to optimize
the tutor plans.

The plans can be exported to overall and individual tutor plans, room plans and student tickets.

The documentation is currently a draft.

If you are new to the tutor planner, you might want to look at :doc:`/contents/getting_started`. If you are searching for the
usage of the planner, you should read :doc:`/contents/cli`.


Contents
--------

.. toctree::
  :maxdepth: 2

  contents/getting_started
  contents/install
  contents/cli
  contents/settings
  contents/tutor_information
  contents/lsf_files
  contents/rooms_csv
  contents/target_plan
  contents/planning
  contents/generated_plans
  contents/plan_states
  contents/manual_updates
  contents/output


API
---

.. toctree::
  :maxdepth: 2

  api/data
  api/plan
  api/rooms
  api/lsf_parser
  api/tutor
  api/settings
  api/converter
  api/read_pickled_files
  api/planning
  api/gurobiinterface
  api/update_plan
  api/output


Contributors
------------

* Matthias Rost <mrost AT inet.tu-berlin.de>
* Alexander Elvers <aelvers AT inet.tu-berlin.de>
* Elias Döhne <edoehne AT inet.tu-berlin.de>


.. Indices and tables are a chapter in html, not in pdf

.. only:: builder_html

  Indices and tables
  ------------------

  * :ref:`genindex`
  * :ref:`modindex`
  * :ref:`search`

.. only:: not builder_html

  * :ref:`modindex`


.. _Internet Network Architectures (INET): https://www.inet.tu-berlin.de/
.. _Gurobi: https://www.gurobi.com/
