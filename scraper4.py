import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import threading
import time
import re
from collections import deque

class WebScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Scraper - Search Across Websites")
        self.root.geometry("800x600")
        
        self.visited_urls = set()
        self.urls_to_visit = deque()
        self.results = []
        self.is_scraping = False
        self.stop_scraping = False
        
        self.setup_gui()
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Search term input
        ttk.Label(main_frame, text="Search Term:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.search_entry = ttk.Entry(main_frame, width=50)
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Starting URL input
        ttk.Label(main_frame, text="Starting URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(main_frame, width=50)
        self.url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.url_entry.insert(0, "https://example.com")
        
        # Options frame
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(options_frame, text="Max Pages:").grid(row=0, column=0, sticky=tk.W)
        self.max_pages_var = tk.StringVar(value="10")
        max_pages_spin = ttk.Spinbox(options_frame, from_=1, to=100, width=10, textvariable=self.max_pages_var)
        max_pages_spin.grid(row=0, column=1, padx=(5, 20))
        
        ttk.Label(options_frame, text="Delay (seconds):").grid(row=0, column=2, sticky=tk.W)
        self.delay_var = tk.StringVar(value="1")
        delay_spin = ttk.Spinbox(options_frame, from_=0.5, to=5.0, increment=0.5, width=10, textvariable=self.delay_var)
        delay_spin.grid(row=0, column=3, padx=(5, 20))
        
        self.case_sensitive_var = tk.BooleanVar()
        case_check = ttk.Checkbutton(options_frame, text="Case Sensitive", variable=self.case_sensitive_var)
        case_check.grid(row=0, column=4)
        
        # Control buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Scraping", command=self.start_scraping)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_scraping_func, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(button_frame, text="Clear Results", command=self.clear_results)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Results area with tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Results tab
        results_frame = ttk.Frame(notebook)
        notebook.add(results_frame, text="Search Results")
        
        # Treeview for results
        columns = ("URL", "Title", "Matches")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)
        
        # Define column headings and widths
        self.results_tree.heading("URL", text="URL")
        self.results_tree.heading("Title", text="Page Title")
        self.results_tree.heading("Matches", text="Match Count")
        
        self.results_tree.column("URL", width=300)
        self.results_tree.column("Title", width=200)
        self.results_tree.column("Matches", width=100)
        
        # Scrollbar for treeview
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Log tab
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Activity Log")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready to scrape")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Bind double-click event to open URL
        self.results_tree.bind("<Double-1>", self.on_result_double_click)
        
    def log_message(self, message):
        """Add a message to the activity log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def start_scraping(self):
        """Start the web scraping process"""
        search_term = self.search_entry.get().strip()
        starting_url = self.url_entry.get().strip()
        
        if not search_term:
            messagebox.showerror("Error", "Please enter a search term")
            return
            
        if not starting_url:
            messagebox.showerror("Error", "Please enter a starting URL")
            return
            
        # Validate URL
        parsed = urlparse(starting_url)
        if not parsed.scheme:
            starting_url = "https://" + starting_url
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, starting_url)
            
        # Reset state
        self.visited_urls.clear()
        self.urls_to_visit.clear()
        self.results.clear()
        self.stop_scraping = False
        
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.log_text.delete(1.0, tk.END)
        
        # Add starting URL to queue
        self.urls_to_visit.append(starting_url)
        
        # Update UI
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_scraping = True
        
        # Start scraping in a separate thread
        scraping_thread = threading.Thread(target=self.scrape_websites, daemon=True)
        scraping_thread.start()
        
    def stop_scraping_func(self):
        """Stop the scraping process"""
        self.stop_scraping = True
        self.is_scraping = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("Scraping stopped by user")
        self.log_message("Scraping stopped by user")
        
    def clear_results(self):
        """Clear all results and logs"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.log_text.delete(1.0, tk.END)
        self.results.clear()
        self.status_var.set("Results cleared")
        
    def scrape_websites(self):
        """Main scraping function that runs in a separate thread"""
        search_term = self.search_entry.get().strip()
        max_pages = int(self.max_pages_var.get())
        delay = float(self.delay_var.get())
        case_sensitive = self.case_sensitive_var.get()
        
        pages_scraped = 0
        total_matches = 0
        
        self.log_message(f"Starting search for '{search_term}'")
        self.log_message(f"Max pages: {max_pages}, Delay: {delay}s, Case sensitive: {case_sensitive}")
        
        while self.urls_to_visit and pages_scraped < max_pages and not self.stop_scraping:
            current_url = self.urls_to_visit.popleft()
            
            if current_url in self.visited_urls:
                continue
                
            self.visited_urls.add(current_url)
            pages_scraped += 1
            
            self.status_var.set(f"Scraping: {current_url[:60]}...")
            self.log_message(f"Scraping page {pages_scraped}/{max_pages}: {current_url}")
            
            try:
                # Make request with timeout and headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(current_url, headers=headers, timeout=10, allow_redirects=True)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Get page title
                title_element = soup.find('title')
                page_title = title_element.text.strip() if title_element else "No title"
                
                # Search for term in page content
                page_text = soup.get_text()
                
                if case_sensitive:
                    matches = len(re.findall(re.escape(search_term), page_text))
                else:
                    matches = len(re.findall(re.escape(search_term), page_text, re.IGNORECASE))
                
                if matches > 0:
                    total_matches += matches
                    self.results.append({
                        'url': current_url,
                        'title': page_title,
                        'matches': matches
                    })
                    
                    # Add to results tree
                    self.root.after(0, self.add_result_to_tree, current_url, page_title, matches)
                    self.log_message(f"Found {matches} matches on: {current_url}")
                
                # Find new links on the same domain
                base_domain = urlparse(current_url).netloc
                links = soup.find_all('a', href=True)
                
                new_links_found = 0
                for link in links:
                    href = link['href']
                    absolute_url = urljoin(current_url, href)
                    
                    # Only follow links on the same domain
                    if urlparse(absolute_url).netloc == base_domain:
                        if absolute_url not in self.visited_urls and absolute_url not in self.urls_to_visit:
                            self.urls_to_visit.append(absolute_url)
                            new_links_found += 1
                            if new_links_found >= 10:  # Limit new links per page
                                break
                
                self.log_message(f"Found {new_links_found} new links to explore")
                
            except requests.exceptions.RequestException as e:
                self.log_message(f"Error scraping {current_url}: {str(e)}")
            except Exception as e:
                self.log_message(f"Unexpected error on {current_url}: {str(e)}")
            
            # Delay between requests
            if not self.stop_scraping and delay > 0:
                time.sleep(delay)
        
        # Scraping completed
        if not self.stop_scraping:
            self.root.after(0, self.scraping_completed, pages_scraped, total_matches)
        
    def add_result_to_tree(self, url, title, matches):
        """Add a result to the treeview (called from main thread)"""
        # Truncate long URLs and titles for display
        display_url = url[:50] + "..." if len(url) > 50 else url
        display_title = title[:30] + "..." if len(title) > 30 else title
        
        self.results_tree.insert("", tk.END, values=(display_url, display_title, matches))
        
    def scraping_completed(self, pages_scraped, total_matches):
        """Handle completion of scraping process"""
        self.is_scraping = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        self.status_var.set(f"Completed: {pages_scraped} pages scraped, {len(self.results)} pages with matches")
        self.log_message(f"Scraping completed!")
        self.log_message(f"Pages scraped: {pages_scraped}")
        self.log_message(f"Pages with matches: {len(self.results)}")
        self.log_message(f"Total matches found: {total_matches}")
        
    def on_result_double_click(self, event):
        """Handle double-click on result to open URL"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            # Find the full URL from results
            display_url = item['values'][0]
            for result in self.results:
                if result['url'].startswith(display_url.replace("...", "")):
                    import webbrowser
                    webbrowser.open(result['url'])
                    break

def main():
    root = tk.Tk()
    app = WebScraperGUI(root)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()