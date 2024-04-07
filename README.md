# BlockChat
Semester project for Distributed Systems course.

## How to run
Execute app.py from command line providing the proper arguments.
Make sure to run a boostrap node instance first.  

### Run as boostrap (on port specified in `constants.py`):
python3 app.py -b

### Run as normal node:
python3 app.py -p &lt;insert port here&gt;

## Setting block capacity and maximum nodes
You can set your own block capacity and the maximum number of nodes
inside `constants.py` altering the properties `MAX_NODES` and `CAPACITY`. 

