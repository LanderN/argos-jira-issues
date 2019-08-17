#!/usr/bin/env python3
import base64
import json
import os
import sys
from datetime import datetime, timedelta

import gi
import pytz
import requests
from jira import JIRA

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # isort:skip

issueListFilter = (
    '(status = "Next" OR status = "In Progress") AND assignee in (currentUser())'
)
allowedTransitions = {}

# LOAD CONFIGURATION

os.chdir(os.path.dirname(os.path.realpath(__file__)))

# TODO: error handling, file creation
with open(".jira_credentials.json", "r") as f:
    credentials = json.load(f)
with open(".jira_reviewers.json", "r") as f:
    reviewers = json.load(f)

try:
    with open(".jira_progress.json", "r") as f:
        progress = json.load(f)
except FileNotFoundError:
    progress = {}


jira = JIRA(
    credentials["host"], basic_auth=(credentials["username"], credentials["password"])
)


# HELPER FUNCTIONS
def startTracking(issue):
    global progress

    # Stop tracking other issues
    for issueToStop in list(progress.keys()):
        stopTracking(issueToStop)

    with open(".jira_progress.json", "w+") as f:
        progress[issue] = datetime.now().timestamp()
        json.dump(progress, f)


def calcTimeBetween(startDateTime: datetime, endDateTime: datetime):

    timeDiff = timedelta()
    currentDateTime = startDateTime

    while currentDateTime < endDateTime:
        # Skip weekends
        if currentDateTime.weekday() > 4:
            currentDateTime += timedelta(days=1)
            continue

        # TODO: make configurable
        breakStartTime = currentDateTime.replace(hour=12, minute=20)
        breakEndTime = currentDateTime.replace(hour=13, minute=0)
        dayEndTime = currentDateTime.replace(hour=17, minute=15)
        dayStartTime = currentDateTime.replace(hour=8, minute=47)

        if currentDateTime <= breakStartTime:
            if endDateTime <= breakStartTime:
                timeDiff += endDateTime - currentDateTime
                currentDateTime = endDateTime
                break
            else:
                timeDiff += breakStartTime - currentDateTime
                currentDateTime = breakEndTime
        elif currentDateTime > breakStartTime and endDateTime <= breakEndTime:
            currentDateTime = breakEndTime
        elif currentDateTime > breakStartTime and endDateTime > breakEndTime:
            if endDateTime <= dayEndTime:
                timeDiff += endDateTime - currentDateTime
                currentDateTime = endDateTime
                break
            else:
                timeDiff += dayEndTime - currentDateTime
                currentDateTime = dayStartTime + timedelta(days=1)

    return timeDiff


def stopTracking(issue):
    global progress

    if issue in progress.keys():
        timeStarted = datetime.fromtimestamp(progress[issue])
        timeNow = datetime.now()
        diffMinutes = calcTimeBetween(timeStarted, timeNow).seconds / 60
        if diffMinutes >= 1:
            jira.add_worklog(
                issue,
                timeSpent=str(diffMinutes) + "m",
                comment="Auto-logged by JIRA Issue Manager",
                started=timeStarted
                - datetime.now(pytz.timezone("Europe/Brussels")).utcoffset(),
            )

        with open(".jira_progress.json", "w+") as f:
            del progress[issue]
            json.dump(progress, f)


def getUserInfoForKey(userKey):
    userInfo = {}

    try:
        with open("cache/" + user + ".json", "r") as f:
            userInfo = json.load(f)

    except FileNotFoundError:
        rawUser = jira.user(user).raw

        try:
            os.mkdir("cache")
        except FileExistsError:
            pass

        with open("cache/" + user + ".json", "w+") as f:
            base64Content = base64.b64encode(
                requests.get(rawUser["avatarUrls"]["16x16"]).content
            ).decode("utf-8")

            userInfo = {"displayName": rawUser["displayName"], "avatar": base64Content}

            json.dump(userInfo, f)

    return userInfo


