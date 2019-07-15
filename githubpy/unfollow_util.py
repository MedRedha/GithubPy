""" Module which handles the follow features like unfollowing and following """
from datetime import datetime
import os
import random
import json
import sqlite3

from socialcommons.time_util import sleep
from socialcommons.util import delete_line_from_file
from socialcommons.util import update_activity
from socialcommons.util import add_user_to_blacklist
from socialcommons.util import click_element
from socialcommons.util import web_address_navigator
from socialcommons.util import get_relationship_counts
from socialcommons.util import emergency_exit
from socialcommons.util import find_user_id
from socialcommons.util import is_page_available
from socialcommons.util import click_visibly
from socialcommons.util import get_action_delay
from socialcommons.print_log_writer import log_followed_pool
from socialcommons.print_log_writer import log_uncertain_unfollowed_pool
from socialcommons.print_log_writer import log_record_all_unfollowed
from socialcommons.print_log_writer import get_log_time
from socialcommons.database_engine import get_database
from socialcommons.quota_supervisor import quota_supervisor
from .settings import Settings

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotVisibleException

def get_following_status(browser, track, username, person, person_id, logger, logfolder):
    """ Verify if you are following the user in the loaded page """
    if track == "profile":
        ig_homepage = "https://github.com/"
        web_address_navigator(browser, ig_homepage + person, Settings)

    follow_button_XP = "//div/div/div/span/span[1]/form/input[3]"
    unfollow_button_XP = "//div/div/div/span/span[2]/form/input[3]"

    follow_button = browser.find_element_by_xpath(follow_button_XP)
    if follow_button:
        # .setAttribute("value", "your value");
        logger.info("get_following_status:follow_button:text:{}, button:{}".format(follow_button.get_attribute('value'), follow_button))
        return follow_button.get_attribute('value'), follow_button

    unfollow_button = browser.find_element_by_xpath(unfollow_button_XP)
    if unfollow_button:
        logger.info("get_following_status:unfollow_button:text:{}, button:{}".format(unfollow_button.get_attribute('value'), unfollow_button))
        return unfollow_button.get_attribute('value'), unfollow_button

    return None, None

def follow_user(browser, track, login, userid_to_follow, button, blacklist,
                logger, logfolder, Settings):
    """ Follow a user either from the profile page or post page or dialog
    box """
    # list of available tracks to follow in: ["profile", "post" "dialog"]

    # check action availability
    if quota_supervisor(Settings, "follows") == "jump":
        return False, "jumped"

    if track in ["profile", "post"]:
        if track == "profile":
            # check URL of the webpage, if it already is user's profile
            # page, then do not navigate to it again
            user_link = "https://github.com/{}/".format(userid_to_follow)
            web_address_navigator( browser, user_link, Settings)

        # find out CURRENT following status
        following_status, follow_button = \
            get_following_status(browser,
                                 track,
                                 login,
                                 userid_to_follow,
                                 None,
                                 logger,
                                 logfolder)

        logger.info("following_status:{}, follow_button:{}".format(following_status, follow_button))

        if following_status in ["Follow", "Follow Back"]:
            click_visibly(browser, Settings, follow_button)  # click to follow
            follow_state, msg =  True, "success"
            # verify_action(browser, "follow", track, login,
            #                                   userid_to_follow, None, logger,
            #                                   logfolder)
            if follow_state is not True:
                return False, msg
        elif following_status is None:
            # TODO:BUG:2nd login has to be fixed with userid of loggedin user
            sirens_wailing, emergency_state = emergency_exit(browser, Settings, "https://www.github.com", login,
                                                             login, logger, logfolder, True)
            if sirens_wailing is True:
                return False, emergency_state

            else:
                logger.warning(
                    "--> Couldn't unfollow '{}'!\t~unexpected failure".format(
                        userid_to_follow))
                return False, "unexpected failure"

    # general tasks after a successful follow
    logger.info("--> Followed '{}'!".format(userid_to_follow.encode("utf-8")))
    update_activity(Settings)

    # get user ID to record alongside username
    user_id = get_user_id(browser, track, userid_to_follow, logger)

    logtime = datetime.now().strftime('%Y-%m-%d %H:%M')
    log_followed_pool(login, userid_to_follow, logger,
                      logfolder, logtime, user_id)

    follow_restriction("write", userid_to_follow, None, logger)

    if blacklist['enabled'] is True:
        action = 'followed'
        add_user_to_blacklist(userid_to_follow,
                              blacklist['campaign'],
                              action,
                              logger,
                              logfolder)

    # get the post-follow delay time to sleep
    naply = get_action_delay("follow", Settings)
    sleep(naply)

    return True, "success"


