import random
import timeit

from aikido_zen.helpers.ip_matcher import IPMatcher


def generate_random_ipv4_networks(n):
    return [f"{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}/{random.randint(8, 32)}" for _ in range(n)]

def generate_random_ipv6_networks(n):
    return [f"{random.randint(0, 65535):04x}:{random.randint(0, 65535):04x}:{random.randint(0, 65535):04x}:{random.randint(0, 65535):04x}:{random.randint(0, 65535):04x}:{random.randint(0, 65535):04x}:{random.randint(0, 65535):04x}:{random.randint(0, 65535):04x}/{random.randint(16, 128)}" for _ in range(n)]

def benchmark_build(networks):
    return timeit.timeit(lambda: IPMatcher(networks), number=1)

def benchmark_has(matcher, networks):
    def check_networks():
        for net in networks:
            matcher.has(net)
    return timeit.timeit(check_networks, number=1)

# Generate random IPv4 and IPv6 networks
ipv4_networks = generate_random_ipv4_networks(1000)
ipv6_networks = generate_random_ipv6_networks(1000)

# Benchmarking
ipv4_build_time = benchmark_build(ipv4_networks)
ipv6_build_time = benchmark_build(ipv6_networks)

ipv4_matcher = IPMatcher(ipv4_networks)
ipv6_matcher = IPMatcher(ipv6_networks)

ipv4_has_time = benchmark_has(ipv4_matcher, ipv4_networks)
ipv6_has_time = benchmark_has(ipv6_matcher, ipv6_networks)

print(f"IPv4 Build Time: {ipv4_build_time:.6f} seconds")
print(f"IPv4 Has Time: {ipv4_has_time:.6f} seconds")
print(f"IPv6 Build Time: {ipv6_build_time:.6f} seconds")
print(f"IPv6 Has Time: {ipv6_has_time:.6f} seconds")
