#### you are given several log files that contain the execution intervals for the jobs executed on the server. 
# We are interested in learning the times when the system is busy. 
# Your task is to create a function that will process all of intervals found in the file(s) and generate a consolidated output that will show the busy times of the system

# Assumptions:
# 1. Assumed that the data has already been parsed and is in the format that can be processed further
# 2. the parsed data is passed into the method that you create

# Sample raw file data
#                                                                                       37----43
# 1---5       10------17                                          29---------39
#        5-7                   19-21
#    3----8                                                           27----32
#
#Sample output

# 1------8 10------17 19-21      27---------------43

def consolidate_busy_times(intervals:list) -> str:
    """
    Consolidate overlapping intervals to determine the busy times of the system.

    Args:
        intervals (list of tuple): A list of intervals (start, end) representing job execution times.

    Returns:
        list of tuple: A list of consolidated intervals representing the system's busy times.
    """
    if not intervals:
        return []

    # Step 1: Sort the intervals by their start times
    intervals.sort(key=lambda x: x[0])
    

    # Step 2: Initialize a list to hold consolidated intervals
    consolidated = [intervals[0]]
    # Step 3: Merge overlapping intervals
    for start, end in intervals[1:]:
        last_start, last_end = consolidated[-1]

        if start <= last_end:  # Overlapping or touching intervals
            # Merge intervals
            consolidated[-1] = (last_start, max(last_end, end))
        else:
            # Add a new interval
            consolidated.append((start, end))

    return consolidated


# Example Usage
parsed_intervals = [
    (1, 5), (10, 17), (29, 39), (37, 43),
    (5, 7), (19, 21), (3, 8), (27, 32)
]

# Consolidate and format the output
busy_times = consolidate_busy_times(parsed_intervals)
print("Consolidated busy times:")
for start, end in busy_times:
    print(f"{start}------{end}", end=" ")