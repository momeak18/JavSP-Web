import unittest
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


class BatchSelectionTest(unittest.TestCase):
    def test_filtered_selection_and_partial_cancellation(self):
        options = webdriver.ChromeOptions()
        for argument in ('--headless', '--no-sandbox', '--disable-dev-shm-usage'):
            options.add_argument(argument)
        browser = webdriver.Chrome(options=options)
        self.addCleanup(browser.quit)
        browser.get('data:text/html,<div id="task-filter-summary"></div><div id="task-table"></div>')
        source = Path('/app/javsp_web/web/assets/app.js').read_text()
        section = source[source.index('const selectedManualTasks'):source.index('async function openTaskDetail')]
        browser.execute_script('''
            window.state = {tasks: [{id:'a',status:'queued'}, {id:'b',status:'running'}, {id:'c',status:'succeeded'}, {id:'hidden',status:'queued'}]};
            window.$ = s => document.querySelector(s);
            window.ensureTaskFilters = window.rememberLogScroll = window.rememberTaskCards = window.restoreLogScroll = () => {};
            window.filteredTasks = () => state.tasks.filter(t => t.id !== 'hidden');
            window.escapeHtml = s => s;
            window.taskCard = t => `<article data-task-card="${t.id}"><div class="task-card-tools"></div></article>`;
            window.calls = [];
            window.api = async url => { calls.push(url); if(url.includes('/b/')) throw new Error('test failure'); state.tasks.find(t => url.includes('/'+t.id+'/')).status='cancelled'; };
            window.loadTasks = async () => {};
            window.confirmAction = o => { window.batchDone=false; o.run().catch(e => window.batchError=e.message).finally(() => window.batchDone=true); };
        ''' + section + '\nrenderTasks();')
        browser.find_element(By.CSS_SELECTOR, '[data-task-select-visible]').click()
        self.assertEqual(len(browser.find_elements(By.CSS_SELECTOR, '[data-manual-task-select]:checked')), 2)
        browser.find_element(By.CSS_SELECTOR, '[data-task-cancel-selected]').click()
        WebDriverWait(browser, 10).until(lambda b: b.execute_script('return window.batchDone'))
        self.assertEqual(set(browser.execute_script('return window.calls')), {'/api/tasks/a/cancel', '/api/tasks/b/cancel'})
        self.assertEqual(len(browser.find_elements(By.CSS_SELECTOR, '[data-manual-task-select]:checked')), 1)
        self.assertIn('1 个任务取消失败', browser.execute_script('return window.batchError'))


if __name__ == '__main__':
    unittest.main()
