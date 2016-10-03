from django.utils.translation import ugettext as _


NARRATIVES = {
    u'management/zone/[^/]*/$': [
        {u'li.manage-tab.active': [
            {u'step': 1},
            {u'text':
                _(u'Welcome! This is the landing page for admins. If at any point you would like to navigate back to this page, click on this tab!')}
        ]},
        {u'li.facility': [
            {u'step': 2},
            {u'text':
                _(u'Clicking on this tab will show you a quick overview of all facilities and devices you have set up.')},
            {u'position': u'right'}
        ]},
        {u'div.col-xs-12': [
            {u'step': 3},
            {u'text': _(u'An overview of all facilities will be shown here')}
        ]},
        {u'a.create-facility': [
            {u'step': 4},
            {u'text': _(u'To add new facilities, click on this link.')}
        ]},
        {u'a.facility-name': [
            {u'step': 5},
            {u'text':
                _(u'To view more detailed information such as learner groups, learners, and coaches belonging to a facility, click on the facility name.')}
        ]},
        {u'#devices-table tbody tr td:nth-child(1)': [
            {u'step': 6},
            {u'text': _(u'Information on your device status will be shown here')}
        ]},
        {u'unattached': [
            {u'step': 7},
            {u'text':
                _(u'Any more questions? Be sure to consult the FAQ and Documentation!')}
        ]}
    ],
    u'update/languages': [
        {u'li.languages.active': [
            {u'step': 1},
            {u'text':
                _(u'Selecting the "Language" tab will take you to the place where you can download or update language packs!')}
        ]},
        {u'#language-packs-selection': [
            {u'step': 2},
            {u'text':
                _(u'Click on this drop down menu to view the available language packs...')}
        ]},
        {u'#language-packs-ul li': [
            {u'step': 3},
            {u'text': _(u'...select the language of your choice...')},
            {u'before-showing': [{u'click': u'#language-packs-selection'}]}
        ]},
        {u'#langpack-details': [
            {u'step': 4},
            {u'text':
                _(u'...and details such as the number of subtitles, translation completion, and total download size will be displayed for the chosen language pack!')},
            {u'before-showing': [{u'click': u'#language-packs-ul li'}]}
        ]},
        {u'#get-language-button': [
            {u'step': 5},
            {u'text': _(u'Just click this button to start your download!')}
        ]},
        {u'#installed-languages-div': [
            {u'step': 6},
            {u'text':
                _(u'Any language packs already installed on your device will be shown in this section')}
        ]}
    ],
    u'update/videos': [
        {u'li.video.active': [
            {u'step': 1},
            {u'text':
                _(u'Selecting this "Videos" tab will lead you to the place where you can download new videos for all topics!')}
        ]},
        {u'#content_tree': [
            {u'step': 2},
            {u'text':
                _(u'Downloadable content will be organized in this topic tree.')}
        ]},
        {u'.fancytree-node': [
            {u'step': 3},
            {u'text':
                _(u'Simply toggle topic button to view see more subtopics.')}
        ]}
    ]
}