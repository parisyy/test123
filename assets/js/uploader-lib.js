function upload_file(element, callback) {
    new AjaxUpload(element, {
        action: '/uploader',
        data: {
            _xsrf: getCookie('_xsrf'),
        },
        onComplete: function(file, response) {
            response = JSON.parse(response);
            if (response["code"] == 0) {
                callback(file, response);
            } else {
                alert(response["error"] + '\n\n上传图片失败！');
            }
        },
    });
}

function upload_avatar(element, uid, callback) {
    new AjaxUpload(element, {
        action: '/avatar_uploader',
        data: {
            _xsrf: getCookie('_xsrf'),
            uid: uid,
        },
        onComplete: function(file, response) {
            response = JSON.parse(response);
            if (response["code"] == 0) {
                callback(file, response);
            } else {
                alert(response["error"] + '\n\n上传图片失败！');
            }
        },
    });
}
