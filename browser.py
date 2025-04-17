import time
import sys
import json
import os
import platform
import pdfkit
import ssl
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import openai

class BrowserWorker:
    
    def __init__(self, headless_mode=False):
        self.headless_mode = headless_mode
        
        # Load OpenAI API key
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                openai.api_key = settings.get('openai_api_key', '')
        except FileNotFoundError:
            print("Settings file not found")
            openai.api_key = ''
        
    def get_chrome_profile_dir(self):
        """Returns Chrome profile directory based on operating system"""
        system = platform.system().lower()
        home = os.path.expanduser('~')
        
        if system == 'darwin':  # macOS
            chrome_path = os.path.join(home, 'Library', 'Application Support', 'Google', 'Chrome')
            if not os.path.exists(chrome_path):
                chrome_path = os.path.join(home, 'Library', 'Application Support', 'Chromium')
            return os.path.join(chrome_path, 'Default')
        elif system == 'linux':
            return os.path.join(home, '.config', 'google-chrome', 'Default')
        elif system == 'windows':
            return os.path.join(home, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default')
        else:
            return None

    def wait_for_element(self, driver, by, value, timeout=10, condition="presence"):
        """
        Waits for an element and returns it if found, returns False if not found
        """
        try:
            wait = WebDriverWait(driver, timeout)
            
            if condition == "presence":
                element = wait.until(EC.presence_of_element_located((by, value)))
            elif condition == "clickable":
                element = wait.until(EC.element_to_be_clickable((by, value)))
            elif condition == "visible":
                element = wait.until(EC.visibility_of_element_located((by, value)))
            else:
                return False
                
            return element
        except:
            return False

    def application(self, driver, job_url):
        job_title, job_description, company_info = self.scrape_job_posting(driver, job_url)
        if not (job_title or job_description or company_info):
            print("Job posting not found!")
            return False
        
        file_location = self.generate_application_content(job_title, job_description, company_info)
        print("Application content generated successfully.")
        self.apply_to_job(driver, file_location)
        print("Applied to job successfully.")
        
        return True
        
    def check_login(self, driver, max_attempts=5):
        """
        Checks if LinkedIn session is active
        """
        attempt = 0
        while attempt < max_attempts:
            try:
                print(f"Checking LinkedIn session... (Attempt {attempt + 1}/{max_attempts})")
                driver.get("https://www.linkedin.com")
                time.sleep(3)
                
                if "feed" in driver.current_url:
                    print("LinkedIn session active, continuing...")
                    return True
                else:
                    print("LinkedIn session not active!")
                    remaining_time = (max_attempts - attempt - 1) * 30
                    print(f"Please login to LinkedIn in Chrome. Remaining time: {remaining_time} seconds")
                    time.sleep(30)
                    attempt += 1
            except Exception as e:
                print(f"Session check error: {str(e)}")
                attempt += 1
        
        return False

    def scrape_job_posting(self, driver, job_url):
        """
        Scrapes a job posting from LinkedIn with improved handling of stale elements
        """
        try:
            print(f"Navigating to job URL: {job_url}")
            driver.get(job_url)
            time.sleep(3)  # Give the page time to fully load
            
            job_title_elem = self.wait_for_element(
                driver, 
                By.XPATH, 
                "//div[contains(@class, 'job-details-jobs-unified-top-card__job-title')]",
                timeout=15
            )
            
            if not job_title_elem:
                print("Job title element not found")
                return None, None, None
                
            job_title = job_title_elem.text
            print(f"Job title found: {job_title}")
            
            # Extract job description with immediate text capture
            job_description_elem = self.wait_for_element(
                driver, 
                By.XPATH, 
                "//div[@id='job-details']",
                timeout=15
            )
            
            if not job_description_elem:
                print("Job description element not found")
                return None, None, None
                
            job_description = job_description_elem.text
            print(f"Job description found: {len(job_description)} characters")
            
            # Get company URL safely
            try:
                company_elem = self.wait_for_element(
                    driver,
                    By.XPATH,
                    "//div[@class='job-details-jobs-unified-top-card__company-name']//a",
                    timeout=15
                )
                
                if not company_elem:
                    print("Company element not found")
                    return job_title, job_description, "No company information available"
                    
                company_url = company_elem.get_attribute("href")
                print(f"Company URL found: {company_url}")
                
                # Get company info
                company_info = self.scrape_company_page(driver, company_url)
                if not company_info:
                    print("Company information could not be retrieved")
                    company_info = "No detailed company information available"
            except Exception as e:
                print(f"Error getting company info: {str(e)}")
                company_info = "No company information available"
            
            return job_title, job_description, company_info
                
        except Exception as e:
            print(f"Error scraping job posting: {str(e)}")
            return None, None, None

    def apply_to_job(self, driver, application_file):
        """
        Applies to a job using the application file
        """
        try:
            print("Applying to job...")
            apply_button = self.wait_for_element(driver, By.XPATH, "//button[@id='jobs-apply-button-id']", timeout=15)
            if (apply_button == False or apply_button.text != "Kolay Başvuru"):
                print("Apply button not found or text is not 'Kolay Başvuru'")
                return False
            
            apply_button.click()
            time.sleep(2)  # Give the page time to update
            
            next_button = self.wait_for_element(driver, By.XPATH, "//span[@class='artdeco-button__text' and (text())='İleri']", timeout=15)
            if not next_button:
                print("Next button not found")
                return False
            
            next_button.click()
            time.sleep(2)  # Give the page time to update
            
            input_element = self.wait_for_element(driver, By.XPATH, "//input[@type='file']", timeout=15)
            if not input_element:
                print("Input element not found")
                return False
            
            input_element.send_keys(application_file)
            time.sleep(3)  # Give time for file upload to complete
            
            # Keep clicking "İleri" or "İncele" buttons until "Başvuruyu gönder" appears
            attempts = 0
            while attempts < 10:
                # Check for "İncele" button first
                incele_button = self.wait_for_element(driver, By.XPATH, "//span[@class='artdeco-button__text' and (text())='İncele']", timeout=3)
                if incele_button:
                    print("Premium user detected, clicking Incele button")
                    incele_button.click()
                    time.sleep(2)  # Give the page time to update
                    continue
                
                # Check for "İleri" button
                ileri_button = self.wait_for_element(driver, By.XPATH, "//span[@class='artdeco-button__text' and (text())='İleri']", timeout=3)
                if ileri_button:
                    print("Clicking İleri button")
                    ileri_button.click()
                    time.sleep(2)  # Give the page time to update
                    continue
                
                # Check for "Başvuruyu gönder" button
                submit_button = self.wait_for_element(driver, By.XPATH, "//span[@class='artdeco-button__text' and (text())='Başvuruyu gönder']", timeout=3)
                if submit_button:
                    print("Found Başvuruyu gönder button")
                    follow_checkbox = self.wait_for_element(driver, By.XPATH, "//label[@for='follow-company-checkbox']", timeout=3)
                    if follow_checkbox:
                        follow_checkbox.click()
                        time.sleep(1)  # Give the page time to update
                    submit_button.click()
                    time.sleep(3)  # Give time for submission to complete
                    return True
                
                attempts += 1
                time.sleep(1)  # Add a small delay between attempts
            
            print("Maximum attempts reached without finding Başvuruyu gönder button")
            return False
            
        except Exception as e:
            print(f"Error applying to job: {str(e)}")
            return False

    def scrape_company_page(self, driver, company_url):
        """
        Scrapes company information with improved error handling
        """
        original_window = driver.current_window_handle
        
        try:
            # Open in new tab instead of new window
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            
            print(f"Navigating to company URL: {company_url}")
            driver.get(company_url)
            time.sleep(2)
            # Wait for the page to load
            about_url = driver.current_url + "/about"
            
            print(f"Navigating to company about page: {about_url}")
            driver.get(about_url)
            time.sleep(3)
            
            # Try different XPATHs for company details
            possible_xpaths = [
                "//h2[@class='fmdBeHpGbHkWrcsljrxolJfRjQreGzEJhc']/ancestor::section",
                "//section[contains(@class, 'org-about-module')]",
                "//section[contains(@class, 'artdeco-card')]",
                "//div[contains(@class, 'org-page-details-module')]"
            ]
            
            company_details = None
            for xpath in possible_xpaths:
                company_details = self.wait_for_element(driver, By.XPATH, xpath, timeout=5)
                if company_details:
                    break
                    
            if not company_details:
                print("Could not find company details")
                company_info = driver.find_element(By.TAG_NAME, "body").text
                driver.close()
                driver.switch_to.window(original_window)
                return company_info[:500] + "..."  # Return at least some content from the page
            
            company_details_text = company_details.text
            
            # Close the tab and switch back
            driver.close()
            driver.switch_to.window(original_window)
            
            return company_details_text
            
        except Exception as e:
            print(f"Error scraping company page: {str(e)}")
            try:
                # Try to clean up and return to original window
                if len(driver.window_handles) > 1:
                    driver.close()
                driver.switch_to.window(original_window)
            except:
                pass
            return "Failed to retrieve company information"
    
    def generate_application_content(self, job_title, job_description, company_info):
        """
        Generates application content using OpenAI API
        """
        try:
            # Read template HTML file
            template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()

            # Prepare the prompt for OpenAI API
            prompt = f"""
            I need to apply for a job as a {job_title}.

            Here's information about the company:
            {company_info}

            Here's the job description:
            {job_description}

            Below is my application template HTML. Please follow these instructions carefully:
            1. Keep the entire <style> tag and its contents EXACTLY as they are - do not modify any CSS
            2. Keep all my existing projects in the CV - do not remove or modify them
            3. You can add new projects if they are relevant to this job
            4. Customize the content (like summary, skills, etc.) to match this specific job and company
            5. Keep the HTML structure intact
            6. Make the content realistic and professional
            7. IMPORTANT: Return ONLY the HTML content without any additional text, markdown formatting, or code block markers
            8. CRITICAL: You MUST return the COMPLETE HTML document including all sections (header, summary, experience, projects, etc.)
            9. The response MUST include the closing </html> tag
            10. Do not truncate or cut off any part of the HTML

            Template HTML:
            {template}
            """
            if not openai.api_key:
                print("OpenAI API key is not set.")
                return None

            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful CV creator assistant. You must return a complete, valid HTML document with all sections and proper closing tags. Never truncate or cut off the HTML content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4096  # Increased token limit to ensure complete response
            )
            application_content = response.choices[0].message.content.strip()

            # Clean up the response
            application_content = application_content.replace("```html", "").replace("```", "").strip()
            
            # Ensure the content starts with <!DOCTYPE html> or <html>
            if not (application_content.startswith("<!DOCTYPE html>") or application_content.startswith("<html")):
                print("Warning: Generated content may not be valid HTML")
            
            # Ensure the content ends with </html>
            if not application_content.endswith("</html>"):
                print("Warning: Generated content is incomplete - missing closing </html> tag")

            # Save the generated content to a file with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")

            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
            os.makedirs(output_dir, exist_ok=True)

            output_file = os.path.join(output_dir, f"application_{timestamp}.html")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(application_content)
                print(f"Application content saved to {output_file}")

            pdf_file = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(output_file))[0]}.pdf")
            pdfkit.from_file(output_file, pdf_file)
            return pdf_file

        except Exception as e:
            print(f"Error generating application content: {str(e)}")
            return None
          
    def get_driver(self):
        """
        Initializes and returns a Chrome driver instance
        """
        driver = None
        try:
            print("Starting Chrome...")
            
            # Get Chrome profile directory
            user_data_dir = self.get_chrome_profile_dir()
            if not user_data_dir:
                print("Unsupported operating system")
                return None
                
            print(f"Chrome profile directory: {user_data_dir}")
            
            # Disable SSL certificate verification
            ssl._create_default_https_context = ssl._create_unverified_context
            
            # Configure Chrome options
            options = uc.ChromeOptions()
            
            # Headless mode settings
            if self.headless_mode:
                options.add_argument('--headless=new')
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
                options.add_argument('--window-size=1920,1080')
                print("Starting Chrome in headless mode...")
            
            # Additional settings for Mac
            if platform.system().lower() == 'darwin':
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-software-rasterizer')
                options.add_argument('--remote-debugging-port=9222')
                options.add_argument('--disable-web-security')
                options.add_argument('--allow-running-insecure-content')
            
            # Additional settings for Linux
            elif platform.system().lower() == 'linux':
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-software-rasterizer')
            
            options.add_argument('--no-first-run')
            options.add_argument('--no-service-autorun')
            options.add_argument('--password-store=basic')
            options.add_argument('--disable-notifications')
            options.add_argument('--enable-popup-blocking=false')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-translate')
            
            # Set Chrome preferences
            prefs = {
                'profile.default_content_setting_values': {
                    'notifications': 1,
                    'popups': 1,
                    'geolocation': 1,
                    'auto_select_certificate': 1,
                    'mouselock': 1,
                    'mixed_script': 1,
                    'media_stream': 1,
                    'media_stream_mic': 1,
                    'media_stream_camera': 1,
                    'protocol_handlers': 1,
                    'ppapi_broker': 1,
                    'automatic_downloads': 1,
                    'midi_sysex': 1,
                    'push_messaging': 1,
                    'ssl_cert_decisions': 1,
                    'metro_switch_to_desktop': 1,
                    'protected_media_identifier': 1,
                    'app_banner': 1,
                    'site_engagement': 1,
                    'durable_storage': 1
                }
            }
            options.add_experimental_option('prefs', prefs)
            
            # Start Chrome driver
            try:
                print("Starting Chrome (first attempt)...")
                driver = uc.Chrome(
                    options=options,
                    user_data_dir=user_data_dir,
                    driver_executable_path=None,
                    browser_executable_path=None,
                    use_subprocess=True
                )
                print("Chrome started successfully.")
            except Exception as e:
                print(f"First Chrome start attempt failed: {str(e)}")
                try:
                    print("Starting Chrome (second attempt)...")
                    options = uc.ChromeOptions()
                    if self.headless_mode:
                        options.add_argument('--headless=new')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-gpu')
                    driver = uc.Chrome(
                        options=options,
                        user_data_dir=user_data_dir,
                        driver_executable_path=None,
                        browser_executable_path=None,
                        use_subprocess=True
                    )
                    print("Chrome started successfully on second attempt.")
                except Exception as e:
                    print(f"Chrome start error: {str(e)}")
                    return None
            
            # Wait for Chrome to be ready
            driver.implicitly_wait(10)
            driver.set_page_load_timeout(30)
            
            # Check LinkedIn session
            if not self.check_login(driver):
                print("LinkedIn session could not be opened. Please login manually and try again.")
                driver.quit()
                return None
                
            print("LinkedIn session active, driver ready.")
            return driver
            
        except Exception as e:
            print(f"General error: {str(e)}")
            if driver:
                driver.quit()
            return None