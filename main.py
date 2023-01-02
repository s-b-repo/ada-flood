import dns.resolver
import dns.query
import dns.zone
import tkinter as tk
import stem
import stem.connection
import stem.process

class App:
    def __init__(self):
        # Start a TOR process and create a controller
        self.tor_process = stem.process.launch_tor_with_config(config={'SocksPort': str(9050)})
        self.controller = stem.control.Controller.from_port()
        self.controller.authenticate()

        # Set up the GUI
        self.window = tk.Tk()
        self.window.title('DNS Scanner')
        tk.Label(self.window, text='Site:').grid(row=0, column=0)
        self.site_entry = tk.Entry(self.window)
        self.site_entry.grid(row=0, column=1)
        tk.Button(self.window, text='Scan', command=self.scan).grid(row=1, column=0, columnspan=2)
        self.results_text = tk.Text(self.window)
        self.results_text.grid(row=2, column=0, columnspan=2)

    def scan(self):
        site = self.site_entry.get()
        self.results_text.delete('1.0', tk.END)

        # Set up a resolver that uses TOR as a DNS server
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['127.0.0.1']  # Use the local TOR proxy as the DNS server
        resolver.port = 9050  # Use the SOCKS port that the TOR process is listening on

        # Use the resolver to look up the NS records for the root zone
        response = resolver.query('.', 'NS')

        # Extract the names of the DNS servers from the response
        servers = [rdata.target for rdata in response]

        # Use a DNS zone transfer to retrieve the list of DNS servers for each server
        for server in servers:
            try:
                zone = dns.zone.from_xfr(dns.query.xfr(server, '.'))
                names = list(zone.nodes.keys())
                self.results_text.insert(tk.END, f'{server}: {names}\n')
            except dns.exception.FormError:
                self.results_text.insert(tk.END, f'Unable to perform zone transfer with {server}\n')
            except dns.query.UnexpectedSource:
                self.results_text.insert(tk.END, f'Invalid response from {server}\n')

        # Use TOR to ping the site through each DNS server
        for server in servers:
            try:
                resolver.nameservers = [server]
                response = resolver.query(site)
                self.results_text.insert(tk.END, f'{site} reachable through {server}\n')
            except dns.resolver.NXDOMAIN:
                self.results_text.insert(tk.END, f'{site} does not exist\n')
            except dns.resolver.NoNameservers:
                self.results_text.insert(tk.END, f'Unable to connect to {server}\n')

        # Loop the scan every 5 seconds
        self.window.after(5000, self.scan)

    def __del__(self):
        # Close the TOR process and controller when the app is closed
        self.tor_process.kill()
        self.controller.close()

app = App()
app.window.mainloop()
