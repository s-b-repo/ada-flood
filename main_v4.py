import dns.resolver
import dns.query
import dns.zone
import random
import string
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import stem
import stem.connection
import stem.process
import socks
import subprocess
import time

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

# Set up an empty list of servers
        self.servers = []

    def generate_random_server(self):
        """Generate a random server name."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10)) + '.com'

    def scan(self):
        """Scan for DNS servers using the TOR network."""
        site = self.site_entry.get()
        self.results_text.delete('1.0', tk.END)

        # Use the TOR proxy as a SOCKS proxy for DNS requests
        resolver = dns.resolver.Resolver()
        resolver.socks_proxy = 'socks5h://127.0.0.1:9050'

        # Generate a random server name
        server = self.generate_random_server()

        # Look up the NS records for the server
        response = resolver.query(server, 'NS')

        # Extract the names of the DNS servers from the response
        servers = [rdata.target for rdata in response]

        # Use a DNS zone transfer to retrieve the list of DNS servers for each server
        for server in servers:
            try:
                zone = dns.zone.from_xfr(dns.query.xfr(server, '.'))
                names = list(zone.nodes.keys())
                self.results_text.insert(tk.END, f'{server}: {names}\n')
                self.servers += names  # Add the names of the servers to the list
            except dns.exception.FormError:
                self.results_text.insert(tk.END, f'{server}: zone transfer failed\n')

        # Save the list of DNS servers to a file
        with open('dns_servers.txt', 'w') as file:
            for server in self.servers:
                file.write(server + '\n')

        # Ping the site using all the DNS servers
        self.ping_site(site)

    def import_list(self):
        """Import a list of DNS servers from a file."""
        filepath = tk.filedialog.askopenfilename()
        if filepath:
            with open(filepath, 'r') as file:
                self.servers = [line.strip() for line in file]

    def export_list(self):
        """Export the list of DNS servers to a file."""
        filepath = tk.filedialog.asksaveasfilename()
        if filepath:
            with open(filepath, 'w') as file:
                for server in self.servers:
                    file.write(server + '\n')

        def ping_site(self, site):
        #Ping the site using all the DNS servers in the list.
            self.results_text.insert(tk.END, f'Pinging {site} using all DNS servers in the list...\n')
        for server in self.servers:
            # Use the TOR proxy as a SOCKS proxy for the ping request
            socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 9050)
            socks.socket = socks.socksocket

            # Use the subprocess module to run the ping command
            result = subprocess.run(['ping', '-c', '1', '-W', '2', ping_site], stdout=subprocess.PIPE)

            # Check the output of the ping command
            if '0% packet loss' in result.stdout.decode():
                self.results_text.insert(tk.END, f'{server}: success\n')
            else:
                self.results_text.insert(tk.END, f'{server}: fail\n')

    def start_random_scan(self):
        """Start a random scan for DNS servers using the TOR network."""
        # Set the stop time for the scan
        self.stop_time = time.time() + self.time_slider.get() * 3600

        # Start the scan
        self.random_scan()

    def random_scan(self):
        """Scan for random DNS servers using the TOR network."""
        if time.time() < self.stop_time:
            self.scan()
            self.remaining_time_label.configure(text=f'Remaining time: {int(self.stop_time - time.time()) // 3600} hours')
            self.window.after(1000, self.random_scan)
        else:
            self.remaining_time_label.configure(text='Scan complete')

if __name__ == '__main__':
    app = App()
    app.window.mainloop()
    
