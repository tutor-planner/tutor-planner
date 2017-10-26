Installation
============

Setting up a virtual environment
--------------------------------

We recommend to set up a virtual environment for the tutor planner. For doing that, you have to execute the following
command:

.. code-block:: bash

  python3 -m venv env

where ``python3`` is the name or path of your Python 3 executable and ``env`` is the folder in which the virtual
environment is created.

Alternatively, you can set up a virtual environment with ``virtualenv``. If you want to use ``virtualenv``,
you have to install it using your system's default package manager or ``pip``.

Every time you want to work in the environment, you have to activate it using the following command in bash:

.. code-block:: bash

  . env/bin/activate  # or
  source env/bin/activate

This command sets some shell variables (e.g. the PATH variable). You can explicitly leave the environment by calling
``deactivate``.

I have created a `script for simpler activation`_ that you can source or insert in your ``.bashrc``. Now you only have
to call ``activate`` and it finds virtual environments in parent directories automatically. For a more complete
virtualenv handling you can use virtualenvwrapper_ or pipenv_, but I don't think that it is necessary.


.. _Installation of tutor-planner:

Installation of ``tutor-planner``
---------------------------------

You can either install the tutor planner in production mode or in development mode (making it possible to edit
the code). Before installing, you should activate the virtual environment and switch to the top directory of
the project.

To install in production mode, you have to execute:

.. code-block:: bash

  pip install .

To install in development mode, you have to execute:

.. code-block:: bash

  pip install -e .[dev]

The parameter ``-e`` leaves the package in editable mode which means that it only links the project when installing.
The parameter ``.`` refers to the current folder. The ``[dev]`` means that it also installs the development
requirements from ``setup.py``.


Now you should be able to run the command line interface ``tutor-planner`` when you are in the virtual environment.
If you want to know more about the command line interface, have a look at :doc:`/contents/cli`.


GurobiPy
^^^^^^^^

Assuming that you have set up Gurobi and already have a license:

.. code-block:: bash

  cd $GUROBI_HOME
  python setup.py install

If it complains about not being able to write to the build directory, you can use:

.. code-block:: bash

  python setup.py build -b /tmp/build install

.. note::
  Make sure to set ``GUROBI_HOME`` and ``LD_LIBRARY_PATH``. Example of ``.bashrc``:

  .. code-block:: bash

    export GUROBI_HOME="/opt/gurobi750/linux64"
    export PATH="$PATH:$GUROBI_HOME/bin"
    export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$GUROBI_HOME/lib"

  Otherwise you would encounter an error:

  .. code-block:: pytb

    Traceback (most recent call last):
      File "...", line 1, in <module>
        from gurobipy import *
      File ".../env/lib/python3.6/site-packages/gurobipy/__init__.py", line 1, in <module>
        from .gurobipy import *
    ImportError: libgurobi75.so: cannot open shared object file: No such file or directory


.. _script for simpler activation: https://gist.github.com/AlexElvers/f9afb8122f4b4c1e3f6d
.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.io/
.. _pipenv: https://docs.pipenv.org/
