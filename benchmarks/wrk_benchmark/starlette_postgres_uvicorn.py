from script import run_benchmark

# Run benchmarks

run_benchmark(
    "http://localhost:8102/delayed_route",
    "http://localhost:8103/delayed_route",
    "a non empty route which makes a simulated request to a database",
    percentage_limit=30
)

run_benchmark(
    "http://localhost:8102/just", "http://localhost:8103/just", "an empty route",
    percentage_limit=40
)
