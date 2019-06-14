""" Quickstart script for GithubPy usage """

# imports
from githubpy import GithubPy
from githubpy import smart_run
from socialcommons.file_manager import set_workspace
from githubpy import settings

import random

# set workspace folder at desired location (default is at your home folder)
set_workspace(settings.Settings, path=None)

# get an GithubPy session!
session = GithubPy(use_firefox=True)

with smart_run(session):
    """ Activity flow """
    # general settings
    session.set_dont_include(["friend1", "friend2", "friend3"])

    session.set_do_follow(enabled=True, percentage=40, times=1)

    targets = ['janandd', 'M0nica', 'gaearon', 'rauchg']
    number = random.randint(3, 5)
    random_targets = targets

    if len(targets) <= number:
        random_targets = targets
    else:
        random_targets = random.sample(targets, number)

    session.copy_contributors(source_user="timgrossmann",
                              source_repo="InstaPy",
                              dest_organisation="socialbotspy")

    session.search_and_copy_contributors(search_query="instagram bot",
                            dest_organisation="socialbotspy")

    session.follow_user_followers(random_targets,
                                  amount=random.randint(30, 60),
                                  randomize=True, sleep_delay=600,
                                  interact=True)

    session.follow_user_following(random_targets,
                                  amount=random.randint(30, 60),
                                  randomize=True, sleep_delay=600,
                                  interact=True)