def get_given_user_followers(browser,
                             login,
                             user_name,
                             userid,
                             amount,
                             dont_include,
                             randomize,
                             blacklist,
                             follow_times,
                             simulation,
                             jumps,
                             logger,
                             logfolder):
    """
    For the given username, follow their followers.

    :param browser: webdriver instance
    :param login:
    :param user_name: given username of account to follow
    :param amount: the number of followers to follow
    :param dont_include: ignore these usernames
    :param randomize: randomly select from users' followers
    :param blacklist:
    :param follow_times:
    :param logger: the logger instance
    :param logfolder: the logger folder
    :return: list of user's followers also followed
    """
    user_name = user_name.strip()

    user_link = "https://www.github.com/{}".format(userid)
    web_address_navigator(browser, user_link, Settings)

    if not is_page_available(browser, logger, Settings):
        return [], []

    # check how many people are following this user.
    allfollowers, allfollowing = get_relationship_counts(browser, "https://www.github.com/", user_name,
                                                         userid, logger, Settings)

    # skip early for no followers
    if not allfollowers:
        logger.info("'{}' has no followers".format(user_name))
        return [], []

    elif allfollowers < amount:
        logger.warning(
            "'{}' has less followers- {}, than the given amount of {}".format(
                user_name, allfollowers, amount))

    # locate element to user's followers
    user_followers_link = "https://www.github.com/{}/followers".format(
        userid)
    web_address_navigator( browser, user_followers_link, Settings)

    try:
        followers_links = browser.find_elements_by_xpath('//div[2]/div[2]/div/ol/li/div[2]/h3/span/a')
        followers_list = []
        for followers_link in followers_links:
            u = followers_link.get_attribute('href').replace('https://github.com/', '')
            followers_list.append(u)
        logger.info('followers_list:')
        logger.info(followers_list)

        # click_element(browser, Settings, followers_link[0])
        # # update server calls
        # update_activity(Settings)

    except NoSuchElementException:
        logger.error(
            'Could not find followers\' link for {}'.format(user_name))
        return [], []

    except BaseException as e:
        logger.error("`followers_link` error {}".format(str(e)))
        return [], []

    # channel = "Follow"

    # TODO: Fix it: Add simulated
    simulated_list = []
    if amount < len(followers_list):
        person_list = random.sample(followers_list, amount)
    else:
        person_list = followers_list

    # person_list, simulated_list = get_users_through_dialog(browser, login,
    #                                                        user_name, amount,
    #                                                        allfollowers,
    #                                                        randomize,
    #                                                        dont_include,
    #                                                        blacklist,
    #                                                        follow_times,
    #                                                        simulation,
    #                                                        channel, jumps,
    #                                                        logger, logfolder)

    return person_list, simulated_list




def get_given_user_following(browser,
                             login,
                             user_name,
                             userid,
                             amount,
                             dont_include,
                             randomize,
                             blacklist,
                             follow_times,
                             simulation,
                             jumps,
                             logger,
                             logfolder):
    """
    For the given username, follow their following.

    :param browser: webdriver instance
    :param login:
    :param user_name: given username of account to follow
    :param amount: the number of following to follow
    :param dont_include: ignore these usernames
    :param randomize: randomly select from users' following
    :param blacklist:
    :param follow_times:
    :param logger: the logger instance
    :param logfolder: the logger folder
    :return: list of user's following also followed
    """
    user_name = user_name.strip()

    user_link = "https://www.github.com/{}".format(userid)
    web_address_navigator(browser, user_link, Settings)

    if not is_page_available(browser, logger, Settings):
        return [], []

    # check how many people are following this user.
    allfollowers, allfollowing = get_relationship_counts(browser, "https://www.github.com/", user_name,
                                                         userid, logger, Settings)

    # skip early for no followers
    if not allfollowing:
        logger.info("'{}' has no following".format(user_name))
        return [], []

    elif allfollowing < amount:
        logger.warning(
            "'{}' has less following- {}, than the given amount of {}".format(
                user_name, allfollowing, amount))

    # locate element to user's following
    user_following_link = "https://www.github.com/{}/following".format(
        userid)
    web_address_navigator( browser, user_following_link, Settings)

    try:
        following_links = browser.find_elements_by_xpath('//div[2]/div[2]/div/ol/li/div[2]/h3/span/a')
        following_list = []
        for following_link in following_links:
            u = following_link.get_attribute('href').replace('https://github.com/', '')
            following_list.append(u)
        logger.info('following_list:')
        logger.info(following_list)

        # click_element(browser, Settings, following_link[0])
        # # update server calls
        # update_activity(Settings)

    except NoSuchElementException:
        logger.error(
            'Could not find following\' link for {}'.format(user_name))
        return [], []

    except BaseException as e:
        logger.error("`following_link` error {}".format(str(e)))
        return [], []

    # channel = "Follow"

    # TODO: Fix it: Add simulated
    simulated_list = []
    if amount < len(following_list):
        person_list = random.sample(following_list, amount)
    else:
        person_list = following_list

    # person_list, simulated_list = get_users_through_dialog(browser, login,
    #                                                        user_name, amount,
    #                                                        allfollowing,
    #                                                        randomize,
    #                                                        dont_include,
    #                                                        blacklist,
    #                                                        follow_times,
    #                                                        simulation,
    #                                                        channel, jumps,
    #                                                        logger, logfolder)

    return person_list, simulated_list


