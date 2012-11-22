function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function popup_alert(element, callback) {
    $(element).dialog({
        autoopen: false,
        model: true,
        buttons: {
            '确定': function() {
                callback();
                $(this).dialog('close');
            },
            '取消': function() {
                $(this).dialog('close');
            },
        },
    });
}
