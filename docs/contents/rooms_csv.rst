Room bookings from CSV and XLSX
===============================

The room bookings can be imported from CSV and exported to CSV and XLSX. Unfortunately, XLSX is not supported for
importing, but you can just save the data area as CSV.

The format of room bookings in these formats is as follows: For each day, there is a block (a sub-table). Different
blocks are separated by an empty row. The block data consists of the date in the top left corner, the slot hours as
row headers, the room names as column headers. The rest of the block is filled with the room availability. If a room
is booked at the time slot, the corresponding cell is marked with `x` or `1`, otherwise the cell is empty or `0`.

You can leave columns of the block empty (without room name and bookings), these are skipped in import.

The name of the bookings file for import is ``settings.paths.bookings``. This has to be a CSV file.

The commands to save :doc:`LSF data </contents/lsf_files>` as CSV or XLSX are:

* ``tutor-planner lsf-to-csv``
* ``tutor-planner lsf-to-xlsx``

Note that ``lsf-to-xlsx`` can take LSF files as well as CSV files. It also has some parameters for filtering
and conditional formatting.
