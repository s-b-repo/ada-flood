import dns.resolver
import dns.query
import dns.zone
import threading
import random
import string
import tkinter as tk
import tkinter.filedialog
import stem
import stem.control
import stem.process
import socks
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from scapy.all import IP, UDP, DNS, DNSQR, send

class App:
    def __init__(self):
        # Start a TOR process and create a controller
        self.tor_process = stem.process.launch_tor_with_config(config={'SocksPort': str(9050)})
        self.controller = stem.control.Controller.from_port()
        self.controller.authenticate()

        # Set up the GUI
        self.window = tk.Tk()
        self.window.title('DNS Scanner')
        self.window.configure(bg='#f0f0f0')
        self.window.geometry('600x400')
        self.window.resizable(False, False)
        
        tk.Label(self.window, text='Site:', font=('Arial', 12), bg='#f0f0f0').grid(row=0, column=0, padx=10, pady=10)
        self.site_entry = tk.Entry(self.window, font=('Arial', 12), bg='#ffffff')
        self.site_entry.grid(row=0, column=1, padx=10, pady=10)
        tk.Button(self.window, text='Scan', font=('Arial', 12), bg='#add8e6', command=self.scan).grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        tk.Button(self.window, text='Import', font=('Arial', 12), bg='#add8e6', command=self.import_list).grid(row=2, column=0, padx=10, pady=10)
        tk.Button(self.window, text='Export', font=('Arial', 12), bg='#add8e6', command=self.export_list).grid(row=2, column=1, padx=10, pady=10)
        tk.Button(self.window, text='Start Random Scan', font=('Arial', 12), bg='#add8e6', command=self.start_random_scan).grid(row=3, column=0, padx=10, pady=10)
        
        # Display the remaining time for the random scan
        self.remaining_time_label = tk.Label(self.window, font=('Arial', 12), bg='#f0f0f0')
        self.remaining_time_label.grid(row=3, column=1, padx=10, pady=10)

        self.results_text = tk.Text(self.window, font=('Arial', 12), bg='#ffffff')
        self.results_text.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

        # Set up the time slider
        self.time_slider = tk.Scale(self.window, from_=1, to=24, orient=tk.HORIZONTAL, font=('Arial', 12), bg='#f0f0f0')
        self.time_slider.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

        # Set up an empty list of servers and proxies
        self.servers = []
        self.proxies = []  # Add a proxy list here
        self.stop_time = None

    def generate_random_server(self):
        """Generate a random server name."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10)) + '.com'

    def scan(self):
        """Scan for DNS servers using the TOR network or proxies."""
        site = self.site_entry.get()
        self.results_text.delete('1.0', tk.END)
        self.servers = []  # Reset server list

        # Start the scan
        self.recursive_dns_scan('com.')

        # Save the list of DNS servers to a file
        self.export_list()

        # Concurrently query all DNS servers for the site information
        self.concurrent_info_gathering(site)

    def import_list(self):
        """Import a list of DNS servers or proxies from a file."""
        filepath = tk.filedialog.askopenfilename()
        if filepath:
            with open(filepath, 'r') as file:
                self.servers = [line.strip() for line in file]
                # You can also import proxies here if needed

    def export_list(self):
        """Export the list of DNS servers to a file."""
        filepath = tk.filedialog.asksaveasfilename(defaultextension=".txt")
        if filepath:
            with open(filepath, 'w') as file:
                for server in self.servers:
                    file.write(server + '\n')

    def recursive_dns_scan(self, domain):
        """Recursively scan DNS servers starting from the root."""
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['127.0.0.1']  # Use local Tor proxy

        try:
            response = resolver.resolve(domain, 'NS')
            servers = [rdata.target.to_text() for rdata in response]

            for server in servers:
                self.results_text.insert(tk.END, f'{domain}: {server}\n')
                self.servers.append(server)  # Add to the list

                # Recursively scan the lower-level domain
                sub_domain = self.generate_random_server()
                self.recursive_dns_scan(sub_domain)

        except dns.exception.DNSException as e:
            self.results_text.insert(tk.END, f'Failed to query {domain}: {e}\n')

    def concurrent_info_gathering(self, site):
        """Concurrently gather information from all DNS servers."""
        self.results_text.insert(tk.END, f'Gathering info from {site} using all DNS servers in the list...\n')

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.ping_site, site, server, proxy) for server, proxy in zip(self.servers, self.proxies)]
            for future in futures:
                result = future.result()
                self.results_text.insert(tk.END, result)

    def ping_site(self, site, server, proxy):
        """Ping the site using a specific DNS server and proxy."""
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, proxy[0], int(proxy[1]))
        socks.socket = socks.socksocket

        try:
            # Send a ping through the proxy to the DNS server using scapy
            packet = IP(dst=server) / UDP(sport=random.randint(1024, 65535)) / DNS(rd=1, qd=DNSQR(qname=site))
            send(packet, verbose=0)  # Use scapy to send the packet
            return f'{server} via {proxy}: Packet sent successfully\n'
        except Exception as e:
            return f'{server} via {proxy}: Failed to send packet - {e}\n'

    def start_random_scan(self):
        """Start a random scan for DNS servers using the TOR network or proxies."""
        self.stop_time = time.time() + self.time_slider.get() * 3600
        self.random_scan()

    def random_scan(self):
        """Scan for random DNS servers using the TOR network or proxies."""
        if time.time() < self.stop_time:
            self.scan()
            self.remaining_time_label.configure(text=f'Remaining time: {int(self.stop_time - time.time()) // 3600} hours')
            self.window.after(1000, self.random_scan)
        else:
            self.remaining_time_label.configure(text='Scan complete')

if __name__ == '__main__':
    app = App()
    app.window.mainloop()
