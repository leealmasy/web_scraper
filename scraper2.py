import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import requests
from bs4 import BeautifulSoup
import threading
import time
from urllib.parse import urljoin, urlparse
import re

class WebScraper:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Scraper - Search Any Topic (app created by Claude AI, implemeneted by Lee Almasy)")
        self.root.geometry("800x600")
        
        # Remove the old search term reference
        self.placeholder_text = "Enter your search term..."
        self.search_entry_has_placeholder = True
        
        self.setup_gui()
        self.is_scraping = False
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Web Scraper - Search Any Topic (app created by Claude AI))", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Search term input
        ttk.Label(main_frame, text="Search Term:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.search_entry = ttk.Entry(main_frame, width=50)
        self.search_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Initialize settings
        self.placeholder_text = "Enter your search term..."
        self.search_entry_has_placeholder = True
        self.max_urls = 15  # Maximum number of URLs to check (adjustable)
        
        # Add placeholder text behavior
        self.add_placeholder()
        self.search_entry.bind('<FocusIn>', self.on_search_focus_in)
        self.search_entry.bind('<FocusOut>', self.on_search_focus_out)
        self.search_entry.bind('<Return>', self.on_enter_pressed)  # Bind Enter key
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=2, sticky=tk.W)
        
        self.start_button = ttk.Button(button_frame, text="Start Scraping", 
                                      command=self.start_scraping)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Stop", 
                                     command=self.stop_scraping, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.clear_button = ttk.Button(button_frame, text="Clear", 
                                      command=self.clear_results)
        self.clear_button.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=1, column=3, sticky=(tk.W, tk.E), padx=(10, 0))
        
        # Results text area with scrollbar
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="5")
        results_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, 
                                                     width=80, height=25, font=("Consolas", 9))
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to start scraping...")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def add_placeholder(self):
        """Add placeholder text to search entry"""
        self.search_entry.insert(0, self.placeholder_text)
        self.search_entry.config(foreground='grey')
        
    def on_search_focus_in(self, event):
        """Remove placeholder text when entry gets focus"""
        if self.search_entry_has_placeholder:
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(foreground='black')
            self.search_entry_has_placeholder = False
            
    def on_search_focus_out(self, event):
        """Add placeholder text when entry loses focus and is empty"""
        if not self.search_entry.get():
            self.search_entry.insert(0, self.placeholder_text)
            self.search_entry.config(foreground='grey')
            self.search_entry_has_placeholder = True
            
    def on_enter_pressed(self, event):
        """Start scraping when Enter key is pressed in search box"""
        # Only start if not already scraping and search term is valid
        if not self.is_scraping:
            search_term = self.search_entry.get().strip()
            if search_term and search_term != self.placeholder_text and not self.search_entry_has_placeholder:
                self.start_scraping()
        return 'break'  # Prevents the default behavior
        
    def log_result(self, message):
        """Add a message to the results text area"""
        self.results_text.insert(tk.END, message + "\n")
        self.results_text.see(tk.END)
        self.root.update_idletasks()
        
    def update_status(self, message):
        """Update the status bar"""
        self.status_var.set(message)
        self.root.update_idletasks()
        
    def contains_search_term_content(self, text, search_term):
        """Check if text contains the specified search term"""
        text_lower = text.lower()
        search_term_lower = search_term.lower()
        
        # Check for exact match and related variations
        search_variations = [
            search_term_lower,
            search_term_lower.replace(' ', ''),
            search_term_lower + 's',  # plural
            search_term_lower + 'ing',  # gerund form
        ]
        
        return any(term in text_lower for term in search_variations)
        
    def scrape_website(self, url, search_term):
        """Scrape a single website for the specified search term content"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No Title"
            
            # Extract main content
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text_content = soup.get_text()
            
            # Check if content is relevant
            if self.contains_search_term_content(text_content, search_term):
                # Extract description/meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                description = meta_desc.get('content', '')[:200] + '...' if meta_desc else ''
                
                return {
                    'url': url,
                    'title': title_text,
                    'description': description,
                    'relevant': True
                }
            else:
                return {'url': url, 'relevant': False}
                
        except requests.RequestException as e:
            return {'url': url, 'error': str(e)}
        except Exception as e:
            return {'url': url, 'error': f"Parsing error: {str(e)}"}
    
    def get_search_urls(self, search_term):
        """Get URLs from multiple sources since Google blocks direct scraping"""
        search_query = search_term.replace(' ', '+')
        urls = []
        
        # Try multiple search approaches
        search_engines = [
            f"https://duckduckgo.com/html/?q={search_query}",
            f"https://www.bing.com/search?q={search_query}",
        ]
        
        self.log_result(f"Trying to fetch search results for '{search_term}'...")
        
        # Try DuckDuckGo first (more scraper-friendly)
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Try DuckDuckGo
            ddg_url = f"https://html.duckduckgo.com/html/?q={search_query}"
            response = requests.get(ddg_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract URLs from DuckDuckGo results
                for link in soup.find_all('a', class_='result__a'):
                    href = link.get('href')
                    if href and href.startswith('http') and 'duckduckgo.com' not in href:
                        urls.append(href)
                        if len(urls) >= self.max_urls:  # Use the configurable limit
                            break
            
        except Exception as e:
            self.log_result(f"DuckDuckGo search failed: {e}")
        
        # If no URLs found, use curated fallback URLs based on search term
        if not urls:
            self.log_result("Using fallback URL strategy...")
            urls = self.get_fallback_urls(search_term)
        
        # Remove duplicates and limit results (configurable)
        unique_urls = list(dict.fromkeys(urls))[:self.max_urls]
        
        if unique_urls:
            self.log_result(f"Found {len(unique_urls)} URLs to check")
        else:
            self.log_result("No URLs found - using default websites")
            unique_urls = self.get_default_websites(search_term)
        
        return unique_urls
    
    def get_fallback_urls(self, search_term):
        """Get fallback URLs based on search term categories"""
        search_lower = search_term.lower()
        
        # Technology/Programming terms
        if any(term in search_lower for term in ['python', 'javascript', 'programming', 'coding', 'llm', 'ai', 'machine learning', 'software']):
            return [
                f"https://en.wikipedia.org/wiki/{search_term.replace(' ', '_')}",
                "https://stackoverflow.com/search?q=" + search_term.replace(' ', '+'),
                "https://github.com/search?q=" + search_term.replace(' ', '+'),
                "https://docs.python.org/3/search.html?q=" + search_term.replace(' ', '+'),
                "https://developer.mozilla.org/en-US/search?q=" + search_term.replace(' ', '+'),
                "https://www.reddit.com/search/?q=" + search_term.replace(' ', '+'),
                "https://medium.com/search?q=" + search_term.replace(' ', '+'),
                "https://dev.to/search?q=" + search_term.replace(' ', '+'),
                "https://www.geeksforgeeks.org/" + search_term.replace(' ', '-'),
                "https://towardsdatascience.com/search?q=" + search_term.replace(' ', '+'),
                "https://www.kaggle.com/search?q=" + search_term.replace(' ', '+'),
                "https://arxiv.org/search/?query=" + search_term.replace(' ', '+'),
                "https://huggingface.co/search/full-text?q=" + search_term.replace(' ', '+'),
                "https://openai.com/search/?query=" + search_term.replace(' ', '+'),
                "https://www.tensorflow.org/s/results?q=" + search_term.replace(' ', '+')
            ]
            
        
        # Food/Cooking terms
        elif any(term in search_lower for term in ['recipe', 'cooking', 'food', 'apple', 'apples', 'cake', 'chicken', 'pasta']):
            return [
                f"https://en.wikipedia.org/wiki/{search_term.replace(' ', '_')}",
                "https://www.allrecipes.com/search/results/?search=" + search_term.replace(' ', '+'),
                "https://www.foodnetwork.com/search/" + search_term.replace(' ', '-'),
                "https://www.epicurious.com/search/" + search_term.replace(' ', '%20'),
                "https://www.bbcgoodfood.com/search/recipes?query=" + search_term.replace(' ', '+'),
                "https://www.delish.com/search/?q=" + search_term.replace(' ', '+'),
                "https://www.taste.com.au/search?q=" + search_term.replace(' ', '+'),
                "https://www.bonappetit.com/search?q=" + search_term.replace(' ', '+'),
                "https://www.foodandwine.com/search?q=" + search_term.replace(' ', '+'),
                "https://www.simplyrecipes.com/search?q=" + search_term.replace(' ', '+'),
                "https://www.kitchn.com/search?q=" + search_term.replace(' ', '+'),
                "https://www.seriouseats.com/search?q=" + search_term.replace(' ', '+'),
                "https://www.marthastewart.com/search?q=" + search_term.replace(' ', '+'),
                "https://www.recipetineats.com/?s=" + search_term.replace(' ', '+'),
                "https://www.tasteofhome.com/search/?q=" + search_term.replace(' ', '+')
            ]
        
        # Health/Medical terms  
        elif any(term in search_lower for term in ['health', 'medicine', 'disease', 'treatment', 'symptoms']):
            return [
                f"https://en.wikipedia.org/wiki/{search_term.replace(' ', '_')}",
                "https://www.mayoclinic.org/search/search-results?q=" + search_term.replace(' ', '+'),
                "https://www.webmd.com/search/search_results/default.aspx?query=" + search_term.replace(' ', '+'),
                "https://medlineplus.gov/search/?query=" + search_term.replace(' ', '+'),
                "https://www.healthline.com/search?q1=" + search_term.replace(' ', '+'),
                "https://www.medicalnewstoday.com/search?q=" + search_term.replace(' ', '+'),
                "https://www.health.com/search?q=" + search_term.replace(' ', '+'),
                "https://www.verywellhealth.com/search?q=" + search_term.replace(' ', '+'),
                "https://www.nhs.uk/search/?q=" + search_term.replace(' ', '+'),
                "https://www.drugs.com/search.php?searchterm=" + search_term.replace(' ', '+'),
                "https://www.everydayhealth.com/search/?q=" + search_term.replace(' ', '+'),
                "https://www.prevention.com/search/?q=" + search_term.replace(' ', '+'),
                "https://www.womenshealthmag.com/search/?q=" + search_term.replace(' ', '+'),
                "https://www.menshealth.com/search/?q=" + search_term.replace(' ', '+'),
                "https://www.healthcentral.com/search?q=" + search_term.replace(' ', '+')
            ]
        
        # General fallback
        else:
            return [
                f"https://en.wikipedia.org/wiki/{search_term.replace(' ', '_')}",
                f"https://www.britannica.com/search?query={search_term.replace(' ', '+')}",
                f"https://www.reddit.com/search/?q={search_term.replace(' ', '+')}",
                f"https://www.quora.com/search?q={search_term.replace(' ', '+')}",
                f"https://medium.com/search?q={search_term.replace(' ', '+')}",
                f"https://scholar.google.com/scholar?q={search_term.replace(' ', '+')}",
                f"https://www.youtube.com/results?search_query={search_term.replace(' ', '+')}",
                f"https://www.coursera.org/search?query={search_term.replace(' ', '%20')}",
                f"https://www.udemy.com/courses/search/?q={search_term.replace(' ', '+')}",
                f"https://www.khanacademy.org/search?page_search_query={search_term.replace(' ', '+')}",
                f"https://www.ted.com/search?q={search_term.replace(' ', '+')}",
                f"https://www.investopedia.com/search?q={search_term.replace(' ', '+')}",
                f"https://www.howstuffworks.com/search.php?terms={search_term.replace(' ', '+')}",
                f"https://www.nationalgeographic.com/search?q={search_term.replace(' ', '+')}",
                f"https://www.smithsonianmag.com/search/?q={search_term.replace(' ', '+')}"
            ]
    
    def get_default_websites(self, search_term):
        """Last resort default websites"""
        return [
            f"https://en.wikipedia.org/wiki/{search_term.replace(' ', '_')}",
            f"https://www.reddit.com/search/?q={search_term.replace(' ', '+')}",
            f"https://medium.com/search?q={search_term.replace(' ', '+')}",
        ]
        
    def scrape_websites(self):
        """Main scraping function that runs in a separate thread"""
        try:
            # Get the search term from the GUI
            search_term = self.search_entry.get().strip()
            
            # Check if it's the placeholder text or empty
            if not search_term or search_term == self.placeholder_text or self.search_entry_has_placeholder:
                self.log_result("Error: Please enter a search term")
                self.update_status("Error: No search term provided")
                return
            
            self.log_result("=" * 60)
            self.log_result(f"STARTING WEBSITE SEARCH FOR: '{search_term.upper()}'")
            self.log_result("=" * 60)
            self.log_result("")
            
            self.update_status("Finding relevant websites...")
            self.log_result("Finding relevant websites to check...")
            
            # Get URLs using multiple strategies
            urls_to_scrape = self.get_search_urls(search_term)
            
            if not urls_to_scrape:
                self.log_result("No URLs found to scrape")
                self.update_status("No search results found")
                return
            
            self.update_status(f"Found {len(urls_to_scrape)} URLs to check...")
            self.log_result(f"Found {len(urls_to_scrape)} URLs from search results")
            self.log_result(f"Checking websites for '{search_term}' content...\n")
            
            relevant_sites = []
            
            for i, url in enumerate(urls_to_scrape, 1):
                if not self.is_scraping:
                    break
                    
                self.update_status(f"Checking website {i}/{len(urls_to_scrape)}: {url[:50]}...")
                self.log_result(f"[{i}/{len(urls_to_scrape)}] Checking: {url}")
                
                result = self.scrape_website(url, search_term)
                
                if 'error' in result:
                    self.log_result(f"   ❌ Error: {result['error']}")
                elif result.get('relevant'):
                    relevant_sites.append(result)
                    self.log_result(f"   ✅ RELEVANT SITE FOUND!")
                    self.log_result(f"   Title: {result['title']}")
                    if result['description']:
                        self.log_result(f"   Description: {result['description']}")
                    self.log_result("")
                else:
                    self.log_result(f"   ➖ Not relevant to '{search_term}'")
                
                self.log_result("")
                time.sleep(2)  # Be respectful to servers - increased delay
                
            # Summary
            self.log_result("=" * 60)
            self.log_result("SCRAPING COMPLETE - SUMMARY")
            self.log_result("=" * 60)
            self.log_result(f"Search term: '{search_term}'")
            self.log_result(f"Total sites checked: {len(urls_to_scrape)}")
            self.log_result(f"Relevant sites found: {len(relevant_sites)}")
            self.log_result("")
            
            if relevant_sites:
                self.log_result(f"SITES CONTAINING '{search_term.upper()}':")
                for i, site in enumerate(relevant_sites, 1):
                    self.log_result(f"{i}. {site['title']}")
                    self.log_result(f"   URL: {site['url']}")
                    if site['description']:
                        self.log_result(f"   Description: {site['description']}")
                    self.log_result("")
            else:
                self.log_result("No relevant sites found. Try a different search term or check your internet connection.")
            
            self.update_status("Scraping completed successfully!")
            
        except Exception as e:
            self.log_result(f"Error during scraping: {str(e)}")
            self.update_status("Error occurred during scraping")
        
        finally:
            self.is_scraping = False
            self.progress.stop()
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
    
    def start_scraping(self):
        """Start the scraping process"""
        if not self.is_scraping:
            self.is_scraping = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.progress.start()
            
            # Start scraping in a separate thread to prevent GUI freezing
            scraping_thread = threading.Thread(target=self.scrape_websites, daemon=True)
            scraping_thread.start()
    
    def stop_scraping(self):
        """Stop the scraping process"""
        self.is_scraping = False
        self.progress.stop()
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.update_status("Scraping stopped by user")
        self.log_result("Scraping stopped by user.\n")
    
    def clear_results(self):
        """Clear the results text area"""
        self.results_text.delete(1.0, tk.END)
        self.update_status("Results cleared")

def main():
    # Check if required packages are available
    try:
        import requests
        import bs4
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Please install required packages:")
        print("pip install requests beautifulsoup4")
        return
    
    root = tk.Tk()
    app = WebScraper(root)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()