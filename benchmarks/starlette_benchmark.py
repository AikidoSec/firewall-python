import subprocess
import sys

CURRENT_ACCEPTABLE_PERCENTAGE = 60

def generate_wrk_command_for_url(url):
    # Define the command with awk included
    return f"wrk -t12 -c400 -d30s --latency {url} | grep 'Requests/sec' | " + "awk '{print $2}'"

# Run the command
command_for_fw = generate_wrk_command_for_url("http://localhost:8102/just")
command_for_no_fw = generate_wrk_command_for_url("http://localhost:8103/just")

result_fw = subprocess.run(command_for_fw, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
result_no_fw = subprocess.run(command_for_no_fw, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# Check if the command was successful
if result_fw.returncode == 0 and result_no_fw.returncode == 0:
    # Print the output, which should be the Requests/sec value
    result_fw_int = float(result_fw.stdout.strip())
    result_no_fw_int = float(result_no_fw.stdout.strip())
    print(f"Requests/sec for firewall: {result_fw_int}")
    print(f"Requests/sec for w/o firewall: {result_no_fw_int}")
    delay_percentage = round((result_no_fw_int-result_fw_int)/result_no_fw_int*100)
    print(f"-> {delay_percentage}% decrease in throughput after Zen installed on empty route.")
    if delay_percentage > CURRENT_ACCEPTABLE_PERCENTAGE:
      sys.exit(1)
    else:
      sys.exit(0)

else:
    print("Error running commands:")
    print(result_fw.stderr.strip())
    print(result_no_fw.stderr.strip())

