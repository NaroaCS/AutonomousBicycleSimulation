---
sidebar_position: 2
---

# Getting Started

Before you start, you will need to download the code from our **[GitHub repo](https://guides.github.com/)**. If you are new to GitHub, **[here's](http://rogerdudler.github.io/git-guide/)** a simple guide to get you started. To get our code run:

```shell
git clone https://github.com/NaroaCS/AutonomousBicycleSimulation.git
```

Make sure you have Python 3.6 or higher. To check your python version:

```shell
python3 --version
```

If you do not have Python 3, you can donwload it from  **[Python.org](https://www.python.org/downloads/)**. 

Finally, you will need some packages:

* simpy
* pandas
* numpy
* matplotlib
* networkx
* scipy==1.6.0
* geopandas
* scikit-learn
* pyproj
* git+git://github.com/imartinezl/pandana.git@master

To install the packages you can use pip3, which comes already ingtegated with Python3. Eg:

```shell
pip3 install numpy
```

Alternatively, you can also use **[Anaconda](https://www.anaconda.com/)**, which can help you to handle packages and libraries. In that case, you would use conda to install the packages. Eg: 

```shell
conda install numpy
```
