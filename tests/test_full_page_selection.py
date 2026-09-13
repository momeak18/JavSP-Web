import functools
import http.server
import threading
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


class FullPageSelectionTest(unittest.TestCase):
    def test_real_page_selection(self):
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory='/app/javsp_web/web'))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        options = webdriver.ChromeOptions()
        for arg in ('--headless', '--no-sandbox', '--disable-dev-shm-usage'):
            options.add_argument(arg)
        browser = webdriver.Chrome(options=options)
        self.addCleanup(browser.quit)
        browser.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': '''
          const originalFetch = window.fetch;
          window.fixtureTasks = ['queued','running','succeeded','succeeded'].map((status,i)=>({id:String(i),status,name:'Test '+i,input_directory:'/video/'+i,created_at:'2026-09-13T00:00:00Z',cover_count:status==='succeeded'?1:0}));
          window.fetch = async (url,opts) => {
            if (!String(url).startsWith('/api/')) return originalFetch(url,opts);
            let data=[];
            if(opts?.method==='DELETE') window.fixtureTasks=fixtureTasks.filter(t=>url!=='/api/tasks/'+t.id);
            if(url==='/api/auth/me') data={username:'admin',role:'admin'};
            if(url==='/api/tasks') data=fixtureTasks;
            return new Response(JSON.stringify(data),{status:200,headers:{'Content-Type':'application/json'}});
          };
        '''})
        browser.get(f'http://127.0.0.1:{server.server_port}/index.html')
        WebDriverWait(browser, 10).until(lambda b: b.find_elements(By.CSS_SELECTOR, '[data-overview-select-all]'))
        browser.find_element(By.CSS_SELECTOR, '[data-overview-select-all]').click()
        self.assertEqual(len(browser.find_elements(By.CSS_SELECTOR, '.overview-cover-card.selected')), 2)
        browser.execute_script("showView('scrape')")
        browser.find_element(By.CSS_SELECTOR, '[data-task-select-visible]').click()
        self.assertEqual(len(browser.find_elements(By.CSS_SELECTOR, '[data-manual-task-select]:checked')), 4)
        browser.execute_script('renderTasks(); renderOverview();')
        self.assertEqual(len(browser.find_elements(By.CSS_SELECTOR, '[data-manual-task-select]:checked')), 4)
        browser.execute_script("window.fixtureTasks=Array.from({length:81},(_,i)=>({id:'failed-'+i,status:'failed',name:'Failed '+i,input_directory:'/video/'+i,created_at:'2026-09-13T00:00:00Z'})); loadTasks();")
        WebDriverWait(browser, 10).until(lambda b: len(b.find_elements(By.CSS_SELECTOR, '[data-manual-task-select]')) == 81)
        browser.find_element(By.CSS_SELECTOR, '[data-task-select-visible]').click()
        self.assertEqual(len(browser.find_elements(By.CSS_SELECTOR, '[data-manual-task-select]:checked')), 81)
        self.assertFalse(browser.find_element(By.CSS_SELECTOR, '[data-task-cancel-selected]').is_enabled())
        self.assertTrue(browser.find_element(By.CSS_SELECTOR, '[data-task-delete-selected]').is_enabled())
        browser.execute_script('loadTasks()')
        WebDriverWait(browser, 10).until(lambda b: len(b.find_elements(By.CSS_SELECTOR, '[data-manual-task-select]:checked')) == 81)
        browser.find_element(By.CSS_SELECTOR, '[data-task-delete-selected]').click()
        browser.find_element(By.ID, 'action-confirm-button').click()
        WebDriverWait(browser, 10).until(lambda b: len(b.find_elements(By.CSS_SELECTOR, '[data-manual-task-select]')) == 0)


if __name__ == '__main__':
    unittest.main()
