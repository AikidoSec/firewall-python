"""Exports create_interval"""


def create_interval(event_scheduler, interval_in_secs, function, args):
    """
    This function creates an interval which first runs "function"
    after waiting "interval_in_secs" seconds and after that keeps
    executing the function every "interval_in_secs" seconds.
    """
    # Sleep interval_in_secs seconds before starting the loop :
    event_scheduler.enter(
        interval_in_secs,
        1,
        interval_loop,
        (event_scheduler, interval_in_secs, function, args),
    )


def interval_loop(event_scheduler, interval_in_secs, function, args):
    """
    This is the actual interval loop which executes and schedules the function
    """
    # Execute function :
    function(*args)
    # Schedule the execution of the function in interval_in_secs seconds :
    event_scheduler.enter(
        interval_in_secs,
        1,
        interval_loop,
        (event_scheduler, interval_in_secs, function, args),
    )
