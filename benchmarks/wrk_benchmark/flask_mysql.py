from script import run_benchmark

# Run benchmarks

run_benchmark(
    "http://localhost:8086/create",
    "http://localhost:8087/create",
    "",
    percentage_limit=40
)
