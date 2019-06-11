#!/usr/bin/env python3
import base64
import json
import os
import sys
from datetime import datetime

import requests
from jira import JIRA

# LOAD CONFIGURATION

os.chdir(os.path.dirname(os.path.realpath(__file__)))

# TODO: error handling, file creation
with open('.jira_credentials.json', 'r') as f:
    credentials = json.load(f)
with open('.jira_reviewers.json', 'r') as f:
    reviewers = json.load(f)

jira = JIRA(credentials['host'],
            basic_auth=(credentials['username'],
                        credentials['password']))

# COMMAND LINE INVOCATION

if (len(sys.argv) > 1):
  if (len(sys.argv) == 2 and str(sys.argv[1]) == "users"):
    print("Username\t(Display Name)")
    print("--------\t--------------")
    for user in jira.search_users('', maxResults=150):
      print(user.key + '\t(%s)' % user.displayName)

  elif (len(sys.argv) >= 4 and str(sys.argv[1]) == "transition"):
    issue = sys.argv[2]
    transition = sys.argv[3]

    if (transition == "Start progress"):
      timelog = open(".jira_progressstarted.txt", "w+")
      timelog.write(str(datetime.now().timestamp()))
      timelog.close()

    if (transition == "Resolved" or transition == "Stop progress"):
      timelog = open(".jira_progressstarted.txt", "r")
      timeStarted = datetime.fromtimestamp(float(timelog.readline()))
      timeNow = datetime.now()
      diffMinutes = (timeNow - timeStarted).seconds / 60
      if diffMinutes >= 1:
        jira.add_worklog(issue, timeSpent=str(diffMinutes) + 'm', comment="Auto-logged by JIRA Issue Manager")
      os.remove(".jira_progressstarted.txt")

    if (transition == "Resolved"):
      jira.transition_issue(issue, transition, assignee={'name': sys.argv[4]})
    else:
      jira.transition_issue(issue, transition)

  exit(0)


# HELPER FUNCTIONS

def getAsBase64(url):
    return base64.b64encode(requests.get(url).content).decode('utf-8')


def getIssueWithStatus(status):
  return jira.search_issues('status = "' + status + '" AND resolution = Unresolved AND assignee in (currentUser())')


def addSeparator():
  print('---')


def addMenuItem(text, options=None):
  optionsText = ''
  if options:
    optionsText += '|'

    # Override defaults
    if 'bash' in options:
      if 'refresh' not in options:
        options['refresh'] = 'true'
      if 'terminal' not in options:
        options['terminal'] = 'false'

    for key in options:
      optionsText += '%s=%s ' % (key, options[key])
  print(text + optionsText)


def addSubMenuItem(text, options):
  addMenuItem('--' + text, options)


def addLinkToIssue(issue, subMenu=False):
  link = '%s/projects/%s/issues/%s' % (credentials['host'], issue.key.split('-')[0], issue.key)
  addMenuItem("%sShow issue in browser..." % ('', '--')[subMenu], {'href': link, 'iconName': 'application-exit'})


# MAIN PROGRAM START

nextIssues = getIssueWithStatus('Next')
inProgressIssues = getIssueWithStatus('In Progress')

if (len(inProgressIssues) == 0):
  addMenuItem('Not working... :coffee:')
  addSeparator()
  if (len(nextIssues) == 0):
    addMenuItem('Put issues in "Next" to work on them')
  for issue in nextIssues:
    addMenuItem("<b>%s</b>: %s" % (issue.key, issue.fields.summary))
    for transition in [('Start progress', 'media-playback-start'), ('Deselect', 'media-playback-stop')]:
      addSubMenuItem(transition[0],
                     {
                     'bash': "'%s transition %s \"%s\"'" % (sys.argv[0], issue.key, transition[0]),
                     'iconName': transition[1]
                     })

    addLinkToIssue(issue, subMenu=True)

elif (len(inProgressIssues) > 1):
  addMenuItem('You may only have 1 issue with status "In progress"!')
  addMenuItem('Use JIRA to fix this')
  addSeparator()

else:
  issue = inProgressIssues[0]
  addMenuItem('Working on ' + issue.key + ' :cold_sweat:')
  addSeparator()
  addMenuItem('<b>' + issue.fields.summary + '</b>')
  if (issue.fields.description):
    addMenuItem(issue.fields.description)
  addSeparator()
  addMenuItem("Resolve and reassign for review", {'iconName': 'document-properties'})
  for user in reviewers:
    rawUser = jira.user(user).raw
    addSubMenuItem(rawUser['displayName'], {'image': getAsBase64(rawUser['avatarUrls']['16x16']), 'imageWidth': 16, 'imageHeight': 16,
                                            'bash': "'%s transition %s \"Resolved\" %s'" % (sys.argv[0], issue.key, rawUser['key'])})
  addMenuItem("Stop progress", {'bash': "'%s transition %s \"Stop progress\"'" % (sys.argv[0], issue.key), 'iconName': 'media-playback-pause'})
  addLinkToIssue(issue)

addSeparator()

addMenuItem("Open JIRA", {'href': credentials["host"], 'image': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAMZJREFUOI2Vkj0OAUEAhb9IJOKn3PM5gEaCWqOROIIrKPWicAm9hEoidHyaXdaameUl00zevL8MpDEFZjWcKDL1ql6ALEZqJAT6QBvoAuO/7dWNbyRTxATOJQGB+T/vW+rDTwRTxDZ4BO66wKjOOQNWQE89+Y3aLeZ53yWwDggkt8jUS867A4uQQDVFeYNx3rO4bwKnyBZf/6LsXmAHTH5J8epewQHoqMe6LULuhQC/pAi5q25zgXQKda/eqgcYlCoOQxx1/wRTboLP64okfwAAAABJRU5ErkJggg=='})
addMenuItem("Refresh", {'bash': '', 'iconName': 'object-rotate-right'})
