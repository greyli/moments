import time
import unittest

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By


class UserInterfaceTestCase(unittest.TestCase):
    def setUp(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        self.browser = webdriver.Chrome(options=options)
        self.browser.maximize_window()

        if not self.browser:
            self.skipTest('Web browser not available.')
        try:
            self.browser.get('http://localhost:5000/')
        except WebDriverException:
            self.skipTest('Server not running. Run the app first with "flask --app tests/app.py run".')

        self.login()

    def tearDown(self):
        if self.browser:
            self.browser.quit()

    def login(self):
        self.browser.get('http://localhost:5000/auth/login')
        time.sleep(1)
        self.browser.find_element(By.NAME, 'email').send_keys('admin@helloflask.com')
        self.browser.find_element(By.NAME, 'password').send_keys('123')
        self.browser.find_element(By.NAME, 'submit').click()
        time.sleep(1)

    def test_login(self):
        self.assertIn('Home', self.browser.title)
        self.assertIn('Login success', self.browser.page_source)

    def test_home_page_collect_uncollect(self):
        self.browser.get('http://localhost:5000/')
        time.sleep(1)
        collect_btn = self.browser.find_element(By.CLASS_NAME, 'collect-btn')
        uncollect_btn = self.browser.find_element(By.CLASS_NAME, 'uncollect-btn')
        origin_collect_count = self.browser.find_element(By.ID, 'collectors-count-1').text
        # collect the photo
        collect_btn.click()
        time.sleep(1)
        self.assertIn('Photo collected', self.browser.page_source)
        new_collect_count = self.browser.find_element(By.ID, 'collectors-count-1').text
        self.assertEqual(int(new_collect_count), int(origin_collect_count) + 1)
        self.assertEqual(uncollect_btn.value_of_css_property('display'), 'block')
        self.assertEqual(collect_btn.value_of_css_property('display'), 'none')
        # uncollect the photo
        uncollect_btn.click()
        time.sleep(1)
        self.assertIn('Collect canceled', self.browser.page_source)
        new_collect_count = self.browser.find_element(By.ID, 'collectors-count-1').text
        self.assertEqual(int(new_collect_count), int(origin_collect_count))
        self.assertEqual(collect_btn.value_of_css_property('display'), 'block')
        self.assertEqual(uncollect_btn.value_of_css_property('display'), 'none')

    def test_photo_page_follow_unfollow(self):
        self.browser.get('http://localhost:5000/photo/1')
        time.sleep(1)
        # hover the mouse over the user avatar
        user_avatar = self.browser.find_element(By.CLASS_NAME, 'avatar-s')
        action = webdriver.ActionChains(self.browser)
        action.move_to_element(user_avatar).perform()
        time.sleep(1)
        self.assertIn('Homepage', self.browser.page_source)
        popover = self.browser.find_element(By.CLASS_NAME, 'popover')
        self.assertEqual(popover.value_of_css_property('display'), 'block')
        # test follow
        origin_follower_count = self.browser.find_element(By.ID, 'followers-count-2').text
        popover.find_element(By.XPATH, '//a[@title="Follow"]').click()
        time.sleep(1)
        self.assertEqual(popover.find_element(By.CLASS_NAME, 'follow-btn').value_of_css_property('display'), 'none')
        self.assertEqual(
            popover.find_element(By.CLASS_NAME, 'unfollow-btn').value_of_css_property('display'), 'inline-block'
        )
        self.assertIn('User followed', self.browser.page_source)
        new_follower_count = self.browser.find_element(By.ID, 'followers-count-2').text
        self.assertEqual(int(new_follower_count), int(origin_follower_count) + 1)
        # test unfollow
        origin_follower_count = new_follower_count
        popover.find_element(By.XPATH, '//a[@title="Unfollow"]').click()
        time.sleep(1)
        self.assertIn('Follow canceled', self.browser.page_source)
        self.assertEqual(popover.find_element(By.CLASS_NAME, 'unfollow-btn').value_of_css_property('display'), 'none')
        self.assertEqual(
            popover.find_element(By.CLASS_NAME, 'follow-btn').value_of_css_property('display'), 'inline-block'
        )
        new_follower_count = self.browser.find_element(By.ID, 'followers-count-2').text
        self.assertEqual(int(new_follower_count), int(origin_follower_count) - 1)

    def test_photo_page_edit_description(self):
        self.browser.get('http://localhost:5000/photo/1')
        time.sleep(1)

        edit_description_btn = self.browser.find_element(By.ID, 'description-btn')
        description_form = self.browser.find_element(By.ID, 'description-form')
        description = self.browser.find_element(By.ID, 'description')
        self.assertEqual(edit_description_btn.value_of_css_property('display'), 'inline')
        self.assertEqual(description.value_of_css_property('display'), 'block')
        self.assertEqual(description_form.value_of_css_property('display'), 'none')

        edit_description_btn.click()
        time.sleep(1)
        self.assertEqual(description.value_of_css_property('display'), 'none')
        self.assertEqual(description_form.value_of_css_property('display'), 'block')
        description_form.find_element(By.NAME, 'description').send_keys(' test description')
        description_form.find_element(By.NAME, 'submit').click()
        time.sleep(1)
        self.assertEqual(self.browser.find_element(By.ID, 'description').value_of_css_property('display'), 'block')
        self.assertEqual(self.browser.find_element(By.ID, 'description-form').value_of_css_property('display'), 'none')
        self.assertIn('test description', self.browser.page_source)

    def test_photo_page_edit_tag(self):
        self.browser.get('http://localhost:5000/photo/1')
        time.sleep(1)

        edit_tag_btn = self.browser.find_element(By.ID, 'tag-btn')
        tag_form = self.browser.find_element(By.ID, 'tag-form')
        tags = self.browser.find_element(By.ID, 'tags')
        self.assertEqual(edit_tag_btn.value_of_css_property('display'), 'inline')
        self.assertEqual(tags.value_of_css_property('display'), 'block')
        self.assertEqual(tag_form.value_of_css_property('display'), 'none')

        edit_tag_btn.click()
        time.sleep(1)
        self.assertEqual(tags.value_of_css_property('display'), 'none')
        self.assertEqual(tag_form.value_of_css_property('display'), 'block')
        tag_form.find_element(By.NAME, 'tag').send_keys('selenium')
        tag_form.find_element(By.NAME, 'submit').click()
        time.sleep(1)

        self.assertEqual(self.browser.find_element(By.ID, 'tags').value_of_css_property('display'), 'block')
        self.assertEqual(self.browser.find_element(By.ID, 'tag-form').value_of_css_property('display'), 'none')
        self.assertIn('selenium', self.browser.page_source)

        self.browser.find_element(By.ID, 'tag-btn').click()
        self.browser.find_element(By.ID, 'tag-form').find_element(By.XPATH, '//a[@title="Delete tag"]').click()
        time.sleep(1)
        self.browser.find_element(By.ID, 'delete-modal').find_element(By.CLASS_NAME, 'btn-confirm').click()
        time.sleep(1)
        self.assertNotIn('selenium', self.browser.page_source)

    def test_photo_page_share_photo(self):
        self.browser.get('http://localhost:5000/photo/1')
        time.sleep(1)

        share_modal = self.browser.find_element(By.ID, 'share-modal')
        self.assertEqual(share_modal.value_of_css_property('display'), 'none')

        # find the share button based on the title attribute
        self.browser.find_element(By.XPATH, '//a[@title="Share"]').click()
        time.sleep(1)
        self.assertEqual(share_modal.value_of_css_property('display'), 'block')

    def test_photo_page_delete_photo(self):
        self.browser.get('http://localhost:5000/photo/1')

        delete_modal = self.browser.find_element(By.ID, 'delete-modal')
        self.assertEqual(delete_modal.value_of_css_property('display'), 'none')

        # find the delete button based on the title attribute
        self.browser.find_element(By.XPATH, '//a[@title="Delete"]').click()
        time.sleep(1)
        self.assertEqual(delete_modal.value_of_css_property('display'), 'block')
