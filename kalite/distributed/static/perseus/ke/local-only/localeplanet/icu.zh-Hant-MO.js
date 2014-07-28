(function() {

	var dfs = {"am_pm":["上午","下午"],"day_name":["星期日","星期一","星期二","星期三","星期四","星期五","星期六"],"day_short":["週日","週一","週二","週三","週四","週五","週六"],"era":["西元前","西元"],"era_name":["西元前","西元"],"month_name":["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"],"month_short":["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"],"order_full":"YMD","order_long":"YMD","order_medium":"YMD","order_short":"YMD"};
	var nfs = {"decimal_separator":".","grouping_separator":",","minus":"-"};
	var df = {SHORT_PADDED_CENTURY:function(d){if(d){return(d.getFullYear()+'-'+((d.getMonth()+101)+'').substring(1)+'-'+((d.getDate()+101)+'').substring(1));}},SHORT:function(d){if(d){return((d.getFullYear()+'').substring(2)+'-'+(d.getMonth()+1)+'-'+d.getDate());}},SHORT_NOYEAR:function(d){if(d){return((d.getMonth()+1)+'-'+d.getDate());}},SHORT_NODAY:function(d){if(d){return((d.getFullYear()+'').substring(2)+'-'+(d.getMonth()+1));}},MEDIUM:function(d){if(d){return(d.getFullYear()+'-'+(d.getMonth()+1)+'-'+d.getDate());}},MEDIUM_NOYEAR:function(d){if(d){return((d.getMonth()+1)+'-'+d.getDate());}},MEDIUM_WEEKDAY_NOYEAR:function(d){if(d){return(dfs.day_short[d.getDay()]+' '+(d.getMonth()+1)+'-'+d.getDate());}},LONG_NODAY:function(d){if(d){return(d.getFullYear()+'年'+(d.getMonth()+1));}},LONG:function(d){if(d){return(d.getFullYear()+'年'+(d.getMonth()+1)+'月'+d.getDate()+'日');}},FULL:function(d){if(d){return(d.getFullYear()+'年'+(d.getMonth()+1)+'月'+d.getDate()+'日'+' '+dfs.day_name[d.getDay()]);}}};
	
	window.icu = window.icu || new Object();
	var icu = window.icu;	
		
	icu.getCountry = function() { return "MO" };
	icu.getCountryName = function() { return "中華人民共和國澳門特別行政區" };
	icu.getDateFormat = function(formatCode) { var retVal = {}; retVal.format = df[formatCode]; return retVal; };
	icu.getDateFormats = function() { return df; };
	icu.getDateFormatSymbols = function() { return dfs; };
	icu.getDecimalFormat = function(places) { var retVal = {}; retVal.format = function(n) { var ns = n < 0 ? Math.abs(n).toFixed(places) : n.toFixed(places); var ns2 = ns.split('.'); s = ns2[0]; var d = ns2[1]; var rgx = /(\d+)(\d{3})/;while(rgx.test(s)){s = s.replace(rgx, '$1' + nfs["grouping_separator"] + '$2');} return (n < 0 ? nfs["minus"] : "") + s + nfs["decimal_separator"] + d;}; return retVal; };
	icu.getDecimalFormatSymbols = function() { return nfs; };
	icu.getIntegerFormat = function() { var retVal = {}; retVal.format = function(i) { var s = i < 0 ? Math.abs(i).toString() : i.toString(); var rgx = /(\d+)(\d{3})/;while(rgx.test(s)){s = s.replace(rgx, '$1' + nfs["grouping_separator"] + '$2');} return i < 0 ? nfs["minus"] + s : s;}; return retVal; };
	icu.getLanguage = function() { return "zh" };
	icu.getLanguageName = function() { return "中文" };
	icu.getLocale = function() { return "zh-Hant-MO" };
	icu.getLocaleName = function() { return "中文（繁體中文，中華人民共和國澳門特別行政區）" };

})();