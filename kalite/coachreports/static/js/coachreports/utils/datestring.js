var date_string = function(date) {
    if (date) {
        return date.getFullYear() + "/" + (date.getMonth() + 1) + "/" + date.getDate();
    }
};

module.exports = {
	date_string: date_string
};