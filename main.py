from browser import BrowserWorker

browser = BrowserWorker(headless_mode=False)
driver = browser.get_driver()

if driver:
    browser.application(driver, "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4188790191&discover=recommended&discoveryOrigin=JOBS_HOME_JYMBII")
    
else:
    print("Failed to initialize driver")