def dump_follow_restriction(profile_name, logger, logfolder):
    """ Dump follow restriction data to a local human-readable JSON """

    try:
        # get a DB and start a connection
        db, id = get_database(Settings)
        conn = sqlite3.connect(db)

        with conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute(
                "SELECT * FROM followRestriction WHERE profile_id=:var",
                {"var": id})
            data = cur.fetchall()

        if data:
            # get the existing data
            filename = "{}followRestriction.json".format(logfolder)
            if os.path.isfile(filename):
                with open(filename) as followResFile:
                    current_data = json.load(followResFile)
            else:
                current_data = {}

            # pack the new data
            follow_data = {user_data[1]: user_data[2] for user_data in
                           data or []}
            current_data[profile_name] = follow_data

            # dump the fresh follow data to a local human readable JSON
            with open(filename, 'w') as followResFile:
                json.dump(current_data, followResFile)

    except Exception as exc:
        logger.error(
            "Pow! Error occurred while dumping follow restriction data to a "
            "local JSON:\n\t{}".format(
                str(exc).encode("utf-8")))

    finally:
        if conn:
            # close the open connection
            conn.close()


def follow_restriction(operation, username, limit, logger):
    """ Keep track of the followed users and help avoid excessive follow of
    the same user """

    try:
        # get a DB and start a connection
        db, id = get_database(Settings)
        conn = sqlite3.connect(db)

        with conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute(
                "SELECT * FROM followRestriction WHERE profile_id=:id_var "
                "AND username=:name_var",
                {"id_var": id, "name_var": username})
            data = cur.fetchone()
            follow_data = dict(data) if data else None

            if operation == "write":
                if follow_data is None:
                    # write a new record
                    cur.execute(
                        "INSERT INTO followRestriction (profile_id, "
                        "username, times) VALUES (?, ?, ?)",
                        (id, username, 1))
                else:
                    # update the existing record
                    follow_data["times"] += 1
                    sql = "UPDATE followRestriction set times = ? WHERE " \
                          "profile_id=? AND username = ?"
                    cur.execute(sql, (follow_data["times"], id, username))

                # commit the latest changes
                conn.commit()

            elif operation == "read":
                if follow_data is None:
                    return False

                elif follow_data["times"] < limit:
                    return False

                else:
                    exceed_msg = "" if follow_data[
                        "times"] == limit else "more than "
                    logger.info("---> {} has already been followed {}{} times"
                                .format(username, exceed_msg, str(limit)))
                    return True

    except Exception as exc:
        logger.error(
            "Dap! Error occurred with follow Restriction:\n\t{}".format(
                str(exc).encode("utf-8")))

    finally:
        if conn:
            # close the open connection
            conn.close()

