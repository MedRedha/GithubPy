"""OS Modules environ method to get the setup vars from the Environment"""
# import built-in & third-party modules
import time
from math import ceil
import random
# from sys import platform
# from platform import python_version
import os
# import csv
# import json
# import requests
# from selenium import webdriver
# from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains

from pyvirtualdisplay import Display
import logging
from contextlib import contextmanager
# from copy import deepcopy
import unicodedata
from sys import exit as clean_exit
from tempfile import gettempdir

# import GithubPy modules
# from socialcommons.clarifai_util import check_image
from .login_util import login_user
# from .settings import Settings
from socialcommons.print_log_writer import log_follower_num
from socialcommons.print_log_writer import log_following_num

from socialcommons.time_util import sleep
# from socialcommons.time_util import set_sleep_percentage
# from socialcommons.util import get_active_users
from socialcommons.util import validate_userid
from socialcommons.util import web_address_navigator
from socialcommons.util import interruption_handler
from socialcommons.util import highlight_print
# from socialcommons.util import dump_record_activity
from socialcommons.util import truncate_float
from socialcommons.util import save_account_progress
from socialcommons.util import parse_cli_args
from .unfollow_util  import get_given_user_followers
from .unfollow_util  import get_given_user_following
# from .unfollow_util  import unfollow
from .unfollow_util  import unfollow_user
from .unfollow_util  import follow_user
from .unfollow_util  import follow_restriction
from .unfollow_util  import dump_follow_restriction
# from .unfollow_util  import set_automated_followed_pool
# from .unfollow_util  import get_follow_requests
# from .relationship_tools import get_following
# from .relationship_tools import get_followers
# from .relationship_tools import get_unfollowers
# from .relationship_tools import get_nonfollowers
# from .relationship_tools import get_fans
# from .relationship_tools import get_mutual_following
from socialcommons.database_engine import get_database
# from socialcommons.text_analytics import text_analysis
# from socialcommons.text_analytics import yandex_supported_languages
from socialcommons.browser import set_selenium_local_session
from socialcommons.browser import close_browser
from socialcommons.file_manager import get_workspace
from socialcommons.file_manager import get_logfolder

# import exceptions
from selenium.common.exceptions import NoSuchElementException
from socialcommons.exceptions import SocialPyError
from .settings import Settings

ROW_HEIGHT = 105#TODO: ROW_HEIGHT is actuallly variable in gihub so added buffer 5 to delay the failure.
ROWS_PER_PAGE = 50

