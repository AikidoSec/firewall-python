import re
import subprocess
import sys
import time

CURRENT_ACCEPTABLE_PERCENTAGE = 55


def generate_wrk_command_for_url(url):
    # Define the command with awk included
    return "wrk -t12 -c400 -d15s " + url

def extract_requests_and_latency_tuple(output):
    if output.returncode == 0:
        # Extracting requests/sec
        requests_sec = re.search(r'Requests/sec:\s+([\d.]+)', output.stdout).group(1)
        # Extracting latency
        latency = re.search(r'Latency\s+([\d.]+)(ms|s)', output.stdout)
        latency_float = float(latency.group(1))
        if latency.group(2) == "s":
            latency_float *= 1000
        return (float(requests_sec), latency_float)
    else:
        print("Error occured running benchmark command:")
        print(output.stderr.strip())
        sys.exit(1)

def run_benchmark(route1, route2, descriptor):

    output_nofw = subprocess.run(
        generate_wrk_command_for_url(route2),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(5)
    output_fw = subprocess.run(
        generate_wrk_command_for_url(route1),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    result_nofw = extract_requests_and_latency_tuple(output_nofw)
    result_fw = extract_requests_and_latency_tuple(output_fw)


    # Check if the command was successful
    if result_nofw and result_fw:
        # Print the output, which should be the Requests/sec value
        print(f"[FIREWALL-ON] Requests/sec: {result_fw[0]} | Latency in ms: {result_fw[1]}")
        print(f"[FIREWALL-OFF] Requests/sec: {result_nofw[0]} | Latency in ms: {result_nofw[1]}")

        delta_in_ms = round(result_fw[1] - result_nofw[1], 2)
        print(f"-> Delta in ms: {delta_in_ms}ms after running load test on {descriptor}")

        delay_percentage = round(
            (result_nofw[0] - result_fw[0]) / result_nofw[0] * 100
        )
        print(
            f"-> {delay_percentage}% decrease in throughput after running load test on {descriptor} \n"
        )
        if delay_percentage > CURRENT_ACCEPTABLE_PERCENTAGE:
            sys.exit(1)

# Run benchmarks :
run_benchmark("http://localhost:8102/just", "http://localhost:8103/just", "an empty route")
run_benchmark(
    "http://localhost:8102/", 
    "http://localhost:8103/", 
    "a non empty route which makes requests to database"
)
