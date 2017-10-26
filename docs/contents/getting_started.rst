Getting started
===============

At first, you have to create a project folder and add a ``settings.yaml`` as described in :doc:`/contents/settings`.
You also need some input data: the tutor information and the room bookings.

You can get the tutor information by sending a CSV file to all tutors. The tutors add their personal information,
preferences and availability and send the CSV file back to you. You have to save the CSVs in a specified folder.
Have a look at :doc:`/contents/tutor_information` for more information.

The room bookings can be exported as XML from LSF_. You can convert LSF files to CSV and XLSX (see
:doc:`/contents/lsf_files` and :doc:`/contents/rooms_csv`).

Next, you have to :doc:`create a target plan </contents/target_plan>` and :doc:`run the planner </contents/planning>`.

At the first run, you have to use the initial planner. If everything works, you get individual plans for each tutor.
Maybe you have to change the target plan, the bookings or the tutor availability later on. For that reason, the
tutor planner has a rolling wave planner. It uses an existing plan as base. Rolling wave planning tries to minimize the
changes in relation to the previous plan.

You can also apply :doc:`manual updates </contents/manual_updates>` on the generated plan.

The plans can be :doc:`exported as PDF, HTML and PNG </contents/output>`.


.. _LSF: https://www.tu-berlin.de/lsf/home/
