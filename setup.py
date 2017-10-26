from setuptools import setup, find_packages

install_requires = [
    "matplotlib",
    "PyYAML",
    "beautifulsoup4",
    "lxml",
    "click",
    "mako",
    "xlsxwriter",
    "openpyxl",
]

dev_requires = [
    "pytest",
    "pytest-cov",
    "sphinx",
]

setup(
    name="tutor-planner",
    # version="1.0a1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        "dev": dev_requires,
    },
    entry_points={
        "console_scripts": [
            "tutor-planner = tutorplanner.__main__:cli",
        ],
    },
)