def getIssueList():
    return jira.search_issues(issueListFilter)


def addSeparator():
    print("---")


def addMenuItem(text, options=None):
    optionsText = ""
    if options:
        optionsText += "|"

        # Override defaults
        if "bash" in options:
            if "refresh" not in options:
                options["refresh"] = "true"
            if "terminal" not in options:
                options["terminal"] = "false"

        for key in options:
            optionsText += "%s=%s " % (key, options[key])
    print(text + optionsText)


def addSubMenuItem(text, options):
    addMenuItem("--" + text, options)


def addLinkToIssue(issue, subMenu=False):
    link = "%s/projects/%s/issues/%s" % (
        credentials["host"],
        issue.key.split("-")[0],
        issue.key,
    )
    addMenuItem(
        "%sShow issue in browser..." % ("", "--")[subMenu],
        {"href": link, "iconName": "application-exit"},
    )


def canTransitionTo(issue, transition):
    if str(issue) in allowedTransitions.keys():
        return transition in allowedTransitions[str(issue)]

    matchingTransitions = [
        (t["id"], t["name"]) for t in jira.transitions(issue) if t["name"] == transition
    ]

    return len(matchingTransitions) > 0


# MAIN PROGRAM START

if __name__ == "__main__":
    # COMMAND LINE INVOCATION

    if len(sys.argv) > 1:
        if len(sys.argv) == 2:
            if str(sys.argv[1]) == "users":
                print("Username\t(Display Name)")
                print("--------\t--------------")
                for user in jira.search_users("", maxResults=150):
                    print(user.key + "\t(%s)" % user.displayName)

            if str(sys.argv[1]) == "custom":

                window = Gtk.Window(title="Track other issue")
                window.set_border_width(20)

                vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                window.add(vbox)

                label = Gtk.Label(label="Enter issue key:")
                vbox.pack_start(label, True, True, 0)

                text = Gtk.Entry()
                vbox.pack_start(text, True, True, 0)

                button = Gtk.Button.new_with_label("Start tracking time")
                vbox.pack_start(button, True, True, 0)

                def start_progress(button):
                    startTracking(text.get_text())
                    exit(0)

                button.connect("clicked", start_progress)
                text.connect("activate", start_progress)

                window.set_position(Gtk.WindowPosition.CENTER)
                window.show_all()
                window.connect("destroy", Gtk.main_quit)
                Gtk.main()

        elif len(sys.argv) >= 4 and str(sys.argv[1]) == "transition":
            issue = sys.argv[2]
            transition = sys.argv[3]

            if transition == "Start progress":
                for issueToStop in list(progress.keys()):
                    if canTransitionTo(issueToStop, "Stop progress"):
                        jira.transition_issue(issueToStop, "Stop progress")

                startTracking(issue)

            elif transition == "Resolved" or transition == "Stop progress":
                stopTracking(issue)

            if canTransitionTo(issue, transition):
                if transition == "Resolved":
                    jira.transition_issue(
                        issue, transition, assignee={"name": sys.argv[4]}
                    )
                else:
                    jira.transition_issue(issue, transition)

        exit(0)

    trackingIssues = [jira.issue(ticket) for ticket in list(progress.keys())]
    ticketList = [ticket for ticket in getIssueList() if ticket not in trackingIssues]

    for ticket in ticketList:
        allowedTransitions[str(ticket)] = [
            transition["name"] for transition in jira.transitions(ticket)
        ]

    if len(trackingIssues) == 0:
        addMenuItem('💤  <span font_weight="normal">Not working...</span>')

        if len(ticketList) == 0:
            addSeparator()
            addMenuItem('Put issues in "Next" to make them appear in this list')

    elif len(trackingIssues) > 1:
        addMenuItem("You can only track one issue!")
        addMenuItem("Something went wrong 🤭")
        addSeparator()

    else:
        issue = trackingIssues[0]
        addMenuItem(
            "👨‍💻  "
            + issue.key
            + ' - <span font_weight="normal">'
            + issue.fields.summary
            + "</span>"
        )
        addSeparator()
        addMenuItem(
            "⏲ <i>Tracking started at "
            + datetime.fromtimestamp(progress[issue.key]).strftime("%H:%M")
            + "</i>"
        )
        addMenuItem("<b>" + issue.fields.summary + "</b>")
        if issue.fields.description:
            splitLines = issue.fields.description.splitlines()
            amountOfLines = len(splitLines)
            splitLines = splitLines[:20]

            if amountOfLines > 20:
                splitLines.append("...")

            addMenuItem("\n".join(splitLines))

        addMenuItem(
            "Stop progress",
            {
                "bash": "'%s transition %s \"Stop progress\"'"
                % (sys.argv[0], issue.key),
                "iconName": "media-playback-pause-symbolic",
            },
        )

        if canTransitionTo(issue, "Resolved"):
            addMenuItem(
                "Resolve and reassign for review",
                {"iconName": "document-properties-symbolic"},
            )
            for user in reviewers:
                userInfo = getUserInfoForKey(user)
                addSubMenuItem(
                    userInfo["displayName"],
                    {
                        "image": userInfo["avatar"],
                        "imageWidth": 16,
                        "imageHeight": 16,
                        "bash": "'%s transition %s \"Resolved\" %s'"
                        % (sys.argv[0], issue.key, user),
                    },
                )

        if canTransitionTo(issue, "Select"):
            addMenuItem(
                "Select",
                {
                    "iconName": "view-pin-symbolic",
                    "bash": "'%s transition %s \"Select\"'" % (sys.argv[0], issue.key),
                },
            )

        addLinkToIssue(issue)

    addSeparator()

    for issue in ticketList:
        addMenuItem("<b>%s</b>: %s" % (issue.key, issue.fields.summary))
        addSubMenuItem(
            ("Start tracking", "Start progress")[
                canTransitionTo(issue, "Start progress")
            ],
            {
                "bash": "'%s transition %s \"%s\"'"
                % (sys.argv[0], issue.key, "Start progress"),
                "iconName": "media-playback-start-symbolic",
            },
        )

        if canTransitionTo(issue, "Stop progress"):
            addSubMenuItem(
                "Stop progress",
                {
                    "bash": "'%s transition %s \"%s\"'"
                    % (sys.argv[0], issue.key, "Stop progress"),
                    "iconName": "media-playback-stop-symbolic",
                },
            )
        if canTransitionTo(issue, "Deselect"):
            addSubMenuItem(
                "Deselect",
                {
                    "bash": "'%s transition %s \"%s\"'"
                    % (sys.argv[0], issue.key, "Deselect"),
                    "iconName": "edit-clear-symbolic",
                },
            )

        addLinkToIssue(issue, subMenu=True)

    addMenuItem("Track other issue...", {"bash": "'%s custom'" % sys.argv[0]})

    addSeparator()

    addMenuItem(
        "Open JIRA",
        {
            "href": credentials["host"],
            "image": "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAMZJREFUOI2Vkj0OAUEAhb9IJOKn3PM5gEaCWqOROIIrKPWicAm9hEoidHyaXdaameUl00zevL8MpDEFZjWcKDL1ql6ALEZqJAT6QBvoAuO/7dWNbyRTxATOJQGB+T/vW+rDTwRTxDZ4BO66wKjOOQNWQE89+Y3aLeZ53yWwDggkt8jUS867A4uQQDVFeYNx3rO4bwKnyBZf/6LsXmAHTH5J8epewQHoqMe6LULuhQC/pAi5q25zgXQKda/eqgcYlCoOQxx1/wRTboLP64okfwAAAABJRU5ErkJggg==",
        },
    )
    addMenuItem("Refresh", {"bash": "", "iconName": "object-rotate-right-symbolic"})
