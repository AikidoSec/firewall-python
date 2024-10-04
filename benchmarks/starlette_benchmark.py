import subprocess
import sys

CURRENT_ACCEPTABLE_PERCENTAGE = 55


def generate_wrk_command_for_url(url):
    # Define the command with awk included
    return (
        f"wrk -t12 -c400 -d15s --latency {url} | grep 'Requests/sec' | "
        + "awk '{print $2}'"
    )

def run_benchmark(route1, route2, descriptor):
    command_for_fw = generate_wrk_command_for_url(route1)
    command_for_no_fw = generate_wrk_command_for_url(route2)

    result_no_fw = subprocess.run(
        command_for_no_fw,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    result_fw = subprocess.run(
        command_for_fw,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Check if the command was successful
    if result_fw.returncode == 0 and result_no_fw.returncode == 0:
        # Print the output, which should be the Requests/sec value
        result_fw_int = float(result_fw.stdout.strip())
        result_no_fw_int = float(result_no_fw.stdout.strip())
        print(f"Requests/sec for firewall: {result_fw_int}")
        print(f"Requests/sec for w/o firewall: {result_no_fw_int}")
        delay_percentage = round(
            (result_no_fw_int - result_fw_int) / result_no_fw_int * 100
        )
        print(
            f"-> {delay_percentage}% decrease in throughput after running load test on {descriptor}"
        )
        if delay_percentage > CURRENT_ACCEPTABLE_PERCENTAGE:
            sys.exit(1)
    else:
        print("Error running commands:")
        print(result_fw.stderr.strip())
        print(result_no_fw.stderr.strip())

# Run benchmarks :
run_benchmark("http://localhost:8102/just", "http://localhost:8103/just", "an empty route")
run_benchmark(
    "http://localhost:8102/", 
    "http://localhost:8103/", 
    "a non empty route which makes requests to database"
)
