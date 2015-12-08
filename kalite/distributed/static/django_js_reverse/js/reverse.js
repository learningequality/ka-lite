this.Urls = (function () {

    var Urls = {};

    var self = {
        url_patterns:{}
    };

    var _get_url = function (url_pattern) {
        return function () {
            var index, url, url_arg, url_args, _i, _len, _ref, _ref_list;
            _ref_list = self.url_patterns[url_pattern];
            for (_i = 0;
                 _ref = _ref_list[_i], _ref[1].length != arguments.length;
                 _i++);

            url = _ref[0], url_args = _ref[1];
            for (index = _i = 0, _len = url_args.length; _i < _len; index = ++_i) {
                url_arg = url_args[index];
                url = url.replace("%(" + url_arg + ")s", arguments[index] || '');
            }
            return '/' + url;
        };
    };

    var name, pattern, self, url_patterns, _i, _len, _ref;
    url_patterns = [
        
            [
                'account_management',
                [
                    
                    [
                        'management/account/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'add_facility',
                [
                    
                    [
                        'management/zone/%(zone_id)s/facility/new/',
                        [
                            
                            'zone_id',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'add_facility_student',
                [
                    
                    [
                        'securesync/student/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'add_facility_teacher',
                [
                    
                    [
                        'securesync/teacher/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'add_group',
                [
                    
                    [
                        'securesync/group/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:app_list',
                [
                    
                    [
                        'admin/%(app_label)s/',
                        [
                            
                            'app_label',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:auth_group_add',
                [
                    
                    [
                        'admin/auth/group/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:auth_group_change',
                [
                    
                    [
                        'admin/auth/group/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:auth_group_changelist',
                [
                    
                    [
                        'admin/auth/group/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:auth_group_delete',
                [
                    
                    [
                        'admin/auth/group/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:auth_group_history',
                [
                    
                    [
                        'admin/auth/group/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:auth_user_add',
                [
                    
                    [
                        'admin/auth/user/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:auth_user_change',
                [
                    
                    [
                        'admin/auth/user/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:auth_user_changelist',
                [
                    
                    [
                        'admin/auth/user/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:auth_user_delete',
                [
                    
                    [
                        'admin/auth/user/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:auth_user_history',
                [
                    
                    [
                        'admin/auth/user/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:chronograph_job_add',
                [
                    
                    [
                        'admin/chronograph/job/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:chronograph_job_change',
                [
                    
                    [
                        'admin/chronograph/job/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:chronograph_job_changelist',
                [
                    
                    [
                        'admin/chronograph/job/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:chronograph_job_delete',
                [
                    
                    [
                        'admin/chronograph/job/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:chronograph_job_history',
                [
                    
                    [
                        'admin/chronograph/job/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:chronograph_job_run',
                [
                    
                    [
                        'admin/chronograph/job/%(_0)s/run/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:chronograph_log_add',
                [
                    
                    [
                        'admin/chronograph/log/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:chronograph_log_change',
                [
                    
                    [
                        'admin/chronograph/log/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:chronograph_log_changelist',
                [
                    
                    [
                        'admin/chronograph/log/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:chronograph_log_delete',
                [
                    
                    [
                        'admin/chronograph/log/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:chronograph_log_history',
                [
                    
                    [
                        'admin/chronograph/log/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:config_settings_add',
                [
                    
                    [
                        'admin/config/settings/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:config_settings_change',
                [
                    
                    [
                        'admin/config/settings/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:config_settings_changelist',
                [
                    
                    [
                        'admin/config/settings/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:config_settings_delete',
                [
                    
                    [
                        'admin/config/settings/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:config_settings_history',
                [
                    
                    [
                        'admin/config/settings/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:index',
                [
                    
                    [
                        'admin/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:jsi18n',
                [
                    
                    [
                        'admin/jsi18n/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:logout',
                [
                    
                    [
                        'admin/logout/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_attemptlog_add',
                [
                    
                    [
                        'admin/main/attemptlog/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_attemptlog_change',
                [
                    
                    [
                        'admin/main/attemptlog/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_attemptlog_changelist',
                [
                    
                    [
                        'admin/main/attemptlog/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_attemptlog_delete',
                [
                    
                    [
                        'admin/main/attemptlog/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_attemptlog_history',
                [
                    
                    [
                        'admin/main/attemptlog/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_contentlog_add',
                [
                    
                    [
                        'admin/main/contentlog/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_contentlog_change',
                [
                    
                    [
                        'admin/main/contentlog/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_contentlog_changelist',
                [
                    
                    [
                        'admin/main/contentlog/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_contentlog_delete',
                [
                    
                    [
                        'admin/main/contentlog/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_contentlog_history',
                [
                    
                    [
                        'admin/main/contentlog/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_exerciselog_add',
                [
                    
                    [
                        'admin/main/exerciselog/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_exerciselog_change',
                [
                    
                    [
                        'admin/main/exerciselog/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_exerciselog_changelist',
                [
                    
                    [
                        'admin/main/exerciselog/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_exerciselog_delete',
                [
                    
                    [
                        'admin/main/exerciselog/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_exerciselog_history',
                [
                    
                    [
                        'admin/main/exerciselog/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_userlog_add',
                [
                    
                    [
                        'admin/main/userlog/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_userlog_change',
                [
                    
                    [
                        'admin/main/userlog/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_userlog_changelist',
                [
                    
                    [
                        'admin/main/userlog/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_userlog_delete',
                [
                    
                    [
                        'admin/main/userlog/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_userlog_history',
                [
                    
                    [
                        'admin/main/userlog/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_userlogsummary_add',
                [
                    
                    [
                        'admin/main/userlogsummary/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_userlogsummary_change',
                [
                    
                    [
                        'admin/main/userlogsummary/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_userlogsummary_changelist',
                [
                    
                    [
                        'admin/main/userlogsummary/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_userlogsummary_delete',
                [
                    
                    [
                        'admin/main/userlogsummary/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_userlogsummary_history',
                [
                    
                    [
                        'admin/main/userlogsummary/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_videolog_add',
                [
                    
                    [
                        'admin/main/videolog/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_videolog_change',
                [
                    
                    [
                        'admin/main/videolog/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_videolog_changelist',
                [
                    
                    [
                        'admin/main/videolog/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_videolog_delete',
                [
                    
                    [
                        'admin/main/videolog/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:main_videolog_history',
                [
                    
                    [
                        'admin/main/videolog/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:password_change',
                [
                    
                    [
                        'admin/password_change/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:password_change_done',
                [
                    
                    [
                        'admin/password_change/done/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_cachedpassword_add',
                [
                    
                    [
                        'admin/securesync/cachedpassword/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_cachedpassword_change',
                [
                    
                    [
                        'admin/securesync/cachedpassword/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_cachedpassword_changelist',
                [
                    
                    [
                        'admin/securesync/cachedpassword/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_cachedpassword_delete',
                [
                    
                    [
                        'admin/securesync/cachedpassword/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_cachedpassword_history',
                [
                    
                    [
                        'admin/securesync/cachedpassword/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_device_add',
                [
                    
                    [
                        'admin/securesync/device/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_device_change',
                [
                    
                    [
                        'admin/securesync/device/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_device_changelist',
                [
                    
                    [
                        'admin/securesync/device/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_device_delete',
                [
                    
                    [
                        'admin/securesync/device/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_device_history',
                [
                    
                    [
                        'admin/securesync/device/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_devicemetadata_add',
                [
                    
                    [
                        'admin/securesync/devicemetadata/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_devicemetadata_change',
                [
                    
                    [
                        'admin/securesync/devicemetadata/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_devicemetadata_changelist',
                [
                    
                    [
                        'admin/securesync/devicemetadata/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_devicemetadata_delete',
                [
                    
                    [
                        'admin/securesync/devicemetadata/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_devicemetadata_history',
                [
                    
                    [
                        'admin/securesync/devicemetadata/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_devicezone_add',
                [
                    
                    [
                        'admin/securesync/devicezone/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_devicezone_change',
                [
                    
                    [
                        'admin/securesync/devicezone/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_devicezone_changelist',
                [
                    
                    [
                        'admin/securesync/devicezone/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_devicezone_delete',
                [
                    
                    [
                        'admin/securesync/devicezone/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_devicezone_history',
                [
                    
                    [
                        'admin/securesync/devicezone/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_facility_add',
                [
                    
                    [
                        'admin/securesync/facility/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_facility_change',
                [
                    
                    [
                        'admin/securesync/facility/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_facility_changelist',
                [
                    
                    [
                        'admin/securesync/facility/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_facility_delete',
                [
                    
                    [
                        'admin/securesync/facility/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_facility_history',
                [
                    
                    [
                        'admin/securesync/facility/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_facilitygroup_add',
                [
                    
                    [
                        'admin/securesync/facilitygroup/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_facilitygroup_change',
                [
                    
                    [
                        'admin/securesync/facilitygroup/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_facilitygroup_changelist',
                [
                    
                    [
                        'admin/securesync/facilitygroup/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_facilitygroup_delete',
                [
                    
                    [
                        'admin/securesync/facilitygroup/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_facilitygroup_history',
                [
                    
                    [
                        'admin/securesync/facilitygroup/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_facilityuser_add',
                [
                    
                    [
                        'admin/securesync/facilityuser/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_facilityuser_change',
                [
                    
                    [
                        'admin/securesync/facilityuser/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_facilityuser_changelist',
                [
                    
                    [
                        'admin/securesync/facilityuser/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_facilityuser_delete',
                [
                    
                    [
                        'admin/securesync/facilityuser/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_facilityuser_history',
                [
                    
                    [
                        'admin/securesync/facilityuser/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_importpurgatory_add',
                [
                    
                    [
                        'admin/securesync/importpurgatory/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_importpurgatory_change',
                [
                    
                    [
                        'admin/securesync/importpurgatory/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_importpurgatory_changelist',
                [
                    
                    [
                        'admin/securesync/importpurgatory/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_importpurgatory_delete',
                [
                    
                    [
                        'admin/securesync/importpurgatory/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_importpurgatory_history',
                [
                    
                    [
                        'admin/securesync/importpurgatory/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_registereddevicepublickey_add',
                [
                    
                    [
                        'admin/securesync/registereddevicepublickey/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_registereddevicepublickey_change',
                [
                    
                    [
                        'admin/securesync/registereddevicepublickey/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_registereddevicepublickey_changelist',
                [
                    
                    [
                        'admin/securesync/registereddevicepublickey/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_registereddevicepublickey_delete',
                [
                    
                    [
                        'admin/securesync/registereddevicepublickey/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_registereddevicepublickey_history',
                [
                    
                    [
                        'admin/securesync/registereddevicepublickey/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_syncsession_add',
                [
                    
                    [
                        'admin/securesync/syncsession/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_syncsession_change',
                [
                    
                    [
                        'admin/securesync/syncsession/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_syncsession_changelist',
                [
                    
                    [
                        'admin/securesync/syncsession/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_syncsession_delete',
                [
                    
                    [
                        'admin/securesync/syncsession/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_syncsession_history',
                [
                    
                    [
                        'admin/securesync/syncsession/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_zone_add',
                [
                    
                    [
                        'admin/securesync/zone/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_zone_change',
                [
                    
                    [
                        'admin/securesync/zone/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_zone_changelist',
                [
                    
                    [
                        'admin/securesync/zone/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_zone_delete',
                [
                    
                    [
                        'admin/securesync/zone/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:securesync_zone_history',
                [
                    
                    [
                        'admin/securesync/zone/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:tastypie_apikey_add',
                [
                    
                    [
                        'admin/tastypie/apikey/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:tastypie_apikey_change',
                [
                    
                    [
                        'admin/tastypie/apikey/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:tastypie_apikey_changelist',
                [
                    
                    [
                        'admin/tastypie/apikey/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:tastypie_apikey_delete',
                [
                    
                    [
                        'admin/tastypie/apikey/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:tastypie_apikey_history',
                [
                    
                    [
                        'admin/tastypie/apikey/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:updates_updateprogresslog_add',
                [
                    
                    [
                        'admin/updates/updateprogresslog/add/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:updates_updateprogresslog_change',
                [
                    
                    [
                        'admin/updates/updateprogresslog/%(_0)s/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:updates_updateprogresslog_changelist',
                [
                    
                    [
                        'admin/updates/updateprogresslog/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:updates_updateprogresslog_delete',
                [
                    
                    [
                        'admin/updates/updateprogresslog/%(_0)s/delete/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:updates_updateprogresslog_history',
                [
                    
                    [
                        'admin/updates/updateprogresslog/%(_0)s/history/',
                        [
                            
                            '_0',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'admin:view_on_site',
                [
                    
                    [
                        'admin/r/%(content_type_id)s/%(object_id)s/',
                        [
                            
                            'content_type_id',
                            
                            'object_id',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'aggregate_learner_logs',
                [
                    
                    [
                        'api/coachreports/summary/',
                        [
                            
                        ],
                    ],
                    
                    [
                        'coachreports/api/summary/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'api_dispatch_detail',
                [
                    
                    [
                        'api/coachreports/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'api/coachreports/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/%(id)s/',
                        [
                            
                            'resource_name',
                            
                            'id',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'coachreports/api/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'coachreports/api/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'securesync/api/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ],
                    ],
                    
                    [
                        'securesync/api/%(resource_name)s/%(pk)s/',
                        [
                            
                            'resource_name',
                            
                            'pk',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'api_dispatch_list',
                [
                    
                    [
                        'api/coachreports/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/coachreports/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'coachreports/api/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'coachreports/api/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'securesync/api/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'securesync/api/%(resource_name)s/',
                        [
                            
                            'resource_name',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'api_force_sync',
                [
                    
                    [
                        'securesync/api/force_sync',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'api_get_multiple',
                [
                    
                    [
                        'api/coachreports/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'api/coachreports/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'coachreports/api/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'coachreports/api/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'securesync/api/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ],
                    ],
                    
                    [
                        'securesync/api/%(resource_name)s/set/%(pk_list)s/',
                        [
                            
                            'resource_name',
                            
                            'pk_list',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'api_get_schema',
                [
                    
                    [
                        'api/coachreports/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/coachreports/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/control_panel/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'api/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'coachreports/api/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'coachreports/api/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'securesync/api/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ],
                    ],
                    
                    [
                        'securesync/api/%(resource_name)s/schema/',
                        [
                            
                            'resource_name',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'api_login',
                [
                    
                    [
                        'securesync/api/%(resource_name)s/login/',
                        [
                            
                            'resource_name',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'api_logout',
                [
                    
                    [
                        'securesync/api/%(resource_name)s/logout/',
                        [
                            
                            'resource_name',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'api_status',
                [
                    
                    [
                        'securesync/api/%(resource_name)s/status/',
                        [
                            
                            'resource_name',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'cancel_update_progress',
                [
                    
                    [
                        'api/updates/cancel',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'cancel_video_download',
                [
                    
                    [
                        'api/videos/cancel',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'check_update_progress',
                [
                    
                    [
                        'api/updates/progress',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'coach_reports',
                [
                    
                    [
                        'coachreports/coach/zone/%(zone_id)s',
                        [
                            
                            'zone_id',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'content_item',
                [
                    
                    [
                        'api/content/%(channel)s/%(content_id)s',
                        [
                            
                            'channel',
                            
                            'content_id',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'content_recommender',
                [
                    
                    [
                        'api/content_recommender',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'create_session',
                [
                    
                    [
                        'securesync/api/session/create',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'crypto_login',
                [
                    
                    [
                        'cryptologin/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'data_export',
                [
                    
                    [
                        'management/export/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'delete_language_pack',
                [
                    
                    [
                        'api/languagepacks/delete',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'delete_users',
                [
                    
                    [
                        'securesync/api/delete_users',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'delete_videos',
                [
                    
                    [
                        'api/videos/delete',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'destroy_session',
                [
                    
                    [
                        'securesync/api/session/destroy',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'device_counters',
                [
                    
                    [
                        'securesync/api/device/counters',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'device_download',
                [
                    
                    [
                        'securesync/api/device/download',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'device_management',
                [
                    
                    [
                        'management/zone/%(zone_id)s/device/%(device_id)s/',
                        [
                            
                            'zone_id',
                            
                            'device_id',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'device_redirect',
                [
                    
                    [
                        'management/device/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'dynamic_css',
                [
                    
                    [
                        '_generated/dynamic.css',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'dynamic_js',
                [
                    
                    [
                        '_generated/dynamic.js',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'edit_facility_user',
                [
                    
                    [
                        'securesync/user/%(facility_user_id)s/edit/',
                        [
                            
                            'facility_user_id',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'facility_delete',
                [
                    
                    [
                        'securesync/api/facility_delete/%(facility_id)s',
                        [
                            
                            'facility_id',
                            
                        ],
                    ],
                    
                    [
                        'securesync/api/facility_delete',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'facility_form',
                [
                    
                    [
                        'management/facility/%(facility_id)s/edit/',
                        [
                            
                            'facility_id',
                            
                        ],
                    ],
                    
                    [
                        'management/zone/%(zone_id)s/facility/%(facility_id)s/edit',
                        [
                            
                            'zone_id',
                            
                            'facility_id',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'facility_management',
                [
                    
                    [
                        'management/zone/%(zone_id)s/facility/%(facility_id)s/management/',
                        [
                            
                            'zone_id',
                            
                            'facility_id',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'facility_user_signup',
                [
                    
                    [
                        'securesync/signup/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'get_server_info',
                [
                    
                    [
                        'securesync/api/info',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'get_update_topic_tree',
                [
                    
                    [
                        'api/videos/topic_tree',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'getpid',
                [
                    
                    [
                        'api/cherrypy/getpid',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'group_delete',
                [
                    
                    [
                        'securesync/api/group_delete/%(group_id)s',
                        [
                            
                            'group_id',
                            
                        ],
                    ],
                    
                    [
                        'securesync/api/group_delete',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'group_edit',
                [
                    
                    [
                        'securesync/group/%(group_id)s/edit/',
                        [
                            
                            'group_id',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'group_management',
                [
                    
                    [
                        'management/zone/%(zone_id)s/facility/%(facility_id)s/management/group/%(group_id)s/',
                        [
                            
                            'zone_id',
                            
                            'facility_id',
                            
                            'group_id',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'help',
                [
                    
                    [
                        'help/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'homepage',
                [
                    
                    [
                        '',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'installed_language_packs',
                [
                    
                    [
                        'api/languagepacks/installed',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'learn',
                [
                    
                    [
                        'learn/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'learner_logs',
                [
                    
                    [
                        'api/coachreports/logs/',
                        [
                            
                        ],
                    ],
                    
                    [
                        'coachreports/api/logs/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'load_test',
                [
                    
                    [
                        'loadtesting/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'model_download',
                [
                    
                    [
                        'securesync/api/models/download',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'model_upload',
                [
                    
                    [
                        'securesync/api/models/upload',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'move_to_group',
                [
                    
                    [
                        'securesync/api/move_to_group',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'narrative',
                [
                    
                    [
                        'api/inline/narrative/%(narrative_id)s',
                        [
                            
                            'narrative_id',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'register_device',
                [
                    
                    [
                        'securesync/api/register',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'register_public_key',
                [
                    
                    [
                        'securesync/register/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'search',
                [
                    
                    [
                        'search/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'search_api',
                [
                    
                    [
                        'api/search/%(channel)s/',
                        [
                            
                            'channel',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'set_default_language',
                [
                    
                    [
                        'api/i18n/set_default_language/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'start_languagepack_download',
                [
                    
                    [
                        'api/languagepacks/start',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'start_update_kalite',
                [
                    
                    [
                        'api/software/start',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'start_video_download',
                [
                    
                    [
                        'api/videos/start',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'student_view',
                [
                    
                    [
                        'coachreports/student/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'test_connection',
                [
                    
                    [
                        'securesync/api/test',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'time_set',
                [
                    
                    [
                        'api/time_set/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'topic_tree',
                [
                    
                    [
                        'api/topic_tree/%(channel)s',
                        [
                            
                            'channel',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'update_all_distributed',
                [
                    
                    [
                        'api/contentload/update/distributed/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'update_all_distributed_callback',
                [
                    
                    [
                        'api/contentload/update/distributed_callback/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'update_languages',
                [
                    
                    [
                        'update/languages/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'update_videos',
                [
                    
                    [
                        'update/videos/',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'video_scan',
                [
                    
                    [
                        'api/videos/scan',
                        [
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'zone_form',
                [
                    
                    [
                        'management/zone/%(zone_id)s/edit',
                        [
                            
                            'zone_id',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'zone_management',
                [
                    
                    [
                        'management/zone/%(zone_id)s/',
                        [
                            
                            'zone_id',
                            
                        ]
                    ]
                    
                ],
            ],
        
            [
                'zone_redirect',
                [
                    
                    [
                        'management/zone/',
                        [
                            
                        ]
                    ]
                    
                ]
            ]
        
    ];
    self.url_patterns = {};
    for (_i = 0, _len = url_patterns.length; _i < _len; _i++) {
        _ref = url_patterns[_i], name = _ref[0], pattern = _ref[1];
        self.url_patterns[name] = pattern;
        Urls[name] = _get_url(name);
        Urls[name.replace(/-/g, '_')] = _get_url(name);
    }

    return Urls;
})();