class GithubPy:
    """Class to be instantiated to use the script"""
    def __init__(self,
                 username=None,
                 userid=None,
                 password=None,
                 nogui=False,
                 selenium_local_session=True,
                 use_firefox=False,
                 browser_profile_path=None,
                 page_delay=25,
                 show_logs=True,
                 headless_browser=False,
                 proxy_address=None,
                 proxy_chrome_extension=None,
                 proxy_port=None,
                 disable_image_load=False,
                 bypass_suspicious_attempt=False,
                 bypass_with_mobile=False,
                 multi_logs=True):

        cli_args = parse_cli_args()
        username = cli_args.username or username
        userid = cli_args.userid or userid
        password = cli_args.password or password
        use_firefox = cli_args.use_firefox or use_firefox
        page_delay = cli_args.page_delay or page_delay
        headless_browser = cli_args.headless_browser or headless_browser
        proxy_address = cli_args.proxy_address or proxy_address
        proxy_port = cli_args.proxy_port or proxy_port
        disable_image_load = cli_args.disable_image_load or disable_image_load
        bypass_suspicious_attempt = (
            cli_args.bypass_suspicious_attempt or bypass_suspicious_attempt)
        bypass_with_mobile = cli_args.bypass_with_mobile or bypass_with_mobile

        if not get_workspace(Settings):
            raise SocialPyError(
                "Oh no! I don't have a workspace to work at :'(")

        self.nogui = nogui
        if nogui:
            self.display = Display(visible=0, size=(800, 600))
            self.display.start()

        self.browser = None
        self.headless_browser = headless_browser
        self.proxy_address = proxy_address
        self.proxy_port = proxy_port
        self.proxy_chrome_extension = proxy_chrome_extension
        self.selenium_local_session = selenium_local_session
        self.bypass_suspicious_attempt = bypass_suspicious_attempt
        self.bypass_with_mobile = bypass_with_mobile
        self.disable_image_load = disable_image_load

        self.username = username or os.environ.get('GITHUB_USER')
        self.password = password or os.environ.get('GITHUB_PW')

        self.userid = userid
        if not self.userid:
            self.userid = self.username.split('@')[0]

        Settings.profile["name"] = self.username

        self.page_delay = page_delay
        self.switch_language = True
        self.use_firefox = use_firefox
        Settings.use_firefox = self.use_firefox
        self.browser_profile_path = browser_profile_path

        self.do_comment = False
        self.comment_percentage = 0
        self.comments = ['Cool!', 'Nice!', 'Looks good!']
        self.photo_comments = []
        self.video_comments = []

        self.do_reply_to_comments = False
        self.reply_to_comments_percent = 0
        self.comment_replies = []
        self.photo_comment_replies = []
        self.video_comment_replies = []

        self.liked_img = 0
        self.already_liked = 0
        self.liked_comments = 0
        self.commented = 0
        self.replied_to_comments = 0
        self.followed = 0
        self.already_followed = 0
        self.unfollowed = 0
        self.followed_by = 0
        self.following_num = 0
        self.inap_img = 0
        self.not_valid_users = 0
        self.video_played = 0
        self.already_Visited = 0

        self.follow_times = 1
        self.do_follow = False
        self.follow_percentage = 0
        self.dont_include = set()
        self.white_list = set()
        self.blacklist = {'enabled': 'True', 'campaign': ''}
        self.automatedFollowedPool = {"all": [], "eligible": []}
        self.do_like = False
        self.like_percentage = 0
        self.smart_hashtags = []

        self.dont_like = ['sex', 'nsfw']
        self.mandatory_words = []
        self.ignore_if_contains = []
        self.ignore_users = []

        self.user_interact_amount = 0
        self.user_interact_media = None
        self.user_interact_percentage = 0
        self.user_interact_random = False
        self.dont_follow_inap_post = True

        self.use_clarifai = False
        self.clarifai_api_key = None
        self.clarifai_models = []
        self.clarifai_workflow = []
        self.clarifai_probability = 0.50
        self.clarifai_img_tags = []
        self.clarifai_img_tags_skip = []
        self.clarifai_full_match = False
        self.clarifai_check_video = False
        self.clarifai_proxy = None

        self.potency_ratio = None   # 1.3466
        self.delimit_by_numbers = None

        self.max_followers = None   # 90000
        self.max_following = None   # 66834
        self.min_followers = None   # 35
        self.min_following = None   # 27

        self.delimit_liking = False
        self.liking_approved = True
        self.max_likes = 1000
        self.min_likes = 0

        self.delimit_commenting = False
        self.commenting_approved = True
        self.max_comments = 35
        self.min_comments = 0
        self.comments_mandatory_words = []
        self.max_posts = None
        self.min_posts = None
        self.skip_business_categories = []
        self.dont_skip_business_categories = []
        self.skip_business = False
        self.skip_no_profile_pic = False
        self.skip_private = True
        self.skip_business_percentage = 100
        self.skip_no_profile_pic_percentage = 100
        self.skip_private_percentage = 100

        self.relationship_data = {
            username: {"all_following": [], "all_followers": []}}

        self.simulation = {"enabled": True, "percentage": 100}

        self.mandatory_language = False
        self.mandatory_character = []
        self.check_letters = {}

        # use this variable to terminate the nested loops after quotient
        # reaches
        self.quotient_breach = False
        # hold the consecutive jumps and set max of it used with QS to break
        # loops
        self.jumps = {"consequent": {"likes": 0, "comments": 0, "follows": 0,
                                     "unfollows": 0},
                      "limit": {"likes": 7, "comments": 3, "follows": 5,
                                "unfollows": 4}}

        # stores the features' name which are being used by other features
        self.internal_usage = {}

        if (
                self.proxy_address and self.proxy_port > 0) or \
                self.proxy_chrome_extension:
            Settings.connection_type = "proxy"

        self.aborting = False
        self.start_time = time.time()

        # assign logger
        self.show_logs = show_logs
        Settings.show_logs = show_logs or None
        self.multi_logs = multi_logs
        self.logfolder = get_logfolder(self.username, self.multi_logs, Settings)
        self.logger = self.get_githubpy_logger(self.show_logs)

        get_database(Settings, make=True)  # IMPORTANT: think twice before relocating

        if self.selenium_local_session is True:
            self.set_selenium_local_session(Settings)

    def get_githubpy_logger(self, show_logs):
        """
        Handles the creation and retrieval of loggers to avoid
        re-instantiation.
        """

        existing_logger = Settings.loggers.get(self.username)
        if existing_logger is not None:
            return existing_logger
        else:
            # initialize and setup logging system for the GithubPy object
            logger = logging.getLogger(self.username)
            logger.setLevel(logging.DEBUG)
            file_handler = logging.FileHandler(
                '{}general.log'.format(self.logfolder))
            file_handler.setLevel(logging.DEBUG)
            extra = {"username": self.username}
            logger_formatter = logging.Formatter(
                '%(levelname)s [%(asctime)s] [%(username)s]  %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(logger_formatter)
            logger.addHandler(file_handler)

            if show_logs is True:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.DEBUG)
                console_handler.setFormatter(logger_formatter)
                logger.addHandler(console_handler)

            logger = logging.LoggerAdapter(logger, extra)

            Settings.loggers[self.username] = logger
            Settings.logger = logger
            return logger

    def set_selenium_local_session(self, Settings):
        self.browser, err_msg = \
            set_selenium_local_session(self.proxy_address,
                                       self.proxy_port,
                                       self.proxy_chrome_extension,
                                       self.headless_browser,
                                       self.use_firefox,
                                       self.browser_profile_path,
                                       # Replaces
                                       # browser User
                                       # Agent from
                                       # "HeadlessChrome".
                                       self.disable_image_load,
                                       self.page_delay,
                                       self.logger,
                                       Settings)
        if len(err_msg) > 0:
            raise SocialPyError(err_msg)

    def login(self):
        """Used to login the user either with the username and password"""
        if not login_user(self.browser,
                          self.username,
                          self.userid,
                          self.password,
                          self.logger,
                          self.logfolder,
                          self.switch_language,
                          self.bypass_suspicious_attempt,
                          self.bypass_with_mobile):
            message = "Wrong login data!"
            highlight_print(Settings, self.username,
                            message,
                            "login",
                            "critical",
                            self.logger)

            self.aborting = True

        else:
            message = "Logged in successfully!"
            highlight_print(Settings, self.username,
                            message,
                            "login",
                            "info",
                            self.logger)
            # try to save account progress
            try:
                save_account_progress(self.browser,
                                    "https://www.github.com/",
                                    self.username,
                                    self.logger)
            except Exception:
                self.logger.warning(
                    'Unable to save account progress, skipping data update')

        self.followed_by = log_follower_num(self.browser,
                                            Settings,
                                            "https://www.github.com/",
                                            self.username,
                                            self.userid,
                                            self.logfolder)

        self.following_num = log_following_num(self.browser,
                                            Settings,
                                            "https://www.github.com/",
                                            self.username,
                                            self.userid,
                                            self.logfolder)

        return self

    def set_do_follow(self, enabled=False, percentage=0, times=1):
        """Defines if the user of the liked image should be followed"""
        if self.aborting:
            return self

        self.follow_times = times
        self.do_follow = enabled
        self.follow_percentage = percentage

        return self

    def set_dont_include(self, friends=None):
        """Defines which accounts should not be unfollowed"""
        if self.aborting:
            return self

        self.dont_include = set(friends) or set()
        self.white_list = set(friends) or set()

        return self

    def move_to_next_page(self, pageno, skip=False, sleep_delay=6):
        delay_random = random.randint(
            ceil(sleep_delay * 0.85),
            ceil(sleep_delay * 1.14))

        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        page_links = self.browser.find_elements_by_css_selector("div > div > div.position-relative > div.paginate-container > div > a")
        next_link = page_links[-1]
        if next_link.text.strip()=='Next':
            (ActionChains(self.browser)
             .move_to_element(next_link)
             .click()
             .perform())
            sleep(delay_random)
            if skip:
                self.logger.info('Skipped {} users'.format(ROWS_PER_PAGE+pageno*ROWS_PER_PAGE))
            else:
                self.logger.info('Moved to page {}'.format(pageno))
            sleep(delay_random)
            return True
        else:
            self.logger.info(next_link.text)
            return False

    def unfollow_users(self, amount, skip=100, sleep_delay=6):
        web_address_navigator(self.browser, "https://github.com/{}?tab=following".format(self.username), Settings)
        start_pageno = int(skip/ROWS_PER_PAGE) + 1

        delay_random = random.randint(
            ceil(sleep_delay * 0.85),
            ceil(sleep_delay * 1.14))
        unfollowed = 0
        failed = 0
        pageno = 1

        for i in range(0, start_pageno-1):
            if self.move_to_next_page(pageno=i, skip=True, sleep_delay=sleep_delay):
                pageno += 1

        if pageno != start_pageno:
            self.logger.info("Currentpage = {}, Couldnt move to desired page {}..Returning".format(pageno, start_pageno))
            return

        self.logger.info('Unfollowing {} users'.format(amount))

        while pageno <= start_pageno + amount/ROWS_PER_PAGE:
            self.logger.info('Browsing page {}'.format(pageno))
            unfollow_buttons = self.browser.find_elements_by_css_selector("div > div > div.position-relative > div > div > span > span.unfollow > form > input.btn")
            for i, unfollow_button in enumerate(unfollow_buttons):
                try:
                    self.browser.execute_script("window.scrollTo(0, " + str(ROW_HEIGHT*i) + ");")
                    if pageno == start_pageno and ROWS_PER_PAGE*(start_pageno-1) + i + 1 <= skip:
                        self.logger.info('Skipped {} users'.format(ROWS_PER_PAGE*(start_pageno-1) + i + 1))
                        continue
                    if unfollow_button.get_attribute('value').strip()=='Unfollow':
                        (ActionChains(self.browser)
                         .move_to_element(unfollow_button)
                         .click()
                         .perform())
                        sleep(delay_random)
                        unfollowed += 1
                        self.logger.info('Unfollowed {} successfully'.format(unfollowed))
                        sleep(delay_random)
                    else:
                        self.logger.info(unfollow_button.get_attribute('value'))
                    if unfollowed >= amount:
                        self.logger.warning('Too many unfollowed for today.. Returning')
                        return
                    if failed >= 6:
                        self.logger.warning('Too many failures.. Returning')
                        return
                except Exception as e:
                    failed +=1
                    self.logger.error(e)
            pageno += 1
            if self.move_to_next_page(pageno=pageno, sleep_delay=sleep_delay)==False:
                break

    def cancel_invites(self, dest_organisation, sleep_delay=6):
        web_address_navigator(self.browser, "https://github.com/orgs/{}/people".format(dest_organisation), Settings)
        delay_random = random.randint(
            ceil(sleep_delay * 0.85),
            ceil(sleep_delay * 1.14))
        try:
            pending_tag = self.browser.find_element_by_css_selector("#org-members-table > div.d-flex.flex-items-center.px-3.table-list-header.table-list-header-next.bulk-actions-header.js-sticky > div.table-list-header-toggle.d-flex.py-1 > details.details-reset.details-overlay.details-overlay-dark.lh-default.text-gray-dark.flex-self-center > summary")
            print(pending_tag.text)
            pending_tag.click()
            sleep(delay_random)
            invitees_tags = self.browser.find_elements_by_css_selector("#org-members-table > div.d-flex.flex-items-center.px-3.table-list-header.table-list-header-next.bulk-actions-header.js-sticky > div.table-list-header-toggle.d-flex.py-1 > details.details-reset.details-overlay.details-overlay-dark.lh-default.text-gray-dark.flex-self-center > details-dialog > div.Box-body.overflow-auto > ul > li > div > a.btn.btn-sm.edit-invitation")
            print(len(invitees_tags))
            users = []
            for invitees_tag in invitees_tags:
                user = invitees_tag.get_attribute('href').split('/')[6]
                users.append(user)
            re_loggedin = False
            uninvited = 0
            for user in users:
                self.logger.info("Checking {}".format(user))
                re_loggedin, is_uninvited = self.uninvite_user(re_loggedin=re_loggedin, dest_organisation=dest_organisation, user=user, sleep_delay=sleep_delay)
                if is_uninvited:
                    uninvited += 1
                self.logger.info('Invitations cancelled in this iteration till now: {}'.format(uninvited))
                self.logger.info("=====")
                if uninvited >= 100:
                    self.logger.info('Enough cancelling for today.. Returning')
                    break
            return uninvited
        except Exception as e:
            print(e)

    def search_and_copy_contributors(self, search_query, dest_organisation, sleep_delay=6):
        search_query = '+'.join(search_query.split())
        web_address_navigator(self.browser, "https://github.com/search?l=Python&q={}&type=Repositories".format(search_query), Settings)
        repo_tags = self.browser.find_elements_by_css_selector("div > div.codesearch-results > div > ul > li > div > h3 > a")
        hrefs = []
        for repo_tag in repo_tags:
            hrefs.append(repo_tag.get_attribute('href'))

        total_count = 0
        for href in hrefs:
            print("Copying contributors of ~------> {}".format(href))
            count = self.copy_contributors(source_user=href.split('/')[3],
                    source_repo=href.split('/')[4],
                    dest_organisation=dest_organisation,
                    sleep_delay=sleep_delay)
            total_count += count
        return total_count

    def uninvite_user(self, re_loggedin, dest_organisation, user, sleep_delay):
        web_address_navigator(self.browser, "https://github.com/orgs/{}/invitations/{}/edit".format(dest_organisation, user), Settings)
        delay_random = random.randint(
            ceil(sleep_delay * 0.85),
            ceil(sleep_delay * 1.14))
        try:
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            cancel_button = self.browser.find_element_by_css_selector("form#cancel-invitation-form > button")
            if cancel_button.text.strip()=='Cancel invitation':
                (ActionChains(self.browser)
                 .move_to_element(cancel_button)
                 .click()
                 .perform())
                sleep(delay_random)
                if self.browser.current_url=='https://github.com/orgs/socialbotspy/people':
                    self.logger.info('Invitation successfully cancelled')
                    return re_loggedin, True
            else:
                self.logger.info(cancel_button.text)
        except Exception as e:
            self.logger.error(e)
            if re_loggedin:
                return re_loggedin, False
            self.logger.info("Checking for password")
            try:
                input_password = self.browser.find_element_by_xpath('//*[@id="sudo_password"]')
                if input_password:
                    self.logger.info("Password field found")
                    self.logger.info('entering input_password')
                    (ActionChains(self.browser)
                     .move_to_element(input_password)
                     .click()
                     .send_keys(self.password)
                     .perform())

                    sleep(delay_random*0.3)

                    self.logger.info('submitting login_button')
                    login_button = self.browser.find_element_by_xpath('//*[@type="submit"]')

                    (ActionChains(self.browser)
                     .move_to_element(login_button)
                     .click()
                     .perform())

                    sleep(delay_random)
                    re_loggedin = True
            except Exception as e:
                self.logger.error(e)
            #if password screen doesnt happen on first iteration it wont come, so lets make it true going forward
            re_loggedin = True
        return re_loggedin, False

    def invite_user(self, re_loggedin, dest_organisation, user, sleep_delay):
        web_address_navigator(self.browser, "https://github.com/orgs/{}/invitations/{}/edit".format(dest_organisation, user), Settings)
        delay_random = random.randint(
            ceil(sleep_delay * 0.85),
            ceil(sleep_delay * 1.14))
        try:
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            invite_button = self.browser.find_element_by_css_selector("div.add-member-wrapper.settings-next > form > div >  div > button")
            if invite_button.text.strip()=='Send invitation':
                (ActionChains(self.browser)
                 .move_to_element(invite_button)
                 .click()
                 .perform())
                sleep(delay_random)
                if self.browser.current_url=='https://github.com/orgs/socialbotspy/people':
                    self.logger.info('Invitation successfully sent')
                    return re_loggedin, True
            elif invite_button.text.strip()=='Update invitation':
                self.logger.info('Already Invited')
            else:
                self.logger.info(invite_button.text)
        except Exception as e:
            self.logger.error(e)
            if re_loggedin:
                return re_loggedin, False
            self.logger.info("Checking for password")
            try:
                input_password = self.browser.find_element_by_xpath('//*[@id="sudo_password"]')
                if input_password:
                    self.logger.info("Password field found")
                    self.logger.info('entering input_password')
                    (ActionChains(self.browser)
                     .move_to_element(input_password)
                     .click()
                     .send_keys(self.password)
                     .perform())

                    sleep(delay_random*0.3)

                    self.logger.info('submitting login_button')
                    login_button = self.browser.find_element_by_xpath('//*[@type="submit"]')

                    (ActionChains(self.browser)
                     .move_to_element(login_button)
                     .click()
                     .perform())

                    sleep(delay_random)
                    re_loggedin = True
            except Exception as e:
                self.logger.error(e)
            #if password screen doesnt happen on first iteration it wont come, so lets make it true going forward
            re_loggedin = True
        return re_loggedin, False

    def copy_contributors(self, source_user, source_repo, dest_organisation, sleep_delay=6):
        web_address_navigator(self.browser, "https://github.com/{}/{}/graphs/contributors".format(source_user, source_repo), Settings)
        contributors_tag = self.browser.find_elements_by_css_selector("#contributors > ol > li > span > h3 > a.text-normal")
        users = []
        for contributor_tag in contributors_tag:
            user = contributor_tag.get_attribute('href').split('/')[3]
            self.logger.info("Collected => {}".format(user))
            users.append(user)

        re_loggedin = False
        invited = 0
        for user in users:
            self.logger.info("Checking {}".format(user))
            re_loggedin, is_invited = self.invite_user(re_loggedin=re_loggedin, dest_organisation=dest_organisation, user=user, sleep_delay=sleep_delay)
            if is_invited:
                invited += 1
            self.logger.info('Invitations sent in this iteration till now: {}'.format(invited))
            self.logger.info("=====")
            if invited >= 100:
                self.logger.info('Enough inviting for today.. Returning')
                break
        return invited

    def follow_by_list(self, followlist, times=1, sleep_delay=600, interact=False):
        """Allows to follow by any scrapped list"""
        if not isinstance(followlist, list):
            followlist = [followlist]

        if self.aborting:
            self.logger.info(">>> self aborting prevented")
            # return self

        # standalone means this feature is started by the user
        standalone = True if "follow_by_list" not in \
                             self.internal_usage.keys() else False
        # skip validation in case of it is already accomplished
        users_validated = True if not standalone and not \
            self.internal_usage["follow_by_list"]["validate"] else False

        self.follow_times = times or 0

        followed_all = 0
        followed_new = 0
        already_followed = 0
        not_valid_users = 0

        # hold the current global values for differentiating at the end
        liked_init = self.liked_img
        already_liked_init = self.already_liked
        commented_init = self.commented
        inap_img_init = self.inap_img

        relax_point = random.randint(7,
                                     14)  # you can use some plain value
        # `10` instead of this quitely randomized score
        self.quotient_breach = False

        for acc_to_follow in followlist:
            if self.jumps["consequent"]["follows"] >= self.jumps["limit"][
                    "follows"]:
                self.logger.warning(
                    "--> Follow quotient reached its peak!\t~leaving "
                    "Follow-By-Tags activity\n")
                # reset jump counter before breaking the loop
                self.jumps["consequent"]["follows"] = 0
                # turn on `quotient_breach` to break the internal iterators
                # of the caller
                self.quotient_breach = True if not standalone else False
                break

            if follow_restriction("read", acc_to_follow, self.follow_times,
                                  self.logger):
                print('')
                continue

            if not users_validated:
                # Verify if the user should be followed
                validation, details = self.validate_user_call(acc_to_follow)
                if validation is not True or acc_to_follow == self.username:
                    self.logger.info(
                        "--> Not a valid user: {}".format(details))
                    not_valid_users += 1
                    continue

            # Take a break after a good following
            if followed_new >= relax_point:
                delay_random = random.randint(
                    ceil(sleep_delay * 0.85),
                    ceil(sleep_delay * 1.14))
                sleep_time = ("{} seconds".format(delay_random) if
                              delay_random < 60 else
                              "{} minutes".format(truncate_float(
                                  delay_random / 60, 2)))
                self.logger.info("Followed {} new users  ~sleeping about {}\n"
                                 .format(followed_new, sleep_time))
                sleep(delay_random)
                followed_new = 0
                relax_point = random.randint(7, 14)
                pass

            if not follow_restriction("read", acc_to_follow, self.follow_times,
                                      self.logger):
                follow_state, msg = follow_user(self.browser,
                                                "profile",
                                                self.username,
                                                acc_to_follow,
                                                None,
                                                self.blacklist,
                                                self.logger,
                                                self.logfolder, Settings)
                sleep(random.randint(1, 3))

                if follow_state is True:
                    followed_all += 1
                    followed_new += 1
                    # reset jump counter after a successful follow
                    self.jumps["consequent"]["follows"] = 0

                    if standalone:  # print only for external usage (
                        # internal callers have their printers)
                        self.logger.info(
                            "Total Follow: {}\n".format(str(followed_all)))

                    # Check if interaction is expected
                    if interact and self.do_like:
                        do_interact = random.randint(0,
                                                     100) <= \
                            self.user_interact_percentage
                        # Do interactions if any
                        if do_interact and self.user_interact_amount > 0:
                            original_do_follow = self.do_follow  # store the
                            # original value of `self.do_follow`
                            self.do_follow = False  # disable following
                            # temporarily cos the user is already followed
                            # above
                            self.interact_by_users(acc_to_follow,
                                                   self.user_interact_amount,
                                                   self.user_interact_random,
                                                   self.user_interact_media)
                            self.do_follow = original_do_follow  # revert
                            # back original `self.do_follow` value (either
                            # it was `False` or `True`)

                elif msg == "already followed":
                    already_followed += 1

                elif msg == "jumped":
                    # will break the loop after certain consecutive jumps
                    self.jumps["consequent"]["follows"] += 1

                sleep(1)

        if standalone:  # print only for external usage (internal callers
            # have their printers)
            self.logger.info("Finished following by List!\n")
            # print summary
            self.logger.info("Followed: {}".format(followed_all))
            self.logger.info("Already followed: {}".format(already_followed))
            self.logger.info("Not valid users: {}".format(not_valid_users))

            if interact is True:
                print('')
                # find the feature-wide action sizes by taking a difference
                liked = (self.liked_img - liked_init)
                already_liked = (self.already_liked - already_liked_init)
                commented = (self.commented - commented_init)
                inap_img = (self.inap_img - inap_img_init)

                # print the summary out of interactions
                self.logger.info("Liked: {}".format(liked))
                self.logger.info("Already Liked: {}".format(already_liked))
                self.logger.info("Commented: {}".format(commented))
                self.logger.info("Inappropriate: {}".format(inap_img))

        # always sum up general objects regardless of the request size
        self.followed += followed_all
        self.already_followed += already_followed
        self.not_valid_users += not_valid_users

        return followed_all

    def validate_user_call(self, user_name):
        """ Short call of validate_userid() function """
        validation, details = \
            validate_userid(self.browser,
                            "https://github.com/",
                            user_name,
                            self.username,
                            self.userid,
                            self.ignore_users,
                            self.blacklist,
                            self.potency_ratio,
                            self.delimit_by_numbers,
                            self.max_followers,
                            self.max_following,
                            self.min_followers,
                            self.min_following,
                            self.min_posts,
                            self.max_posts,
                            self.skip_private,
                            self.skip_private_percentage,
                            self.skip_no_profile_pic,
                            self.skip_no_profile_pic_percentage,
                            self.skip_business,
                            self.skip_business_percentage,
                            self.skip_business_categories,
                            self.dont_skip_business_categories,
                            self.logger,
                            self.logfolder, Settings)
        return validation, details

    def fetch_smart_comments(self, is_video, temp_comments):
        if temp_comments:
            # Use clarifai related comments only!
            comments = temp_comments
        elif is_video:
            comments = (self.comments +
                        self.video_comments)
        else:
            comments = (self.comments +
                        self.photo_comments)

        return comments

    def interact_by_users(self, usernames, amount=10, randomize=False, media=None):
        """Likes some amounts of images for each usernames"""
        if self.aborting:
            return self

        message = "Starting to interact by users.."
        highlight_print(Settings, self.username, message, "feature", "info", self.logger)

        if not isinstance(usernames, list):
            usernames = [usernames]

        # standalone means this feature is started by the user
        standalone = True if "interact_by_users" not in \
                             self.internal_usage.keys() else False
        # skip validation in case of it is already accomplished
        users_validated = True if not standalone and not \
            self.internal_usage["interact_by_users"]["validate"] else False

        total_liked_img = 0
        already_liked = 0
        inap_img = 0
        commented = 0
        followed = 0
        already_followed = 0
        not_valid_users = 0

        self.quotient_breach = False

        for index, username in enumerate(usernames):
            if self.quotient_breach:
                # keep `quotient_breach` active to break the internal
                # iterators of the caller
                self.quotient_breach = True if not standalone else False
                break

            self.logger.info(
                'Username [{}/{}]'.format(index + 1, len(usernames)))
            self.logger.info('--> {}'.format(username.encode('utf-8')))

            if not users_validated:
                validation, details = self.validate_user_call(username)
                if not validation:
                    self.logger.info(
                        "--> not a valid user: {}".format(details))
                    not_valid_users += 1
                    continue

            track = 'profile'
            # decision making
            # static conditions
            not_dont_include = username not in self.dont_include
            follow_restricted = follow_restriction("read", username,
                                                   self.follow_times,
                                                   self.logger)
            counter = 0
            while True:
                following = (random.randint(0,
                                            100) <= self.follow_percentage and
                             self.do_follow and
                             not_dont_include and
                             not follow_restricted)
                commenting = (random.randint(0,
                                             100) <= self.comment_percentage
                              and
                              self.do_comment and
                              not_dont_include)
                liking = (random.randint(0, 100) <= self.like_percentage)

                counter += 1

                # if we have only one image to like/comment
                if commenting and not liking and amount == 1:
                    continue

                if following or commenting or liking:
                    self.logger.info(
                        'username actions: following={} commenting={} '
                        'liking={}'.format(
                            following, commenting, liking))
                    break

                # if for some reason we have no actions on this user
                if counter > 5:
                    self.logger.info(
                        'username={} could not get interacted'.format(
                            username))
                    break

            # follow
            if following and not (self.dont_follow_inap_post and inap_img > 0):

                follow_state, msg = follow_user(
                    self.browser,
                    track,
                    self.username,
                    username,
                    None,
                    self.blacklist,
                    self.logger,
                    self.logfolder)
                if follow_state is True:
                    followed += 1

                elif msg == "already followed":
                    already_followed += 1

            else:
                self.logger.info('--> Not following')
                sleep(1)

            if total_liked_img < amount:
                self.logger.info('-------------')
                self.logger.info("--> Given amount not fullfilled, image pool "
                                 "reached its end\n")

        if len(usernames) > 1:
            # final words
            interacted_media_size = (len(usernames) * amount - inap_img)
            self.logger.info(
                "Finished interacting on total of {} "
                "images from {} users! xD\n"
                .format(interacted_media_size, len(usernames)))

            # print results
            self.logger.info('Liked: {}'.format(total_liked_img))
            self.logger.info('Already Liked: {}'.format(already_liked))
            self.logger.info('Commented: {}'.format(commented))
            self.logger.info('Followed: {}'.format(followed))
            self.logger.info('Already Followed: {}'.format(already_followed))
            self.logger.info('Inappropriate: {}'.format(inap_img))
            self.logger.info('Not valid users: {}\n'.format(not_valid_users))

        self.liked_img += total_liked_img
        self.already_liked += already_liked
        self.commented += commented
        self.followed += followed
        self.already_followed += already_followed
        self.inap_img += inap_img
        self.not_valid_users += not_valid_users

        return self

    def follow_user_followers(self, usernames, amount=10, randomize=False, interact=False, sleep_delay=600):
        """ Follow the `Followers` of given users """
        if self.aborting:
            return self

        message = "Starting to follow user `Followers`.."
        highlight_print(Settings, self.username, message, "feature", "info", self.logger)

        if not isinstance(usernames, list):
            usernames = [usernames]

        followed_all = 0
        followed_new = 0
        not_valid_users = 0

        # below, you can use some static value `10` instead of random ones..
        relax_point = random.randint(7, 14)

        # hold the current global values for differentiating at the end
        already_followed_init = self.already_followed
        liked_init = self.liked_img
        already_liked_init = self.already_liked
        commented_init = self.commented
        inap_img_init = self.inap_img

        self.quotient_breach = False

        for index, user in enumerate(usernames):
            if self.quotient_breach:
                break

            self.logger.info(
                "User '{}' [{}/{}]".format((user), index + 1, len(usernames)))

            try:
                person_list, simulated_list = get_given_user_followers(
                    self.browser,
                    self.username,
                    self.userid,
                    user,
                    amount,
                    self.dont_include,
                    randomize,
                    self.blacklist,
                    self.follow_times,
                    self.simulation,
                    self.jumps,
                    self.logger,
                    self.logfolder)

            except (TypeError, RuntimeWarning) as err:
                if isinstance(err, RuntimeWarning):
                    self.logger.warning(
                        u'Warning: {} , skipping to next user'.format(err))
                    continue

                else:
                    self.logger.error(
                        'Sorry, an error occurred: {}'.format(err))
                    self.aborting = True
                    return self

            print('')
            self.logger.info(
                "Grabbed {} usernames from '{}'s `Followers` to do following\n"
                .format(len(person_list), user))

            followed_personal = 0
            simulated_unfollow = 0

            for index, person in enumerate(person_list):
                if self.quotient_breach:
                    self.logger.warning(
                        "--> Follow quotient reached its peak!"
                        "\t~leaving Follow-User-Followers activity\n")
                    break

                self.logger.info(
                    "Ongoing Follow [{}/{}]: now following '{}'..."
                    .format(index + 1, len(person_list), person))

                validation, details = self.validate_user_call(person)
                if validation is not True:
                    self.logger.info(details)
                    not_valid_users += 1

                    if person in simulated_list:
                        self.logger.warning(
                            "--> Simulated Unfollow {}: unfollowing"
                            " '{}' due to mismatching validation...\n"
                            .format(simulated_unfollow + 1, person))

                        unfollow_state, msg = unfollow_user(
                            self.browser,
                            "profile",
                            self.username,
                            person,
                            None,
                            None,
                            self.relationship_data,
                            self.logger,
                            self.logfolder)
                        if unfollow_state is True:
                            simulated_unfollow += 1
                    # skip this [non-validated] user
                    continue

                # go ahead and follow, then interact (if any)
                with self.feature_in_feature("follow_by_list", False):
                    followed = self.follow_by_list(person,
                                                   self.follow_times,
                                                   sleep_delay,
                                                   interact)
                sleep(1)

                if followed > 0:
                    followed_all += 1
                    followed_new += 1
                    followed_personal += 1

                self.logger.info("Follow per user: {}  |  Total Follow: {}\n"
                                 .format(followed_personal, followed_all))

                # take a break after a good following
                if followed_new >= relax_point:
                    delay_random = random.randint(
                        ceil(sleep_delay * 0.85),
                        ceil(sleep_delay * 1.14))
                    sleep_time = ("{} seconds".format(delay_random) if
                                  delay_random < 60 else
                                  "{} minutes".format(truncate_float(
                                      delay_random / 60, 2)))
                    self.logger.info(
                        "------=>  Followed {} new users ~sleeping about {}\n"
                        .format(followed_new, sleep_time))
                    sleep(delay_random)
                    relax_point = random.randint(7, 14)
                    followed_new = 0

        # final words
        self.logger.info("Finished following {} users' `Followers`! xD\n"
                         .format(len(usernames)))
        # find the feature-wide action sizes by taking a difference
        already_followed = (self.already_followed - already_followed_init)
        inap_img = (self.inap_img - inap_img_init)
        liked = (self.liked_img - liked_init)
        already_liked = (self.already_liked - already_liked_init)
        commented = (self.commented - commented_init)

        # print results
        self.logger.info("Followed: {}".format(followed_all))
        self.logger.info("Already followed: {}".format(already_followed))
        self.logger.info("Not valid users: {}".format(not_valid_users))

        if interact is True:
            print('')
            # print results out of interactions
            self.logger.info("Liked: {}".format(liked))
            self.logger.info("Already Liked: {}".format(already_liked))
            self.logger.info("Commented: {}".format(commented))
            self.logger.info("Inappropriate: {}".format(inap_img))

        self.not_valid_users += not_valid_users

        return self

    def follow_user_following(self, usernames, amount=10, randomize=False, interact=False, sleep_delay=600):
        """ Follow the `Following` of given users """
        if self.aborting:
            return self

        message = "Starting to follow user `Following`.."
        highlight_print(Settings, self.username, message, "feature", "info", self.logger)

        if not isinstance(usernames, list):
            usernames = [usernames]

        followed_all = 0
        followed_new = 0
        not_valid_users = 0

        # hold the current global values for differentiating at the end
        already_followed_init = self.already_followed
        liked_init = self.liked_img
        already_liked_init = self.already_liked
        commented_init = self.commented
        inap_img_init = self.inap_img

        # below, can use a static value instead of from random range..
        relax_point = random.randint(7, 14)
        self.quotient_breach = False

        for index, user in enumerate(usernames):
            if self.quotient_breach:
                break

            self.logger.info("User '{}' [{}/{}]".format((user),
                                                        index + 1,
                                                        len(usernames)))
            try:
                person_list, simulated_list = get_given_user_following(
                    self.browser,
                    self.username,
                    self.username,
                    user,
                    amount,
                    self.dont_include,
                    randomize,
                    self.blacklist,
                    self.follow_times,
                    self.simulation,
                    self.jumps,
                    self.logger,
                    self.logfolder)

            except (TypeError, RuntimeWarning) as err:
                if isinstance(err, RuntimeWarning):
                    self.logger.warning(
                        u'Warning: {} , skipping to next user'.format(err))
                    continue

                else:
                    self.logger.error(
                        'Sorry, an error occurred: {}'.format(err))
                    self.aborting = True
                    return self

            print('')
            self.logger.info(
                "Grabbed {} usernames from '{}'s `Following` to do following\n"
                .format(len(person_list), user))

            followed_personal = 0
            simulated_unfollow = 0

            for index, person in enumerate(person_list):
                if self.quotient_breach:
                    self.logger.warning(
                        "--> Follow quotient reached its peak!"
                        "\t~leaving Follow-User-Following activity\n")
                    break

                self.logger.info(
                    "Ongoing Follow [{}/{}]: now following '{}'..."
                    .format(index + 1, len(person_list), person)
                )

                validation, details = self.validate_user_call(person)
                if validation is not True:
                    self.logger.info(details)
                    not_valid_users += 1

                    if person in simulated_list:
                        self.logger.warning(
                            "--> Simulated Unfollow {}:"
                            " unfollowing '{}' due to mismatching "
                            "validation...\n"
                            .format(simulated_unfollow + 1, person))

                        unfollow_state, msg = unfollow_user(
                            self.browser,
                            "profile",
                            self.username,
                            person,
                            None,
                            None,
                            self.relationship_data,
                            self.logger,
                            self.logfolder)
                        if unfollow_state is True:
                            simulated_unfollow += 1
                    # skip the [non-validated] user
                    continue

                # go ahead and follow, then interact (if any)
                with self.feature_in_feature("follow_by_list", False):
                    followed = self.follow_by_list(person,
                                                   self.follow_times,
                                                   sleep_delay,
                                                   interact)
                sleep(1)

                if followed > 0:
                    followed_all += 1
                    followed_new += 1
                    followed_personal += 1

                self.logger.info("Follow per user: {}  |  Total Follow: {}\n"
                                 .format(followed_personal, followed_all))

                # take a break after a good following
                if followed_new >= relax_point:
                    delay_random = random.randint(
                        ceil(sleep_delay * 0.85),
                        ceil(sleep_delay * 1.14))
                    sleep_time = ("{} seconds".format(delay_random) if
                                  delay_random < 60 else
                                  "{} minutes".format(truncate_float(
                                      delay_random / 60, 2)))
                    self.logger.info(
                        "------=>  Followed {} new users ~sleeping about {}\n"
                        .format(followed_new, sleep_time))
                    sleep(delay_random)
                    relax_point = random.randint(7, 14)
                    followed_new = 0

        # final words
        self.logger.info("Finished following {} users' `Following`! xD\n"
                         .format(len(usernames)))

        # find the feature-wide action sizes by taking a difference
        already_followed = (self.already_followed - already_followed_init)
        inap_img = (self.inap_img - inap_img_init)
        liked = (self.liked_img - liked_init)
        already_liked = (self.already_liked - already_liked_init)
        commented = (self.commented - commented_init)

        # print results
        self.logger.info("Followed: {}".format(followed_all))
        self.logger.info("Already followed: {}".format(already_followed))
        self.logger.info("Not valid users: {}".format(not_valid_users))

        if interact is True:
            print('')
            # print results out of interactions
            self.logger.info("Liked: {}".format(liked))
            self.logger.info("Already Liked: {}".format(already_liked))
            self.logger.info("Commented: {}".format(commented))
            self.logger.info("Inappropriate: {}".format(inap_img))

        self.not_valid_users += not_valid_users

        return self

    def end(self):
        """Closes the current session"""
        close_browser(self.browser, False, self.logger)

        with interruption_handler():
            # close virtual display
            if self.nogui:
                self.display.stop()

            # write useful information
            dump_follow_restriction(self.username,
                                    self.logger,
                                    self.logfolder)
            # dump_record_activity(self.username,
            #                      self.logger,
            #                      self.logfolder,
            #                      Settings)

            with open('{}followed.txt'.format(self.logfolder), 'w') \
                    as followFile:
                followFile.write(str(self.followed))

            # output live stats before leaving
            self.live_report()

            message = "Session ended!"
            highlight_print(Settings, self.username, message, "end", "info", self.logger)
            print("\n\n")

    @contextmanager
    def feature_in_feature(self, feature, validate_users):
        """
         Use once a host feature calls a guest
        feature WHERE guest needs special behaviour(s)
        """
        try:
            # add the guest which is gonna be used by the host :)
            self.internal_usage[feature] = {"validate": validate_users}
            yield

        finally:
            # remove the guest just after using it
            self.internal_usage.pop(feature)

    def live_report(self):
        """ Report live sessional statistics """

        print('')

        stats = [self.liked_img, self.already_liked,
                 self.commented,
                 self.followed, self.already_followed,
                 self.unfollowed,
                 self.inap_img,
                 self.not_valid_users]

        if self.following_num and self.followed_by:
            owner_relationship_info = (
                "On session start was FOLLOWING {} users"
                " & had {} FOLLOWERS"
                .format(self.following_num,
                        self.followed_by))
        else:
            owner_relationship_info = ''

        sessional_run_time = self.run_time()
        run_time_info = ("{} seconds".format(sessional_run_time) if
                         sessional_run_time < 60 else
                         "{} minutes".format(truncate_float(
                             sessional_run_time / 60, 2)) if
                         sessional_run_time < 3600 else
                         "{} hours".format(truncate_float(
                             sessional_run_time / 60 / 60, 2)))
        run_time_msg = "[Session lasted {}]".format(run_time_info)

        if any(stat for stat in stats):
            self.logger.info(
                "Sessional Live Report:\n"
                "\t|> LIKED {} images  |  ALREADY LIKED: {}\n"
                "\t|> COMMENTED on {} images\n"
                "\t|> FOLLOWED {} users  |  ALREADY FOLLOWED: {}\n"
                "\t|> UNFOLLOWED {} users\n"
                "\t|> LIKED {} comments\n"
                "\t|> REPLIED to {} comments\n"
                "\t|> INAPPROPRIATE images: {}\n"
                "\t|> NOT VALID users: {}\n"
                "\n{}\n{}"
                .format(self.liked_img,
                        self.already_liked,
                        self.commented,
                        self.followed,
                        self.already_followed,
                        self.unfollowed,
                        self.liked_comments,
                        self.replied_to_comments,
                        self.inap_img,
                        self.not_valid_users,
                        owner_relationship_info,
                        run_time_msg))
        else:
            self.logger.info("Sessional Live Report:\n"
                             "\t|> No any statistics to show\n"
                             "\n{}\n{}"
                             .format(owner_relationship_info,
                                     run_time_msg))

    def is_mandatory_character(self, uchr):
        if self.aborting:
            return self
        try:
            return self.check_letters[uchr]
        except KeyError:
            return self.check_letters.setdefault(uchr,
                                                 self.mandatory_character in
                                                 unicodedata.name(uchr))

    def run_time(self):
        """ Get the time session lasted in seconds """

        real_time = time.time()
        run_time = (real_time - self.start_time)
        run_time = truncate_float(run_time, 2)

        return run_time

    def check_character_set(self, unistr):
        self.check_letters = {}
        if self.aborting:
            return self
        return all(self.is_mandatory_character(uchr)
                   for uchr in unistr
                   if uchr.isalpha())

@contextmanager
def smart_run(session):
    try:
        if session.login():
            yield
        else:
            self.logger.info("Not proceeding as login failed")

    except (Exception, KeyboardInterrupt) as exc:
        if isinstance(exc, NoSuchElementException):
            # the problem is with a change in IG page layout
            log_file = "{}.html".format(time.strftime("%Y%m%d-%H%M%S"))
            file_path = os.path.join(gettempdir(), log_file)
            with open(file_path, "wb") as fp:
                fp.write(session.browser.page_source.encode("utf-8"))
            print("{0}\nIf raising an issue, "
                  "please also upload the file located at:\n{1}\n{0}"
                  .format('*' * 70, file_path))

        # provide full stacktrace (else than external interrupt)
        if isinstance(exc, KeyboardInterrupt):
            clean_exit("You have exited successfully.")
        else:
            raise

    finally:
        session.end()
