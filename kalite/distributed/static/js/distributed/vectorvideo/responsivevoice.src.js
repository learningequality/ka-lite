/**
 * @license ResponsiveVoice JS v1.4.5
 *
 * (c) 2015 LearnBrite
 *
 * License: http://responsivevoice.org/license
 */

if (typeof responsiveVoice != 'undefined') {
    console.log('ResponsiveVoice already loaded');
    console.log(responsiveVoice);
} else {

    var ResponsiveVoice = function () {

        var self = this;

        self.version = "1.4.5";
        console.log("ResponsiveVoice r" + self.version);

        // Our own collection of voices
        self.responsivevoices = [
            {name: 'UK English Female', flag: 'gb', gender: 'f', voiceIDs: [3, 5, 1, 6, 7, 171, 201, 8]},
            {name: 'UK English Male', flag: 'gb', gender: 'm', voiceIDs: [0, 4, 2, 75, 202, 159, 6, 7]},
            {name: 'US English Female', flag: 'us', gender: 'f', voiceIDs: [39, 40, 41, 42, 43, 173, 205, 204,44]},
            {name: 'Arabic Male', flag: 'ar', gender: 'm', voiceIDs: [96,95,97,196, 98]},
            {name: 'Armenian Male', flag: 'hy', gender: 'f', voiceIDs: [99]},
            {name: 'Australian Female', flag: 'au', gender: 'f', voiceIDs: [87,86,5,201,88]},
            {name: 'Brazilian Portuguese Female', flag: 'br', gender: 'f', voiceIDs: [124,123,125,186,223,126]},
            {name: 'Chinese Female', flag: 'cn', gender: 'f', voiceIDs: [58, 59, 60, 155, 191, 231,61]},
            {name: 'Czech Female', flag: 'cz', gender: 'f', voiceIDs: [101,100,102,197,103]},
            {name: 'Danish Female', flag: 'dk', gender: 'f', voiceIDs: [105,104,106,198,107]},
            {name: 'Deutsch Female', flag: 'de', gender: 'f', voiceIDs: [27, 28, 29, 30, 31, 78, 170,199, 32]},
            {name: 'Dutch Female', flag: 'nl', gender: 'f', voiceIDs: [219,84, 157,  158, 184,45]},
            {name: 'Finnish Female', flag: 'fi', gender: 'f', voiceIDs: [90,89,91,209,92]},
            {name: 'French Female', flag: 'fr', gender: 'f', voiceIDs: [21, 22, 23, 77, 178, 210,26]},
            {name: 'Greek Female', flag: 'gr', gender: 'f', voiceIDs: [62, 63, 80, 200,64]},
            {name: 'Hatian Creole Female', flag: 'ht', gender: 'f', voiceIDs: [109]},
            {name: 'Hindi Female', flag: 'hi', gender: 'f', voiceIDs: [66, 154, 179, 213,67]},
            {name: 'Hungarian Female', flag: 'hu', gender: 'f', voiceIDs: [9, 10, 81,214, 11]},
            {name: 'Indonesian Female', flag: 'id', gender: 'f', voiceIDs: [111,112,180,215,113]},
            {name: 'Italian Female', flag: 'it', gender: 'f', voiceIDs: [33, 34, 35, 36, 37, 79, 181, 216,38]},
            {name: 'Japanese Female', flag: 'jp', gender: 'f', voiceIDs: [50, 51, 52, 153, 182, 217,53]},
            {name: 'Korean Female', flag: 'kr', gender: 'f', voiceIDs: [54, 55, 56, 156, 183, 218,57]},
            {name: 'Latin Female', flag: 'va', gender: 'f', voiceIDs: [114]},
            {name: 'Norwegian Female', flag: 'no', gender: 'f', voiceIDs: [72, 73, 221,74]},
            {name: 'Polish Female', flag: 'pl', gender: 'f', voiceIDs: [120,119,121,185,222,122]},
            {name: 'Portuguese Female', flag: 'br', gender: 'f', voiceIDs: [128,127,129,187,224,130]},
            {name: 'Romanian Male', flag: 'ro', gender: 'm', voiceIDs: [151, 150, 152, 225,46]},
            {name: 'Russian Female', flag: 'ru', gender: 'f', voiceIDs: [47,48,83,188,226,49]},
            {name: 'Slovak Female', flag: 'sk', gender: 'f', voiceIDs: [133,132,134,227,135]},
            {name: 'Spanish Female', flag: 'es', gender: 'f', voiceIDs: [19, 16, 17, 18, 20, 76, 174, 207,15]},
            {name: 'Spanish Latin American Female', flag: 'es', gender: 'f', voiceIDs: [137,136,138,175,208,139]},
            {name: 'Swedish Female', flag: 'sv', gender: 'f', voiceIDs: [85, 148, 149, 228,65]},
            {name: 'Tamil Male', flag: 'hi', gender: 'm', voiceIDs: [141]},
            {name: 'Thai Female', flag: 'th', gender: 'f', voiceIDs: [143,142,144,189,229,145]},
            {name: 'Turkish Female', flag: 'tr', gender: 'f', voiceIDs: [69, 70, 82, 190, 230,71]},
            {name: 'Afrikaans Male', flag: 'af', gender: 'm', voiceIDs: [93]},
            {name: 'Albanian Male', flag: 'sq', gender: 'm', voiceIDs: [94]},
            {name: 'Bosnian Male', flag: 'bs', gender: 'm', voiceIDs: [14]},
            {name: 'Catalan Male', flag: 'catalonia', gender: 'm', voiceIDs: [68]},
            {name: 'Croatian Male', flag: 'hr', gender: 'm', voiceIDs: [13]},
            {name: 'Czech Male', flag: 'cz', gender: 'm', voiceIDs: [161]},	
            {name: 'Danish Male', flag: 'da', gender: 'm', voiceIDs: [162]},	
            {name: 'Esperanto Male', flag: 'eo', gender: 'm', voiceIDs: [108]},
            {name: 'Finnish Male', flag: 'fi', gender: 'm', voiceIDs: [160]},	
            {name: 'Greek Male', flag: 'gr', gender: 'm', voiceIDs: [163]},	
            {name: 'Hungarian Male', flag: 'hu', gender: 'm', voiceIDs: [164]},	
            {name: 'Icelandic Male', flag: 'is', gender: 'm', voiceIDs: [110]},
            {name: 'Latin Male', flag: 'va', gender: 'm', voiceIDs: [165]},	
            {name: 'Latvian Male', flag: 'lv', gender: 'm', voiceIDs: [115]},
            {name: 'Macedonian Male', flag: 'mk', gender: 'm', voiceIDs: [116]},
            {name: 'Moldavian Male', flag: 'md', gender: 'm', voiceIDs: [117]},
            {name: 'Montenegrin Male', flag: 'me', gender: 'm', voiceIDs: [118]},
            {name: 'Norwegian Male', flag: 'no', gender: 'm', voiceIDs: [166]},	
            {name: 'Serbian Male', flag: 'sr', gender: 'm', voiceIDs: [12]},
            {name: 'Serbo-Croatian Male', flag: 'hr', gender: 'm', voiceIDs: [131]},
            {name: 'Slovak Male', flag: 'sk', gender: 'm', voiceIDs: [167]},	
            {name: 'Swahili Male', flag: 'sw', gender: 'm', voiceIDs: [140]},
            {name: 'Swedish Male', flag: 'sv', gender: 'm', voiceIDs: [168]},
            {name: 'Vietnamese Male', flag: 'vi', gender: 'm', voiceIDs: [146]},
            {name: 'Welsh Male', flag: 'cy', gender: 'm', voiceIDs: [147]},
            {name: 'US English Male', flag: 'us', gender: 'm', voiceIDs: [0, 4, 2, 6, 7, 75, 159]},//[195,169]}, original service is (temporary?) down
            {name: 'Fallback UK Female', flag: 'gb', gender: 'f', voiceIDs: [8]}

        ];

        //All voices available on every system and device
        self.voicecollection = [
            {name: 'Google UK English Male'}, //0 male uk android/chrome
            {name: 'Agnes'}, //1 female us safari mac
            {name: 'Daniel Compact'}, //2 male us safari mac

            {name: 'Google UK English Female'}, //3 female uk android/chrome
            {name: 'en-GB', rate: 0.25, pitch: 1}, //4 male uk IOS
            {name: 'en-AU', rate: 0.25, pitch: 1}, //5 female english IOS
            
            {name: 'inglés Reino Unido'}, //6 spanish english android
            {name: 'English United Kingdom'}, //7 english english android
            {name: 'Fallback en-GB Female', lang: 'en-GB', fallbackvoice: true}, //8 fallback english female
            
            {name: 'Eszter Compact'}, //9 Hungarian mac 
            {name: 'hu-HU', rate: 0.4}, //10 Hungarian iOS
            {name: 'Fallback Hungarian', lang: 'hu', fallbackvoice: true, service: 'g2'}, //11 Hungarian fallback

            {name: 'Fallback Serbian', lang: 'sr', fallbackvoice: true}, //12 Serbian fallback

            {name: 'Fallback Croatian', lang: 'hr', fallbackvoice: true}, //13 Croatian fallback		

            {name: 'Fallback Bosnian', lang: 'bs', fallbackvoice: true}, //14 Bosnian fallback	

            {name: 'Fallback Spanish', lang: 'es', fallbackvoice: true}, //15 Spanish fallback						
            {name: 'Spanish Spain'}, //16 female es android/chrome		
            {name: 'español España'}, //17 female es android/chrome	
            {name: 'Diego Compact', rate: 0.3}, //18 male es mac
            {name: 'Google Español'}, //19 male es chrome				
            {name: 'es-ES', rate: 0.20}, //20 male es iOS

            {name: 'Google Français'}, //21 FR chrome				
            {name: 'French France'}, //22 android/chrome		
            {name: 'francés Francia'}, //23 android/chrome	
            {name: 'Virginie Compact', rate: 0.5}, //24 mac
            {name: 'fr-FR', rate: 0.25}, //25 iOS		
            {name: 'Fallback French', lang: 'fr', fallbackvoice: true}, //26 fallback								

            {name: 'Google Deutsch'}, //27 DE chrome				
            {name: 'German Germany'}, //28 android/chrome		
            {name: 'alemán Alemania'}, //29 android/chrome	
            {name: 'Yannick Compact', rate: 0.5}, //30 mac
            {name: 'de-DE', rate: 0.25}, //31 iOS		
            {name: 'Fallback Deutsch', lang: 'de', fallbackvoice: true}, //32 fallback			

            {name: 'Google Italiano'}, //33 IT chrome				
            {name: 'Italian Italy'}, //34 android/chrome		
            {name: 'italiano Italia'}, //35 android/chrome	
            {name: 'Paolo Compact', rate: 0.5}, //36 mac
            {name: 'it-IT', rate: 0.25}, //37 iOS		
            {name: 'Fallback Italian', lang: 'it', fallbackvoice: true}, //38 fallback								

            {name: 'Google US English', timerSpeed:1}, //39 EN chrome				
            {name: 'English United States'}, //40 android/chrome		
            {name: 'inglés Estados Unidos'}, //41 android/chrome	
            {name: 'Vicki'}, //42 mac
            {name: 'en-US', rate: 0.2, pitch: 1, timerSpeed:1.3}, //43 iOS		
            {name: 'Fallback English', lang: 'en-US', fallbackvoice: true, timerSpeed:0}, //44 fallback										
            {name: 'Fallback Dutch', lang: 'nl', fallbackvoice: true, timerSpeed:0}, //45 fallback

            {name: 'Fallback Romanian', lang: 'ro', fallbackvoice: true}, //46 Romanian Male fallback	

            {name: 'Milena Compact'}, //47 Russian mac 
            {name: 'ru-RU', rate: 0.25}, //48 iOS		
            {name: 'Fallback Russian', lang: 'ru', fallbackvoice: true}, //49 Russian fallback	

            {name: 'Google 日本人', timerSpeed:1}, //50 JP Chrome 
            {name: 'Kyoko Compact'}, //51 Japanese mac 
            {name: 'ja-JP', rate: 0.25}, //52 iOS		
            {name: 'Fallback Japanese', lang: 'ja', fallbackvoice: true}, //53 Japanese fallback	

            {name: 'Google 한국의', timerSpeed:1}, //54 KO Chrome 
            {name: 'Narae Compact'}, //55 Korean mac 
            {name: 'ko-KR', rate: 0.25}, //56 iOS		
            {name: 'Fallback Korean', lang: 'ko', fallbackvoice: true}, //57 Korean fallback	

            {name: 'Google 中国的', timerSpeed:1}, //58 CN Chrome 
            {name: 'Ting-Ting Compact'}, //59 Chinese mac 
            {name: 'zh-CN', rate: 0.25}, //60 iOS		
            {name: 'Fallback Chinese', lang: 'zh-CN', fallbackvoice: true}, //61 Chinese fallback	

            {name: 'Alexandros Compact'}, //62 Greek Male Mac 
            {name: 'el-GR', rate: 0.25}, //63 iOS		
            {name: 'Fallback Greek', lang: 'el', fallbackvoice: true, service: 'g2'}, //64 Greek Female fallback	

            {name: 'Fallback Swedish', lang: 'sv', fallbackvoice: true, service: 'g2'}, //65 Swedish Female fallback	

            {name: 'hi-IN', rate: 0.25}, //66 iOS		
            {name: 'Fallback Hindi', lang: 'hi', fallbackvoice: true}, //67 Hindi Female fallback	

            {name: 'Fallback Catalan', lang: 'ca', fallbackvoice: true}, //68 Catalan Male fallback	

            {name: 'Aylin Compact'}, //69 Turkish Female Mac 
            {name: 'tr-TR', rate: 0.25}, //70 iOS Turkish Female	
            {name: 'Fallback Turkish', lang: 'tr', fallbackvoice: true}, //71 Turkish Female fallback	

            {name: 'Stine Compact'}, //72 Norweigan Male Mac 

            {name: 'no-NO', rate: 0.25}, //73 iOS Female		
            {name: 'Fallback Norwegian', lang: 'no', fallbackvoice: true, service: 'g2'}, //74 Norwegian Female fallback
            
            {name: 'Daniel'}, //75 English UK male uk safari 8 mac	
            {name: 'Monica'}, //76 Spanish female es safari 8 mac
            {name: 'Amelie'}, //77 French Canadian female fr safari 8 mac
            {name: 'Anna'}, //78 female de safari 8 mac
            {name: 'Alice'}, //79 Italian female it safari 8 mac
            {name: 'Melina'}, //80 Greek female gr safari 8 mac
            {name: 'Mariska'}, //81 Hungarian female hu safari 8 mac
            {name: 'Yelda'}, //82 Turkish female tr safari 8 mac
            {name: 'Milena'}, //83 Russian female ru safari 8 mac

            //Gender Disparity
            {name: 'Xander'}, //84 Dutch female nl safari 8 mac
            {name: 'Alva'},  //85 Swedish female sv safari 8 mac

            // Gender Disparity
            {name: 'Lee Compact'}, //86 Australian Male Mac 
            {name: 'Karen'}, //87 Australian Female safari 8 mac 
            {name: 'Fallback Australian', lang: 'en-AU', fallbackvoice: true}, //88 Australian Female fallback	

            // Gender Disparity
            {name: 'Mikko Compact'}, //89 Finnish Male Mac 
            {name: 'Satu'}, //90 Finnish Female safari 8 mac 
            {name: 'fi-FI', rate: 0.25}, //91 iOS		
            {name: 'Fallback Finnish', lang: 'fi', fallbackvoice: true, service: 'g2'}, //92 Finnish Female fallback	

            {name: 'Fallback Afrikans', lang: 'af', fallbackvoice: true}, //93 Afrikans Male fallback	
 
            {name: 'Fallback Albanian', lang: 'sq', fallbackvoice: true}, //94 Albanian Male fallback	

            {name: 'Maged Compact'}, //95 Arabic Male Mac 
            {name: 'Tarik'}, //96 Arabic Male safari 8 mac 
            {name: 'ar-SA', rate: 0.25}, //97 iOS	
            {name: 'Fallback Arabic', lang: 'ar', fallbackvoice: true, service: 'g2'}, //98 Arabic Male fallback	

            {name: 'Fallback Armenian', lang: 'hy', fallbackvoice: true, service: 'g2'}, //99 Armenian Male fallback	

            {name: 'Zuzana Compact'}, //100 Czech Female Mac 
            {name: 'Zuzana'}, //101 Czech Female safari 8 mac 
            {name: 'cs-CZ', rate: 0.25}, //102 iOS	
            {name: 'Fallback Czech', lang: 'cs', fallbackvoice: true, service: 'g2'}, //103 Czech Female fallback	

            {name: 'Ida Compact'}, //104 Danish Female Mac 
            {name: 'Sara'}, //105 Danish Female safari 8 mac 
            {name: 'da-DK', rate: 0.25}, //106 iOS	
            {name: 'Fallback Danish', lang: 'da', fallbackvoice: true, service: 'g2'}, //107 Danish Female fallback	

            {name: 'Fallback Esperanto', lang: 'eo', fallbackvoice: true}, //108 Esperanto Male fallback	
 
            {name: 'Fallback Hatian Creole', lang: 'ht', fallbackvoice: true}, //109 Hatian Creole Female fallback	

            {name: 'Fallback Icelandic', lang: 'is', fallbackvoice: true}, //110 Icelandic Male fallback	

            {name: 'Damayanti'}, //111 Indonesian Female safari 8 mac 
            {name: 'id-ID', rate: 0.25}, //112 iOS		
            {name: 'Fallback Indonesian', lang: 'id', fallbackvoice: true}, //113 Indonesian Female fallback	

            {name: 'Fallback Latin', lang: 'la', fallbackvoice: true, service: 'g2'}, //114 Latin Female fallback	
            {name: 'Fallback Latvian', lang: 'lv', fallbackvoice: true}, //115 Latvian Male fallback	
            {name: 'Fallback Macedonian', lang: 'mk', fallbackvoice: true}, //116 Macedonian Male fallback	
            {name: 'Fallback Moldavian', lang: 'mo', fallbackvoice: true, service: 'g2'}, //117 Moldavian Male fallback	
            {name: 'Fallback Montenegrin', lang: 'sr-ME', fallbackvoice: true}, //118 Montenegrin Male fallback	

            {name: 'Agata Compact'}, //119 Polish Female Mac 
            {name: 'Zosia'}, //120 Polish Female safari 8 mac 
            {name: 'pl-PL', rate: 0.25}, //121 iOS		
            {name: 'Fallback Polish', lang: 'pl', fallbackvoice: true}, //122 Polish Female fallback	

            {name: 'Raquel Compact'}, //123 Brazilian Portugese Female Male Mac 
            {name: 'Luciana'}, //124 Brazilian Portugese Female safari 8 mac 
            {name: 'pt-BR', rate: 0.25}, //125 iOS		
            {name: 'Fallback Brazilian Portugese', lang: 'pt-BR', fallbackvoice: true, service: 'g2'}, //126 Brazilian Portugese Female fallback	

            {name: 'Joana Compact'}, //127 Portuguese Female Mac 
            {name: 'Joana'}, //128 Portuguese Female safari 8 mac 
            {name: 'pt-PT', rate: 0.25}, //129 iOS		
            {name: 'Fallback Portuguese', lang: 'pt-PT', fallbackvoice: true}, //130 Portuguese Female fallback	

            {name: 'Fallback Serbo-Croation', lang: 'sh', fallbackvoice: true, service: 'g2'}, //131 Serbo-Croation Male fallback	

            {name: 'Laura Compact'}, //132 Slovak Female Mac 
            {name: 'Laura'}, //133 Slovak Female safari 8 mac 
            {name: 'sk-SK', rate: 0.25}, //134 iOS		
            {name: 'Fallback Slovak', lang: 'sk', fallbackvoice: true, service: 'g2'}, //135 Slovak Female fallback	

            //Gender Disparity
            {name: 'Javier Compact'}, //136 Spanish (Latin American) Male Mac 
            {name: 'Paulina'}, //137 Spanish Mexican Female safari 8 mac 
            {name: 'es-MX', rate: 0.25}, //138 iOS		
            {name: 'Fallback Spanish (Latin American)', lang: 'es-419', fallbackvoice: true, service: 'g2'}, //139 Spanish (Latin American) Female fallback	

            {name: 'Fallback Swahili', lang: 'sw', fallbackvoice: true}, //140 Swahili Male fallback	

            {name: 'Fallback Tamil', lang: 'ta', fallbackvoice: true}, //141 Tamil Male fallback	

            {name: 'Narisa Compact'}, //142 Thai Female Mac 
            {name: 'Kanya'}, //143 Thai Female safari 8 mac 
            {name: 'th-TH', rate: 0.25}, //144 iOS		
            {name: 'Fallback Thai', lang: 'th', fallbackvoice: true}, //145 Thai Female fallback	

            {name: 'Fallback Vietnamese', lang: 'vi', fallbackvoice: true}, //146 Vietnamese Male fallback	

            {name: 'Fallback Welsh', lang: 'cy', fallbackvoice: true}, //147 Welsh Male fallback	

            // Gender Disparity
            {name: 'Oskar Compact'}, //148 Swedish Male Mac 
            {name: 'sv-SE', rate: 0.25}, //149 iOS	

            // Gender Disparity
            {name: 'Simona Compact'}, //150 Romanian mac female
            {name: 'Ioana'}, //151 Romanian Female safari 8 mac
            {name: 'ro-RO', rate: 0.25}, //152 iOS female

            {name: 'Kyoko'}, //153 Japanese Female safari 8 mac 

            {name: 'Lekha'}, //154 Hindi Female safari 8 mac 

            {name: 'Ting-Ting'}, //155 Chinese Female safari 8 mac 

            {name: 'Yuna'}, //156 Korean Female safari 8 mac 

            // Gender Disparity
            {name: 'Xander Compact'}, //157 Dutch male or female nl safari 8 mac
            {name: 'nl-NL', rate: 0.25}, //158 iOS		

            {name: 'Fallback UK English Male', lang: 'en-GB', fallbackvoice: true, service: 'g1', voicename: 'rjs'}, //159 UK Male fallback	

            {name: 'Finnish Male', lang: 'fi', fallbackvoice: true, service: 'g1', voicename: ''}, //160 Finnish Male fallback	

            {name: 'Czech Male', lang: 'cs', fallbackvoice: true, service: 'g1', voicename: ''}, //161 Czech Male fallback	

            {name: 'Danish Male', lang: 'da', fallbackvoice: true, service: 'g1', voicename: ''}, //162 Danish Male fallback	

            {name: 'Greek Male', lang: 'el', fallbackvoice: true, service: 'g1', voicename: '', rate: 0.25}, //163 Greek Male fallback	

            {name: 'Hungarian Male', lang: 'hu', fallbackvoice: true, service: 'g1', voicename: ''}, //164 Hungarian Male fallback	

            {name: 'Latin Male', lang: 'la', fallbackvoice: true, service: 'g1', voicename: ''}, //165 Latin Male fallback	

            {name: 'Norwegian Male', lang: 'no', fallbackvoice: true, service: 'g1', voicename: ''}, //166 Norwegian Male fallback	

            {name: 'Slovak Male', lang: 'sk', fallbackvoice: true, service: 'g1', voicename: ''}, //167 Slovak Male fallback	

            {name: 'Swedish Male', lang: 'sv', fallbackvoice: true, service: 'g1', voicename: ''}, //168 Swedish Male fallback
	
            {name: 'Fallback US English Male', lang: 'en', fallbackvoice: true, service: 'tts-api', voicename: ''}, //169 US English Male fallback

            {name: 'German Germany', lang: 'de_DE'}, //170 Android 5 German Female
            {name: 'English United Kingdom', lang: 'en_GB'}, //171 Android 5 English United Kingdom Female
            {name: 'English India', lang: 'en_IN'}, //172 Android 5 English India Female
            {name: 'English United States', lang: 'en_US'}, //173 Android 5 English United States Female
            {name: 'Spanish Spain', lang: 'es_ES'}, //174 Android 5 Spanish Female
            {name: 'Spanish Mexico', lang: 'es_MX'}, //175 Android 5 Spanish Mexico Female
            {name: 'Spanish United States', lang: 'es_US'}, //176 Android 5 Spanish Mexico Female
            {name: 'French Belgium', lang: 'fr_BE'}, //177 Android 5 French Belgium Female
            {name: 'French France', lang: 'fr_FR'}, //178 Android 5 French France Female
            {name: 'Hindi India', lang: 'hi_IN'}, //179 Android 5 Hindi India Female
            {name: 'Indonesian Indonesia', lang: 'in_ID'}, //180 Android 5 Indonesian Female
            {name: 'Italian Italy', lang: 'it_IT'}, //181 Android 5 Italian Female
            {name: 'Japanese Japan', lang: 'ja_JP'}, //182 Android 5 Japanese Female
            {name: 'Korean South Korea', lang: 'ko_KR'}, //183 Android 5 Japanese Female
            {name: 'Dutch Netherlands', lang: 'nl_NL'}, //184 Android 5 Dutch Female
            {name: 'Polish Poland', lang: 'pl_PL'}, //185 Android 5 Polish Female
            {name: 'Portuguese Brazil', lang: 'pt_BR'}, //186 Android 5 Portuguese Brazil Female
            {name: 'Portuguese Portugal', lang: 'pt_PT'}, //187 Android 5 Portuguese Portugal Female
            {name: 'Russian Russia', lang: 'ru_RU'}, //188 Android 5 Russian Female
            {name: 'Thai Thailand', lang: 'th_TH'}, //189 Android 5 Thai Female
            {name: 'Turkish Turkey', lang: 'tr_TR'}, //190 Android 5 Turkish Female
            {name: 'Chinese China', lang: 'zh_CN_#Hans'}, //191 Android 5 Chinese China Female
            {name: 'Chinese Hong Kong', lang: 'zh_HK_#Hans'}, //192 Android 5 Chinese Hong Kong Simplified Female
            {name: 'Chinese Hong Kong', lang: 'zh_HK_#Hant'}, //193 Android 5 Chinese Hong Kong Traditional Female
            {name: 'Chinese Taiwan', lang: 'zh_TW_#Hant'}, //194 Android 5 Chinese Taiwan Female

            {name: 'Alex'}, //195 US English Male safari 8 mac

            {name: 'Maged', lang: 'ar-SA'}, //196 iOS 9 Arabic Female
            {name: 'Zuzana', lang: 'cs-CZ'}, //197 iOS 9 Czech Female
            {name: 'Sara', lang: 'da-DK'}, //198 iOS 9 Danish Female
            {name: 'Anna', lang: 'de-DE'}, //199 iOS 9 Deutsch Female
            {name: 'Melina', lang: 'el-GR'}, //200 iOS 9 Greek Female
            {name: 'Karen', lang: 'en-AU'}, //201 iOS 9 English (AU) Female
            {name: 'Daniel', lang: 'en-GB'}, //202 iOS 9 English (GB) Male
            {name: 'Moira', lang: 'en-IE'}, //203 iOS 9 English (IE) Female
            {name: 'Samantha (Enhanced)', lang: 'en-US'}, //204 iOS 9 English (US) Female
            {name: 'Samantha', lang: 'en-US'}, //205 iOS 9 English (US) Female
            {name: 'Tessa', lang: 'en-ZA'}, //206 iOS 9 English Female
            {name: 'Monica', lang: 'es-ES'}, //207 iOS 9 Spanish Female
            {name: 'Paulina', lang: 'es-MX'}, //208 iOS 9 Spanish Latin American Female
            {name: 'Satu', lang: 'fi-FI'}, //209 iOS 9 Finnish Female
            {name: 'Amelie', lang: 'fr-CA'}, //210 iOS 9 French (CA) Female
            {name: 'Thomas', lang: 'fr-FR'}, //211 iOS 9 French (FR) Male
            {name: 'Carmit', lang: 'he-IL'}, //212 iOS 9 Hebrew Female
            {name: 'Lekha', lang: 'hi-IN'}, //213 iOS 9 Hindi Female
            {name: 'Mariska', lang: 'hu-HU'}, //214 iOS 9 Hungarian Female
            {name: 'Damayanti', lang: 'id-ID'}, //215 iOS 9 Indonesian Female
            {name: 'Alice', lang: 'it-IT'}, //216 iOS 9 Italian Female
            {name: 'Kyoko', lang: 'ja-JP'}, //217 iOS 9 Japanese Female
            {name: 'Yuna', lang: 'ko-KR'}, //218 iOS 9 Korean Female
            {name: 'Ellen', lang: 'nl-BE'}, //219 iOS 9 Dutch Female
            {name: 'Xander', lang: 'nl-NL'}, //220 iOS 9 Dutch Male
            {name: 'Nora', lang: 'no-NO'}, //221 iOS 9 Norwegian Female
            {name: 'Zosia', lang: 'pl-PL'}, //222 iOS 9 Polish Female
            {name: 'Luciana', lang: 'pt-BR'}, //223 iOS 9 Portuguese (BR) Female
            {name: 'Joana', lang: 'pt-PT'}, //224 iOS 9 Portuguese (PT) Female
            {name: 'Ioana', lang: 'ro-RO'}, //225 iOS 9 Romanian Female
            {name: 'Milena', lang: 'ru-RU'}, //226 iOS 9 Russian Female
            {name: 'Laura', lang: 'sk-SK'}, //227 iOS 9 Slovak Female
            {name: 'Alva', lang: 'sv-SE'}, //228 iOS 9 Swedish Female
            {name: 'Kanya', lang: 'th-TH'}, //229 iOS 9 Thai Female
            {name: 'Yelda', lang: 'tr-TR'}, //230 iOS 9 Turkish Female
            {name: 'Ting-Ting', lang: 'zh-CN'}, //231 iOS 9 Chinese (PRC) Female
            {name: 'Sin-Ji', lang: 'zh-HK'}, //232 iOS 9 Chinese (Hong Kong SAR) Female
            {name: 'Mei-Jia', lang: 'zh-TW'} //233 iOS 9 Chinese (Taiwan) Female

        ];
        
        self.iOS = /(iPad|iPhone|iPod)/g.test( navigator.userAgent );
        self.iOS9  = /(iphone|ipod|ipad).* os 9_/.test(navigator.userAgent.toLowerCase());
        self.is_chrome = navigator.userAgent.indexOf('Chrome') > -1;
        self.is_safari = navigator.userAgent.indexOf("Safari") > -1;
        if ((self.is_chrome)&&(self.is_safari)) {self.is_safari=false;}
        self.is_opera = !!window.opera || navigator.userAgent.indexOf(' OPR/') >= 0;
        
        
        self.iOS_initialized = false;
        
        
        //Fallback cache voices
        self.cache_ios_voices = [{"name":"he-IL","voiceURI":"he-IL","lang":"he-IL"},{"name":"th-TH","voiceURI":"th-TH","lang":"th-TH"},{"name":"pt-BR","voiceURI":"pt-BR","lang":"pt-BR"},{"name":"sk-SK","voiceURI":"sk-SK","lang":"sk-SK"},{"name":"fr-CA","voiceURI":"fr-CA","lang":"fr-CA"},{"name":"ro-RO","voiceURI":"ro-RO","lang":"ro-RO"},{"name":"no-NO","voiceURI":"no-NO","lang":"no-NO"},{"name":"fi-FI","voiceURI":"fi-FI","lang":"fi-FI"},{"name":"pl-PL","voiceURI":"pl-PL","lang":"pl-PL"},{"name":"de-DE","voiceURI":"de-DE","lang":"de-DE"},{"name":"nl-NL","voiceURI":"nl-NL","lang":"nl-NL"},{"name":"id-ID","voiceURI":"id-ID","lang":"id-ID"},{"name":"tr-TR","voiceURI":"tr-TR","lang":"tr-TR"},{"name":"it-IT","voiceURI":"it-IT","lang":"it-IT"},{"name":"pt-PT","voiceURI":"pt-PT","lang":"pt-PT"},{"name":"fr-FR","voiceURI":"fr-FR","lang":"fr-FR"},{"name":"ru-RU","voiceURI":"ru-RU","lang":"ru-RU"},{"name":"es-MX","voiceURI":"es-MX","lang":"es-MX"},{"name":"zh-HK","voiceURI":"zh-HK","lang":"zh-HK"},{"name":"sv-SE","voiceURI":"sv-SE","lang":"sv-SE"},{"name":"hu-HU","voiceURI":"hu-HU","lang":"hu-HU"},{"name":"zh-TW","voiceURI":"zh-TW","lang":"zh-TW"},{"name":"es-ES","voiceURI":"es-ES","lang":"es-ES"},{"name":"zh-CN","voiceURI":"zh-CN","lang":"zh-CN"},{"name":"nl-BE","voiceURI":"nl-BE","lang":"nl-BE"},{"name":"en-GB","voiceURI":"en-GB","lang":"en-GB"},{"name":"ar-SA","voiceURI":"ar-SA","lang":"ar-SA"},{"name":"ko-KR","voiceURI":"ko-KR","lang":"ko-KR"},{"name":"cs-CZ","voiceURI":"cs-CZ","lang":"cs-CZ"},{"name":"en-ZA","voiceURI":"en-ZA","lang":"en-ZA"},{"name":"en-AU","voiceURI":"en-AU","lang":"en-AU"},{"name":"da-DK","voiceURI":"da-DK","lang":"da-DK"},{"name":"en-US","voiceURI":"en-US","lang":"en-US"},{"name":"en-IE","voiceURI":"en-IE","lang":"en-IE"},{"name":"hi-IN","voiceURI":"hi-IN","lang":"hi-IN"},{"name":"el-GR","voiceURI":"el-GR","lang":"el-GR"},{"name":"ja-JP","voiceURI":"ja-JP","lang":"ja-JP"}];
        self.cache_ios9_voices = [{name:"Maged",voiceURI:"com.apple.ttsbundle.Maged-compact",lang:"ar-SA",localService:!0,"default":!0},{name:"Zuzana",voiceURI:"com.apple.ttsbundle.Zuzana-compact",lang:"cs-CZ",localService:!0,"default":!0},{name:"Sara",voiceURI:"com.apple.ttsbundle.Sara-compact",lang:"da-DK",localService:!0,"default":!0},{name:"Anna",voiceURI:"com.apple.ttsbundle.Anna-compact",lang:"de-DE",localService:!0,"default":!0},{name:"Melina",voiceURI:"com.apple.ttsbundle.Melina-compact",lang:"el-GR",localService:!0,"default":!0},{name:"Karen",voiceURI:"com.apple.ttsbundle.Karen-compact",lang:"en-AU",localService:!0,"default":!0},{name:"Daniel",voiceURI:"com.apple.ttsbundle.Daniel-compact",lang:"en-GB",localService:!0,"default":!0},{name:"Moira",voiceURI:"com.apple.ttsbundle.Moira-compact",lang:"en-IE",localService:!0,"default":!0},{name:"Samantha (Enhanced)",voiceURI:"com.apple.ttsbundle.Samantha-premium",lang:"en-US",localService:!0,"default":!0},{name:"Samantha",voiceURI:"com.apple.ttsbundle.Samantha-compact",lang:"en-US",localService:!0,"default":!0},{name:"Tessa",voiceURI:"com.apple.ttsbundle.Tessa-compact",lang:"en-ZA",localService:!0,"default":!0},{name:"Monica",voiceURI:"com.apple.ttsbundle.Monica-compact",lang:"es-ES",localService:!0,"default":!0},{name:"Paulina",voiceURI:"com.apple.ttsbundle.Paulina-compact",lang:"es-MX",localService:!0,"default":!0},{name:"Satu",voiceURI:"com.apple.ttsbundle.Satu-compact",lang:"fi-FI",localService:!0,"default":!0},{name:"Amelie",voiceURI:"com.apple.ttsbundle.Amelie-compact",lang:"fr-CA",localService:!0,"default":!0},{name:"Thomas",voiceURI:"com.apple.ttsbundle.Thomas-compact",lang:"fr-FR",localService:!0,"default":!0},{name:"Carmit",voiceURI:"com.apple.ttsbundle.Carmit-compact",lang:"he-IL",localService:!0,"default":!0},{name:"Lekha",voiceURI:"com.apple.ttsbundle.Lekha-compact",lang:"hi-IN",localService:!0,"default":!0},{name:"Mariska",voiceURI:"com.apple.ttsbundle.Mariska-compact",lang:"hu-HU",localService:!0,"default":!0},{name:"Damayanti",voiceURI:"com.apple.ttsbundle.Damayanti-compact",lang:"id-ID",localService:!0,"default":!0},{name:"Alice",voiceURI:"com.apple.ttsbundle.Alice-compact",lang:"it-IT",localService:!0,"default":!0},{name:"Kyoko",voiceURI:"com.apple.ttsbundle.Kyoko-compact",lang:"ja-JP",localService:!0,"default":!0},{name:"Yuna",voiceURI:"com.apple.ttsbundle.Yuna-compact",lang:"ko-KR",localService:!0,"default":!0},{name:"Ellen",voiceURI:"com.apple.ttsbundle.Ellen-compact",lang:"nl-BE",localService:!0,"default":!0},{name:"Xander",voiceURI:"com.apple.ttsbundle.Xander-compact",lang:"nl-NL",localService:!0,"default":!0},{name:"Nora",voiceURI:"com.apple.ttsbundle.Nora-compact",lang:"no-NO",localService:!0,"default":!0},{name:"Zosia",voiceURI:"com.apple.ttsbundle.Zosia-compact",lang:"pl-PL",localService:!0,"default":!0},{name:"Luciana",voiceURI:"com.apple.ttsbundle.Luciana-compact",lang:"pt-BR",localService:!0,"default":!0},{name:"Joana",voiceURI:"com.apple.ttsbundle.Joana-compact",lang:"pt-PT",localService:!0,"default":!0},{name:"Ioana",voiceURI:"com.apple.ttsbundle.Ioana-compact",lang:"ro-RO",localService:!0,"default":!0},{name:"Milena",voiceURI:"com.apple.ttsbundle.Milena-compact",lang:"ru-RU",localService:!0,"default":!0},{name:"Laura",voiceURI:"com.apple.ttsbundle.Laura-compact",lang:"sk-SK",localService:!0,"default":!0},{name:"Alva",voiceURI:"com.apple.ttsbundle.Alva-compact",lang:"sv-SE",localService:!0,"default":!0},{name:"Kanya",voiceURI:"com.apple.ttsbundle.Kanya-compact",lang:"th-TH",localService:!0,"default":!0},{name:"Yelda",voiceURI:"com.apple.ttsbundle.Yelda-compact",lang:"tr-TR",localService:!0,"default":!0},{name:"Ting-Ting",voiceURI:"com.apple.ttsbundle.Ting-Ting-compact",lang:"zh-CN",localService:!0,"default":!0},{name:"Sin-Ji",voiceURI:"com.apple.ttsbundle.Sin-Ji-compact",lang:"zh-HK",localService:!0,"default":!0},{name:"Mei-Jia",voiceURI:"com.apple.ttsbundle.Mei-Jia-compact",lang:"zh-TW",localService:!0,"default":!0}];
        

        self.systemvoices = null;

        self.CHARACTER_LIMIT = 100;
        self.VOICESUPPORT_ATTEMPTLIMIT = 5;
        self.voicesupport_attempts = 0;
        self.fallbackMode = false;
        self.WORDS_PER_MINUTE = 130;

        
        self.fallback_parts = null;
        self.fallback_part_index = 0;
        self.fallback_audio = null;
        self.fallback_playbackrate = 1;
        self.def_fallback_playbackrate = self.fallback_playbackrate;
        self.fallback_audiopool = [];
        self.msgparameters = null;
        self.timeoutId = null;
        self.OnLoad_callbacks = [];
        self.useTimer = false;
        self.utterances = [];

        self.tstCompiled = function(xy) { xy = 0; return eval("typeof x" + "y === 'undefined'"); }  
        
        self.fallbackServicePath = 'https://code.responsivevoice.org/' + (self.tstCompiled()?'':'develop/') + 'getvoice.php';

        
        //onvoiceschanged Deprecated: Only works on chrome and introduces glitches.
        /*
        //Wait until system voices are ready and trigger the event OnVoiceReady
        if (typeof speechSynthesis != 'undefined') {
            speechSynthesis.onvoiceschanged = function () {
                
                self.systemvoices = window.speechSynthesis.getVoices();
                console.log("OnVoiceReady - from onvoiceschanged");
               // console.log(self.OnVoiceReady);
                if (self.OnVoiceReady != null) {
                    self.OnVoiceReady.call();
                }
                
                
            };
        }*/

        self.default_rv = self.responsivevoices[0];



        //self.OnVoiceReady = null; // OnVoiceReady is meant to be defined externally 


        self.init = function() {
            
            //Disable RV on IOS temporally
            /*if (self.iOS) {
                self.enableFallbackMode();
                return;
            }*/

            //Force Opera to fallback mode
            if (self.is_opera || typeof speechSynthesis === 'undefined') {

                console.log('RV: Voice synthesis not supported');
                self.enableFallbackMode();
                
                

            } else {


                //Waiting a few ms before calling getVoices() fixes some issues with safari on IOS as well as Chrome
                setTimeout(function () {
                    var gsvinterval = setInterval(function () {

                        var v = window.speechSynthesis.getVoices();

                        if (v.length == 0 && (self.systemvoices == null || self.systemvoices.length == 0)) {
                            console.log('Voice support NOT ready');

                            self.voicesupport_attempts++;
                            if (self.voicesupport_attempts > self.VOICESUPPORT_ATTEMPTLIMIT) {
                                
                                clearInterval(gsvinterval);
                                
                                //On IOS, sometimes getVoices is just empty, but speech works. So we use a cached voice collection.
                                if (window.speechSynthesis != null) {
                                    
                                    if (self.iOS) {
                                        
                                        //Determine iOS version:
                                        if (self.iOS9) {
                                            //iOS 9
                                            self.systemVoicesReady(self.cache_ios9_voices);
                                            
                                        }else{
                                            //iOS <9
                                            self.systemVoicesReady(self.cache_ios_voices);
                                            
                                        }
                                        console.log('RV: Voice support ready (cached)');
                                        
                                        
                                    }else{
                                        
                                        console.log("RV: speechSynthesis present but no system voices found");
                                        self.enableFallbackMode();
                                    }
                                    
                                } else {
                                
                                    //We don't support voices. Using fallback
                                    self.enableFallbackMode();
                                }
                            }

                        } else {

                            console.log('RV: Voice support ready');
                            self.systemVoicesReady(v);
                            
                            clearInterval(gsvinterval);

                        }

                    }, 100);
                }, 100);
            }
            
            self.Dispatch("OnLoad");
        }

        self.systemVoicesReady = function(v) {
            self.systemvoices = v;

            self.mapRVs();

            if (self.OnVoiceReady != null)
                self.OnVoiceReady.call();           // TO BE DEPRECATED
            
            self.Dispatch("OnReady");
            if (window.hasOwnProperty('dispatchEvent'))
                window.dispatchEvent(new Event("ResponsiveVoice_OnReady"));
        }

        self.enableFallbackMode = function() {

            self.fallbackMode = true;
            console.log('RV: Enabling fallback mode');

            self.mapRVs();

            if (self.OnVoiceReady != null)
                self.OnVoiceReady.call();           // TO BE DEPRECATED

            self.Dispatch("OnReady");
            if (window.hasOwnProperty('dispatchEvent'))            
                window.dispatchEvent(new Event("ResponsiveVoice_OnReady"));
        }


        self.getVoices = function () {

            //Create voices array

            var v = [];

            for (var i = 0; i < self.responsivevoices.length; i++) {
                v.push({name: self.responsivevoices[i].name});
            }

            return v;

        }


        self.speak = function (text, voicename, parameters) {

            //Cancel previous speech if it's already playing
            if (self.isPlaying()){
                console.log("Cancelling previous speech");
                self.cancel();                
            }
            //Prevent fallbackmode to play more than 1 speech at the same time
            if (self.fallbackMode && self.fallback_audiopool.length>0) {
                self.clearFallbackPool();
            }
            
            //Clean text
            // Quotes " and ` -> '
            text = text.replace(/[\"\`]/gm,"'");
            
            self.msgparameters = parameters ||  {};
            self.msgtext = text;
            self.msgvoicename = voicename;

            self.onstartFired = false;

            //Support for multipart text (there is a limit on characters)
            var multipartText = [];

            if (text.length > self.CHARACTER_LIMIT) {
                   
                var tmptxt = text;

                while (tmptxt.length > self.CHARACTER_LIMIT) {
                    
                    //Split by common phrase delimiters
                    var p = tmptxt.search(/[:!?.;]+/);
                    var part = '';

                    //Coludn't split by priority characters, try commas
                    if (p == -1 || p >= self.CHARACTER_LIMIT) {
                        p = tmptxt.search(/[,]+/);
                    }
                    
                    //Check for spaces. If no spaces then split by 99 characters.
                    if (p== -1) {
                        
                        if (tmptxt.search(' ')==-1)
                            p=99;
                    }
                    
                    //Couldn't split by normal characters, then we use spaces
                    if (p == -1 || p >= self.CHARACTER_LIMIT) {

                        var words = tmptxt.split(' ');

                        for (var i = 0; i < words.length; i++) {

                            if (part.length + words[i].length + 1 > self.CHARACTER_LIMIT)
                                break;

                            part += (i != 0 ? ' ' : '') + words[i];

                        }

                    } else {

                        part = tmptxt.substr(0, p + 1);

                    }

                    tmptxt = tmptxt.substr(part.length, tmptxt.length - part.length);

                    multipartText.push(part);
                    //console.log(part.length + " - " + part);

                }

                //Add the remaining text
                if (tmptxt.length > 0) {
                    multipartText.push(tmptxt);
                }

            } else {

                //Small text
                multipartText.push(text);
            }
            self.multipartText = multipartText;

            //Find system voice that matches voice name
            var rv;

            if (voicename == null) {
                rv = self.default_rv;
            } else {
                rv = self.getResponsiveVoice(voicename);
            }

            var profile = {};




            //Map was done so no need to look for the mapped voice
            if (rv.mappedProfile != null) {

                profile = rv.mappedProfile;

            } else {

                profile.systemvoice = self.getMatchedVoice(rv);
                profile.collectionvoice = {};

                if (profile.systemvoice == null) {
                    console.log('RV: ERROR: No voice found for: ' + voicename);
                    return;
                }
            }


            if (profile.collectionvoice.fallbackvoice == true) {
                self.fallbackMode = true;
                self.fallback_parts = [];
            } else {
                self.fallbackMode = false;
            }
            
            self.msgprofile = profile;
            //console.log("Start multipart play");

            self.utterances=[];

            //Play multipart text
            for (var i = 0; i < multipartText.length; i++) {

                if (!self.fallbackMode) {
                    //Use SpeechSynthesis

                    //Create msg object
                    var msg = new SpeechSynthesisUtterance();
                    msg.voice = profile.systemvoice;
                    msg.voiceURI = profile.systemvoice.voiceURI;
                    msg.volume = self.selectBest([profile.collectionvoice.volume, profile.systemvoice.volume, 1]); // 0 to 1
                    msg.rate = self.selectBest([(self.iOS9?1:null), profile.collectionvoice.rate, profile.systemvoice.rate, 1]); // 0.1 to 10 ** override iOS 0.25 rate
                    msg.pitch = self.selectBest([profile.collectionvoice.pitch, profile.systemvoice.pitch, 1]); //0 to 2*/
                    msg.text = multipartText[i];
                    msg.lang = self.selectBest([profile.collectionvoice.lang, profile.systemvoice.lang]);
                    msg.rvIndex = i;
                    msg.rvTotal = multipartText.length;
                    
                    if (i == 0) {
                        msg.onstart = self.speech_onstart;
                    }        
                    self.msgparameters.onendcalled = false;
                    
                    if (parameters != null) {

                        

                        if (i < multipartText.length - 1 && multipartText.length > 1) {
                            msg.onend = self.onPartEnd;
                            if (msg.hasOwnProperty("addEventListener"))
                                msg.addEventListener('end',self.onPartEnd);
                            
                        } else {
                            msg.onend = self.speech_onend;
                            if (msg.hasOwnProperty("addEventListener"))
                                msg.addEventListener('end',self.speech_onend);
                        }



                        msg.onerror = parameters.onerror || function (e) {
                            console.log('RV: Unknow Error');
                            console.log(e);
                        };
                        
                        msg.onpause = parameters.onpause;
                        msg.onresume = parameters.onresume;
                        msg.onmark = parameters.onmark;
                        msg.onboundary = parameters.onboundary || self.onboundary;
                        msg.pitch = parameters.pitch!=null?parameters.pitch:msg.pitch;
                        if (self.iOS) {
                            msg.rate = (parameters.rate!=null?(parameters.rate*parameters.rate):1) * msg.rate;
                        }else{
                            msg.rate = (parameters.rate!=null?parameters.rate:1) * msg.rate;
                        }
                        
                        msg.volume = parameters.volume!=null?parameters.volume:msg.volume;
                        
                        
                    } else {
                        msg.onend = self.speech_onend;
                        msg.onerror = function (e) {
                            console.log('RV: Unknow Error');
                            console.log(e);
                        };
                    }
                    
                    self.utterances.push(msg);
                    if (i==0)
                        self.currentMsg = msg;
                    
                    console.log(msg);				
                    //setTimeout(function(){
                    //speechSynthesis.speak(msg);
                    //},0);
                    self.tts_speak(msg);

                } else {
                    
                    self.fallback_playbackrate = self.def_fallback_playbackrate;
                    
                    var pitch = self.selectBest([profile.collectionvoice.pitch, profile.systemvoice.pitch, 1]) //0 to 2*/
                    var rate = self.selectBest([ (self.iOS9?1:null), profile.collectionvoice.rate, profile.systemvoice.rate, 1]) ; // 0.1 to 10 ** override iOS 0.25 rate
                    var volume = self.selectBest([profile.collectionvoice.volume, profile.systemvoice.volume, 1]); // 0 to 1
                    
                    if (parameters != null) {
                        pitch = (parameters.pitch!=null?parameters.pitch:1) * pitch;
                        rate = (parameters.rate!=null?parameters.rate:1) * rate;
                        volume = (parameters.volume!=null?parameters.volume:1) * volume;
                    }
                    pitch /= 2;
                    rate /=2;
                    volume *=2;
                    pitch = Math.min(Math.max(pitch, 0), 1);
                    rate = Math.min(Math.max(rate, 0), 1);
                    volume = Math.min(Math.max(volume, 0), 1);                    
                    //console.log(volume);
                    //self.fallback_playbackrate = pitch;                    
                    
                    var url = self.fallbackServicePath + '?t=' + encodeURIComponent(multipartText[i]) + '&tl=' + (profile.collectionvoice.lang || profile.systemvoice.lang || 'en-US') + '&sv=' + (profile.collectionvoice.service || profile.systemvoice.service || '') + '&vn=' + (profile.collectionvoice.voicename || profile.systemvoice.voicename || '') + '&pitch=' + pitch.toString()+ '&rate=' + rate.toString() + '&vol=' + volume.toString();
                            
                    
                    var audio = document.createElement("AUDIO");
                    audio.src = url;
                    audio.playbackRate = self.fallback_playbackrate;
                    audio.preload = 'auto';
                    audio.load(); // android doesn't allow playing audio without an user action. this initializes all audio chunks at first action so restriction is removed.
                    //audio.volume = volume ||profile.collectionvoice.volume || profile.systemvoice.volume || 1; // 0 to 1;
                    self.fallback_parts.push(audio);
                            //console.log(audio);


                }


            }

            if (self.fallbackMode) {


                self.fallback_part_index = 0;
                self.fallback_startPart();

            }

        }

        self.startTimeout = function (text, callback) {
            
           //if (self.iOS) {
            //   multiplier = 0.5;
           //}

           var multiplier = self.msgprofile.collectionvoice.timerSpeed;
           if (self.msgprofile.collectionvoice.timerSpeed==null)
               multiplier = 1;
            
           //console.log(self.msgprofile.collectionvoice.name);
           if (multiplier <=0)
               return;
           
           var words = text.split(/\s+/).length;
           var chars = (text.match(/[^ ]/igm) || text).length;
           var wlf = (chars/words) / 5.1;    //word length factor: 5.1 is the average word length in english.
           
           var length = multiplier * 1000 * (60 / self.WORDS_PER_MINUTE) * wlf * words; //avg 140 words per minute speech time
           
           if (words<3) {
               length = 4000;
           }
           
           if (length < 3000)
               length = 3000;
           
            self.timeoutId = setTimeout(callback, length); 
            //console.log("Timeout " + self.timeoutId + " started: " + length);            
        }

        self.checkAndCancelTimeout = function () {
            if (self.timeoutId != null) {
                //console.log("Timeout " + self.timeoutId + " cancelled");
                clearTimeout(self.timeoutId);
                self.timeoutId = null;
            }
        }

        self.speech_timedout = function() {
            //console.log("Speech cancelled: Timeout " + self.timeoutId + " ended");
            self.cancel();
            self.cancelled = false;
            //if (!self.iOS) //On iOS, cancel calls msg.onend 
                self.speech_onend();
            
        }

        self.speech_onend = function () {
            self.checkAndCancelTimeout();
            
            //Avoid this being automatically called just after calling speechSynthesis.cancel
            if (self.cancelled === true) {
                self.cancelled = false;
                return;
            }
            
            //console.log("on end fired");
            if (self.msgparameters != null && self.msgparameters.onend != null && self.msgparameters.onendcalled!=true) {
                //console.log("Speech on end called  -" + self.msgtext);
                self.msgparameters.onendcalled=true;
                self.msgparameters.onend();
                
            } 

        }

        self.speech_onstart = function () {
            //Start can be triggered after onboundary!
            if (self.onstartFired) return
            
            self.onstartFired = true;
            //if (!self.iOS)
            //console.log("Speech start");
            if (self.iOS || self.is_safari || self.useTimer) {
                if (!self.fallbackMode)
                    self.startTimeout(self.msgtext,self.speech_timedout);
                    
            }
                
            
            self.msgparameters.onendcalled=false;
            if (self.msgparameters != null && self.msgparameters.onstart != null) {
                self.msgparameters.onstart();
            }

        }



        self.fallback_startPart = function () {

            if (self.fallback_part_index == 0) {
                self.speech_onstart();
            }
            
            self.fallback_audio = self.fallback_parts[self.fallback_part_index];
            
            if (self.fallback_audio == null) {

                //Fallback audio is not working. Just wait for the timeout event
                console.log("RV: Fallback Audio is not available");

            } else {

                
                var audio = self.fallback_audio;
                
                //Add to pool to prevent multiple streams to be played at the same time
                self.fallback_audiopool.push(audio);
                
                setTimeout(function(){audio.playbackRate = self.fallback_playbackrate;},50)
                audio.onloadedmetadata = function() {
                    audio.play();
                    audio.playbackRate = self.fallback_playbackrate;
                }                
                self.fallback_audio.play();
                self.fallback_audio.addEventListener('ended', self.fallback_finishPart);
                    
                if (self.useTimer)
                    self.startTimeout(self.multipartText[self.fallback_part_index],self.fallback_finishPart);
                
            }
        }

        self.fallback_finishPart = function (e) {
                
            self.checkAndCancelTimeout();

            if (self.fallback_part_index < self.fallback_parts.length - 1) {
                //console.log('chunk ended');
                self.fallback_part_index++;
                self.fallback_startPart();

            } else {
                //console.log('msg ended');
                self.speech_onend();

            }

        }


        self.cancel = function () {

            self.checkAndCancelTimeout();

            if (self.fallbackMode){
                if (self.fallback_audio!=null)
                    self.fallback_audio.pause();
                self.clearFallbackPool();
            }else{
                self.cancelled = true;
                speechSynthesis.cancel();

            }
        }


        self.voiceSupport = function () {

            return ('speechSynthesis' in window);

        }

        self.OnFinishedPlaying = function (event) {
            //console.log("OnFinishedPlaying");
            if (self.msgparameters != null) {
                if (self.msgparameters.onend != null)
                    self.msgparameters.onend();
            }

        }

        //Set default voice to use when no voice name is supplied to speak()
        self.setDefaultVoice = function (voicename) {

            var rv = self.getResponsiveVoice(voicename);

            if (rv != null) {
                self.default_rv = rv;
            }

        }

        //Map responsivevoices to system voices
        self.mapRVs = function() {

            for (var i = 0; i < self.responsivevoices.length; i++) {

                var rv = self.responsivevoices[i];

                for (var j = 0; j < rv.voiceIDs.length; j++) {

                    var vcoll = self.voicecollection[rv.voiceIDs[j]];

                    if (vcoll.fallbackvoice != true) {		// vcoll.fallbackvoice would be null instead of false

                        // Look on system voices
                        var v = self.getSystemVoice(vcoll.name);
                        if (v != null) {
                            rv.mappedProfile = {
                                systemvoice: v,
                                collectionvoice: vcoll
                            };
                            //console.log("Mapped " + rv.name + " to " + v.name);
                            break;
                        }

                    } else {

                        //Pick the fallback voice
                        rv.mappedProfile = {
                            systemvoice: {},
                            collectionvoice: vcoll
                        };
                        //console.log("Mapped " + rv.name + " to " + vcoll.lang + " fallback voice");
                        break;

                    }
                }
            }


        }


        //Look for the voice in the system that matches the one in our collection
        self.getMatchedVoice = function(rv) {

            for (var i = 0; i < rv.voiceIDs.length; i++) {
                var v = self.getSystemVoice(self.voicecollection[rv.voiceIDs[i]].name);
                if (v != null)
                    return v;
            }

            return null;

        }

        self.getSystemVoice = function(name) {

            if (typeof self.systemvoices === 'undefined' || self.systemvoices === null)
                return null;

            for (var i = 0; i < self.systemvoices.length; i++) {
                if (self.systemvoices[i].name == name)
                    return self.systemvoices[i];
            }

            //Not found by name. Try lang (iOS9) -- mixes up chrome voices with android voices
            /*for (var i = 0; i < self.systemvoices.length; i++) {
                if (self.systemvoices[i].lang == name)
                    return self.systemvoices[i];
            }*/

            return null;

        }

        self.getResponsiveVoice = function(name) {

            for (var i = 0; i < self.responsivevoices.length; i++) {
                if (self.responsivevoices[i].name == name) {
                    return self.responsivevoices[i];
                }
            }

            return null;

        }
        
        self.Dispatch = function(name) {
            //console.log("Dispatching " +name);
            if (self.hasOwnProperty(name + "_callbacks") && 
                self[name + "_callbacks"] != null &&     
                self[name + "_callbacks"].length > 0) {
                var callbacks = self[name + "_callbacks"];
                for(var i=0; i<callbacks.length; i++) {
                    callbacks[i]();
                }
                //console.log("Dispatched " + name);
                return true;
            }else {
                //Try calling a few ms later
                var timeoutName = name + "_callbacks_timeout";
                var timeoutCount = name + "_callbacks_timeoutCount";
                if (self.hasOwnProperty(timeoutName)) {
                    
                }else{
                    //console.log("Setting up timeout for " + name);
                    self[timeoutCount] = 10;
                    self[timeoutName] = setInterval(function() {
                        //console.log("Timeout function for " + name)
                        self[timeoutCount] = self[timeoutCount] - 1;
                        
                        if (self.Dispatch(name) || self[timeoutCount]<0) {
                            clearTimeout(self[timeoutName]);
                            //if (self[timeoutCount]<0) console.log("Timeout ran out");
                        } else{
                           //console.log("Keep waiting..." + name);
                        }
                    },50);
                }
                
                
                //console.log("not found");
                return false;
            }
        }
        
        self.AddEventListener = function(name,callback) {
            if (!self.hasOwnProperty(name + "_callbacks")) {
                self[name + "_callbacks"] = [];
            }
            self[name + "_callbacks"].push(callback);
        }
        
        self.addEventListener = self.AddEventListener;
        
        //Event to initialize speak on iOS
        self.clickEvent = function() {
            if (self.iOS && !self.iOS_initialized) {
                self.speak(" ");
                self.iOS_initialized = true;
            }
        }
        
        
        self.isPlaying = function() {
            if (self.fallbackMode) {
                
                return  (self.fallback_audio!=null &&
                        !self.fallback_audio.ended &&
                        !self.fallback_audio.paused);
                
            }else{
                
                return speechSynthesis.speaking;
                
            }
        }
        
        self.clearFallbackPool = function() {
            
            for (var i=0; i<self.fallback_audiopool.length; i++) {
                
                if (self.fallback_audiopool[i]!=null) {
                    self.fallback_audiopool[i].pause();
                    self.fallback_audiopool[i].src='';
                    //self.fallback_audiopool[i].parentElement.removeChild(self.fallback_audiopool[i]);
                }
            }
            self.fallback_audiopool = [];
        }
        
        if(document.readyState === "complete") {
            //Already loaded
            self.init();
        }else {
            document.addEventListener('DOMContentLoaded', function () {
                self.init();
            });
        }
        
      

        self.selectBest = function(a) {
            
            for(var i=0; i<a.length; i++) {
                if (a[i]!=null) return a[i];
            }
            return null;
        }


        self.pause = function() {
            
            if (self.fallbackMode) {
                if (self.fallback_audio!=null) {
                    self.fallback_audio.pause();
                }
            }else{
                speechSynthesis.pause();
            }
        
        }
        
        self.resume = function() {
            if (self.fallbackMode) {
                if (self.fallback_audio!=null) {
                    self.fallback_audio.play();
                }
            }else{
                speechSynthesis.resume();
            }           
            
        }
        
        self.tts_speak = function(msg) {
            
            setTimeout(function(){
                self.cancelled = false;
                speechSynthesis.speak(msg);
            },0.01);
            
        }
        
        self.setVolume = function(v) {
            
            if (self.isPlaying()) {
                if (self.fallbackMode) {
                    for (var i=0; i<self.fallback_parts.length; i++) {
                        self.fallback_parts[i].volume = v;
                    }
                    for (var i=0; i<self.fallback_audiopool.length; i++) {
                        self.fallback_audiopool[i].volume = v;
                    }                    
                    self.fallback_audio.volume = v;
                }else{
                    for (var i=0; i<self.utterances.length; i++) {
                        self.utterances[i].volume = v;
                    }
                }
            }
        }
        
        self.onPartEnd = function(e) {
            
            if (self.msgparameters!=null && self.msgparameters.onchuckend!=null) {
                self.msgparameters.onchuckend();
            }
            
            self.Dispatch("OnPartEnd");
            
            var i = self.utterances.indexOf(e.utterance);
            self.currentMsg = self.utterances[i+1];
            
        }
        
        self.onboundary = function(e) {
            
            console.log("On Boundary");
            
            //on iOS on boundary sometimes will be fired when start hasn't. We use this as a false start.
            if (self.iOS && !self.onstartFired) {
                self.speech_onstart();
            }
            
        }

    }
    var responsiveVoice = new ResponsiveVoice();
}
