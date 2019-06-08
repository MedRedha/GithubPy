# GithubPy

## Installation:
It is recomended to use via pyenv We will be supporting python 3.6.0 and above going forward

```
pip install --upgrade pip
curl https://pyenv.run | bash
curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
pyenv local 3.6.0
pip install --upgrade git+https://github.com/socialbotspy/SocialCommons.git
pip install -r requirements.txt
```

##  APIs:
  - [follow user followers](#follow-user-followers)
  - [follow user following](#follow-user-following)

### follow user followers
 
```python

 session = TwitterPy()

 with smart_run(session):
    session.follow_user_followers(random_targets,
                                  amount=random.randint(30, 60),
                                  randomize=True, sleep_delay=600,
                                  interact=True)
 ```
 
### follow user following
 
```python

 session = TwitterPy()

 with smart_run(session):
    session.follow_user_following(random_targets,
                                  amount=random.randint(30, 60),
                                  randomize=True, sleep_delay=600,
                                  interact=True)
 ```

