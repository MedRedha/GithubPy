# GithubPy

## Installation:
It is recomended to use via pyenv We will be supporting python 3.6.0 and above going forward

```
pip install --upgrade pip
curl https://pyenv.run | bash
curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
pyenv local 3.6.0
pip install -r requirements.txt
```

##  APIs:
  - [follow user followers](#follow-user-followers)
  - [follow user following](#follow-user-following)
  - [copy contributors](#copy-contributors)
  - [search and copy contributors](#search-and-copy-contributors)
  - [cancel invites](#cancel-invites)
  - [unfollow users](#unfollow-users)
  - [download contributors](#download-contributors)
  - [download forkers](#download-forkers)
  - [download stargazers](#download-stargazers)
  - [download issuers](#download-issuers)

### follow user followers
 
```python

 session = GithubPy()

 with smart_run(session):
    session.follow_user_followers(random_targets,
                                  amount=random.randint(30, 60),
                                  randomize=True, sleep_delay=600,
                                  interact=True)
 ```
 
### follow user following
 
```python

 session = GithubPy()

 with smart_run(session):
    session.follow_user_following(random_targets,
                                  amount=random.randint(30, 60),
                                  randomize=True, sleep_delay=600,
                                  interact=True)
 ```

### copy contributors

Invites all contributors of a given repo

```python

 session = GithubPy()

 with smart_run(session):
    session.copy_contributors(source_user="timgrossmann",
                              source_repo="InstaPy",
                              dest_organisation="socialbotspy")
 ```


### search and copy contributors

Same as above, just that you dont need to explicitly find repos. It uses `copy_contributors` internally

```python

 session = GithubPy()

 with smart_run(session):
    session.search_and_copy_contributors(search_query="instagram bot",
                                        dest_organisation="socialbotspy")
 ```

### cancel invites

```python

 session = GithubPy()

 with smart_run(session):
    session.cancel_invites(dest_organisation="socialbotspy")
 ```


### unfollow users

```python

 session = GithubPy()

 with smart_run(session):
    session.unfollow_users(amount=random.randint(30, 50), skip=100)
 ```

### download contributors

Create a file `config.txt` with following content
```text
[configuration]
github_id = <your Github id>
github_password =  <your Github password>
github_api_token = <your Github API token>
```

```bash
 python download-contributors.py --repo https://github.com/timgrossmann/InstaPy
```
It will download results in a file `repo-owner_repo-name_contributors.csv`

### download forkers

Create file `config.txt` as mentioned above
```bash
 python download-forkers.py --repo https://github.com/timgrossmann/InstaPy
```
It will download results in a file `repo-owner_repo-name_forkers.csv`

### download stargazers

Create file `config.txt` as mentioned above
```bash
 python download-stargazers.py --repo https://github.com/timgrossmann/InstaPy --max_page 7
```
It will download results in a file `repo-owner_repo-name_stargazers.csv`

Note:
- option `max_page` is 5 by default

### download issuers

Create file `config.txt` as mentioned above

```bash
 python download-issuers.py --repo https://github.com/timgrossmann/InstaPy --add_issue_detail True --start_page 2 --end_page 6
```
It will download results in a file `repo-owner_repo-name_issuers.csv`

Note:
- option `add_issue_detail` is `False` by default ie Issue-title and Issue-url are not included.
- option `start_page` is 1 by default
- option `end_page` is 5 by default


## How to run:

 -  modify `quickstart.py` according to your requirements
 -  `python quickstart.py -u <my_github_username> -p <mypssword>`


## How to schedule as a job:

```bash
    */10 * * * * bash /path/to/GithubPy/run_githubpy_only_once_for_mac.sh /path/to/GithubPy/quickstart.py $USERNAME $PASSWORD
```

## Help build socialbotspy
Check out this short guide on [how to start contributing!](https://github.com/InstaPy/instapy-docs/blob/master/CONTRIBUTORS.md).





