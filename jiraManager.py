#! /bin/python
import json
import os
import sys

from jira import JIRA

# TODO: error handling, file creation
with open(os.path.dirname(os.path.realpath(__file__)) + '/.jira_credentials.json', 'r') as f:
    credentials = json.load(f)


def getIssueWithStatus(status):
    return jira.search_issues('status = "' + status + '" AND resolution = Unresolved AND assignee in (currentUser())')


jira = JIRA(credentials['host'],
            basic_auth=(credentials['username'],
                        credentials['password']))

if (len(sys.argv) == 4 and str(sys.argv[1]) == "transition"):
    jira.transition_issue(sys.argv[2], sys.argv[3])

nextIssues = getIssueWithStatus('Next')
inProgressIssues = getIssueWithStatus('In Progress')

if (len(inProgressIssues) == 0):
    print('Not working... :coffee:\n---')
    if (len(nextIssues) == 0):
        print('Put issues in "Next" to work on them')
    for issue in nextIssues:
        print("<b>%s</b>: %s" % (issue.key, issue.fields.summary))
        for transition in [('Start progress', 'media-playback-start'), ('Deselect', 'media-playback-stop')]:
            print("--%s | bash='python %s transition %s \"%s\"' terminal=false refresh=true iconName=%s" % (transition[0], sys.argv[0], issue.key, transition[0], transition[1]))
        
        print("--Show in browser... | href='%s/projects/%s/issues/%s' iconName=application-exit" % (credentials['host'], issue.key.split('-')[0], issue.key))
                
        
elif (len(inProgressIssues) > 1):
    print('Can only have 1 issue in progress!')
else:
    issue = inProgressIssues[0]
    print('Working on ' + issue.key + ' :cold_sweat:')
    print('---')
    print('<b>' + issue.fields.summary + '</b>')
    print(issue.fields.description)
    print('---')
    print('Log work')
    print('--TODO: implement logging time')
    print('--5 min')
    print('--10 min')
    print('--15 min')
    print('--20 min')
    print("Stop progress | bash='python %s transition %s \"Stop progress\"' terminal=false refresh=true iconName=media-playback-pause" % (sys.argv[0], issue.key))
    print("Show in browser... | href='%s/projects/%s/issues/%s' iconName=application-exit" % (credentials['host'], issue.key.split('-')[0], issue.key))