def unfollow_user(browser, track, username, userid, person, person_id, button,
                  relationship_data, logger, logfolder, Settings):
    """ Unfollow a user either from the profile or post page or dialog box """
    # list of available tracks to unfollow in: ["profile", "post" "dialog"]

    # check action availability
    if quota_supervisor(Settings, "unfollows") == "jump":
        return False, "jumped"

    if track in ["profile", "post"]:
        """ Method of unfollowing from a user's profile page or post page """
        if track == "profile":
            user_link = "https://www.github.com/{}/".format(person)
            web_address_navigator( browser, user_link, Settings)

        # find out CURRENT follow status
        following_status, follow_button = get_following_status(browser,
                                                               track,
                                                               username,
                                                               person,
                                                               person_id,
                                                               logger,
                                                               logfolder)

        if following_status in ["Following", "Requested"]:
            click_element(browser, Settings, follow_button)  # click to unfollow
            sleep(4)  # TODO: use explicit wait here
            confirm_unfollow(browser)
            unfollow_state, msg = verify_action(browser, "unfollow", track,
                                                username,
                                                person, person_id, logger,
                                                logfolder)
            if unfollow_state is not True:
                return False, msg

        elif following_status in ["Follow", "Follow Back"]:
            logger.info(
                "--> Already unfollowed '{}'! or a private user that "
                "rejected your req".format(
                    person))
            post_unfollow_cleanup(["successful", "uncertain"], username,
                                  person, relationship_data, person_id, logger,
                                  logfolder)
            return False, "already unfollowed"

        elif following_status in ["Unblock", "UNAVAILABLE"]:
            if following_status == "Unblock":
                failure_msg = "user is in block"

            elif following_status == "UNAVAILABLE":
                failure_msg = "user is inaccessible"

            logger.warning(
                "--> Couldn't unfollow '{}'!\t~{}".format(person, failure_msg))
            post_unfollow_cleanup("uncertain", username, person,
                                  relationship_data, person_id, logger,
                                  logfolder)
            return False, following_status

        elif following_status is None:
            sirens_wailing, emergency_state = emergency_exit(browser, Settings, username,
                                                             userid, logger, logfolder)
            if sirens_wailing is True:
                return False, emergency_state

            else:
                logger.warning(
                    "--> Couldn't unfollow '{}'!\t~unexpected failure".format(
                        person))
                return False, "unexpected failure"
    elif track == "dialog":
        """  Method of unfollowing from a dialog box """
        click_element(browser, Settings, button)
        sleep(4)  # TODO: use explicit wait here
        confirm_unfollow(browser)

    # general tasks after a successful unfollow
    logger.info("--> Unfollowed '{}'!".format(person))
    update_activity(Settings, 'unfollows')
    post_unfollow_cleanup("successful", username, person, relationship_data,
                          person_id, logger, logfolder)

    # get the post-unfollow delay time to sleep
    naply = get_action_delay("unfollow", Settings)
    sleep(naply)

    return True, "success"


def confirm_unfollow(browser):
    """ Deal with the confirmation dialog boxes during an unfollow """
    attempt = 0

    while attempt < 3:
        try:
            attempt += 1
            button_xp = "//button[text()='Unfollow']"  # "//button[contains(
            # text(), 'Unfollow')]"
            unfollow_button = browser.find_element_by_xpath(button_xp)

            if unfollow_button.is_displayed():
                click_element(browser, Settings, unfollow_button)
                sleep(2)
                break

        except (ElementNotVisibleException, NoSuchElementException) as exc:
            # prob confirm dialog didn't pop up
            if isinstance(exc, ElementNotVisibleException):
                break

            elif isinstance(exc, NoSuchElementException):
                sleep(1)
                pass

def post_unfollow_cleanup(state, username, person, relationship_data,
                          person_id, logger, logfolder):
    """ Casual local data cleaning after an unfollow """
    if not isinstance(state, list):
        state = [state]

    delete_line_from_file("{0}{1}_followedPool.csv"
                          .format(logfolder, username), person, logger)

    if "successful" in state:
        if person in relationship_data[username]["all_following"]:
            relationship_data[username]["all_following"].remove(person)

    if "uncertain" in state:
        # this user was found in our unfollow list but currently is not
        # being followed
        logtime = get_log_time()
        log_uncertain_unfollowed_pool(username, person, logger, logfolder,
                                      logtime, person_id)
        # take a generic 3 seconds of sleep per each uncertain unfollow
        sleep(3)

    # save any unfollowed person
    log_record_all_unfollowed(username, person, logger, logfolder)
    print('')

def get_user_id(browser, track, username, logger):
    """ Get user's ID either from a profile page or post page """
    user_id = "unknown"

    if track != "dialog":  # currently do not get the user ID for follows
        # from 'dialog'
        user_id = find_user_id(Settings, browser, track, username, logger)

    return user_id

def verify_action(browser, action, track, username, person, person_id, logger,
                  logfolder):
    """ Verify if the action has succeeded """
    if action not in ["follow", "unfollow"]:
        return False, "unexpected"
    # reload_webpage(browser, Settings)

    following_status, follow_button = get_following_status(browser,
                                                        "profile",
                                                        username,
                                                        person,
                                                        None,
                                                        logger,
                                                        logfolder)

    logger.info("Reloaded following_status:{}, follow_button:{}".format(following_status, follow_button))


    follow_unfollow_button_XP = ("//div/div/div/span/span/form/button")
    follow_unfollow_button = browser.find_element_by_xpath(follow_unfollow_button_XP)
    if follow_unfollow_button:
        logger.info("button_change: {} , {}".format(follow_unfollow_button.text, follow_unfollow_button))
        if (action == "follow" and follow_unfollow_button.text == "Unfollow")\
            or (action == "unfollow" and follow_unfollow_button.text == "Follow"):
            return True, "success"
        else:
            return False, "unexpected"
    if not follow_unfollow_button:
        logger.info("button_change:WTF")
    return False, "unexpected"

def post_unfollow_actions(browser, person, logger):
    pass
