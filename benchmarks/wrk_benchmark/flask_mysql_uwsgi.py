from script import run_benchmark

# Run benchmarks

run_benchmark(
    "http://localhost:8088/benchmark",
    "http://localhost:8089/benchmark",
    "a non empty route which makes a simulated request to a database",
    percentage_limit=40
)


run_benchmark(
    "http://localhost:8088/benchmark_io",
    "http://localhost:8089/benchmark_io",
    "a route that makes multiple I/O calls",
    percentage_limit=35
)
