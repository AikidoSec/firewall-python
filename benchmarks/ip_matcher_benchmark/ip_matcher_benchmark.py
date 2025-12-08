import random
import timeit

from aikido_zen.helpers.ip_matcher import IPMatcher


def generate_random_ipv4_networks(n):
    return [f"{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}/{random.randint(8, 32)}" for _ in range(n)]

def generate_random_ipv6_networks(n):
    return [f"{random.randint(0, 65535):04x}:{random.randint(0, 65535):04x}:{random.randint(0, 65535):04x}:{random.randint(0, 65535):04x}:{random.randint(0, 65535):04x}:{random.randint(0, 65535):04x}:{random.randint(0, 65535):04x}:{random.randint(0, 65535):04x}/{random.randint(16, 128)}" for _ in range(n)]

def benchmark_add(networks):
    matcher = IPMatcher()
    def add_networks():
        for net in networks:
            matcher.add(net)
    return timeit.timeit(add_networks, number=1)

def benchmark_has(matcher, networks):
    def check_networks():
        for net in networks:
            matcher.has(net)
    return timeit.timeit(check_networks, number=1)

# Generate random IPv4 and IPv6 networks
ipv4_networks = generate_random_ipv4_networks(1000)
ipv6_networks = generate_random_ipv6_networks(1000)

# Benchmarking
ipv4_add_time = benchmark_add(ipv4_networks)
ipv6_add_time = benchmark_add(ipv6_networks)

ipv4_matcher = IPMatcher()
for net in ipv4_networks:
    ipv4_matcher.add(net)

ipv6_matcher = IPMatcher()
for net in ipv6_networks:
    ipv6_matcher.add(net)

ipv4_has_time = benchmark_has(ipv4_matcher, ipv4_networks)
ipv6_has_time = benchmark_has(ipv6_matcher, ipv6_networks)

print(f"IPv4 Add Time: {ipv4_add_time:.6f} seconds")
print(f"IPv4 Has Time: {ipv4_has_time:.6f} seconds")
print(f"IPv6 Add Time: {ipv6_add_time:.6f} seconds")
print(f"IPv6 Has Time: {ipv6_has_time:.6f} seconds")
