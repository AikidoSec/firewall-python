from script import run_benchmark

# Run benchmarks

run_benchmark(
    "http://localhost:8102/benchmark",
    "http://localhost:8103/benchmark",
    "a non empty route which makes a simulated request to a database",
    percentage_limit=40
)
