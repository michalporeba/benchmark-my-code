# benchmark-my-code
A simple, even if not the most efficient, way to benchmark python code for educational purposes. 

## usage 

```python
import benchmark_my_code

def my_function():
    pass

if __name__ == '__main__':
    results = benchit(my_function)
    print(results)
```


## ideas and objectives

* The module's objective is to support learning pythong by making understand performance of code easier. 
* While the code being evaluated doesn't have to be functional, for simplicity, parts tested are functions. 
* It needs to be easy to compare multiple implementations. 
* It could be helpful to validate correctness of an implementation.
* The code being tested might be very inefficient so timeouts are essential. 
* Memory analysis are much slower, so they have to be less frequent, but built into the default behaviour. 

## how to get reliable results

* split the desired number of executions into batches
* run the first batch and discard the results - this is the warmup to account for run time optimisation.
* run the first batch again, keep the results, calculate stats, including median
* run another batch, calculate median. if it is within 1% of the overall median then stop, otherwise aggregate the data with previous batches. 
* continue th eprevious step until it is true, or max runs , or max time is reached. 

If multiple functions or parameter variations are provided, run each variant following the above.  