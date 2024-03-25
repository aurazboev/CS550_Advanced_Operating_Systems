import matplotlib.pyplot as plt

dns_entries = []
rtt = []

with open('network-test-latency.txt', 'r') as records:
    for line in records:
        part = line.strip().split(' ')
        dns_entries.append(part[0])
        rtt.append(float(part[1]) if part[1] != '-' else None)

plt.title('Average RTT for Various DNS entries')
plt.ylabel('Average RTT (ms)')
plt.xlabel('DNS Entries')

plt.bar(dns_entries, rtt, color='red')
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()

