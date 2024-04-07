# BlockChat
Semester project for Distributed Systems course.

## How to run
Install required libraries: `pip install -r requirements.txt`.

Execute app.py from command line providing the proper arguments.
Make sure to run a boostrap node instance first.  

### Run as boostrap (on port specified in `constants.py`):
python3 app.py -b

### Run as normal node:
python3 app.py -p <insert port here\>

## Setting block capacity and maximum nodes
You can set your own block capacity and the maximum number of nodes
inside `constants.py` altering the properties `MAX_NODES` and `CAPACITY`. 

